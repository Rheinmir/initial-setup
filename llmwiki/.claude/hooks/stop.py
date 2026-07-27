#!/usr/bin/env python3
"""L1/Stop: trước khi Claude kết thúc lượt — nếu phiên có sửa wiki thì index.md phải khớp (R3).
Exit 2 = chặn dừng, Claude phải sửa index trước. Có guard chống lặp vô hạn."""
import json
import os
import re
import subprocess
import sys
import time

from hooklib import audit, code_log, find_validators, find_wiki_dir, project_dir, read_payload, resolve_tool, run_validator


# file code (đa ngôn ngữ) trong git-status → trigger regen phần code-graph của wiki-graph.
# `$` + re.M vì mỗi dòng porcelain kết ở đường dẫn; khớp SUPPORTED_EXTS của code_imports.
_CODE_RE = re.compile(r"\.(py|js|jsx|ts|tsx|mjs|cjs|go|rs|java|rb|php|c|h|cpp|cc|sh)$", re.M)

# p-45 (fdk-problem-tree, đo 2026-07-21): build-wiki-graph.py 49.0s + medic.py --ci 26.1s —
# hai bước nặng nhất trong Stop hook, chạy TUẦN TỰ. Cổng kích hoạt cả hai ("wiki/code có đổi
# trong git status") rất lỏng nên với một phiên dev framework (chạm fdk/harness/skills/llmwiki
# liên tục) chúng fire gần như MỌI lượt — 75-90s thuế mỗi lần dừng, không phải "thỉnh thoảng".
# Đòn bẩy rẻ: debounce theo thời gian (đã có tiền lệ trong repo — watcher.py debounce 2s cho
# code-graph). KHÔNG đổi thuật toán generator (build-wiki-graph.py là engine dùng chung, sửa
# sai lan rộng — để dành cho /propose riêng nếu cần incremental thật). Window là default CHƯA
# đo trên hành vi thật, chỉnh qua biến môi trường khi cần, không phải hằng số thiêng.
_DEBOUNCE_STATE = "harness/metrics/.stop-debounce.json"
_DEBOUNCE_WINDOW_S = int(os.environ.get("OVERSTACK_STOP_DEBOUNCE_S", "180"))


def _debounce_state(root: str) -> dict:
    path = os.path.join(root, _DEBOUNCE_STATE)
    try:
        return json.load(open(path, encoding="utf-8")) if os.path.isfile(path) else {}
    except Exception:
        return {}


def _debounce_mark(root: str, key: str, ok: bool = True) -> None:
    path = os.path.join(root, _DEBOUNCE_STATE)
    state = _debounce_state(root)
    state[key] = {"ts": time.time(), "ok": ok}
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(state, open(path, "w", encoding="utf-8"))
    except Exception:
        pass  # ghi state lỗi → chỉ mất tác dụng debounce lần sau, không chặn gì


def _debounced(root: str, key: str, require_ok: bool = False) -> bool:
    """True = NÊN BỎ QUA lần chạy này (vừa chạy trong window giây gần đây).

    `require_ok=True` — dùng cho GATE sức khoẻ (medic --ci), KHÔNG dùng cho việc trang trí:
    chỉ bỏ qua nếu lần trước ĐÃ healthy. Một FAIL luôn được chạy lại ngay lượt sau — debounce
    không bao giờ được phép giấu một regression thật, chỉ tiết kiệm khi hệ đang khoẻ.
    Fail-open: state đọc lỗi/thiếu → coi như CHƯA chạy, không bao giờ chặn vì debounce hỏng."""
    rec = _debounce_state(root).get(key)
    if not isinstance(rec, dict):
        return False
    fresh = time.time() - rec.get("ts", 0) < _DEBOUNCE_WINDOW_S
    return fresh and (not require_ok or rec.get("ok") is True)


