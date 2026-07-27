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
        wiki = root / "fdk" / "wiki" if (root / "fdk" / "wiki").is_dir() else root / "llmwiki" / "wiki"
        if wiki.is_dir():
            bits.append(f"• wiki `{wiki.relative_to(root)}` — query concept/entity/sources/adr/decisions cho context.")
        for cap in (root / "fdk" / "CAPABILITIES.md", root / "CAPABILITIES.md"):
            if cap.is_file():
                bits.append(f"• `{cap.relative_to(root)}` — bản đồ skill/tool đang có (đọc khi chưa chắc có đồ nghề gì).")
                break
        if bits:
            print("📍 [orientation] Project này có — QUERY trước khi đọc/grep rộng:\n  " + "\n  ".join(bits))
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
    if not (root / ".template-manifest.json").is_file():
        sys.exit(0)  # không phải project dùng template → bỏ qua

    output_style(root)  # đầu phiên: chốt KIỂU nói chuyện (chat), trước khi nói gì
    orient(root)  # đầu phiên: cho agent BIẾT project có gì + nhắc query trước (chống 'lơ ngơ')

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
