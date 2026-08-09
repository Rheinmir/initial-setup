#!/usr/bin/env python3
"""token-attrib — BƯỚC NÀO đang đốt token, đo từ transcript thật (tất định, 0-token, KHÔNG LLM).

`code-logger.py --run-cost` đã trả lời "một run tốn bao nhiêu". Cái còn thiếu là quy trách
nhiệm theo TỪNG NGUỒN BƠM: hook nào, file auto-load nào, reminder nào đã đẩy chữ vào context.

Điểm cốt lõi mà mọi bảng "đếm token" đơn giản đều bỏ sót — KHUẾCH ĐẠI. Một khối chữ bơm vào ở
lượt thứ N không tốn một lần; nó nằm lại trong context và bị đọc lại ở MỌI lượt sau. Chi phí thật
là `token × số_lượt_còn_lại`, đơn vị token·lượt. Đo trên một phiên thật 1.136 lượt: 5.309 token
của một file auto-load bơm 4 lần thành 7,2 TRIỆU token·lượt — trong khi bảng đếm thường chỉ ghi
21 nghìn. Sai số ba bậc độ lớn, và nó lái người đọc tối ưu nhầm chỗ.

  --transcript PATH   file .jsonl cụ thể; bỏ qua → tự tìm transcript MỚI NHẤT của dự án hiện tại
  --top N             chỉ in N nguồn nặng nhất (mặc định 12)
  --json              xuất máy đọc
  --all-sessions      gộp mọi transcript của dự án thay vì phiên mới nhất
  --self-test         kiểm tất định, không đọc gì ngoài fixture trong bộ nhớ

Exit: 0 = đo được · 3 = không tìm/không đọc được transcript (KHÔNG trả 0 để cổng không hiểu
nhầm "đã đo và sạch" — cùng bài học ba-mã-thoát của grounding-check.py).
"""
import json
import os
import re
import sys
from bisect import bisect_left
from pathlib import Path

CHARS_PER_TOKEN = 4          # xấp xỉ; đủ để XẾP HẠNG, không dùng để tính tiền
SIG_LEN = 64                 # độ dài chữ ký gom nhóm


def project_slug(cwd: str) -> str:
    return "-" + str(Path(cwd).resolve()).strip("/").replace("/", "-")


def find_transcripts(cwd: str):
    """Cả hai vendor cùng khuôn ~/.<cli>/projects/<slug>/*.jsonl."""
    out = []
    for home in (".claude", ".openclaude"):
        d = Path.home() / home / "projects" / project_slug(cwd)
        if d.is_dir():
            out += sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    return out


# Nguồn bơm ĐÃ BIẾT — chỉ để đặt tên cho dễ đọc. Khối lạ vẫn được gom tự động theo chữ ký,
# nên công cụ không mù ở dự án có hook khác.
KNOWN = [
    (re.compile(r"Behavioral guidelines|## Invocation rules"), "file auto-load (CLAUDE.md/AGENT.md)"),
    (re.compile(r"The following skills are available"),        "bảng skills"),
    (re.compile(r"rule đang gác \(policy\.yaml\)"),            "SessionStart: harness rule"),
    (re.compile(r"\[orientation\]"),                            "SessionStart: orientation"),
    (re.compile(r"\[pattern-health\]"),                         "SessionStart: pattern-health"),
    (re.compile(r"\[wiki-sync\]"),                              "SessionStart: wiki-sync"),
    (re.compile(r"\[harness-integrity\]"),                      "SessionStart: harness-integrity"),
    (re.compile(r"docs-gate"),                                  "UserPromptSubmit: R10 docs-gate"),
    (re.compile(r"CAVEMAN MODE ACTIVE"),                        "UserPromptSubmit: caveman"),
    (re.compile(r"medic gương-soi"),                            "Stop: medic mirror"),
    (re.compile(r"\[R3 index-sync\]"),                          "Stop: R3 index-sync"),
    (re.compile(r"task tools haven't been used"),               "reminder: task tools"),
    (re.compile(r"\[anti-idle\]"),                              "Stop: anti-idle"),
]


def label_for(text: str) -> str:
    for rx, name in KNOWN:
        if rx.search(text):
            return name
    sig = " ".join(text.split())[:SIG_LEN]
    return f"(chưa đặt tên) {sig}"


def injected_blocks(rows):
    """Chữ KHÔNG do người gõ và KHÔNG do model sinh — tức thứ hook/hệ thống đẩy vào context.

    Claude Code ghi phần lớn thứ này thành entry `type: attachment` có `attachment.type` phân
    loại sẵn (hook_success, hook_additional_context, task_reminder, nested_memory, skill_listing…).
    Bản đầu của hàm này chỉ soi `system` và `<system-reminder>` nên BỎ SÓT đúng nguồn nặng nhất:
    `nested_memory` — file CLAUDE.md/AGENT.md bơm lại, mỗi lần ~5.300 token.
    """
    for i, r in enumerate(rows):
        t = r.get("type")

        if t == "attachment":
            a = r.get("attachment") or {}
            kind = a.get("type", "attachment")
            body = a.get("content")
            if not isinstance(body, str):
                body = json.dumps(body, ensure_ascii=False) if body is not None else ""
            if not body.strip():
                continue
            name = a.get("displayPath") or a.get("path") or ""
            label = f"{kind} · {Path(name).name}" if name else kind
            yield i, body, label
            continue

        if t == "system":
            c = r.get("content")
            if isinstance(c, str) and c.strip():
                yield i, c, None
            continue

        if t != "user":
            continue
        c = (r.get("message") or {}).get("content")
        parts = [c] if isinstance(c, str) else [
            b.get("text", "") for b in (c or []) if isinstance(b, dict) and b.get("type") == "text"]
        for txt in parts:
            for m in re.finditer(r"<system-reminder>(.*?)</system-reminder>", txt or "", re.S):
                if m.group(1).strip():
                    yield i, m.group(1), None