def _scope_config(root: str):
    """GH#49: khai báo scope index TƯỜNG MINH qua .overstack.yaml tại root dự án — thay vì
    ngầm-định code-root=repo-root. Parser tối giản (không thêm dep pyyaml), chỉ 2 khoá scalar:
        wiki_dir: llmwiki/wiki        # wiki chính để dựng graph
        code_root: src               # vùng code để index (relocate/thu hẹp được)
    Fallback = hành vi cũ (llmwiki/wiki + '.') nếu thiếu file/khoá → KHÔNG hồi quy. Fail-open."""
    wiki_dir, code_root = "llmwiki/wiki", "."
    cfg = os.path.join(root, ".overstack.yaml")
    if not os.path.isfile(cfg):
        return wiki_dir, code_root
    try:
        for ln in open(cfg, encoding="utf-8"):
            ln = ln.split("#", 1)[0].rstrip()
            if ":" not in ln:
                continue
            k, v = ln.split(":", 1)
            k, v = k.strip(), v.strip().strip("'\"")
            if k == "wiki_dir" and v:
                wiki_dir = v
            elif k == "code_root" and v:
                code_root = v
    except Exception:
        pass  # config hỏng → dùng mặc định, không chặn phiên
    return wiki_dir, code_root


def regen_docs(root: str) -> None:
    """Auto-fresh derived docs NGAY khi nguồn của chúng đổi, fail-open, gác bằng git-status nên
    không đụng = không tốn. Hai nhóm ĐỘC LẬP, phạm vi KHÁC nhau:
    (A) overstack.html + CAPABILITIES + skill-search — CHỈ repo framework (có build-overstack-docs.py),
        khi skill/rule/generator đổi.
    (B) wiki-graph.html (whiteboard quan hệ + code-graph cho NGƯỜI xem) — chạy khi có engine
        build-wiki-graph.py, ở CẢ downstream (GH#41 phương án B): repo framework luôn bật; downstream
        bật qua opt-in OVERSTACK_WIKIGRAPH=1 (Taleb: engine chạy trên máy người khác → không auto-on).
        MỘT codepath duy nhất — cùng engine, khác môi trường, không đẻ hook riêng (Munger)."""
    td = os.path.join(root, "fdk", "tools")
    is_framework = os.path.isfile(os.path.join(td, "build-overstack-docs.py"))
    # GLOBAL-SHARED (council-036): engine wiki-graph tìm REPO-LOCAL → GLOBAL ~/.claude/harness/.
    # Downstream KHÔNG copy engine vào repo — dùng bản global (cài 1 lần). resolve_tool trả None nếu
    # thiếu cả hai → wikigraph_on False → bỏ (fail-open).
    wg = resolve_tool(root, "fdk/tools/build-wiki-graph.py")
    # (B) chạy khi CÓ engine (local/global) và (repo framework HOẶC downstream đã bootstrap overstack).
    # OPT-IN downstream = sự tồn tại của llmwiki/.harness-stamp — CÙNG tín hiệu đã gate hook global fire
    # (install-harness.sh: `if [ -f .../llmwiki/.harness-stamp ]`). Trước đây opt-in dựa env
    # OVERSTACK_WIKIGRAPH=1, nhưng env đó CHỈ được set ở section 4b per-repo của install-harness.sh —
    # nhánh `--global` (đường bootstrap thật) exit TRƯỚC 4b nên không repo downstream nào có → graph
    # không bao giờ regen (GH#70). Khoá enablement vào chính stamp (đã gate hook) làm vòng tự-nhất-quán:
    # tín hiệu bật hook = tín hiệu bật wiki-graph. Giữ env cũ làm override tương thích ngược.
    has_stamp = os.path.isfile(os.path.join(root, "llmwiki", ".harness-stamp"))
    wikigraph_on = bool(wg) and (is_framework or has_stamp or os.environ.get("OVERSTACK_WIKIGRAPH") == "1")
    if not is_framework and not wikigraph_on:
        return  # không phải framework và cũng không bật wiki-graph downstream → bỏ hẳn (rẻ)
    try:
        st = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                            capture_output=True, text=True, timeout=8).stdout
        # (A) chỉ repo framework: skill/rule/generator đổi → overstack + CAPABILITIES + skill-search
        if is_framework and re.search(r"(skills/.*SKILL\.md|llmwiki/skills/|policy\.yaml|"
                     r"build-overstack-docs\.py|build-capabilities\.py|sync-skills\.py)", st):
            # mirror parity TRƯỚC: sửa canonical skills/<name>/SKILL.md → sinh lại llmwiki/skills/ y hệt
            # NGAY cuối lượt, để 2 cây không stale tạm thời (trước đây phải cp tay → gate mới bắt).
            ss = os.path.join(root, "harness", "scripts", "sync-skills.py")
            if os.path.isfile(ss):
                subprocess.run([sys.executable, ss], capture_output=True, timeout=40)
            for t in ("build-capabilities.py", "build-overstack-docs.py", "build-skill-search.py"):
                subprocess.run([sys.executable, os.path.join(td, t)], capture_output=True, timeout=40)
        # (B) wiki-graph.html: nội dung wiki, engine, HOẶC file code đổi → dựng lại.
        # GH#49: scope KHAI TƯỜNG MINH qua .overstack.yaml (wiki_dir + code_root) — relocate/thu hẹp
        # vùng index, tách được mẹ/con; thiếu config → mặc định cũ (llmwiki/wiki + root). cwd=root vì
        # generator resolve output + code_root theo cwd. --also fdk/wiki chỉ khi tồn tại.
        if (wikigraph_on and (re.search(r"(wiki/|build-wiki-graph\.py)", st) or _CODE_RE.search(st))
                and not _debounced(root, "wiki-graph")):
            wiki_dir, code_root = _scope_config(root)
            also = ["--also", "fdk/wiki"] if os.path.isdir(os.path.join(root, "fdk", "wiki")) else []
            subprocess.run([sys.executable, wg, wiki_dir, *also, "--code-root", code_root],
                           cwd=root, capture_output=True, timeout=90)
            _debounce_mark(root, "wiki-graph")
        # T5 (provenance-log, T-260722-01): phân loại file đổi theo path-prefix, ghi sự kiện
        # artifact-level. Gọi qua subprocess (CLI, không import chéo hooks/ <-> harness/scripts/)
        # — cùng pattern subprocess.run([sys.executable, wg, ...]) đã dùng cho wiki-graph ở trên.
        pl = resolve_tool(root, "harness/scripts/provenance-log.py")
        if pl:
            subprocess.run([sys.executable, pl, "record-changed", "--root", root],
                           cwd=root, capture_output=True, timeout=30)
    except Exception:
        pass


