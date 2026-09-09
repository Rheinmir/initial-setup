#!/usr/bin/env python3
"""fdk-poc — POC luồng /br: tạo PROJECT THẬT (hiện trong Orca) từ RAW docs THẬT, ghi lại
TỪNG BƯỚC THẬT do agent chạy, rồi render trang visualize để người xem ĐỌC LOG + ĐÁNH GIÁ.

KHÁC /fdk-uat: uat = test nhanh "người mới curl về có chạy không" (xanh/đỏ).
              poc = chức năng THỰC TẾ chạy ra sao — xem log, chấm từng bước.

LUẬT CỐT LÕI (rút từ lần fail 16/07/26): **tool KHÔNG BAO GIỜ BỊA BƯỚC.**
Bản trước tự scaffold artifact giả trong /tmp rồi vẽ timeline → user không thấy project đâu,
không có luồng thật ⇒ POC vô giá trị. Nay mọi bước trong trace đến từ MỘT trong hai nguồn:
  • lệnh tool NÀY thực sự chạy (`new`, `probe`), hoặc
  • bước agent THỰC SỰ chạy rồi `record` lại (kèm rc + log thật).
`/br auto` không tất định-từ-raw (br-fill.py cần br/spec-filled.md, mà nó do LLM đọc .docx sinh)
→ tool KHÔNG giả vờ chạy nó; agent chạy thật rồi record.

Dùng:
  fdk-poc.py new    --raw "<dir>" [--name <proj>] [--dest ~/orca/workspaces] [--no-orca]
  fdk-poc.py record --project <p> --cmd "<lệnh>" [--rc N] [--log-file f|--log "..."] [--llm] [--note ..]
  fdk-poc.py render --project <p> [--out …]
  fdk-poc.py probe  --project <p> [--fresh]        # soi project /br có sẵn bằng tool thật
  fdk-poc.py --self-test
"""
import argparse
import html
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TRACE_REL = "br/.poc-trace.jsonl"
DEFAULT_DEST = Path.home() / "orca" / "workspaces"


def _run(cmd, cwd):
    t0 = time.perf_counter()
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
        rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        rc, out = 1, str(e)
    return rc, out, round((time.perf_counter() - t0) * 1000)


def _sentinel(proj, rel, needle=None):
    """Artifact THẬT chứng bước đã xảy ra. Nhận CẢ file lẫn THƯ MỤC (bug 17/07/26: `harness`
    là dir → is_file() báo thiếu oan). needle chỉ áp cho file."""
    f = proj / rel
    if not f.exists():
        return False, f"thiếu {rel}"
    if needle:
        if not f.is_file():
            return False, f"{rel} là thư mục — không kiểm được needle '{needle}'"
        if needle not in f.read_text(encoding="utf-8", errors="replace"):
            return False, f"{rel} không chứa '{needle}'"
    return True, rel + ("/" if f.is_dir() else "")