def analyse(rows):
    turns = [i for i, r in enumerate(rows) if r.get("type") == "assistant"]
    total_turns = len(turns)
    usage = {}
    for r in rows:
        if r.get("type") != "assistant":
            continue
        for k, v in ((r.get("message") or {}).get("usage") or {}).items():
            if isinstance(v, int):
                usage[k] = usage.get(k, 0) + v

    agg = {}
    for idx, text, label in injected_blocks(rows):
        tok = max(1, len(text) // CHARS_PER_TOKEN)
        remaining = total_turns - bisect_left(turns, idx)
        e = agg.setdefault(label or label_for(text), {"n": 0, "tok": 0, "amp": 0})
        e["n"] += 1
        e["tok"] += tok
        e["amp"] += tok * remaining          # ← chi phí THẬT: token · số lượt còn lại
    return {"turns": total_turns, "usage": usage,
            "sources": dict(sorted(agg.items(), key=lambda kv: -kv[1]["amp"]))}


def report(res, top, path):
    u = res["usage"]
    cr = u.get("cache_read_input_tokens", 0)
    print(f"transcript : {path}")
    print(f"lượt        : {res['turns']:,}")
    print("usage       : " + " · ".join(f"{k.replace('_input_tokens','')}={v:,}"
                                        for k, v in sorted(u.items(), key=lambda kv: -kv[1])))
    print()
    print(f"{'NGUỒN BƠM VÀO CONTEXT':<46}{'lần':>5}{'tok':>9}{'token·lượt':>14}{'%cache_read':>13}")
    print("-" * 87)
    tot = 0
    for name, e in list(res["sources"].items())[:top]:
        tot += e["amp"]
        pct = (e["amp"] / cr * 100) if cr else 0
        print(f"{name[:45]:<46}{e['n']:>5}{e['tok']:>9,}{e['amp']:>14,}{pct:>12.2f}%")
    allamp = sum(e["amp"] for e in res["sources"].values())
    pct = (allamp / cr * 100) if cr else 0
    print("-" * 87)
    print(f"{'TỔNG mọi nguồn bơm':<46}{'':>5}{'':>9}{allamp:>14,}{pct:>12.2f}%")
    print()
    print("token·lượt = token × số lượt CÒN LẠI sau khi bơm. Đây mới là chi phí thật: một khối")
    print("nằm lại trong context thì mọi lượt sau đều phải đọc lại nó.")
    if cr and pct < 5:
        print(f"\nGhi chú trung thực: phần bơm chỉ chiếm {pct:.1f}% cache_read. Phần còn lại là")
        print("LỊCH SỬ HỘI THOẠI. Cắt hook lúc này lãi rất ít — muốn giảm thật thì rút ngắn phiên,")
        print("tách việc sang phiên mới, hoặc giảm output dài trong hội thoại.")


def self_test() -> int:
    rows = [
        {"type": "user", "message": {"content": [
            {"type": "text", "text": "<system-reminder>" + "x" * 400 + "</system-reminder>"}]}},
        {"type": "attachment", "attachment": {"type": "nested_memory",
                                              "displayPath": "llmwiki/CLAUDE.md",
                                              "content": "y" * 800}},
        {"type": "assistant", "message": {"usage": {"cache_read_input_tokens": 1000}}},
        {"type": "assistant", "message": {"usage": {"cache_read_input_tokens": 1000}}},
    ]
    r = analyse(rows)
    fails = []
    if r["turns"] != 2:
        fails.append(f"đếm lượt sai: {r['turns']}")
    src = list(r["sources"].values())
    if not src:
        fails.append("không bắt được khối system-reminder")
    elif src[0]["amp"] != src[0]["tok"] * 2:
        fails.append(f"khuếch đại sai: {src[0]} (phải = tok × 2 lượt còn lại)")
    # khối rỗng không được tính
    r2 = analyse([{"type": "user", "message": {"content": [
        {"type": "text", "text": "<system-reminder>   </system-reminder>"}]}}])
    if r2["sources"]:
        fails.append("khối rỗng vẫn bị tính")
    for f in fails:
        print("FAIL:", f)
    print("self-test:", "PASS" if not fails else f"{len(fails)} FAIL")
    return 0 if not fails else 2


def main() -> None:
    a = sys.argv[1:]
    if "--self-test" in a:
        sys.exit(self_test())
    top = int(a[a.index("--top") + 1]) if "--top" in a else 12

    if "--transcript" in a:
        paths = [Path(a[a.index("--transcript") + 1])]
    else:
        paths = find_transcripts(os.getcwd())
        if not paths:
            print("[token-attrib] không tìm thấy transcript cho dự án này — "
                  "truyền --transcript PATH", file=sys.stderr)
            sys.exit(3)
        paths = paths if "--all-sessions" in a else [paths[-1]]

    rows = []
    for p in paths:
        try:
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
        except OSError as e:
            print(f"[token-attrib] KHÔNG đọc được {p} ({e})", file=sys.stderr)
            sys.exit(3)
    if not rows:
        print("[token-attrib] transcript rỗng — không kết luận được", file=sys.stderr)
        sys.exit(3)

    res = analyse(rows)
    if "--json" in a:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        report(res, top, ", ".join(p.name[:8] for p in paths))


if __name__ == "__main__":
    main()