def secondary_memory(root: str, session: str) -> None:
    """Chốt 1+2 (council-030, issue #5): nối bộ-nhớ-thứ-cấp vào chính Stop-hook đang ghi ledger,
    để context/sửa-vụn được lưu durable + visualizable mà KHÔNG cần agent nhớ gõ tay (leverage
    Meadows #6 — cấu trúc luồng thông tin, không phải kỷ luật người). Mỗi lần dừng, khi phiên có
    SỬA thật (git dirty): (a) `scratch-log auto` tự điền why từ git nếu phiên chưa có why thủ công;
    (b) `scratch-log distill` gom → sources/DDMMYY-session-provenance.md; (c) `memory-map` regenerate
    llmwiki/html/memory-map.html; (d) `mem-rank episode` tự ghi episode có-cấu-trúc (did=commit subject,
    files=đổi trong phiên) vào tầng episodic — trước bản vá này layer này CHƯA từng được gọi tự động
    (memory.jsonl rỗng, phải gõ tay `/record-episode`); giờ mỗi phiên có sửa thật đều để lại 1 episode
    retrieve được, không cần agent nhớ. ĐỐI XỨNG wiki-graph: engine resolve REPO-LOCAL → GLOBAL
    ~/.claude/harness/ (downstream KHÔNG copy engine vào repo), enablement bật MẶC ĐỊNH downstream qua
    llmwiki/.harness-stamp (cùng tín hiệu đã gate hook global) — không cần setting tay. cwd=root nên engine
    global vẫn đọc/ghi ĐÚNG project. Fail-open tuyệt đối: thiếu engine / lỗi / timeout → im lặng."""
    sl = resolve_tool(root, "harness/scripts/scratch-log.py")
    if not sl:
        return  # thiếu engine (local+global) → bỏ (fail-open)
    is_framework = os.path.isfile(os.path.join(root, "fdk", "tools", "build-overstack-docs.py"))
    has_stamp = os.path.isfile(os.path.join(root, "llmwiki", ".harness-stamp"))
    if not (is_framework or has_stamp or os.environ.get("OVERSTACK_WIKIGRAPH") == "1"):
        return  # downstream chưa bootstrap (không stamp) → bỏ
    try:
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                               capture_output=True, text=True, timeout=8).stdout
    except Exception:
        return
    if not dirty.strip():
        return  # phiên không sửa gì → khỏi ghi provenance rỗng
    import datetime
    today = datetime.date.today().isoformat()
    mm = resolve_tool(root, "fdk/tools/memory-map.py")
    try:
        subprocess.run([sys.executable, sl, "auto", "--session", session, "--root", root],
                       cwd=root, capture_output=True, timeout=20)
        subprocess.run([sys.executable, sl, "distill", "--session", session, "--date", today],
                       cwd=root, capture_output=True, timeout=20)
        if mm:
            subprocess.run([sys.executable, mm], cwd=root, capture_output=True, timeout=40)
    except Exception:
        pass
    mr = resolve_tool(root, "harness/scripts/mem-rank.py")
    if mr:
        try:
            subject = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=root,
                                      capture_output=True, text=True, timeout=8).stdout.strip()
            changed = [ln[3:] for ln in dirty.splitlines() if len(ln) > 3][:8]
            did = subject or "(phiên có sửa, chưa commit)"
            subprocess.run([sys.executable, mr, "episode", did,
                             "--files", ",".join(changed), "--session", session],
                           cwd=root, capture_output=True, timeout=15)
        except Exception:
            pass


