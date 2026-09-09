#!/usr/bin/env python3
"""L1/SessionStart: chạy health-check pattern-sync, BÁO CÁO (không chặn).

Đầu phiên: so version.json local ↔ remote ↔ disk. Nếu lệch (behind/drift/missing)
in 1 đoạn ngắn vào context để agent biết cần /sync-template. Fail-open tuyệt đối:
thiếu script / mạng chậm / lỗi gì cũng exit 0, không bao giờ làm gãy phiên.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from hooklib import HARNESS_HOME, audit, project_dir, read_payload, resolve_tool


def find_health_check(root: Path):
    """harness/scripts cạnh repo, hoặc bản copy cạnh hooks (deploy standalone)."""
    here = Path(__file__).resolve().parent
    for cand in (root / "harness" / "scripts" / "health-check.py",
                 here / "health-check.py",
                 here.parent.parent.parent / "harness" / "scripts" / "health-check.py"):
        if cand.is_file():
            return cand
    return None


def harness_integrity(root: Path) -> None:
    """U11 (GH#63 Phase 5): self-integrity — so llmwiki/.harness-stamp (hợp đồng install,
    travel theo git) vs ~/.claude/harness/version.json (global đang cài trên máy).
    LỆCH MAJOR → cảnh báo TO; stamp là HỢP ĐỒNG, không tự ép/tự sửa gì.
    Chạy TRƯỚC early-exit template-manifest (downstream v4 không có manifest).
    Fail-open tuyệt đối: thiếu file / JSON hỏng → im lặng, không bao giờ gãy phiên."""
    try:
        stamp_p = root / "llmwiki" / ".harness-stamp"
        if not stamp_p.is_file():
            return  # repo chưa bootstrap v4 → không có hợp đồng để so
        gv_p = HARNESS_HOME / "version.json"
        if not gv_p.is_file():
            print("⚠️ [harness-integrity] repo có llmwiki/.harness-stamp nhưng GLOBAL "
                  "~/.claude/harness CHƯA cài trên máy này — engine/validator global không chạy. "
                  "Cài: bash harness/scripts/install-harness.sh --global (hoặc re-curl bootstrap).")
            return
        want = str(json.loads(stamp_p.read_text()).get("guarded_by", "0"))
        have = str(json.loads(gv_p.read_text()).get("template_version", "0"))
        if want.split(".")[0] != have.split(".")[0]:
            print(f"🚨 [harness-integrity] LỆCH MAJOR: repo khai được gác bản v{want} "
                  f"(llmwiki/.harness-stamp) nhưng global đang cài v{have}. Stamp là hợp đồng — "
                  f"KHÔNG tự ép. Đồng bộ: re-curl bootstrap (cập nhật stamp) hoặc "
                  f"install-harness.sh --global (cập nhật global).")
        elif want != have:
            print(f"⟳ [harness-integrity] stamp v{want} ≠ global v{have} (cùng MAJOR — vẫn chạy "
                  f"bình thường; re-curl bootstrap khi tiện để khớp).")
    except Exception:
        pass


def wiki_drift(root: Path) -> None:
    """Nhắc code→wiki drift đầu phiên (distill openwiki 2026-07-06): wiki có neo
    .last-sync.json (do harness/scripts/wiki-sync.py --mark-synced chốt) mà code đã
    đổi kể từ neo → in 1 dòng nhắc /lint. Phục vụ dự án hiện tại (hợp ADR-004);
    tất định, 0 token, fail-open tuyệt đối."""
    try:
        for wd in (root / "llmwiki" / "wiki", root / "wiki"):
            anchor = wd / ".last-sync.json"
            if not anchor.is_file():
                continue
            head = json.loads(anchor.read_text(encoding="utf-8")).get("gitHead", "")
            if not head:
                return
            n = subprocess.run(["git", "rev-list", "--count", f"{head}..HEAD"],
                               cwd=root, capture_output=True, text=True, timeout=4)
            cnt = int(n.stdout.strip() or 0) if n.returncode == 0 else 0
            if cnt:
                print(f"⟳ [wiki-sync] code đã đổi {cnt} commit kể từ lần sync wiki "
                      f"(neo {head[:10]}) — chạy /lint để rà; chi tiết: "
                      f"wiki-sync.py --check.")
            return
    except Exception:
        pass



def draft_threshold(root: Path) -> None:
    """Kho nháp phình (draft/*.md tầng gốc > ngưỡng, mặc định 10) → in 1 khối HỎI user có chạy /tidy
    không (quét outdated → promote/ingest → cold archive). Vòng phản hồi Meadows cho docs-sprawl
    (proposal 090926-docs-curate-threshold-gate). Hỏi 1 lần/phiên (SessionStart chạy 1 lần);
    tất định, 0 token, fail-open; không có tidy.py (bản cũ) → im lặng."""
    try:
        t = resolve_tool(str(root), "harness/scripts/tidy.py")
        if not t:
            return
        r = subprocess.run([sys.executable, t, "check", "--root", str(root), "--json"],
                           cwd=root, capture_output=True, text=True, timeout=5)
        if r.returncode != 3:
            return
        s = json.loads(r.stdout or "{}")
        print(f"🧹 [tidy] draft/ có {s.get('draft_top')} file .md tầng gốc (> ngưỡng {s.get('threshold')}) — "
              f"outdated {s.get('outdated')} · promote? {s.get('promote')} · html cũ {s.get('html_archive')}.\n"
              f"   HỎI user (1 câu, trước khi làm việc khác): \"Chạy /tidy để quét nháp lỗi thời so với thực tế → "
              f"promote/ingest bản chất quý vào wiki → dời .md đã xong vào cold archive?\" "
              f"ĐỒNG Ý → gọi skill `tidy`. TỪ CHỐI → bỏ qua, KHÔNG hỏi lại trong phiên này.")
    except Exception:
        pass


def output_style(root: Path) -> None:
    """Nhắc kiểu OUTPUT đầu mỗi phiên — chỉ khi skill thật sự có mặt (thăm dò, không đoán).

    ADR-004 không cấm: đây KHÔNG phải context nội-bộ-framework, nó là cách nói chuyện với
    user, áp cho mọi dự án. Nhưng vẫn theo đúng luật đã học hôm nay — quảng cáo một năng
    lực thì phải KIỂM nó có mặt, không được nhắc mù.

    Ranh giới phải nói rõ, vì hai luật đang kéo ngược nhau: i-have-adhd bảo cắt ngắn, còn
    CLAUDE.md bảo tài liệu-người-đọc phải là văn xuôi đầy đủ. Phân xử: skill này áp cho
    phần CHAT; file tài liệu (ADR, proposal, README, report, trang HTML) giữ nguyên luật cũ.
    """
    try:
        for cand in (Path.home() / ".claude/skills/i-have-adhd/SKILL.md",
                     root / "skills/i-have-adhd/SKILL.md"):
            if cand.is_file():
                print("🧠 [output] Áp `/i-have-adhd` cho phần CHAT: hành động trước · đánh số bước · "
                      "nêu lại state mỗi lượt · chặn lạc đề · ước lượng thời gian cụ thể · "
                      "không mở bài/kết bài xã giao · list tối đa 5 mục.\n"
                      "   NGOẠI LỆ giữ nguyên: user hỏi \"giải thích/walk me through\" → viết đủ dài; "
                      "trước hành động phá huỷ → xác nhận đã; và TÀI LIỆU người đọc "
                      "(ADR/proposal/README/report/HTML) vẫn theo luật văn xuôi đầy đủ của CLAUDE.md.")
                return
    except Exception:
        pass


def orient(root: Path) -> None:
    """SessionStart orientation: in NGẮN để agent BIẾT project có code-index + wiki + capabilities,
    và NHẮC query chúng để định vị nhanh (đừng grep/đọc mù). Project-relevant — KHÔNG phải FDK
    framework-dev (ADR-004 chỉ cấm auto-bơm FDK). Chỉ in khi thật sự có; fail-open tuyệt đối."""
    try:
        bits = []
        # QUẢNG CÁO PHẢI DỰA TRÊN THĂM DÒ, KHÔNG DỰA TRÊN FILE TỒN TẠI.
        # Bản cũ hỏi đúng một câu: `(root/".graph-agent"/"index.db").is_file()`. DB 0 byte,
        # DB thiếu schema, server chết — đều lọt. Hậu quả thật: code-graph hỏng nhiều tuần
        # mà mọi phiên vẫn được lùa vào nó (đo: 37 tool-call so với 14 của grep).
        # Nguyên tắc đảo lại: chỉ quảng cáo khi CHỨNG MINH ĐƯỢC là chạy — không chứng minh
        # được thì im. Fail-open ở tầng hook (không bao giờ làm gãy phiên), nhưng fail-CLOSED
        # ở tầng quảng cáo (thà thiếu một dòng gợi ý còn hơn lùa agent vào tool chết).
        has_cg = False
        try:
            probe = resolve_tool(str(root), "harness/scripts/dep-health.py")
            if probe:
                out = subprocess.run([sys.executable, str(probe), "--root", str(root), "--json"],
                                     capture_output=True, text=True, timeout=10)
                deps = json.loads(out.stdout).get("deps", [])
                has_cg = any(d.get("name") == "code-graph" and d.get("status") == "ok"
                             for d in deps)
        except Exception:
            has_cg = False  # không thăm dò được → KHÔNG quảng cáo
        if has_cg:
            # Khai RÕ phạm vi, đừng khuyên chung chung "đừng grep mù". Đo A/B 2026-07-20
            # (harness/metrics/code-graph-ab.json, 5 task × 2 nhánh, sau khi sửa bug 2727ede):
            #   · tra HÀM/LỚP/METHOD  → code-graph 11 vs grep 11 tool-call = HOÀ
            #   · tra HẰNG SỐ         → code-graph 13 vs grep  5 tool-call = THUA 2.6×
            # Vì code-graph CHỈ index function/class/method — `search_symbols("CONTENT_DIRS")`
            # trả rỗng. Khuyên dùng nó trước cho MỌI thứ khiến mỗi lần tìm hằng số phải trả
            # phí hai lần (thử code-graph, hụt, rồi mới grep). Một dòng hướng dẫn đúng phạm vi
            # biến khoản thua đó thành hoà.
            bits.append("• code-index (code-graph, auto-reindex khi code đổi) — query `mcp__code-graph__*` "
                        "cho HÀM/LỚP/METHOD (search_symbols / get_symbol_context) và nhất là "
                        "get_callers (quan hệ gọi — grep không làm được). HẰNG SỐ · config · chuỗi "
                        "thì grep THẲNG: code-graph không index chúng, thử trước chỉ tốn thêm lượt.")
        wiki = None
        for cand in (root / "fdk" / "wiki", root / ".llmwiki" / "wiki", root / "llmwiki" / "wiki"):
            if cand.is_dir():
                wiki = cand
                break
        if wiki is not None:
            bits.append(f"• wiki `{wiki.relative_to(root)}` — query concept/entity/sources/adr/decisions cho context.")
            # Layout ẨN: ripgrep (và Grep của agent) BỎ QUA thư mục dấu chấm theo mặc định.
            # Đo 2026-09-04 trong sandbox: file trong .llmwiki/ thì `grep -r` tìm ra, `rg` KHÔNG.
            # Ta không sửa được ripgrep của agent → phải NHẮC. Chỉ nhắc khi dự án thật sự dùng
            # layout ẩn: repo framework và bản chưa migrate im lặng (no-op là kết quả tốt).
            if wiki.parts and wiki.relative_to(root).parts[0].startswith("."):
                bits.append(f"• ⚠ `{wiki.relative_to(root).parts[0]}/` là thư mục ẨN — `rg`/Grep bỏ qua "
                            f"hidden theo MẶC ĐỊNH. Tìm trong đó phải thêm `--hidden`, hoặc trỏ "
                            f"đường dẫn thẳng. `grep -r` thì vẫn thấy bình thường.")
        for cap in (root / "fdk" / "CAPABILITIES.md", root / "CAPABILITIES.md"):
            if cap.is_file():
                bits.append(f"• `{cap.relative_to(root)}` — bản đồ skill/tool đang có (đọc khi chưa chắc có đồ nghề gì).")
                break
        if bits:
            print("📍 [orientation] Project này có — QUERY trước khi đọc/grep rộng:\n  " + "\n  ".join(bits))
    except Exception:
        pass


def recall(root: Path, sid: str = "") -> None:
    """Đầu phiên: in CHUỖI vài phiên gần nhất (mem-rank chain) vào context.

    Đây là mắt xích đã thiếu của tầng memory: Stop-hook GHI episode mỗi phiên có sửa thật, nhưng
    trước bản này KHÔNG AI ĐỌC LẠI — `mem-rank retrieve/chain` không có caller runtime nào, nên
    store chỉ để đó (đo 2026-09-07: memory.jsonl 0 dòng ở repo, không hook nào gọi retrieve).
    Ghi mà không đọc thì không phải trí nhớ, chỉ là log. Ở đây đọc chuỗi mới→cũ có PARENT nên
    agent thấy "phiên trước làm gì, tiếp phiên nào", không phải một đống episode rời.

    Rẻ và tất định: đọc một file JSONL, in tối đa 3 dòng, 0 token LLM. Fail-open tuyệt đối.
    """
    try:
        mr = resolve_tool(str(root), "harness/scripts/mem-rank.py")
        if not mr:
            return
        out = subprocess.run([sys.executable, str(mr), "chain", "--root", str(root), "--json"],
                             capture_output=True, text=True, timeout=10)
        rows = json.loads(out.stdout or "[]")
        lines = []
        for m in rows[:3]:
            # KHÔNG đặt tên `sid` ở đây: nó sẽ đè tham số sid (session của phiên HIỆN TẠI) và
            # biên lai okf-scan bên dưới bị ghi nhầm sang phiên cũ. Bug thật, bắt bằng test.
            esid = (m.get("session") or "?")[:8]
            did = (m.get("did") or m.get("text") or "").strip().splitlines()[0][:90]
            files = ", ".join((m.get("files") or [])[:3])
            lines.append(f"  • {esid} ({m.get('ts', '')[:10]}) — {did}" + (f"  [{files}]" if files else ""))
        more = f"  … còn {len(rows) - 3} phiên nữa: `mem-rank.py chain`" if len(rows) > 3 else ""
        # Quét OKF THẬT (wiki + memory) và để lại BIÊN LAI: có bằng chứng việc quét đã chạy,
        # và Stop-hook sẽ đối chiếu transcript xem agent có MỞ những mục này không (okf-scan
        # verify). "Agent bảo đã đọc wiki" không phải bằng chứng; biên lai + coverage thì có.
        scan_line = ""
        try:
            ok_tool = resolve_tool(str(root), "harness/scripts/okf-scan.py")
            if ok_tool:
                # Chưa có episode nào (dự án mới) thì vẫn quét — dùng nhánh git làm truy vấn.
                q = " ".join((rows[0].get("did") or "").split()[:8]) if rows else ""
                if not q:
                    q = subprocess.run(["git", "branch", "--show-current"], cwd=str(root),
                                       capture_output=True, text=True, timeout=5).stdout.strip().replace("-", " ") or "context"
                sc = subprocess.run([sys.executable, str(ok_tool), "query", q, "--root", str(root),
                                     "--session", sid, "--k", "4", "--json"],
                                    capture_output=True, text=True, timeout=12)
                rec = json.loads(sc.stdout or "{}")
                if rec.get("hits"):
                    scan_line = ("\n  Quét OKF (" + str(rec.get("scanned", 0)) + " mục, có biên lai) → nên đọc:\n    "
                                 + "\n    ".join(f"{h['path']}  [{h['type']}]" for h in rec["hits"]))
        except Exception:
            scan_line = ""
        if not lines and not scan_line:
            return                                  # chưa có gì để nhắc → im lặng, không nhiễu
        head = ("🧠 [recall] Chuỗi phiên gần nhất (mới → cũ, tự ghi ở Stop-hook):\n"
                + "\n".join(lines) + (("\n" + more) if more else "")) if lines else "🧠 [recall]"
        print(head
              + scan_line
              + "\n  Đây là NHẮC, không phải sự thật — file trong repo mới là nguồn đúng.")
    except Exception:
        pass


def wikigraph_reminder(root: Path) -> None:
    """Cờ auto-draw BẬT mà artifact vector thiếu/cũ → nhắc 1 dòng kèm đúng lệnh vẽ.
    Diệt pain im-lặng: Stop hook chỉ regen khi git-status có diff ở wiki/ hay code — project
    vừa cài/onboard xong ngồi im thì vector không xuất hiện VÀ không có gì báo. KHÔNG auto-chạy
    generator (tốn ~5s/phiên) — chỉ LỘ DIỆN. Chỉ khi opt-in (tôn trọng Taleb: không nag project
    chưa bật cờ). Fail-open tuyệt đối; TRƯỚC early-exit manifest nên downstream v4 cũng nhận."""
    try:
        if os.environ.get("OVERSTACK_WIKIGRAPH") != "1":
            return
        wiki = root / "llmwiki" / "wiki"
        if not wiki.is_dir():
            return
        mds = [p for p in wiki.rglob("*.md") if p.name not in ("index.md", "log.md")]
        if not mds:
            return  # wiki rỗng → chưa có gì để vẽ (chạy orca-onboard trước)
        graph = root / "llmwiki" / "html" / "wiki-graph.html"
        newest = max(p.stat().st_mtime for p in mds)
        if graph.is_file() and graph.stat().st_mtime >= newest:
            return  # vector đã vẽ & mới hơn wiki → im
        wg = resolve_tool(str(root), "fdk/tools/build-wiki-graph.py")
        if not wg:
            return  # engine không tới được → gợi lệnh cũng vô ích (harness-integrity lo)
        why = "chưa vẽ" if not graph.is_file() else "cũ hơn wiki"
        print(f"🕸️ [wiki-graph] vector quan hệ {why} — vẽ ngay: "
              f"python3 {wg} llmwiki/wiki --code-root .  "
              f"(hoặc để Stop tự vẽ khi có diff ở wiki/ hay code)")
    except Exception:
        pass


def main() -> None:
    payload = read_payload()
    audit(payload, "SessionStart")

    root = Path(project_dir(payload))
    harness_integrity(root)  # U11: so stamp↔global TRƯỚC early-exit (downstream v4 không có manifest)
    wiki_drift(root)         # code→wiki drift — cũng TRƯỚC early-exit (downstream v4 là đích chính)
    wikigraph_reminder(root) # C: cờ bật mà vector thiếu/cũ → nhắc 1 dòng (trước early-exit, downstream primary)
    draft_threshold(root)    # kho nháp vượt ngưỡng → HỎI user chạy /tidy (trước early-exit, downstream primary)
    if not (root / ".template-manifest.json").is_file():
        sys.exit(0)  # không phải project dùng template → bỏ qua

    output_style(root)  # đầu phiên: chốt KIỂU nói chuyện (chat), trước khi nói gì
    orient(root)  # đầu phiên: cho agent BIẾT project có gì + nhắc query trước (chống 'lơ ngơ')
    recall(root, payload.get("session_id") or "")  # đầu phiên: chuỗi phiên gần nhất (episodic) — đóng vòng ghi→đọc của mem-rank

    # NOTE: KHÔNG auto-bơm context framework-dev (FDK) ở đây. Phần lớn phiên là dùng
    # framework để dev DỰ ÁN KHÁC, không phải dev chính framework → bơm nội-bộ-framework
    # vào mọi phiên là nhiễu. Front-door FDK là skill gọi chủ động `/fdk` (xem ADR-004).
    script = find_health_check(root)
    if script is None or not (root / "harness" / "version.json").is_file():
        sys.exit(0)  # chưa có version.json → chưa khởi tạo, im lặng

    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--root", str(root), "--json",
             "--remote-timeout", "4", "--branch", "orca"],
            capture_output=True, text=True, timeout=8,
        )
        rep = json.loads(proc.stdout)
    except Exception:
        sys.exit(0)  # fail-open

    if rep.get("status") == "ok":
        sys.exit(0)

    lines = ["⟳ [pattern-health] cấu hình template lệch — cân nhắc đồng bộ:"]
    if rep.get("behind") or rep.get("version_behind"):
        n = len(rep.get("behind", []))
        rv = rep.get("remote_version")
        lines.append(f"  • {n} pattern cũ hơn remote"
                     + (f" (remote v{rv} > local v{rep.get('local_version')})" if rep.get("version_behind") else "")
                     + " → chạy /health-check rồi /sync-template (downstream).")
    if rep.get("missing"):
        lines.append(f"  • thiếu {len(rep['missing'])} file pattern: "
                     + ", ".join(rep["missing"][:5]) + (" …" if len(rep["missing"]) > 5 else ""))
    if rep.get("drift"):
        lines.append(f"  • {len(rep['drift'])} pattern đã sửa local: "
                     + ", ".join(d.split('/')[-1] for d in rep["drift"][:5])
                     + (" …" if len(rep["drift"]) > 5 else "") + " (upstream hoặc revert).")
    if not rep.get("remote_reachable"):
        lines.append("  • (remote offline — chỉ so local; chạy /health-check khi có mạng để đối chiếu version remote.)")
    print("\n".join(lines))
    sys.exit(0)


if __name__ == "__main__":
    main()
