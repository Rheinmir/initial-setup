#!/usr/bin/env python3
"""wiki-sync — neo đồng bộ CODE→WIKI, tất định, 0 token (distill từ openwiki, GH langchain-ai).

Bịt lỗ "code đổi mà wiki không hay": stale.json của wiki_ledger chỉ lan truyền
stale WIKI→WIKI (trang đổi → trang link tới nó); nếu code đổi ngoài phiên có kỷ
luật wiki (人 sửa tay, tool khác, session quên) thì không gì phát hiện. Script này
giữ một NEO (<wiki>/.last-sync.json: gitHead + content-hash của wiki) và:

  --check        cổng no-op tất định: code không đổi kể từ neo → exit 0, KHÔNG cần
                 gọi LLM (0 token). Có đổi → map file-code-đổi → trang wiki nhắc tới
                 file đó, ghi vào stale.json (action="code-drift") rồi exit 3.
  --mark-synced  chốt neo sau khi wiki đã được rà/cập nhật: chỉ ghi khi (gitHead,
                 content-hash) thực sự đổi — cron chạy lại không tự churn metadata.
                 Đồng thời xoá các cờ code-drift (đã được rà theo định nghĩa).
  --json         output máy đọc cho CI.

Exit: 0 = wiki current / đã chốt neo · 2 = chưa có neo hoặc neo mất hiệu lực
      (sau rebase/squash — chạy --mark-synced để neo lại) · 3 = có drift cần rà.
Khác hook (fail-open), đây là công cụ CLI/CI: lỗi bất ngờ phải nổi (exit ≠ 0).
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import time

try:
    import fcntl  # POSIX only — cùng quy ước wiki_ledger
except ImportError:
    fcntl = None

# Cùng danh sách thư mục nội dung với wiki_ledger.py — đổi một nơi phải đổi nơi kia
# (harness-lint bắt hằng-số-lệch giữa script).
CONTENT_DIRS = ("concepts/", "entities/", "sources/", "draft/", "architecture/", "tours/")
ANCHOR_NAME = ".last-sync.json"
MAX_CHANGED_LIST = 200  # cap hiển thị — vượt thì nói rõ, không cắt im lặng


def run_git(root: pathlib.Path, *args: str) -> str:
    """Trả stdout RAW (không strip) — `git status --short` mã hoá trạng thái bằng
    khoảng trắng ĐẦU DÒNG; strip toàn cục sẽ cắt lệch path của dòng đầu."""
    out = subprocess.run(["git", "--no-pager", *args], cwd=root,
                         capture_output=True, text=True)
    return out.stdout


def detect_wiki_dir(root: pathlib.Path, arg) -> pathlib.Path:
    if arg:
        return (root / arg).resolve() if not pathlib.Path(arg).is_absolute() else pathlib.Path(arg)
    for cand in (root / "llmwiki" / "wiki", root / "wiki"):
        if cand.is_dir():
            return cand
    sys.exit("wiki-sync: không tìm thấy thư mục wiki (llmwiki/wiki hay wiki/) — chỉ định --wiki-dir")


def read_anchor(wiki_dir: pathlib.Path):
    p = wiki_dir / ANCHOR_NAME
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) and data.get("gitHead") else None
    except (OSError, ValueError):
        return None


def content_hash(wiki_dir: pathlib.Path) -> str:
    """sha256 nội dung wiki (chỉ CONTENT_DIRS, path-sorted) — metadata vận hành
    (neo, stale.json, ledger, log) không tham gia hash nên không tự làm 'đổi'."""
    h = hashlib.sha256()
    for d in CONTENT_DIRS:
        base = wiki_dir / d.rstrip("/")
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md"), key=lambda x: x.as_posix()):
            rel = p.relative_to(wiki_dir).as_posix()
            try:
                body = p.read_bytes()
            except OSError:
                continue  # file biến mất giữa scan — bỏ qua, lần sau hash lại
            h.update(f"file:{rel}\0".encode())
            h.update(body)
            h.update(b"\0")
    return h.hexdigest()


def changed_since(root: pathlib.Path, wiki_dir: pathlib.Path, head_anchor: str):
    """File đổi (commit + chưa commit) kể từ neo, LOẠI phần thuộc wiki/html —
    còn lại coi là code/nguồn. None = neo mất hiệu lực (rebase/gc)."""
    ok = subprocess.run(["git", "cat-file", "-e", f"{head_anchor}^{{commit}}"],
                        cwd=root, capture_output=True)
    if ok.returncode != 0:
        return None
    files: set[str] = set()
    for line in run_git(root, "diff", "--name-only", f"{head_anchor}..HEAD").splitlines():
        if line.strip():
            files.add(line.strip())
    for line in run_git(root, "status", "--short", "--untracked-files=all").splitlines():
        if len(line) > 3:  # "XY <path>" — path bắt đầu cột 3 (dòng KHÔNG được strip)
            files.add(line[3:].rstrip().split(" -> ")[-1])
    wiki_rel = wiki_dir.relative_to(root).as_posix()
    html_rel = wiki_rel.rsplit("/", 1)[0] + "/html"  # llmwiki/html — render ephemeral
    keep = []
    for f in sorted(files):
        if f.startswith(wiki_rel + "/") or f == wiki_rel:
            continue
        if f.startswith(html_rel + "/"):
            continue
        keep.append(f)
    return keep


def map_suspects(wiki_dir: pathlib.Path, changed: list[str]) -> dict[str, list[str]]:
    """Trang wiki nhắc tới file code đã đổi (theo path đầy đủ hoặc basename).
    Heuristic tất định, thiên về recall — /lint là người phán xử cuối."""
    needles = {}
    for f in changed:
        base = f.rsplit("/", 1)[-1]
        needles[f] = {f, base} if len(base) >= 5 else {f}
    suspects: dict[str, list[str]] = {}
    for d in CONTENT_DIRS:
        basedir = wiki_dir / d.rstrip("/")
        if not basedir.is_dir():
            continue
        for p in basedir.rglob("*.md"):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel = p.relative_to(wiki_dir).as_posix()
            hits = [f for f, ns in needles.items() if any(n in text for n in ns)]
            if hits:
                suspects[rel] = hits
    return suspects


def flag_stale(wiki_dir: pathlib.Path, suspects: dict[str, list[str]]) -> None:
    """Ghi cờ code-drift vào stale.json — cùng schema + flock với wiki_ledger."""
    stale_path = wiki_dir / "stale.json"
    lock_path = wiki_dir / ".stale.lock"
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    with open(lock_path, "w") as lk:
        if fcntl is not None:
            fcntl.flock(lk.fileno(), fcntl.LOCK_EX)
        try:
            try:
                stale = json.loads(stale_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                stale = {}
            for rel, hits in suspects.items():
                stale[rel] = {"by": hits[0] if len(hits) == 1 else f"{hits[0]} (+{len(hits) - 1})",
                              "action": "code-drift", "ts": ts, "session": None}
            stale_path.write_text(json.dumps(stale, ensure_ascii=False, indent=1) + "\n",
                                  encoding="utf-8")
        finally:
            if fcntl is not None:
                fcntl.flock(lk.fileno(), fcntl.LOCK_UN)


def clear_code_drift(wiki_dir: pathlib.Path) -> int:
    stale_path = wiki_dir / "stale.json"
    lock_path = wiki_dir / ".stale.lock"
    with open(lock_path, "w") as lk:
        if fcntl is not None:
            fcntl.flock(lk.fileno(), fcntl.LOCK_EX)
        try:
            try:
                stale = json.loads(stale_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return 0
            keep = {k: v for k, v in stale.items()
                    if not (isinstance(v, dict) and v.get("action") == "code-drift")}
            removed = len(stale) - len(keep)
            if removed:
                stale_path.write_text(json.dumps(keep, ensure_ascii=False, indent=1) + "\n",
                                      encoding="utf-8")
            return removed
        finally:
            if fcntl is not None:
                fcntl.flock(lk.fileno(), fcntl.LOCK_UN)


def log_sync_cost(root: pathlib.Path, status: str, ms: int, suspects: int) -> None:
    """Ghi chi phí một lượt --check vào harness/metrics/sync-log.jsonl (fail-open).

    Vì sao: kiến trúc này cố ý KHÔNG embedding — cổng no-op trả lời "có cần rà không" mà
    không gọi model (0 token). Nhưng một lợi thế không đo được thì không phải lợi thế, chỉ
    là niềm tin: không có số thì vừa không chứng minh được, vừa không phát hiện được lúc nó
    thoái hoá. `sync_tokens` giữ chỗ cho đủ trường — ở cổng no-op nó luôn 0 theo thiết kế.

    Guardrail thật nằm ở `sync_ms`: cổng chậm thì dev tắt hook, mà cổng bị tắt là cổng chết.
    KHÔNG tự tạo thư mục — downstream không có harness/ trong repo (ADR-017) thì im lặng bỏ qua.
    """
    try:
        d = root / "harness" / "metrics"
        if not d.is_dir():
            return
        rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
               "status": status, "sync_ms": ms, "sync_tokens": 0, "suspects": suspects}
        with open(d / "sync-log.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — đo lường không bao giờ được làm gãy cổng
        pass


def cmd_check(root: pathlib.Path, wiki_dir: pathlib.Path, as_json: bool) -> int:
    t0 = time.perf_counter()
    head = run_git(root, "rev-parse", "HEAD").strip()
    anchor = read_anchor(wiki_dir)
    if anchor is None:
        msg = {"status": "no-anchor", "head": head,
               "hint": "chưa có neo — chạy: wiki-sync.py --mark-synced sau lần rà wiki kế tiếp"}
        print(json.dumps(msg, ensure_ascii=False) if as_json else
              f"⚠ wiki-sync: chưa có neo {ANCHOR_NAME} — sau lần rà wiki kế tiếp chạy "
              f"`wiki-sync.py --mark-synced` để bật cổng no-op.")
        log_sync_cost(root, "no-anchor", int((time.perf_counter() - t0) * 1000), 0)
        return 2
    changed = changed_since(root, wiki_dir, anchor["gitHead"])
    if changed is None:
        msg = {"status": "anchor-invalid", "anchor": anchor["gitHead"], "head": head,
               "hint": "neo trỏ commit không còn (rebase/squash) — --mark-synced để neo lại"}
        print(json.dumps(msg, ensure_ascii=False) if as_json else
              f"⚠ wiki-sync: neo {anchor['gitHead'][:10]} không còn trong lịch sử "
              f"(rebase/squash?) — rà wiki một lượt rồi `--mark-synced` để neo lại.")
        log_sync_cost(root, "anchor-invalid", int((time.perf_counter() - t0) * 1000), 0)
        return 2
    if not changed:
        msg = {"status": "current", "head": head, "anchor": anchor["gitHead"],
               "since": anchor.get("updatedAt")}
        print(json.dumps(msg, ensure_ascii=False) if as_json else
              f"✓ wiki current — code không đổi kể từ neo {anchor['gitHead'][:10]} "
              f"({anchor.get('updatedAt', '?')}). No-op, 0 token.")
        log_sync_cost(root, "current", int((time.perf_counter() - t0) * 1000), 0)
        return 0
    suspects = map_suspects(wiki_dir, changed)
    if suspects:
        flag_stale(wiki_dir, suspects)
    if as_json:
        print(json.dumps({"status": "drift", "head": head, "anchor": anchor["gitHead"],
                          "changed": changed[:MAX_CHANGED_LIST],
                          "changed_total": len(changed),
                          "suspects": suspects}, ensure_ascii=False, indent=1))
    else:
        print(f"⟳ wiki-sync: {len(changed)} file code/nguồn đổi kể từ neo "
              f"{anchor['gitHead'][:10]} ({anchor.get('updatedAt', '?')}):")
        for f in changed[:MAX_CHANGED_LIST]:
            print(f"   · {f}")
        if len(changed) > MAX_CHANGED_LIST:
            print(f"   … và {len(changed) - MAX_CHANGED_LIST} file nữa (cap hiển thị "
                  f"{MAX_CHANGED_LIST} — danh sách đầy đủ qua --json).")
        if suspects:
            print(f"  → {len(suspects)} trang wiki nhắc tới file đổi — đã cờ code-drift "
                  f"vào stale.json:")
            for rel, hits in sorted(suspects.items()):
                print(f"   ⚑ {rel}  ⇐ {', '.join(hits[:3])}{' …' if len(hits) > 3 else ''}")
        else:
            print("  → không trang wiki nào nhắc trực tiếp tới file đổi — vẫn nên /lint "
                  "nếu thay đổi mang tính kiến trúc.")
        print("  Rà xong chạy: wiki-sync.py --mark-synced")
    log_sync_cost(root, "drift", int((time.perf_counter() - t0) * 1000), len(suspects))
    return 3


def cmd_flags_for(wiki_dir: pathlib.Path, pages: str, as_json: bool) -> int:
    """Trang nào TRONG SỐ pages đang mang cờ code-drift — dùng trên ĐƯỜNG ĐỌC (/query).

    Vì sao tồn tại: `--check` ghi cờ vào stale.json nhưng tới 2026-07-19 chỉ `/lint` đọc
    cờ đó, mà lint chạy theo chu kỳ → giữa hai lần lint, /query trả trang đã lệch code mà
    KHÔNG cảnh báo (đúng ca "graph là source-of-truth nhưng nội dung lệch" → model lập
    luận trên tri thức cũ). Đây là đầu tiêu thụ cờ cho đường đọc.

    FAIL-OPEN TUYỆT ĐỐI — khác mọi subcommand khác của file này (CLI/CI, lỗi phải nổi).
    Lý do: nó nằm trên đường ĐỌC. stale.json thiếu/hỏng/khoá không bao giờ được phép làm
    gãy một câu trả lời; mất cảnh báo là suy giảm chấp nhận được, mất đường đọc thì không.
    """
    try:
        wanted = [s.strip() for s in pages.split(",") if s.strip()]
        if not wanted:
            return 0
        try:
            stale = json.loads((wiki_dir / "stale.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            stale = {}
        hits = {}
        for rel, meta in (stale.items() if isinstance(stale, dict) else []):
            if not isinstance(meta, dict) or meta.get("action") != "code-drift":
                continue
            stem = rel.rsplit("/", 1)[-1].removesuffix(".md")
            for w in wanted:
                wstem = w.rsplit("/", 1)[-1].removesuffix(".md")
                if w == rel or wstem == stem:
                    hits[rel] = meta
                    break
        if as_json:
            print(json.dumps({"flagged": hits}, ensure_ascii=False, indent=1))
        elif hits:
            for rel, meta in sorted(hits.items()):
                print(f"⚑ CẢNH BÁO DRIFT: `{rel}` có thể đã lỗi thời — code đổi kể từ lần "
                      f"rà cuối (⇐ {meta.get('by', '?')}, cờ {meta.get('ts', '?')}). "
                      f"Kiểm lại trước khi tin; chạy /lint để rà.")
    except Exception:  # noqa: BLE001 — fail-open có chủ đích, xem docstring
        pass
    return 0


def cmd_mark(root: pathlib.Path, wiki_dir: pathlib.Path, as_json: bool) -> int:
    head = run_git(root, "rev-parse", "HEAD").strip()
    if not head:
        sys.exit("wiki-sync: không lấy được git HEAD — đây có phải git repo?")
    chash = content_hash(wiki_dir)
    anchor = read_anchor(wiki_dir)
    if anchor and anchor.get("gitHead") == head and anchor.get("contentHash") == chash:
        print(json.dumps({"status": "unchanged", "head": head}, ensure_ascii=False)
              if as_json else f"= neo giữ nguyên (HEAD {head[:10]} + nội dung wiki không đổi).")
        return 0
    cleared = clear_code_drift(wiki_dir)
    (wiki_dir / ANCHOR_NAME).write_text(json.dumps({
        "gitHead": head,
        "updatedAt": datetime.datetime.now().isoformat(timespec="seconds"),
        "contentHash": chash,
        "tool": "wiki-sync",
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"status": "marked", "head": head, "clearedCodeDrift": cleared},
                     ensure_ascii=False) if as_json else
          f"✓ đã chốt neo tại {head[:10]}" +
          (f" — xoá {cleared} cờ code-drift (đã rà)." if cleared else "."))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="neo đồng bộ code→wiki (no-op gate 0 token)")
    ap.add_argument("--root", default=".", help="gốc repo (mặc định: .)")
    ap.add_argument("--wiki-dir", default=None, help="thư mục wiki (mặc định: llmwiki/wiki hoặc wiki/)")
    ap.add_argument("--check", action="store_true", help="kiểm drift (mặc định)")
    ap.add_argument("--mark-synced", action="store_true", help="chốt neo sau khi rà wiki")
    ap.add_argument("--flags-for", default=None, metavar="PAGES",
                    help="đường ĐỌC: trang nào trong danh sách (slug/relpath, phân tách bằng dấu "
                         "phẩy) đang mang cờ code-drift — luôn exit 0, fail-open")
    ap.add_argument("--json", action="store_true", help="output máy đọc")
    a = ap.parse_args()
    if a.flags_for is not None:
        # Fail-open ngay từ khâu định vị: không có git/wiki cũng không được gãy đường đọc.
        try:
            root = pathlib.Path(run_git(pathlib.Path(a.root).resolve(), "rev-parse",
                                        "--show-toplevel").strip() or a.root).resolve()
            wiki_dir = detect_wiki_dir(root, a.wiki_dir)
        except Exception:  # noqa: BLE001
            sys.exit(0)
        sys.exit(cmd_flags_for(wiki_dir, a.flags_for, a.json))
    root = pathlib.Path(run_git(pathlib.Path(a.root).resolve(), "rev-parse", "--show-toplevel").strip()
                        or a.root).resolve()
    wiki_dir = detect_wiki_dir(root, a.wiki_dir)
    sys.exit(cmd_mark(root, wiki_dir, a.json) if a.mark_synced
             else cmd_check(root, wiki_dir, a.json))


if __name__ == "__main__":
    main()