_ANSI = re.compile(r"\033\[[0-9;]*m")
FW_SURFACES = ("fdk/", "harness/", "skills/", "llmwiki/")


def _strip(s: str) -> str:
    return _ANSI.sub("", s).rstrip()


def framework_medic_mirror(root: str) -> int:
    """T2 gương-soi cuối phiên: phiên có ĐỤNG bề mặt framework (fdk/ harness/ skills/
    llmwiki/) → tự chạy `medic --ci` NGAY trước khi kết thúc lượt, để dark-rail/docs-lệch/
    code-vỡ lộ SỚM (không đợi tới commit-gate — bài học R7-f v1.0.5).

    Phạm vi (chống theater): CHỈ repo framework (có fdk/tools/medic.py) — phiên dev PROJECT
    thường không có medic.py nên bỏ qua hoàn toàn; và chỉ khi git-status thật sự chạm surface.
    Khoẻ (warn cũng tính khoẻ) → 1 dòng khẽ báo đã soi. FAIL thật (medic --ci exit≠0, chỉ khi
    có fail) → trả 2 để CHẶN dừng, in chỗ hở cho agent sửa (guard stop_hook_active chống lặp).
    Fail-open tuyệt đối: thiếu medic/git lỗi/timeout → 0, không bao giờ làm gãy phiên."""
    medic = os.path.join(root, "fdk", "tools", "medic.py")
    if not os.path.isfile(medic):
        return 0  # không phải repo framework → không soi
    try:
        st = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                            capture_output=True, text=True, timeout=8).stdout
    except Exception:
        return 0
    if not any(ln[3:].startswith(FW_SURFACES) for ln in st.splitlines() if len(ln) > 3):
        return 0  # phiên không chạm framework → im lặng (chống theater)
    # p-45: medic --ci đo 26.1s, fire gần mọi lượt trong phiên dev framework. Debounce CHỈ khi
    # lần trước healthy — một FAIL luôn chạy lại ngay, không bao giờ bị giấu (require_ok=True).
    if _debounced(root, "medic", require_ok=True):
        return 0
    try:
        p = subprocess.run([sys.executable, medic, "--ci"], cwd=root,
                           capture_output=True, text=True, timeout=120)
    except Exception:
        return 0  # medic lỗi/timeout không được chặn người dùng
    if p.returncode == 0:
        _debounce_mark(root, "medic", ok=True)
        head = next((_strip(ln) for ln in p.stdout.splitlines() if "▉" in ln), "medic KHOẺ")
        print(f"🩺 [medic gương-soi] phiên đụng framework → đã tự soi: {head}", file=sys.stderr)
        return 0
    _debounce_mark(root, "medic", ok=False)
    fails = [_strip(ln) for ln in p.stdout.splitlines() if "✗" in ln or "▉ FAIL" in ln]
    print("🩺 [medic gương-soi] phiên ĐỤNG framework mà medic --ci CÓ FAIL — sửa trước khi kết thúc:\n"
          + "\n".join(fails[:10])
          + "\n  → xem đầy đủ: `python3 fdk/tools/medic.py`", file=sys.stderr)
    return 2


