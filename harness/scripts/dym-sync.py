#!/usr/bin/env python3
"""dym-sync — bundle /doyourmagic dưới .overstack/doyourmagic/ ↔ kho rheinmir/dym.

Một file, stdlib, 0 token. Sáu việc:
  lint     [bundle]                 mọi bundle phải ở DẠNG SKILL: skills/<hub>/SKILL.md (+domains) và sub-skill. rc 1 nếu lệch.
  migrate  <bundle> --domains a,b   dạng cũ NN-*.md → skills/<hub>-<slug>/SKILL.md + hub. Tất định, giữ nguyên thân.
  index                             sinh meta-hub .overstack/doyourmagic/dym/SKILL.md: bảng domain → hub → slug (1 dòng context).
  install  [dym|<bundle>] [--auto slug,..]  symlink vào .claude/skills/ — hub luôn; slug --auto thì bỏ disable-model-invocation (agent tự nạp).
  check    [--yes] [--json]         so đĩa ↔ baseline ↔ dym (clone --depth 1 vào tmp). rc 0 sạch · 3 có việc cần quyết.
  push     <bundle> [--yes]         copy vào clone dym → nhánh → commit → PR (gh). Ghi baseline.
  --selftest

Baseline: <bundle>/.dym-baseline.json {remote, commit, tree} ghi lúc push/pull → phân biệt
"mình sửa local" với "dym có bản mới". Chưa có baseline → chỉ so được đĩa ↔ dym.
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

DYM_REMOTE = os.environ.get("DYM_REMOTE", "https://github.com/Rheinmir/dym.git")
BUNDLES_REL = Path(".overstack/doyourmagic")
BASELINE = ".dym-baseline.json"
SKIP = {BASELINE, ".DS_Store"}


def root_of(p="."):
    r = Path(p).resolve()
    for c in [r, *r.parents]:
        if (c / BUNDLES_REL).is_dir() or (c / ".git").exists():
            return c
    return r


def bundles(root):
    d = root / BUNDLES_REL
    return sorted(p for p in d.iterdir() if p.is_dir() and p.name != "dym") if d.is_dir() else []


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip().strip('"')
            fm[k.strip()] = [x.strip() for x in v.strip("[]").split(",") if x.strip()] if k.strip() == "domains" else v
    return fm


def hub_of(b):
    """(hub_dir, fm) — thư mục skills/<hub> là cái KHÔNG có dấu '-' sau tiền tố chung."""
    sk = b / "skills"
    if not sk.is_dir():
        return None, {}
    dirs = sorted(p for p in sk.iterdir() if (p / "SKILL.md").is_file())
    names = [p.name for p in dirs]
    for p in dirs:  # hub = tiền tố của ít nhất một dir khác, và không là hậu tố của dir nào
        if any(n.startswith(p.name + "-") for n in names) and not any(p.name.startswith(n + "-") for n in names):
            return p, frontmatter((p / "SKILL.md").read_text(encoding="utf-8"))
    return None, {}


def tree_hash(d):
    h = hashlib.sha256()
    for p in sorted(x for x in d.rglob("*") if x.is_file() and x.name not in SKIP and ".git" not in x.parts):
        h.update(str(p.relative_to(d)).encode()); h.update(p.read_bytes())
    return h.hexdigest()[:16]


# ---------------- lint ----------------
def cmd_lint(a):
    root = root_of(a.root); bad = 0
    for b in bundles(root):
        if a.bundle and b.name != a.bundle:
            continue
        hub, fm = hub_of(b)
        if not hub:
            print(f"✗ {b.name}: dạng cũ — thiếu skills/<hub>/SKILL.md  → dym-sync.py migrate {b.name} --domains ..."); bad += 1; continue
        if not fm.get("domains"):
            print(f"✗ {b.name}: hub {hub.name} thiếu `domains:` → agent không định tuyến được"); bad += 1
        for s in sorted(hub.parent.iterdir()):
            if s == hub or not s.is_dir():
                continue
            sfm = frontmatter((s / "SKILL.md").read_text(encoding="utf-8")) if (s / "SKILL.md").is_file() else {}
            if not sfm.get("name") or not sfm.get("description"):
                print(f"✗ {b.name}: {s.name}/SKILL.md thiếu name/description"); bad += 1
        if not bad:
            print(f"✓ {b.name}: hub {hub.name} · domains {','.join(fm['domains'])}")
    return 1 if bad else 0


# ---------------- migrate ----------------
def _title_desc(text):
    lines = text.splitlines()
    title = next((re.sub(r"^#\s*\d*\s*[—-]?\s*", "", l).strip() for l in lines if l.startswith("# ")), "")
    why = next((re.sub(r"\*\*Vì sao dùng:\*\*\s*", "", l).strip() for l in lines if "Vì sao dùng" in l), "")
    if not why:
        why = next((l.strip() for l in lines[1:] if l.strip() and not l.startswith(("#", ">", "|", "```", "-"))), "")
    return title, re.sub(r"[`*]", "", why)[:220]


def _source_of(b):
    wf = (b / "workflows.md").read_text(encoding="utf-8", errors="replace") if (b / "workflows.md").is_file() else ""
    m = re.search(r"repo `([^`]+)`", wf) or re.search(r"(git@github\.com:[^\s`]+|https://github\.com/[^\s`)]+)", wf)
    return m.group(1) if m else ""


def cmd_migrate(a):
    root = root_of(a.root); b = root / BUNDLES_REL / a.bundle
    if not b.is_dir():
        sys.exit(f"không có bundle {b}")
    hub = a.hub or f"dym-{a.bundle}"
    docs = sorted(p for p in b.glob("[0-9][0-9]-*.md"))
    if not docs:
        sys.exit(f"{a.bundle}: không có NN-*.md để migrate")
    sk = b / "skills"; rows = []
    for d in docs:
        slug = re.sub(r"^\d+-", "", d.stem)
        text = d.read_text(encoding="utf-8")
        title, desc = _title_desc(text)
        name = f"{hub}-{slug}"
        body = re.sub(r"^# .*\n", f"# Skill: {name} — {title}\n", text, count=1, flags=re.M)
        out = sk / name / "SKILL.md"; out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f'---\nname: {name}\ndescription: "{title}. {desc}"\ndisable-model-invocation: true\n---\n\n{body}', encoding="utf-8")
        rows.append((slug, title))
        if not a.keep:
            subprocess.run(["git", "-C", str(root), "rm", "-q", "--cached", str(d)], capture_output=True); d.unlink()
    src = _source_of(b)
    table = "\n".join(f"   | `{s}` | {t} |" for s, t in rows)
    hubmd = f'''---
name: {hub}
disable-model-invocation: true
domains: [{", ".join(a.domains.split(","))}]
source: {src}
description: "{a.bundle} ({src or 'tool ngoài'}) — workflow đã kiểm chứng. Gõ /{hub} <slug>. slugs: {" · ".join(s for s, _ in rows)}"
---

# Skill: {hub} — hub workflow cho {a.bundle}

## When to use
- User gõ `/{hub}` (không tham số → bảng slug) hoặc `/{hub} <slug>`; hoặc `/dym` định tuyến tới đây theo domain.
- Hub chỉ tốn dòng description; thân workflow con chỉ đọc khi được gọi.

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi dừng, không đọc file nào.

   | slug | mục đích |
   |---|---|
{table}

2. Tìm file con theo thứ tự, lấy file ĐẦU TIÊN tồn tại rồi đọc ĐÚNG MỘT file:
   (1) `../{hub}-<slug>/SKILL.md` (cạnh hub — cài qua `npx skills add rheinmir/dym`);
   (2) `.overstack/doyourmagic/{a.bundle}/skills/{hub}-<slug>/SKILL.md` (bundle trong dự án);
   (3) `.claude/skills/{hub}-<slug>/SKILL.md`.
   Làm theo Steps/Rules của file đó; không đọc file con khác; không thấy cả 3 → nói rõ, dừng.

## Rules
- Mỗi sub-skill tự chứa; hub không nhồi cả bundle vào context.
- `workflows.md` cạnh bundle là chỉ mục + bảng kiểm chứng, không phải nguồn lệnh.
'''
    (sk / hub).mkdir(parents=True, exist_ok=True)
    (sk / hub / "SKILL.md").write_text(hubmd, encoding="utf-8")
    print(f"✓ {a.bundle}: hub {hub} + {len(rows)} sub-skill · domains {a.domains}")
    return 0


# ---------------- index (meta-hub /dym) ----------------
def cmd_index(a):
    root = root_of(a.root); bydom = {}; rows = []
    for b in bundles(root):
        hub, fm = hub_of(b)
        if not hub:
            continue
        slugs = sorted(p.name[len(hub.name) + 1:] for p in hub.parent.iterdir() if p.name.startswith(hub.name + "-"))
        rows.append((b.name, hub.name, fm.get("domains", []), slugs, fm.get("source", "")))
        for d in fm.get("domains", []):
            bydom.setdefault(d, []).append(hub.name)
    doms = sorted(bydom)
    table = "\n".join(f"| {d} | {' · '.join(f'`{h}`' for h in bydom[d])} |" for d in doms)
    detail = "\n".join(f"| `{h}` | {b} | {', '.join(dm)} | {' · '.join(s)} |" for b, h, dm, s, _ in rows)
    md = f'''---
name: dym
description: "Tool ngoài ĐÃ KIỂM CHỨNG, chọn theo domain: {" · ".join(doms)}. Gọi khi việc thuộc một domain đó (vd vẽ chart → lieflat-charts, frontend → impeccable) và skill canonical chưa phủ; gõ /dym <domain> hoặc /dym."
---

# Skill: dym — định tuyến domain → bundle tool ngoài

Sinh bởi `harness/scripts/dym-sync.py index` từ `domains:` trong hub của từng bundle. **Không sửa tay** — sửa `domains:` ở hub rồi chạy lại.

## Steps
1. Xác định domain của việc đang làm (bảng 1). Nhiều hub cùng domain → đọc bảng 2, chọn theo slug khớp việc; vẫn phân vân → hỏi user một câu.
2. Đọc ĐÚNG MỘT hub: `.overstack/doyourmagic/<bundle>/skills/<hub>/SKILL.md`, rồi làm theo nó (hub sẽ chỉ tới sub-skill).
3. Frontend/UI: `hallmark` vẫn là SÀN, bundle chỉ là flavour bên trên.

## Bảng 1 — domain → hub
| domain | hub |
|---|---|
{table}

## Bảng 2 — hub → slug
| hub | bundle | domains | slugs |
|---|---|---|---|
{detail}
'''
    out = root / BUNDLES_REL / "dym" / "SKILL.md"; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"✓ meta-hub {out.relative_to(root)}: {len(rows)} hub · {len(doms)} domain: {', '.join(doms)}")
    return 0


# ---------------- install ----------------
def cmd_install(a):
    root = root_of(a.root); dst = root / ".claude/skills"; dst.mkdir(parents=True, exist_ok=True)
    def link(name, target):
        l = dst / name
        if l.is_symlink() or l.exists():
            l.unlink() if l.is_symlink() else shutil.rmtree(l)
        l.symlink_to(os.path.relpath(target, dst)); print(f"  {l.relative_to(root)} → {target.relative_to(root)}")
    if a.bundle in (None, "dym"):
        link("dym", root / BUNDLES_REL / "dym")
        if a.bundle == "dym":
            return 0
    for b in bundles(root):
        if a.bundle and b.name != a.bundle:
            continue
        hub, _ = hub_of(b)
        if not hub:
            print(f"  bỏ qua {b.name}: chưa migrate"); continue
        link(hub.name, hub)
        for slug in (a.auto.split(",") if a.auto else []):
            s = hub.parent / f"{hub.name}-{slug}"
            if not s.is_dir():
                print(f"  ✗ không có slug {slug}"); continue
            p = s / "SKILL.md"; p.write_text(p.read_text(encoding="utf-8").replace("disable-model-invocation: true\n", ""), encoding="utf-8")
            link(s.name, s); print(f"    auto-nạp: {s.name} (description là trigger)")
    return 0


# ---------------- check / push ----------------
def _clone(tmp, timeout=20):
    r = subprocess.run(["git", "clone", "-q", "--depth", "1", DYM_REMOTE, tmp], capture_output=True, text=True, timeout=timeout)
    if r.returncode:
        raise RuntimeError(r.stderr.strip()[:200])
    return subprocess.run(["git", "-C", tmp, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def classify(local, remote, base):
    """3 mốc: L=đĩa R=dym B=baseline (None = chưa có). Trả (nhãn, hành động)."""
    if remote is None:
        return "NEW-LOCAL", "push"
    if local == remote:
        return "SAME", ""
    if base is None:
        return "DIFF-NO-BASELINE", "xem diff rồi push/pull"
    if local == base:
        return "REMOTE-AHEAD", "pull"
    if remote == base:
        return "LOCAL", "push"
    return "CONFLICT", "hợp nhất tay"


def cmd_check(a):
    root = root_of(a.root); rows = []
    with tempfile.TemporaryDirectory() as tmp:
        try:
            commit = _clone(tmp)
        except Exception as e:  # mạng — fail-open, không chặn ai
            print(f"dym-sync: không clone được dym ({e}) — bỏ qua"); return 0
        for b in bundles(root):
            rb = Path(tmp) / b.name
            bl = json.loads((b / BASELINE).read_text()) if (b / BASELINE).is_file() else {}
            lab, act = classify(tree_hash(b), tree_hash(rb) if rb.is_dir() else None, bl.get("tree"))
            rows.append((b.name, lab, act))
    if a.json:
        print(json.dumps({"commit": commit, "bundles": [dict(zip(("bundle", "state", "action"), r)) for r in rows]}, ensure_ascii=False)); return 0
    todo = [r for r in rows if r[2]]
    for n, lab, act in rows:
        print(f"  {'✓' if not act else '⚑'} {n:<26} {lab:<18} {act}")
    if not todo:
        print("dym-sync: đồng bộ với dym"); return 0
    pushable = [n for n, lab, act in rows if act == "push"]
    if pushable and (a.yes or (sys.stdin.isatty() and input(f"đẩy {len(pushable)} bundle lên dym ({', '.join(pushable)})? [y/N] ").lower() == "y")):
        for n in pushable:
            cmd_push(argparse.Namespace(root=a.root, bundle=n, yes=True))
        return 0
    print(f"dym-sync: {len(todo)} bundle cần quyết → dym-sync.py push <bundle>  |  check --yes để đẩy hết"); return 3


def cmd_push(a):
    root = root_of(a.root); b = root / BUNDLES_REL / a.bundle
    if not b.is_dir():
        sys.exit(f"không có bundle {a.bundle}")
    if not a.yes and sys.stdin.isatty() and input(f"đẩy {a.bundle} lên {DYM_REMOTE}? [y/N] ").lower() != "y":
        return 3
    with tempfile.TemporaryDirectory() as tmp:
        commit = _clone(tmp)
        dst = Path(tmp) / a.bundle
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(b, dst, ignore=shutil.ignore_patterns(*SKIP))
        br = f"dym/{a.bundle}"
        def g(*x): return subprocess.run(["git", "-C", tmp, *x], capture_output=True, text=True)
        g("checkout", "-q", "-B", br); g("add", "-A")
        if not g("status", "--porcelain").stdout.strip():
            print(f"  {a.bundle}: không khác dym"); return 0
        g("commit", "-q", "-m", f"bundle {a.bundle}: đồng bộ từ dự án ({tree_hash(b)})")
        r = g("push", "-q", "-f", "origin", br)
        if r.returncode:
            print(r.stderr.strip()[:300]); return 1
        repo = "/".join(DYM_REMOTE.replace(".git", "").rstrip("/").split("/")[-2:])
        pr = subprocess.run(["gh", "pr", "create", "--repo", repo, "--head", br, "--fill"], capture_output=True, text=True, cwd=tmp)
        if pr.returncode == 0:
            tail = f" · PR {pr.stdout.strip()}"
        elif "already exists" in pr.stderr:
            tail = " · PR đã có, nhánh vừa cập nhật"
        else:
            tail = f" · gh pr: {pr.stderr.strip()[:120]}"
        print(f"  ✓ {a.bundle} → nhánh {br}{tail}")
    (b / BASELINE).write_text(json.dumps({"remote": DYM_REMOTE, "commit": commit, "tree": tree_hash(b)}, indent=1))
    return 0


# ---------------- selftest ----------------
def selftest():
    assert classify("a", None, None) == ("NEW-LOCAL", "push")
    assert classify("a", "a", None)[0] == "SAME"
    assert classify("a", "b", None)[0] == "DIFF-NO-BASELINE"
    assert classify("a", "b", "a") == ("REMOTE-AHEAD", "pull")
    assert classify("b", "a", "a") == ("LOCAL", "push")
    assert classify("b", "c", "a")[0] == "CONFLICT"
    with tempfile.TemporaryDirectory() as d:
        r = Path(d); b = r / BUNDLES_REL / "foo"; b.mkdir(parents=True)
        (b / "workflows.md").write_text("# foo\n\nSinh từ repo `x/foo` (commit abc)\n")
        (b / "01-install.md").write_text("# 01 — Cài đặt\n\n**Vì sao dùng:** để có `foo`.\n\n## Steps\n- a\n")
        (b / "02-run.md").write_text("# 02 — Chạy\n\nChạy thật.\n")
        assert cmd_lint(argparse.Namespace(root=d, bundle=None)) == 1
        cmd_migrate(argparse.Namespace(root=d, bundle="foo", domains="chart,report", hub=None, keep=False))
        hub, fm = hub_of(b); assert hub.name == "dym-foo" and fm["domains"] == ["chart", "report"] and fm["source"] == "x/foo"
        sub = (b / "skills/dym-foo-install/SKILL.md").read_text()
        assert "name: dym-foo-install" in sub and "để có foo" in sub and "# Skill: dym-foo-install — Cài đặt" in sub
        assert not (b / "01-install.md").exists() and cmd_lint(argparse.Namespace(root=d, bundle=None)) == 0
        cmd_index(argparse.Namespace(root=d)); meta = (r / BUNDLES_REL / "dym/SKILL.md").read_text()
        assert "| chart | `dym-foo` |" in meta and "install · run" in meta
        cmd_install(argparse.Namespace(root=d, bundle="foo", auto="run"))
        assert (r / ".claude/skills/dym-foo").is_symlink() and "disable-model" not in (b / "skills/dym-foo-run/SKILL.md").read_text()
        h1 = tree_hash(b); (b / "workflows.md").write_text("x"); assert tree_hash(b) != h1
    print("dym-sync selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--selftest", action="store_true")
    sp = ap.add_subparsers(dest="cmd")
    p = sp.add_parser("lint"); p.add_argument("bundle", nargs="?")
    p = sp.add_parser("migrate"); p.add_argument("bundle"); p.add_argument("--domains", required=True); p.add_argument("--hub"); p.add_argument("--keep", action="store_true", help="giữ NN-*.md cũ")
    sp.add_parser("index")
    p = sp.add_parser("install"); p.add_argument("bundle", nargs="?"); p.add_argument("--auto", help="slug,slug — bỏ disable-model-invocation, agent tự nạp")
    p = sp.add_parser("check"); p.add_argument("--yes", action="store_true"); p.add_argument("--json", action="store_true")
    p = sp.add_parser("push"); p.add_argument("bundle"); p.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.cmd:
        ap.print_help(); return 2
    return globals()[f"cmd_{a.cmd}"](a)


if __name__ == "__main__":
    sys.exit(main() or 0)