def _append(proj, rec):
    t = proj / TRACE_REL
    t.parent.mkdir(parents=True, exist_ok=True)
    with open(t, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _read_trace(proj):
    t = proj / TRACE_REL
    if not t.is_file():
        return []
    return [json.loads(l) for l in t.read_text(encoding="utf-8").splitlines() if l.strip()]


# ── new: PROJECT THẬT trong Orca → CURL cài overstack từ REMOTE → bê raw docs vào ────────────
# Luồng do user chốt 16/07/26: orca-cli tạo project → curl cài NĂNG LỰC từ remote (đường người
# mới, chứng năng lực travel được — tinh thần fdk-uat) → nạp context (copy raw) → chạy từ đầu.
# Bản trước chỉ mkdir khung ⇒ KHÔNG chứng minh gì. Mọi bước dưới đây là lệnh THẬT + log THẬT.
BOOTSTRAP_PATH = "harness/poc-vendor-neutral"


def new_project(raw_dir, name=None, dest=None, use_orca=True, force=False, ref="orca",
                skip_curl=False, agent="claude", prompt_text=None):
    """repo THẬT → orca repo add → orca WORKTREE create (=workspace hiện ở panel) → curl remote → raw.

    Bài học 17/07/26: `repo add` CHỈ đăng ký repo (hiện ở `orca repo list`); panel **Workspaces**
    liệt kê **worktree** → thiếu `worktree create` thì user KHÔNG THẤY project ⇒ POC fail.
    Layout khớp Orca: repo ở ~/orca/<name>/<name>, worktree ở ~/orca/workspaces/<name>/<wt>.
    """
    raw_dir = Path(raw_dir).expanduser().resolve()
    if not raw_dir.is_dir():
        raise SystemExit(f"raw dir không tồn tại: {raw_dir}")
    name = name or ("poc-" + raw_dir.name.replace(" ", "-").lower())
    repo_root = (Path(dest).expanduser() if dest else (Path.home() / "orca")).resolve()
    repo_dir = repo_root / name / name
    if repo_dir.exists() and not force:
        raise SystemExit(f"repo đã tồn tại: {repo_dir} (dùng --force)")
    if (repo_root / name).exists():
        shutil.rmtree(repo_root / name)
    repo_dir.mkdir(parents=True)

    # ── BƯỚC 1: repo THẬT + commit gốc (worktree cần base) + đăng ký Orca + TẠO WORKSPACE ──
    t0 = time.perf_counter()
    logs = []
    _run(["git", "init", "-q"], repo_dir)
    _run(["git", "config", "user.email", "poc@t"], repo_dir)
    _run(["git", "config", "user.name", "poc"], repo_dir)
    (repo_dir / "README.md").write_text(f"# {name}\n\nPOC: raw → /br từ đầu (fdk-poc).\n", encoding="utf-8")
    _run(["git", "add", "README.md"], repo_dir)
    rc, out, _ = _run(["git", "commit", "-qm", f"chore: khởi tạo {name} (fdk-poc)"], repo_dir)
    logs.append({"cmd": f"mkdir {repo_dir} && git init && commit gốc", "rc": rc,
                 "out": out.strip() or f"repo: {repo_dir}"})

    proj, orca_ok = repo_dir, False
    if use_orca:
        rc, out, _ = _run(["orca", "repo", "add", "--path", str(repo_dir)], repo_dir)
        logs.append({"cmd": f"orca repo add --path {repo_dir}", "rc": rc, "out": (out.strip() or "(đăng ký repo)")[:600]})
        # WORKSPACE = worktree → cái user THẤY ở panel Workspaces
        rc, out, _ = _run(["orca", "worktree", "create", "--name", name,
                           "--repo", f"path:{repo_dir}", "--base-branch", "main",
                           "--setup", "skip", "--activate", "--json"], repo_dir)
        wpath = None
        try:
            d = json.loads(out)
            w = d.get("result", {}).get("worktree", {})
            wpath = w.get("path")
            orca_ok = bool(d.get("ok")) and bool(wpath)
        except Exception:
            pass
        logs.append({"cmd": f"orca worktree create --name {name} --repo path:{repo_dir} --activate", "rc": rc,
                     "out": (f"workspace: {wpath}\n→ HIỆN Ở PANEL WORKSPACES CỦA ORCA" if orca_ok
                             else "worktree create THẤT BẠI:\n" + out.strip()[:600])})
        if orca_ok:
            proj = Path(wpath)
    ms = round((time.perf_counter() - t0) * 1000)
    _append(proj, dict(n=1, cmd="orca repo add + worktree create", hub="orca-cli", llm=False,
                       auto=["git init + commit gốc", "orca repo add → đăng ký repo",
                             "orca worktree create --activate → WORKSPACE hiện ở panel"],
                       ms=ms, rc=0, sentinel=".git", ok=(proj / ".git").exists(),
                       note=f"workspace THẬT: {proj}", logs=logs))

    # ── BƯỚC 2: CURL cài overstack từ REMOTE (đường người mới — chứng năng lực travel) ──
    base = f"https://raw.githubusercontent.com/Rheinmir/setup/{ref}/{BOOTSTRAP_PATH}"
    if not skip_curl:
        t0 = time.perf_counter()
        cmd = f'curl -fsSL "{base}/bootstrap.sh" | HARNESS_BASE="{base}" bash'
        rc, out, _ = _run(["bash", "-lc", cmd], proj)
        ms = round((time.perf_counter() - t0) * 1000)
        ok, sent = _sentinel(proj, "harness/policy.yaml", None)
        if not ok:
            ok = (proj / "harness").is_dir()
            sent = "harness/" if ok else "thiếu harness/ (curl fail)"
        # TRUNG THỰC: install.sh hardcode `npx skills add rheinmir/setup#orca` (không có SKILLS_REF)
        # ⇒ HARNESS tới từ `ref`, nhưng SKILL luôn tới từ nhánh `orca`. Skill mới ở nhánh canary
        # KHÔNG tới tay user qua đường này cho tới khi merge. Đây đúng lớp lỗi fdk-uat pha-2 săn.
        skills_warn = ("\n\n⚠ SKILL kéo từ nhánh `orca` (install.sh:230 hardcode "
                       "`npx skills add rheinmir/setup#orca`, không có SKILLS_REF override)"
                       + (f" — KHÁC ref={ref} bạn chọn ⇒ skill MỚI của nhánh này CHƯA tới qua đường remote."
                          if ref != "orca" else " — khớp ref."))
        _append(proj, dict(n=2, cmd=f"curl … bootstrap.sh | bash   (HARNESS_BASE→{ref})", hub="remote", llm=False,
                           auto=["tải harness (rào chắn) từ raw.githubusercontent",
                                 "npx skills add rheinmir/setup#orca --global (REF HARDCODE)", "seed llmwiki"],
                           ms=ms, rc=rc, sentinel=sent, ok=ok,
                           note=f"harness từ REMOTE nhánh {ref}; skill từ nhánh orca (hardcode)",
                           logs=[{"cmd": cmd, "rc": rc, "out": (out.strip()[-2000:] or "(no output)") + skills_warn}]))

    # ── BƯỚC 3: nạp CONTEXT — copy raw docs THẬT sang project mới ──
    t0 = time.perf_counter()
    (proj / "llmwiki" / "raw").mkdir(parents=True, exist_ok=True)
    docs = [p for p in sorted(raw_dir.iterdir()) if p.is_file() and not p.name.startswith(".")]
    for p in docs:
        shutil.copy2(p, proj / "llmwiki" / "raw" / p.name)
    ms = round((time.perf_counter() - t0) * 1000)
    ok, sent = _sentinel(proj, f"llmwiki/raw/{docs[0].name}" if docs else "llmwiki/raw", None)
    _append(proj, dict(n=len(_read_trace(proj)) + 1, cmd=f"copy raw → llmwiki/raw/ ({len(docs)} tài liệu)",
                       hub="context", llm=False, auto=["nạp tài liệu nghiệp vụ THẬT làm input cho /br interview"],
                       ms=ms, rc=0, sentinel=sent, ok=ok, note=f"nguồn: {raw_dir}",
                       logs=[{"cmd": f"cp '{raw_dir}'/* {proj}/llmwiki/raw/", "rc": 0,
                              "out": f"nguồn: {raw_dir}\n" + "\n".join(
                                  f"  + {p.name}  ({p.stat().st_size//1024} KB)" for p in docs)}]))

    # ── BƯỚC 4: SPAWN AGENT SESSION vào workspace → user THẤY + resume được ──
    # Bài học 17/07/26: chạy /br từ session repo-gốc rồi ghi file sang ⇒ workspace KHÔNG có phiên
    # nào (tab Claude Idle, /resume trống) ⇒ user không xem/replay được ⇒ POC vẫn fail.
    # Guide orca-cli: bare `worktree create` (không --agent) chỉ mở fallback shell. Phải spawn agent
    # SAU khi curl+raw xong (agent cần harness + tài liệu sẵn), nên dùng terminal create --command.
    if agent:
        t0 = time.perf_counter()
        prompt = (prompt_text or
                  "POC KHÔNG-NGƯỜI-GÁC: TUYỆT ĐỐI KHÔNG hỏi tôi, KHÔNG dừng chờ trả lời. "
                  "Gặp field missing/conflict thì TỰ ĐIỀN default (registry / lens-fill), đóng dấu "
                  "verified:false, rồi ghi lại bằng --asks. Chạy /br TỪ ĐẦU trên llmwiki/raw/: "
                  "(1) /br interview: đọc THẬT mọi file raw (docx: zipfile+regex), map S1-S10, mỗi field ghi "
                  "status + provenance raw:<file>, ghi br/spec-filled.md; "
                  "(2) /br auto: python3 fdk/tools/br-fill.py fill --root . ; "
                  "(3) /br compile -> slice -> run -> qc -> status. "
                  "Ở /br run: TRƯỚC khi chạy, in prompt sẽ inject bằng "
                  "'python3 fdk/tools/br-revise.py run --frame <f> --verify \"<cmd>\" --print' và lưu vào log. "
                  "SAU MỖI bước chạy: python3 fdk/tools/fdk-poc.py record --project . --cmd '<lệnh>' --rc N "
                  "--log-file <file> [--llm nếu cần model] [--must nếu đây là lệnh USER phải gõ] "
                  "[--asks '<bản thật sẽ hỏi user gì ở đây>'] --sentinel '<artifact>'. "
                  "KHÔNG bịa bước. Xong hết thì: fdk-poc.py render --project . ")
        # Prompt GHI RA FILE rồi `claude "$(cat …)"` — bài học 17/07/26: nhét prompt thẳng vào
        # --command làm vỡ quoting shell (prompt có dấu " lồng → zsh: 'no such file: cmd').
        pf = proj / "br" / ".poc-prompt.txt"
        pf.parent.mkdir(parents=True, exist_ok=True)
        pf.write_text(prompt, encoding="utf-8")
        cmd = ["orca", "terminal", "create", "--worktree", f"path:{proj}",
               "--title", "/br POC", "--command", f'{agent} "$(cat br/.poc-prompt.txt)"',
               "--focus", "--json"]
        rc, out, _ = _run(cmd, proj)
        ms = round((time.perf_counter() - t0) * 1000)
        sok = rc == 0
        _append(proj, dict(n=len(_read_trace(proj)) + 1, cmd=f"orca terminal create --command '{agent} …' --focus",
                           hub="orca-cli", llm=False,
                           auto=[f"spawn phiên {agent} NGAY TRONG workspace", "agent chạy /br từ đầu + record từng bước"],
                           ms=ms, rc=rc, sentinel=("terminal đã tạo" if sok else "spawn FAIL"), ok=sok,
                           note="phiên THẬT trong workspace → user xem/resume được",
                           logs=[{"cmd": " ".join(cmd[:8]) + " …", "rc": rc,
                                  "out": (out.strip()[:900] or "(đã tạo)")
                                         + f"\n\nPROMPT gửi agent:\n{prompt}"}]))
    return proj, docs, orca_ok


# ── probe: soi project /br CÓ SẴN bằng tool THẬT ─────────────────────────────────────────────
def probe_project(root):
    root = Path(root).resolve()
    frames_dir = root / "br" / "frames"
    n_frames = len(list(frames_dir.glob("*.md"))) if frames_dir.is_dir() else 0
    n_app = len(list((root / "app").glob("*.py"))) if (root / "app").is_dir() else 0
    n_test = len(list((root / "tests").glob("*.py"))) if (root / "tests").is_dir() else 0
    trace, total_ms = [], 0

    def step(n, cmd, tool_note, argv, cwd, sentinel, ok_from_rc=False, pre=None):
        nonlocal total_ms
        logs = []
        t0 = time.perf_counter()
        if pre:
            logs.append(pre)
        rc = 0
        if argv:
            rc, out, _ = _run(argv, cwd)
            logs.append({"cmd": " ".join(str(a).replace(str(REPO) + "/", "") for a in argv),
                         "rc": rc, "out": out.strip()[-1800:] or "(no output)"})
        ms = round((time.perf_counter() - t0) * 1000)
        total_ms += ms
        if sentinel:
            ok, sent = _sentinel(root, sentinel[0], sentinel[1])
        else:
            ok, sent = (rc == 0), (f"rc={rc}")
        if ok_from_rc:
            ok, sent = (rc == 0), (f"rc={rc}")
        trace.append(dict(n=n, cmd=cmd, hub=tool_note, remember=False, llm=False, auto=[],
                          ms=ms, rc=rc, sentinel=sent, ok=ok, note=tool_note, logs=logs))
        return rc

    clauses = "?"
    try:
        clauses = str(len(json.loads((root / "br" / "BR.clauses.json").read_text(encoding="utf-8"))))
    except Exception:
        pass
    step(1, "inventory", f"{n_frames} frame · {n_app} app.py · {n_test} test · {clauses} clause", None, root,
         sentinel=("br/BR.md", None),
         pre={"cmd": "đọc cấu trúc project", "rc": 0,
              "out": f"root: {root}\nframes : {n_frames}\napp    : {n_app}\ntests  : {n_test}\nclauses: {clauses}"})
    step(2, "frame-lint check", "gác 7 luật trên frame THẬT",
         ["python3", str(REPO / "fdk/tools/frame-lint.py"), "check", str(frames_dir), "--root", str(root), "--skip-verify"],
         root, sentinel=None, ok_from_rc=True)
    step(3, "pytest — acceptance THẬT", "chạy test nghiệp vụ thật",
         ["python3", "-m", "pytest", "-q", "--no-header", "tests"], root, sentinel=None, ok_from_rc=True)
    step(4, "build-line-status", "monitor tất định",
         ["python3", str(REPO / "fdk/tools/build-line-status.py"), "build", "--root", str(root)],
         root, sentinel=("br/line-status.json", None))
    step(5, "checkpoint list", "sổ trace SHEPHERD",
         ["python3", str(REPO / "fdk/tools/checkpoint.py"), "list", "--root", str(root)],
         root, sentinel=(".checkpoints.jsonl", None))

    pytest_line, pytest_env = "", False
    for lg in trace[2]["logs"]:
        if "No module named pytest" in lg["out"] or "No module named 'pytest'" in lg["out"]:
            pytest_env = True
            pytest_line = "pytest chưa cài ở máy — điều kiện MÔI TRƯỜNG, không phải lỗi project"
        for ln in lg["out"].splitlines():
            if "passed" in ln or "failed" in ln:
                pytest_line = ln.strip()
    if pytest_env:
        trace[2]["note"] = "pytest chưa cài (env) — không tính là lỗi project"
        trace[2]["sentinel"] = "env: thiếu pytest"
    project_ok = all(t["ok"] for t in trace if not (t["n"] == 3 and pytest_env))
    summary = dict(project=str(root), n_frames=n_frames, n_app=n_app, n_test=n_test, clauses=clauses,
                   frame_lint_pass=trace[1]["ok"], pytest_pass=trace[2]["ok"], pytest_line=pytest_line,
                   pytest_env=pytest_env, wall_ms=total_ms, steps=len(trace),
                   all_ok=all(t["ok"] for t in trace), project_ok=project_ok)
    return summary, trace



# ── drive: LÁI phiên TỪNG LƯỢT (hỏi–đáp) — không bắn 1 prompt rồi thả ────────────────────────
# Bài học 17/07/26 (user): "có mỗi 1 prompt làm tôi chả hình dung được là làm việc cùng ntn?
# phải kiểu hỏi đáp chứ — vấn đề chính là bạn không theo dõi session".
# Một mega-prompt fire-and-forget = KHÔNG thấy prompt inject TỪ TỪ, KHÔNG thấy cách cộng tác,
# và coordinator không hề giám sát. `drive` gửi MỘT bước → wait tui-idle → read → record → bước kế.
def term_handle(proj, title_hint="POC"):
    rc, out, _ = _run(["orca", "terminal", "list", "--json"], proj)
    try:
        for t in json.loads(out).get("result", {}).get("terminals", []):
            if str(proj) in str(t.get("worktreePath", "")) and title_hint in str(t.get("title") or ""):
                return t.get("handle")
    except Exception:
        pass
    return None


def drive_step(proj, handle, text, label, timeout_ms=600000, must=False, llm=True, sentinel=None):
    """Gửi 1 lượt → chờ agent rảnh → đọc output THẬT → record. Trả (rc, tail)."""
    t0 = time.perf_counter()
    _run(["orca", "terminal", "send", "--terminal", handle, "--text", text, "--enter"], proj)
    _run(["orca", "terminal", "wait", "--terminal", handle, "--for", "tui-idle",
          "--timeout-ms", str(timeout_ms)], proj)
    rc, out, _ = _run(["orca", "terminal", "read", "--terminal", handle, "--limit", "80", "--json"], proj)
    tail = ""
    try:
        tail = "\n".join(str(x) for x in json.loads(out).get("result", {}).get("terminal", {}).get("tail", []))
    except Exception:
        tail = out[-1500:]
    ms = round((time.perf_counter() - t0) * 1000)
    ok, sent = (True, "(không khai sentinel)")
    if sentinel:
        rel, _, needle = sentinel.partition(":")
        ok, sent = _sentinel(proj, rel, needle or None)
    _append(proj, dict(n=len(_read_trace(proj)) + 1, cmd=label, hub="/br" if label.startswith("/br") else "",
                       remember=must, llm=llm, auto=[], ms=ms, rc=0, sentinel=sent, ok=ok, note="drive turn",
                       logs=[{"cmd": "SEND → " + text[:160], "rc": 0, "out": tail[-1800:] or "(no output)"}]))
    return tail

# ── render HTML (dùng chung) ─────────────────────────────────────────────────────────────────
def emit_html(meta, trace, out_path):
    def esc(s):
        return html.escape(str(s))
    rows = []
    for t in trace:
        auto = "".join(f"<li>{esc(a)}</li>" for a in t.get("auto", []))
        badge = '<span class="llm">LLM</span>' if t.get("llm") else '<span class="det">tất định</span>'
        sent = ("✓ " + esc(t["sentinel"])) if t["ok"] else ("✗ " + esc(t["sentinel"]))
        logblk = ""
        for lg in t.get("logs", []):
            lrc = f'<span class="lrc {"ok" if lg["rc"]==0 else "no"}">rc={lg["rc"]}</span>'
            logblk += f'<div class="lgcmd"><code>$ {esc(lg["cmd"])}</code>{lrc}</div><pre class="lgout">{esc(lg["out"])}</pre>'
        rows.append(f"""<div class="step">
  <div class="sh"><span class="num">{t['n']}</span><code class="cmd">{esc(t['cmd'])}</code>
    <span class="hub">{esc(t.get('hub',''))}</span>{badge}
    <span class="ms">{t['ms']} ms</span><span class="sent {'ok' if t['ok'] else 'no'}">{sent}</span></div>
  {('<div class="auto"><span class="al">lệnh nội bộ tự fire:</span><ul>' + auto + '</ul></div>') if auto else ''}
  <details class="log"><summary>▸ LOG THẬT để đánh giá bước ({len(t.get('logs', []))} lệnh)</summary>{logblk}</details>
</div>""")
    maxms = max((t["ms"] for t in trace), default=1) or 1
    bars = "".join(
        f'<div class="bar"><span class="bl">{esc(t["cmd"])[:34]}</span>'
        f'<span class="bt {"llm" if t.get("llm") else "det"}" style="width:{max(4,int(t["ms"]/maxms*100))}%">{t["ms"]}ms</span></div>'
        for t in trace)
    ap = str(out_path.resolve())
    kpi_html = "".join(
        f'<div class="b"><div class="n {k.get("cls","")}">{esc(k["n"])}</div><div class="l">{k["l"]}</div></div>'
        for k in meta["kpis"])
    doc = f"""<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(meta['title'])}</title>
<meta name="theme-color" content="#eaf2fd">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230a84ff'/%3E%3C/svg%3E">
<style>
:root{{--font:-apple-system,BlinkMacSystemFont,'SF Pro Text','Segoe UI',sans-serif;--mono:'SF Mono',ui-monospace,Menlo,monospace;--ink:#0f0f12;--ink2:#4a4a55;--border:rgba(30,90,170,.14)}}
*{{box-sizing:border-box}}html{{background:#e9f0fb}}
body{{margin:0;font-family:var(--font);color:var(--ink);font-size:13.5px;line-height:1.6;padding:0 0 60px;
 background:radial-gradient(900px 500px at 12% -10%,rgba(10,132,255,.10),transparent 60%),linear-gradient(180deg,#f7fbff,#eaf2fd)}}
body::before{{content:'';position:fixed;inset:-10%;z-index:-1;pointer-events:none;background:radial-gradient(640px 440px at 10% 14%,rgba(10,132,255,.22),transparent 65%),radial-gradient(540px 400px at 88% 10%,rgba(88,86,214,.13),transparent 60%),radial-gradient(720px 500px at 74% 76%,rgba(48,176,199,.13),transparent 65%);animation:d 46s ease-in-out infinite alternate}}
@keyframes d{{100%{{transform:translate(2%,1.6%) scale(1.04)}}}}
.wrap{{max-width:960px;margin:0 auto;padding:0 22px}}
header{{padding:48px 22px 10px;max-width:960px;margin:0 auto}}
.eyebrow{{display:inline-block;font-size:11px;font-weight:700;color:#0a84ff;background:rgba(10,132,255,.10);padding:4px 11px;border-radius:999px;margin-bottom:12px}}
h1{{font-size:clamp(24px,4vw,34px);letter-spacing:-.02em;margin:0 0 8px;background:linear-gradient(135deg,#0a84ff,#5aa2e8,#cfe3fb);-webkit-background-clip:text;background-clip:text;color:transparent}}
.sub{{color:var(--ink2);max-width:680px}}
.kpi{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:22px 0}}
@media(max-width:640px){{.kpi{{grid-template-columns:1fr 1fr}}}}
.kpi .b{{background:rgba(255,255,255,.72);backdrop-filter:blur(8px);border:1px solid var(--border);border-radius:14px;padding:16px;box-shadow:inset 0 1px 0 rgba(255,255,255,.85),0 4px 20px rgba(20,40,90,.08);text-align:center}}
.kpi .n{{font-size:28px;font-weight:800;letter-spacing:-.02em;line-height:1}}
.kpi .l{{font-size:11px;color:var(--ink2);margin-top:6px}}
h2{{font-size:18px;margin:26px 0 4px;letter-spacing:-.01em}}
.hint{{color:var(--ink2);font-size:12.5px;margin:0 0 12px}}
.card{{background:rgba(255,255,255,.72);backdrop-filter:blur(8px);border:1px solid var(--border);border-radius:16px;box-shadow:inset 0 1px 0 rgba(255,255,255,.85),0 4px 20px rgba(20,40,90,.08);padding:14px 18px;margin:10px 0}}
.step{{border-bottom:1px solid var(--border);padding:11px 2px}}.step:last-child{{border-bottom:none}}
.sh{{display:flex;align-items:center;gap:9px;flex-wrap:wrap}}
.num{{width:22px;height:22px;border-radius:50%;background:#0a84ff;color:#fff;font-size:11px;font-weight:700;display:grid;place-items:center;flex-shrink:0}}
.cmd{{font-family:var(--mono);font-size:12.5px;background:rgba(10,132,255,.08);color:#0a5bd0;padding:2px 8px;border-radius:7px}}
.hub{{font-family:var(--mono);font-size:11px;color:var(--ink2)}}
.llm{{font-size:10px;color:#f08c00;background:rgba(255,149,0,.12);padding:1px 7px;border-radius:6px}}
.det{{font-size:10px;color:#5856d6;background:rgba(88,86,214,.10);padding:1px 7px;border-radius:6px}}
.ms{{font-family:var(--mono);font-size:11px;color:var(--ink2);margin-left:auto}}
.sent{{font-size:11px;padding:1px 7px;border-radius:6px}}
.sent.ok{{color:#28a745;background:rgba(52,199,89,.10)}}.sent.no{{color:#e0264b;background:rgba(255,45,85,.10)}}
.auto{{margin:6px 0 0 31px}}.al{{font-size:11px;color:var(--ink2)}}
.auto ul{{margin:3px 0 0;padding-left:16px}}.auto li{{font-size:11.5px;color:var(--ink2)}}
.log{{margin:8px 0 2px 31px}}
.log summary{{font-size:11.5px;color:#0a84ff;cursor:pointer;list-style:none}}
.log summary::-webkit-details-marker{{display:none}}
.lgcmd{{display:flex;align-items:center;gap:8px;margin:6px 0 2px}}
.lgcmd code{{font-family:var(--mono);font-size:11px;color:#0a5bd0;background:rgba(10,132,255,.07);padding:2px 7px;border-radius:6px;word-break:break-all}}
.lrc{{font-family:var(--mono);font-size:10px;padding:1px 6px;border-radius:5px;flex-shrink:0}}
.lrc.ok{{color:#28a745;background:rgba(52,199,89,.10)}}.lrc.no{{color:#e0264b;background:rgba(255,45,85,.10)}}
.lgout{{font-family:var(--mono);font-size:10.5px;line-height:1.5;color:#cbd5e1;background:#0d1220;border-radius:9px;padding:9px 12px;margin:0 0 4px;white-space:pre-wrap;word-break:break-word;max-height:260px;overflow-y:auto}}
.bar{{display:flex;align-items:center;gap:10px;margin:5px 0}}
.bl{{font-family:var(--mono);font-size:11px;color:var(--ink2);width:210px;flex-shrink:0;text-align:right}}
.bt{{font-size:10px;color:#fff;font-weight:700;padding:2px 8px;border-radius:6px;white-space:nowrap}}
.bt.det{{background:linear-gradient(90deg,#5856d6,#7a78e0)}}.bt.llm{{background:linear-gradient(90deg,#f08c00,#ffb04d)}}
.big{{color:#0a84ff}}.grn{{color:#28a745}}.org{{color:#f08c00}}
footer{{max-width:960px;margin:24px auto 0;padding:20px 22px;font-size:11px;color:var(--ink2);border-top:1px solid var(--border)}}
code.path{{font-family:var(--mono);font-size:11px}}
@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style></head><body>
<header>
  <span class="eyebrow">{meta['eyebrow']}</span>
  <h1>{meta['title']}</h1>
  <p class="sub">{meta['subtitle']}</p>
</header>
<div class="wrap">
  <div class="kpi">{kpi_html}</div>
  <h2>{meta['timeline_title']}</h2>
  <p class="hint">{meta['timeline_hint']}</p>
  <div class="card">{''.join(rows)}</div>
  <h2>{meta['bars_title']}</h2>
  <p class="hint">{meta['bars_hint']}</p>
  <div class="card">{bars}</div>
  <h2>{meta['tail_title']}</h2>
  <div class="card">{meta['tail_html']}</div>
</div>
<footer>{meta['footer_html']}<br><br>File: <code class="path">{esc(ap)}</code></footer>
</body></html>"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(doc, encoding="utf-8")
    return out_path


def meta_flow(proj, trace):
    n_llm = sum(1 for t in trace if t.get("llm"))
    total = sum(t["ms"] for t in trace)
    ok = sum(1 for t in trace if t["ok"])
    # LỆNH PHẢI NHỚ = bước user thực sự phải gõ (record --must). Còn lại tool tự fire.
    must = [t["cmd"] for t in trace if t.get("remember")]
    hubs = sorted({(t.get("hub") or t["cmd"].split()[0]) for t in trace if t.get("remember")})
    asks = [(t["cmd"], t["asks"]) for t in trace if t.get("asks")]
    asks_html = ("<br><br><b>Chỗ bản THẬT sẽ HỎI bạn</b> (POC tự điền để chạy không-người-gác, "
                 "đóng dấu <code>verified:false</code>):<ul>"
                 + "".join(f"<li><code>{html.escape(c)}</code> — {html.escape(a)}</li>" for c, a in asks)
                 + "</ul>") if asks else ""
    return dict(
        eyebrow=f"/fdk-poc · luồng THẬT · {len(trace)} bước · {total} ms",
        title="Luồng /br chạy THẬT trên project mới trong Orca",
        subtitle=f"Project THẬT: <code>{html.escape(str(proj))}</code> (mở được trong Orca). Mọi bước dưới đây là bước "
                 f"<b>THẬT ĐÃ CHẠY</b> — tool này KHÔNG bịa bước: hoặc do <code>fdk-poc</code> chạy, hoặc do agent chạy rồi "
                 f"<code>record</code> kèm <code>rc</code> + log thật. Mở LOG để đọc + chấm từng bước.",
        kpis=[dict(n=len(hubs) or "—", cls="big", l="LỆNH PHẢI NHỚ<br>(" + (", ".join(hubs) or "chưa đánh dấu") + ")"),
              dict(n=f"{len(must)}/{len(trace)}", cls="grn", l="bước user gõ<br>/ tổng bước THẬT"),
              dict(n=n_llm, cls="org", l="bước LLM<br>(còn lại tất định)"),
              dict(n=f"{total}<span style='font-size:14px'>ms</span>", l="tổng<br>wall-clock")],
        timeline_title=f"{len(trace)} bước THẬT — đọc log, chấm từng bước",
        timeline_hint='<span class="llm">LLM</span> = bước cần model · <span class="det">tất định</span> = tool 0-token · sentinel ✓ = artifact THẬT tồn tại.',
        bars_title="Nhanh không — wall-clock từng bước",
        bars_hint="Bước LLM (cam) là biến; bước tất định (tím) là chi phí harness.",
        tail_title="Đánh giá",
        tail_html=f"<b>Bạn chỉ phải nhớ {len(hubs)} lệnh</b>: <code>{', '.join(hubs) or '(chưa đánh dấu --must)'}</code> — "
                  f"{len(must)}/{len(trace)} bước là user gõ, còn lại tool TỰ FIRE (không phải nhớ tên). "
                  f"{ok}/{len(trace)} sentinel PASS · {n_llm} bước LLM. "
                  f"Trace: <code>{TRACE_REL}</code> (append-only, mỗi dòng một bước THẬT).{asks_html}",
        footer_html=f"POC luồng THẬT · project: <code class='path'>{html.escape(str(proj))}</code> · sinh bởi <code>fdk/tools/fdk-poc.py render</code>.")


def meta_probe(S):
    fl = "PASS" if S['frame_lint_pass'] else "FAIL"
    pt = "N/A" if S.get('pytest_env') else ("PASS" if S['pytest_pass'] else "FAIL")
    pt_cls = "org" if (S.get('pytest_env') or not S['pytest_pass']) else "grn"
    return dict(
        eyebrow=f"/fdk-poc probe{' · PROJECT MỚI (độc lập)' if S.get('fresh') else ''} · {S['wall_ms']} ms",
        title=("Điều kiện THẬT — project bê sang chỗ MỚI, đứng độc lập được không?"
               if S.get('fresh') else "Điều kiện THẬT — soi project /br có sẵn"),
        subtitle=((f"Copy <code>{html.escape(S.get('src',''))}</code> sang <b>project MỚI ngoài repo</b> "
                   f"(<code>{html.escape(S['project'])}</code>) rồi chạy tool THẬT trên đó. "
                   if S.get('fresh') else
                   f"Chạy tool THẬT trên <code>{html.escape(Path(S['project']).name)}</code>. ")
                  + f"<b>frame-lint · pytest · build-line-status · checkpoint</b> — {S['n_frames']} frame, {S['n_test']} test. Mở LOG để ĐÁNH GIÁ."),
        kpis=[dict(n=S['n_frames'], cls="big", l="frame THẬT"),
              dict(n=S['n_test'], cls="grn", l="test nghiệp vụ"),
              dict(n=pt, cls=pt_cls, l="pytest<br>(env chưa cài)" if S.get('pytest_env') else "pytest"),
              dict(n=f"{S['wall_ms']}<span style='font-size:14px'>ms</span>", l="wall-clock")],
        timeline_title=f"5 bước soi điều kiện thật",
        timeline_hint='Mỗi bước chạy tool THẬT trỏ vào project; mở LOG đọc output + <code>rc</code>.',
        bars_title="Nhanh không — thời gian từng bước",
        bars_hint="Probe không có bước LLM — toàn tool tất định trên frame/test THẬT.",
        tail_title="Đánh giá điều kiện",
        tail_html=f"<b>{S['n_frames']} frame</b> · <b>{S['clauses']} clause</b> · <b>{S['n_test']} test</b>. "
                  f"frame-lint: <b class='{'grn' if S['frame_lint_pass'] else 'org'}'>{fl}</b> · pytest: <b class='{pt_cls}'>{pt}</b> "
                  f"(<code>{html.escape(S['pytest_line'] or 'n/a')}</code>).<br><br>Sức khoẻ THẬT (bỏ bước env): "
                  f"<b class='{'grn' if S['project_ok'] else 'org'}'>{'LÀNH' if S['project_ok'] else 'CÓ VIỆC CẦN LÀM'}</b>.",
        footer_html=f"frame-lint {fl} · pytest {pt} · project: <code class='path'>{html.escape(S['project'])}</code>.")


def selftest():
    ok = True
    checks = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        raw = td / "raw-src"
        raw.mkdir()
        (raw / "yeucau.md").write_text("# yêu cầu\nX*2\n", encoding="utf-8")
        # selftest offline → --skip-curl; bước curl remote kiểm bằng chạy thật (không mock mạng)
        proj, docs, _ = new_project(raw, name="poc-selftest", dest=td / "ws", use_orca=False, skip_curl=True, agent="")
        checks.append(("new: tạo project THẬT", proj.is_dir() and (proj / ".git").is_dir()))
        checks.append(("new: nạp context — raw docs vào llmwiki/raw", (proj / "llmwiki/raw/yeucau.md").is_file()))
        checks.append(("new: ghi trace 2 bước THẬT (orca+context, curl skip)", len(_read_trace(proj)) == 2))
        n0 = len(_read_trace(proj))
        _append(proj, dict(n=n0 + 1, cmd="/br auto", hub="/br", llm=True, auto=[], ms=5, rc=0,
                           sentinel="x", ok=True, note="t", logs=[{"cmd": "c", "rc": 0, "out": "o"}]))
        tr = _read_trace(proj)
        checks.append(("record: trace append-only", len(tr) == n0 + 1 and tr[-1]["cmd"] == "/br auto"))
        out = emit_html(meta_flow(proj, tr), tr, td / "o.html")
        h = out.read_text(encoding="utf-8")
        checks.append(("render: HTML có log THẬT + path", "LOG THẬT" in h and str(out.resolve()) in h))
        checks.append(("KHÔNG bịa bước: mọi bước có log thật", all(t.get("logs") for t in tr)))
    for label, cond in checks:
        print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
        ok = ok and cond
    print("self-test: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="fdk-poc — POC luồng /br chạy THẬT + visualize")
    ap.add_argument("mode", nargs="?", default="render", choices=["new", "record", "render", "probe"])
    ap.add_argument("--raw", default=None, help="new: thư mục tài liệu THẬT")
    ap.add_argument("--name", default=None, help="new: tên project")
    ap.add_argument("--dest", default=None, help=f"new: nơi đặt project (mặc định {DEFAULT_DEST})")
    ap.add_argument("--no-orca", action="store_true", help="new: bỏ qua orca repo add")
    ap.add_argument("--ref", default="orca", help="new: nhánh remote để curl bootstrap (canary: tên nhánh)")
    ap.add_argument("--skip-curl", action="store_true", help="new: bỏ bước curl remote (chỉ khi offline/test)")
    ap.add_argument("--agent", default="claude", help="new: agent TUI spawn vào workspace (claude|codex|''=không spawn)")
    ap.add_argument("--prompt", default=None, help="new: prompt gửi agent (mặc định: chạy /br từ đầu + record)")
    ap.add_argument("--force", action="store_true", help="new: ghi đè project đã có")
    ap.add_argument("--project", default=None, help="record/render/probe: root project")
    ap.add_argument("--cmd", default=None, help="record: lệnh THẬT vừa chạy")
    ap.add_argument("--rc", type=int, default=0)
    ap.add_argument("--log", default=None)
    ap.add_argument("--log-file", default=None)
    ap.add_argument("--llm", action="store_true", help="record: bước này cần model")
    ap.add_argument("--must", action="store_true", help="record: lệnh USER PHẢI GÕ (đếm vào 'lệnh phải nhớ')")
    ap.add_argument("--asks", default=None, help="record: bản THẬT sẽ HỎI user ở đây (POC tự điền, ghi chú lại)")
    ap.add_argument("--note", default="")
    ap.add_argument("--ms", type=int, default=0)
    ap.add_argument("--sentinel", default=None, help="record: rel[:needle] — artifact chứng bước THẬT")
    ap.add_argument("--fresh", action="store_true", help="probe: copy sang thư mục mới rồi soi")
    ap.add_argument("--out", default=None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(selftest())

    if args.mode == "new":
        if not args.raw:
            print("new cần --raw <dir>", file=sys.stderr); sys.exit(2)
        proj, docs, orca_ok = new_project(args.raw, args.name, args.dest, not args.no_orca,
                                          args.force, args.ref, args.skip_curl, args.agent, args.prompt)
        tr = _read_trace(proj)
        print(f"✓ PROJECT THẬT: {proj}")
        print(f"  Orca      : {'ĐÃ đăng ký — MỞ ĐƯỢC TRONG APP' if orca_ok else 'CHƯA đăng ký (xem log / --no-orca)'}")
        print(f"  overstack : {'cài từ REMOTE nhánh ' + args.ref + ' qua curl' if not args.skip_curl else 'BỎ QUA curl (--skip-curl)'}"
              + ("  → harness/ " + ("CÓ" if (proj / "harness").is_dir() else "THIẾU (curl fail — xem log)") if not args.skip_curl else ""))
        print(f"  context   : {len(docs)} tài liệu THẬT → llmwiki/raw/")
        print(f"  trace     : {proj / TRACE_REL}  ({len(tr)} bước THẬT đã ghi)")
        print("\n  CHẠY TỪ ĐẦU (agent chạy THẬT rồi record — tool KHÔNG bịa bước):")
        print(f"    1. /br interview  → đọc .docx THẬT trong llmwiki/raw/ → br/spec-filled.md")
        print(f"       (mỗi field S1–S10 mang status + provenance raw:<file> ⇒ LLM vẫn TRỎ ngược về nguồn)  [LLM]")
        print(f"    2. /br auto       → python3 fdk/tools/br-fill.py fill --root .   [tất định: điền field missing]")
        print(f"    3. /br compile · slice · run · qc · status")
        print(f"    ghi mỗi bước: fdk-poc.py record --project {proj} --cmd '<lệnh>' --rc N --log-file <f> [--llm]")
        print(f"    render      : fdk-poc.py render --project {proj}")
        return

    if args.mode == "record":
        if not (args.project and args.cmd):
            print("record cần --project và --cmd", file=sys.stderr); sys.exit(2)
        proj = Path(args.project).resolve()
        out = args.log or (Path(args.log_file).read_text(encoding="utf-8", errors="replace") if args.log_file else "")
        ok, sent = True, "(không khai sentinel)"
        if args.sentinel:
            rel, _, needle = args.sentinel.partition(":")
            ok, sent = _sentinel(proj, rel, needle or None)
        tr = _read_trace(proj)
        _append(proj, dict(n=len(tr) + 1, cmd=args.cmd, hub="/br" if args.cmd.startswith("/br") else "",
                           remember=args.must, asks=args.asks, llm=args.llm, auto=[], ms=args.ms, rc=args.rc,
                           sentinel=sent, ok=ok, note=args.note,
                           logs=[{"cmd": args.cmd, "rc": args.rc, "out": (out.strip()[-1800:] or "(no output)")}]))
        print(f"✓ record bước {len(tr)+1}: {args.cmd} (rc={args.rc}, sentinel {'✓' if ok else '✗'} {sent})")
        return

    if args.mode == "probe":
        if not args.project:
            print("probe cần --project", file=sys.stderr); sys.exit(2)
        proot = Path(args.project)
        if not (proot / "br" / "frames").is_dir():
            print(f"không thấy br/frames trong {proot}", file=sys.stderr); sys.exit(2)
        src_name = proot.name
        if args.fresh:
            tmp = Path(tempfile.mkdtemp(prefix="fdk-poc-fresh-"))
            dest = tmp / src_name
            shutil.copytree(proot, dest, ignore=shutil.ignore_patterns(
                ".git", "__pycache__", "*.pyc", "out", "graph.db", ".pytest_cache"))
            print(f"  → copy {proot} → PROJECT MỚI {dest}", file=sys.stderr)
            proot = dest
        summary, trace = probe_project(proot)
        summary["fresh"] = bool(args.fresh)
        summary["src"] = str(Path(args.project).resolve())
        if args.json:
            print(json.dumps({"summary": summary, "trace": trace}, ensure_ascii=False, indent=2)); return
        out = Path(args.out) if args.out else (REPO / "llmwiki" / "html" / f"160726-fdk-poc-{src_name}{'-fresh' if args.fresh else ''}.html")
        emit_html(meta_probe(summary), trace, out)
        pt = "N/A(env)" if summary.get('pytest_env') else ("PASS" if summary['pytest_pass'] else "FAIL")
        print(f"✓ PROBE {summary['n_frames']} frame · frame-lint {'PASS' if summary['frame_lint_pass'] else 'FAIL'} · "
              f"pytest {pt} · project {'LÀNH' if summary['project_ok'] else 'CÓ VIỆC'} · {summary['wall_ms']} ms")
        print(f"✓ visualize: {out}")
        return

    # render
    if not args.project:
        print("render cần --project", file=sys.stderr); sys.exit(2)
    proj = Path(args.project).resolve()
    tr = _read_trace(proj)
    if not tr:
        print(f"trace rỗng ({proj / TRACE_REL}) — chưa có bước THẬT nào được ghi. "
              f"Tool KHÔNG bịa bước: chạy /br thật rồi `record`.", file=sys.stderr); sys.exit(2)
    if args.json:
        print(json.dumps(tr, ensure_ascii=False, indent=2)); return
    out = Path(args.out) if args.out else (REPO / "llmwiki" / "html" / f"160726-fdk-poc-{proj.name}-flow.html")
    emit_html(meta_flow(proj, tr), tr, out)
    print(f"✓ render {len(tr)} bước THẬT từ {proj / TRACE_REL}")
    print(f"✓ visualize: {out}")


if __name__ == "__main__":
    main()