def wiki_changed(root: str) -> bool:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root, capture_output=True, text=True, timeout=10,
        ).stdout
        return "wiki/" in out
    except Exception:
        return False


def main() -> None:
    payload = read_payload()
    audit(payload, "Stop")

    if payload.get("stop_hook_active"):
        sys.exit(0)  # đã block một lần rồi → không lặp vô hạn

    root = project_dir(payload)
    code_log(root, "--render-md")  # log.md auto-block do CODE sinh từ events.jsonl (không nhờ agent ghi)
    tp = payload.get("transcript_path")  # Trụ 1 Cost Attribution: 1 cost record / run, upsert theo session (cumulative, idempotent)
    if tp:
        code_log(root, "--run-cost", f"--transcript={tp}", f"--session={payload.get('session_id') or ''}")
    # THỨ TỰ CÓ CHỦ ĐÍCH: thứ SINH nội dung chạy trước thứ RENDER nội dung.
    # secondary_memory ghi session-provenance vào wiki và sinh lại memory-map; regen_docs
    # dựng wiki-graph + overstack (overstack NHÚNG memory-map). Thứ tự cũ ngược lại nên
    # overstack luôn ôm bản memory-map cũ và medic báo "docs CŨ so đĩa" ở MỌI phiên —
    # một cảnh báo đúng nhưng vô phương sửa bằng cách chạy lại generator.
    secondary_memory(root, (payload.get("session_id") or ""))  # issue #5: bộ-nhớ-thứ-cấp tự lưu context vụn cuối lượt
    regen_docs(root)               # overstack.html + CAPABILITIES tự cập nhật khi skill/rule đổi (repo framework)
    if framework_medic_mirror(root) == 2:  # T2: đụng framework → soi medic; FAIL thật thì chặn dừng
        sys.exit(2)
    if not wiki_changed(root):
        sys.exit(0)  # phiên không đụng wiki → không can thiệp

    wiki = find_wiki_dir(root)
    vdir = find_validators(root)
    if wiki is None or vdir is None:
        sys.exit(0)

    # (1) AUTO-INDEX: tự thêm row cho file wiki MỚI vào index.md (self-heal) NGAY khi có thay đổi —
    # index khớp mà không bắt agent sửa tay. Chiều 'stale' (xóa file mà còn row) vẫn để check bên dưới
    # chặn (gỡ row là quyết định của người). Fail-open: lỗi git/python → bỏ qua, không chặn lượt.
    try:
        subprocess.run([sys.executable, os.path.join(vdir, "index_sync.py"),
                        "--wiki-dir", str(wiki), "--fix"], capture_output=True, timeout=15)
    except Exception:
        pass

    rc, err = run_validator("index_sync.py", {"action": "stop", "wiki_dir": str(wiki)}, vdir)
    if rc == 2:
        print(err, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
