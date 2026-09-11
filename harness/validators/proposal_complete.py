#!/usr/bin/env python3
"""R7 proposal-complete: SPEC chờ duyệt + PLAN thi hành đều phải đủ chất, không thì chặn.

Vòng đời một feature sinh BỘ BA:
  SPEC  `DDMMYY-<ten>.md`       — NGƯỜI đọc để bấm duyệt ở cổng  (do /propose sinh, kèm .html)
  PLAN  `DDMMYY-<ten>-PLAN.md`  — MÁY đọc để thi hành            (do /plan sinh, KHÔNG cần .html)
  HTML  `DDMMYY-<ten>-seq.html` — trang người xem lúc duyệt

Scope: file .md trong wiki draft dir, CÓ section '## Plan', Status còn 'proposed'.
Output-report (không có Plan) và draft đã implemented/done tự miễn.

Nhánh SPEC:
  (a) Bảng '## Agent Task Assignment' ≥1 data row, không ô Agent nào trống
  (b) Link '**Sequence diagram**' trỏ tới file .html TỒN TẠI
  (c) Mỗi task '- [ ]' trong '## Plan' có một sơ đồ THẬT. Draft đặt tên từ 100926: đếm artifact
      archify trang nhúng/trỏ tới (iframe/a/embed) — khung list vẽ tay không còn được tính.
      Draft cũ hơn giữ luật cũ: số '<div class="diagram-box"' ≥ số task.
  (d) html KHÔNG ẩn nhãn message bằng 'opacity:0' (.msg phải hiện sẵn — bài học 130626).
      CHỈ quét trong khối <style> — trước đây quét cả trang nên cắn nhầm văn xuôi nào
      nhắc tới chính chuỗi CSS bị cấm (dính lúc soạn draft 140726).
  (e) html có ≥1 prose 'class="desc"' mỗi diagram (đọc hiểu không cần animation)
  (c)(d)(e) MIỄN khi html là artifact archify (chữ ký `archify <ver>` + ≥1 <svg>):
      archify đã gác hình học tất định (9 check + visual-check) mạnh hơn đếm diagram-box —
      luật này gác NỘI DUNG, không gác định dạng vẽ tay (bài học 080926).
  (f) '## Context' có nội dung — force-query grounding (ADR-009)
  (g) không còn placeholder ('TBD', 'xử lý lỗi phù hợp', 'tương tự Task N'…)
  (h) '## Global constraints' có nội dung — ràng buộc bao trùm, mỗi task ngầm mang theo

Nhánh PLAN (tên file kết thúc '-PLAN.md') — miễn (b)(c)(d)(e) vì PLAN không cần .html:
  (i) mỗi '### Task' phải có '**Files:**' với ≥1 đường dẫn thật
  (j) mỗi '### Task' phải có ≥1 khối code (bước đổi code thì phải CÓ code)
  (k) PLAN có ≥2 task → mỗi task bắt buộc '**Interfaces:**' (Consumes/Produces).
      Agent thi hành chỉ thấy task của nó; không khai chữ ký thì hai agent song song
      đặt tên hàm lệch nhau và phần ghép vỡ.
  (l) không còn placeholder
  (m) '## Global constraints' có nội dung

Contract chung: stdin JSON {"action":"write","file_path":...} hoặc argv files. Exit 0/2.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

DRAFT_RE = re.compile(r"(?:^|/)wiki/(?:draft|sources/draft)(?:/|$)")
STATUS_RE = re.compile(r"^\*\*Status:\*\*(.*)$", re.MULTILINE | re.IGNORECASE)
SEQ_LINK_RE = re.compile(r"\*\*Sequence diagram[^*]*\*\*:?\s*\[[^\]]*\]\(([^)]+\.html)\)", re.IGNORECASE)
TASK_RE = re.compile(r"^\s*-\s*\[[ xX]\]", re.MULTILINE)
DIAGRAM_RE = re.compile(r'<div\s+class="diagram-box"')
# nhãn message bị ẩn cứng: rule CSS .msg{...opacity:0...} — chỉ hiện qua JS (bài học 130626).
# Scope vào selector .msg để không bắt nhầm opacity:0 của ripple/animation khác.
HIDDEN_MSG_RE = re.compile(r"\.msg\b[^{}]*\{[^}]*opacity:\s*0\s*[;}]")
DESC_STATIC_RE = re.compile(r'class="desc"')          # prose tĩnh <p class="desc">
DESC_DATA_RE = re.compile(r"\bdesc\s*:\s*['\"`]")     # prose trong data JS: desc:'...'
STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.IGNORECASE | re.DOTALL)
ARCHIFY_RE = re.compile(r"\barchify \d+\.\d+")  # chữ ký viewer archify nhúng trong html


def is_archify_artifact(html_text):
    return bool(ARCHIFY_RE.search(html_text)) and "<svg" in html_text


# Từ 100926 sơ đồ trong seq html phải do ENGINE vẽ (/diagram → archify). Khung list vẽ tay
# (diagram-box + chip .lifeline + dòng .msg) lọt (c) vì (c) chỉ đếm class — trang ticket-composer
# 7 task, 0 sơ đồ vẫn qua. Draft đặt tên ngày trước mốc giữ luật cũ: không đỏ hồi tố.
ENGINE_CUTOFF = date(2026, 9, 10)
DRAFT_DATE_RE = re.compile(r"^(\d{2})(\d{2})(\d{2})-")
EMBED_RE = re.compile(r'<(?:iframe|a|embed|object)\b[^>]*?\b(?:src|href|data)="([^"#?]+\.html)"', re.IGNORECASE)


def needs_engine_diagrams(path):
    m = DRAFT_DATE_RE.match(Path(path).name)
    if not m:
        return True                    # không đọc được ngày → áp luật mới (fail-closed)
    try:
        return date(2000 + int(m[3]), int(m[2]), int(m[1])) >= ENGINE_CUTOFF
    except ValueError:
        return True


def embedded_archify(html_path, html_text):
    """Số artifact archify KHÁC NHAU trang seq nhúng/trỏ tới: file tồn tại + chữ ký archify + <svg>."""
    found = set()
    for rel in EMBED_RE.findall(html_text):
        p = (html_path.parent / rel).resolve()
        if p in found or p == html_path.resolve() or not p.is_file():
            continue
        if is_archify_artifact(p.read_text(encoding="utf-8", errors="replace")):
            found.add(p)
    return len(found)

# --- nhánh PLAN ---
PLAN_FILE_SUFFIX = "-PLAN.md"
TASK_HEAD_RE = re.compile(r"^###\s+Task\b.*$", re.MULTILINE)
FILES_RE = re.compile(r"^\s*\*\*Files:?\*\*", re.MULTILINE)          # nhận cả '**Files**' thiếu ':'
IFACE_RE = re.compile(r"^\s*\*\*Interfaces:?\*\*", re.MULTILINE)
CODE_FENCE_RE = re.compile(r"^\s*```", re.MULTILINE)
# đường dẫn thật: có '/' và một đuôi file, hoặc nằm trong `backtick`
PATH_RE = re.compile(r"[\w./~-]+/[\w.-]+\.\w+")

# placeholder BỊ CẤM — plan/spec còn mấy chuỗi này là plan HỎNG, không phải plan chưa xong.
# Agent CLI rẻ không hỏi lại được: gặp chỗ mơ hồ nó sẽ ĐOÁN rồi im lặng.
PLACEHOLDERS = [
    (re.compile(r"\bTBD\b", re.IGNORECASE), "TBD"),
    (re.compile(r"\bTO-?DO\b(?!\s*\.md)", re.IGNORECASE), "TODO"),
    (re.compile(r"\b(?:điền|chi tiết|bổ sung)\s+sau\b", re.IGNORECASE), "'điền/chi tiết sau'"),
    (re.compile(r"xử lý lỗi\s+(?:phù hợp|thích hợp)", re.IGNORECASE), "'xử lý lỗi phù hợp'"),
    (re.compile(r"\b(?:add\s+)?appropriate error handling\b", re.IGNORECASE), "'appropriate error handling'"),
    (re.compile(r"\bhandle edge cases\b", re.IGNORECASE), "'handle edge cases'"),
    (re.compile(r"(?:tương tự|similar to)\s+task\s+\d", re.IGNORECASE), "'tương tự Task N' (phải chép code ra)"),
]


META_DOC_RE = re.compile(r"^r7_meta:\s*true\s*(?:#.*)?$", re.MULTILINE | re.IGNORECASE)  # YAML cho phép comment cuối dòng
FENCE_BLOCK_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


# --- truy vết SPEC ↔ PLAN (spec-kit: id ổn định + coverage) ---
FR_ID_RE = re.compile(r"\bFR-(\d{3})\b")
THOA_RE = re.compile(r"^\s*\*\*Thoả:?\*\*(.*)$", re.MULTILINE)
# unknown NGUY HIỂM: model từ chối đoán → phải được trả lời trước khi hỏi duyệt
NEEDS_CLARIFY_RE = re.compile(r"\[CẦN LÀM RÕ:([^\]]*)\]")


def is_plan(path) -> bool:
    return str(path).replace("\\", "/").endswith(PLAN_FILE_SUFFIX)


def spec_of(plan_path):
    """PLAN `<stem>-PLAN.md` → SPEC anh em `<stem>.md`. Không có → None (fail-open)."""
    p = Path(plan_path)
    spec = p.parent / (p.name[: -len(PLAN_FILE_SUFFIX)] + ".md")
    return spec if spec.is_file() else None


def fr_ids(text):
    """Chỉ gom id trong section '## Requirements' — id nhắc trong văn xuôi (vd mục Risks)
    KHÔNG phải một yêu cầu, quét cả file sẽ chặn nhầm."""
    sec = None
    for title in ("Requirements (FR)", "Requirements"):
        sec = section(text, title)
        if sec:
            break
    return sorted(set(FR_ID_RE.findall(sec))) if sec else []


def is_meta_doc(text) -> bool:
    """Draft NÓI VỀ chính luật R7 (nên buộc phải trích nguyên văn chuỗi bị cấm) khai
    `r7_meta: true` ở frontmatter → miễn check placeholder. Ngoại lệ HIỆN và grep được,
    không phải heuristic đoán mò 'chuỗi này nằm trong backtick nên chắc là trích dẫn'."""
    return bool(META_DOC_RE.search(text))


def strip_fences(text) -> str:
    """Bỏ khối ``` … ``` — code mẫu/khuôn template được phép chứa chuỗi minh hoạ."""
    return FENCE_BLOCK_RE.sub("", text)


def find_placeholders(text):
    """Bỏ qua dòng đang ĐỊNH NGHĨA lệnh cấm (skill/validator tự nói về nó) — chỉ cắn dùng thật."""
    hits = []
    for rx, label in PLACEHOLDERS:
        m = rx.search(text)
        if m:
            hits.append(f"{label} (dòng {text[:m.start()].count(chr(10)) + 1})")
    return hits


def task_blocks(text):
    """Cắt text thành từng khối '### Task N ...' → [(tiêu đề, thân)]."""
    heads = list(TASK_HEAD_RE.finditer(text))
    out = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out.append((h.group(0).strip(), text[h.end():end]))
    return out


def section(text, title):
    m = re.search(rf"^##\s+{re.escape(title)}\s*$(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else None


def is_in_scope(path):
    p = (path or "").replace("\\", "/")
    return (p.endswith(".md") and DRAFT_RE.search(p) and Path(p).name not in ("README.md", "_template.md")
            and "/archive/" not in p)   # archive/ = nháp đông cứng (tidy) — không soi lại lịch sử (GH#146)


def check(path):
    if not is_in_scope(path):
        return
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return

    if is_plan(path):
        check_plan(path, text)
        return

    plan = section(text, "Plan")
    if plan is None:
        return  # output-report / draft không phải plan → miễn
    m = STATUS_RE.search(text)
    status = (m.group(1) if m else "").lower()
    if "proposed" not in status or "implement" in status or "done" in status:
        return  # đã qua gate / đã làm xong → miễn

    problems = []

    # (h) ràng buộc bao trùm — agent thi hành chỉ thấy task của nó, luật chung phải nằm một chỗ
    gc = section(text, "Global constraints")
    if gc is None or len(gc.strip()) < 20:
        problems.append("(h) thieu '## Global constraints' co noi dung — rang buoc bao trum moi task "
                        "(san version, gioi han dep, gate truoc push), chep NGUYEN VAN tu wiki/ADR/policy")

    # (g) placeholder — tai lieu NOI VE luat cam thi khai 'r7_meta: true' o frontmatter
    if not is_meta_doc(text):
        for hit in find_placeholders(strip_fences(text)):
            problems.append(f"(g) con placeholder {hit} — agent CLI re khong hoi lai duoc, no se DOAN roi im lang")

    # (n) unknown NGUY HIEM chua duoc tra loi → KHONG duoc hoi duyet.
    #     Model tu dien mac dinh la BINH THUONG (tag '(default)'), nhung nhom auth/du-lieu/tien/
    #     phap-ly/ranh-gioi-tin-cay thi mot mac dinh sai = hong kien truc → phai hoi that.
    if not is_meta_doc(text):
        for m in NEEDS_CLARIFY_RE.finditer(strip_fences(text)):
            line = text[: m.start()].count("\n") + 1
            problems.append(
                f"(n) con '[CAN LAM RO: {m.group(1).strip()[:60]}]' chua tra loi (dong {line}) — "
                f"user phai tra loi, HOAC ha xuong tag '(default)' MOT CACH CO CHU Y. "
                f"Khong duoc mang unknown nguy hiem ra cong duyet."
            )

    # (f) FORCE-QUERY grounding (R7-f, ADR-009): draft proposed có Plan PHẢI có '## Context'
    #     có nội dung (>=20 ký tự) — tóm tắt wiki liên quan đã query. Chống propose "mù".
    ctx = section(text, "Context")
    if ctx is None or len(ctx.strip()) < 20:
        problems.append("(f) thieu '## Context' co noi dung (>=20 ky tu) — force-query grounding (R7-f): "
                        "phai tom tat wiki/ADR/decision lien quan da query truoc khi propose")

    # (a) Agent Task Assignment
    agent_sec = section(text, "Agent Task Assignment")
    if agent_sec is None:
        problems.append("(a) thieu section '## Agent Task Assignment' — phai khai task nao do AI/CLI nao lam NGAY LUC PROPOSE")
    else:
        rows = [l for l in agent_sec.splitlines() if l.strip().startswith("|") and "---" not in l]
        data = rows[1:] if rows else []  # bỏ header
        if not data:
            problems.append("(a) bang Agent Task Assignment khong co data row nao")
        else:
            for l in data:
                cells = [c.strip() for c in l.strip().strip("|").split("|")]
                if len(cells) < 2 or not cells[1]:
                    problems.append(f"(a) row thieu o Agent: {l.strip()[:80]}")
                    break

    # (b) + (c) sequence html
    n_tasks = len(TASK_RE.findall(plan))
    mlink = SEQ_LINK_RE.search(text)
    if not mlink:
        problems.append("(b) thieu link '**Sequence diagram**: [..](...html)' trong draft")
    else:
        html_path = (Path(path).parent / mlink.group(1)).resolve()
        if not html_path.is_file():
            problems.append(f"(b) seq html khong ton tai: {mlink.group(1)}")
        else:
            html_text = html_path.read_text(encoding="utf-8", errors="replace")
            if is_archify_artifact(html_text):
                n_tasks = 0  # archify: hình học đã được gác bằng máy — miễn (c)(d)(e)
                html_text = ""
            if needs_engine_diagrams(path):
                n_diagrams = embedded_archify(html_path, html_text) if html_text else 0
                if n_tasks and n_diagrams < n_tasks:
                    problems.append(
                        f"(c) Plan co {n_tasks} task nhung seq html chi nhung {n_diagrams} so do archify — "
                        f"MOI task phai co sequence diagram do /diagram (archify) ve, nhung bang <iframe src=...html>. "
                        f"Khung list 'diagram-box' + chip .lifeline ve tay KHONG phai sequence diagram (bai hoc 100926)"
                    )
            else:
                n_diagrams = len(DIAGRAM_RE.findall(html_text))
                if n_tasks and n_diagrams < n_tasks:
                    problems.append(
                        f"(c) Plan co {n_tasks} task nhung seq html chi co {n_diagrams} diagram-box — "
                        f"MOI task phai co sequence diagram rieng"
                    )
            # (d) khong duoc an nhan message — doc ra phai thay chu ngay, khong cho animation reveal.
            #     Chi quet trong <style>: quet ca trang thi can nham van xuoi nhac toi chuoi CSS bi cam.
            css = "\n".join(STYLE_BLOCK_RE.findall(html_text))
            if HIDDEN_MSG_RE.search(css):
                problems.append(
                    "(d) seq html an nhan bang 'opacity:0' — nhan message PHAI hien san "
                    "(.msg opacity >=.82), animation chi lam noi buoc dang chay. Bai hoc 130626."
                )
            # (e) moi diagram phai co 1 doan prose doc hieu khong can xem animation —
            #     dem ca prose tinh (<p class="desc">) lan prose render tu data JS (desc:'...')
            n_desc = max(len(DESC_STATIC_RE.findall(html_text)), len(DESC_DATA_RE.findall(html_text)))
            if n_diagrams and n_desc < n_diagrams:
                problems.append(
                    f"(e) seq html co {n_diagrams} diagram nhung chi {n_desc} doan prose 'class=\"desc\"' — "
                    f"MOI task can 1 doan mo ta text (ai lam gi, du lieu chay, nhanh an toan)"
                )

    if problems:
        print(
            f"[R7 proposal-complete] {path} chua du chuan de hoi duyet:\n  - " + "\n  - ".join(problems),
            file=sys.stderr,
        )
        sys.exit(2)


def check_plan(path, text):
    """Nhánh PLAN — file `*-PLAN.md` do /plan sinh: thứ BƠM THẲNG vào agent context=0.
    Miễn (b)(c)(d)(e): PLAN không cần .html (HTML là để NGƯỜI xem lúc duyệt, gắn với SPEC)."""
    m = STATUS_RE.search(text)
    status = (m.group(1) if m else "").lower()
    if status and ("implement" in status or "done" in status):
        return  # đã thi hành xong → miễn

    problems = []
    tasks = task_blocks(text)
    if not tasks:
        problems.append("PLAN khong co '### Task N' nao — /plan phai chia task, moi task mot deliverable test duoc")

    # (m) ràng buộc bao trùm — mỗi task chỉ được bơm phần của nó, luật chung phải đi kèm
    gc = section(text, "Global constraints")
    if gc is None or len(gc.strip()) < 20:
        problems.append("(m) thieu '## Global constraints' co noi dung — chep NGUYEN VAN tu SPEC; "
                        "moi task ngam mang theo section nay khi dispatch --inject")

    multi = len(tasks) >= 2
    for title, body in tasks:
        short = title[:60]
        # (i) đường dẫn chính xác — agent khong doan duoc file nao
        mf = FILES_RE.search(body)
        if not mf:
            problems.append(f"(i) {short}: thieu '**Files:**' — phai khai duong dan CHINH XAC (tao/sua/test)")
        else:
            nl = body.find("\n\n", mf.end())
            files_blk = body[mf.end(): nl if nl > 0 else len(body)]
            if not PATH_RE.search(files_blk):
                problems.append(f"(i) {short}: '**Files:**' khong co duong dan that (vd `src/x/y.py`)")
        # (j) bước đổi code phải CÓ code
        if len(CODE_FENCE_RE.findall(body)) < 2:   # mở + đóng = 1 khối
            problems.append(f"(j) {short}: khong co khoi code nao — buoc doi code thi PHAI co code, "
                            f"khong mo ta suong (agent re se doan)")
        # (k) ≥2 task → bắt buộc khai chữ ký cho task hàng xóm
        if multi and not IFACE_RE.search(body):
            problems.append(f"(k) {short}: thieu '**Interfaces:**' (Consumes/Produces) — PLAN co {len(tasks)} task, "
                            f"agent chi thay task CUA NO; khong khai chu ky thi 2 agent dat ten ham lech nhau")

    # (l) placeholder
    if not is_meta_doc(text):
        for hit in find_placeholders(strip_fences(text)):
            problems.append(f"(l) con placeholder {hit} — PLAN la thu bom thang vao agent, mo ho = doan sai im lang")

    # (o) CONG TRUY VET: moi FR-xxx cua SPEC anh em phai duoc it nhat 1 task nhan.
    #     Mot yeu cau troi mat giua hai task la loi tham lang nhat cua moi ke hoach —
    #     no chi lo ra luc agent giao hang thieu, hoac te hon, luc user dung.
    spec = spec_of(path)
    if spec and tasks:
        want = fr_ids(spec.read_text(encoding="utf-8", errors="replace"))
        if want:
            claimed = set()
            for _, body in tasks:
                for m in THOA_RE.finditer(body):
                    claimed.update(FR_ID_RE.findall(m.group(1)))
            missing = [i for i in want if i not in claimed]
            if missing:
                problems.append(
                    f"(o) PLAN bo roi {len(missing)}/{len(want)} yeu cau cua SPEC: "
                    + ", ".join("FR-" + i for i in missing)
                    + f" — moi '### Task' phai khai '**Thoa:** FR-xxx'. SPEC: {spec.name}"
                )

    if problems:
        print(
            f"[R7 plan-executable] {path} chua du chuan de dispatch:\n  - " + "\n  - ".join(problems),
            file=sys.stderr,
        )
        sys.exit(2)


def self_test():
    """Ca đã cháy thật 080926: seq html do archify sinh không có diagram-box → (c) cắn nhầm."""
    assert is_archify_artifact("<html>archify 2.17.0-dev.1 <svg></svg></html>")
    assert not is_archify_artifact("<html>archify 2.17.0 no svg</html>")
    assert not is_archify_artifact('<div class="diagram-box"><svg></svg></div>')
    assert is_archify_artifact("x archify 3.0 y <svg viewBox='0 0 1 1'/>")

    # Ca đã cháy thật 100926: seq html dạng list (diagram-box + chip .lifeline) qua (c) dù 0 sơ đồ.
    import contextlib
    import io
    import tempfile
    draft = ("---\ntype: source\n---\n# F\n**Status:** proposed\n"
             "**Sequence diagram:** [seq](../../../html/p-seq.html)\n"
             "## Context\nĐã query wiki về luồng owner auth và đính kèm.\n"
             "## Global constraints\nDevice API giữ nguyên như bản trước.\n"
             "## Plan\n- [ ] T1 auth\n- [ ] T2 schema\n"
             "## Agent Task Assignment\n| Task | Agent |\n|---|---|\n| T1 | Claude |\n| T2 | Claude |\n")
    listing = ('<div class="diagram-box"><span class="lifeline">Owner</span><div class="msg add">Owner → API</div></div>'
               '<p class="desc">Mô tả T1.</p>' * 2)
    archify = "<html>archify 2.17.0 <svg viewBox='0 0 1 1'></svg></html>"
    shell = '<iframe src="p-t1.html"></iframe><p class="desc">T1.</p><iframe src="p-t2.html"></iframe><p class="desc">T2.</p>'

    def rc(name, page, extra=None):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "wiki" / "sources" / "draft"; d.mkdir(parents=True)
            h = Path(t) / "html"; h.mkdir()
            (h / "p-seq.html").write_text(page, encoding="utf-8")
            for fn, body in (extra or {}).items():
                (h / fn).write_text(body, encoding="utf-8")
            (d / name).write_text(draft, encoding="utf-8")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                try:
                    check(str(d / name))
                    return 0, err.getvalue()
                except SystemExit as e:
                    return e.code, err.getvalue()

    code, err = rc("100926-f.md", listing)
    assert code == 2 and "(c)" in err, err                       # list vẽ tay từ mốc → đỏ
    assert rc("080926-f.md", listing)[0] == 0                    # draft cũ: luật cũ, không đỏ hồi tố
    assert rc("100926-f.md", shell, {"p-t1.html": archify, "p-t2.html": archify})[0] == 0
    code, err = rc("100926-f.md", shell, {"p-t1.html": archify, "p-t2.html": "<html>list</html>"})
    assert code == 2 and "1 so do archify" in err, err           # 2 task mà chỉ 1 sơ đồ thật → đỏ
    print("proposal_complete --self-test: 8/8 ok")


def main():
    args = sys.argv[1:]
    if args == ["--self-test"]:
        self_test()
        sys.exit(0)
    if args:
        for p in args:
            check(p)
        sys.exit(0)
    try:
        ev = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if ev.get("action") == "write":
        check(ev.get("file_path", ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
