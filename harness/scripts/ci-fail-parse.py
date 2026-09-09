#!/usr/bin/env python3
"""Cắt log CI đỏ thành KHỐI CẤU TRÚC để agent đoán ngay được, thay vì một cục log.

Đọc `gh run view --log-failed` trên stdin (bytes, có ANSI, có thể lẫn byte không
UTF-8 — nên đọc nhị phân rồi decode errors="replace"; sed/awk/cut trên macOS gãy ở
đúng chỗ này). In ra YAML một tầng + phần log đã cắt.

Chỉ bám quy ước in của CHÍNH repo này (ok()/bad() trong harness/tests/*.sh,
`↳ sửa:` của medic, `✗` của 35 tool). Không khớp thì khai parsed:false và để log
thô lại — thà nói không biết còn hơn đoán sai cho agent.

    gh run view <id> --log-failed | python3 harness/scripts/ci-fail-parse.py
    python3 harness/scripts/ci-fail-parse.py --self-test
"""
import re, sys

# GitHub trả màu ở HAI dạng: ESC thật, và caret-notation "^[" (hai ký tự) tuỳ job.
ANSI = re.compile(r"(?:\x1b|\^\[)\[[0-9;]*m")
TS = re.compile(r"^[0-9T:.Z-]{20,} ")
FAILED = re.compile(r"^\s*(?:✗|FAIL)\s+(.*)$")
TALLY = re.compile(r"\b\d+/\d+ pass\b|TỔNG:.*")
EXIT = re.compile(r"exit code (\d+)")
HINT = re.compile(r"↳ sửa:\s*(.+)|—\s*(chạy .+)")
RUNCMD = "##[group]Run "
WINDOW = 25


def parse(raw: bytes):
    lines = ANSI.sub("", raw.decode("utf-8", "replace")).splitlines()
    step = ""
    body = []          # dòng đã bỏ cột job/step/timestamp, song song với lines
    for ln in lines:
        col = ln.split("\t")
        body.append(TS.sub("", col[2] if len(col) > 2 else col[-1]))
    err = next((i for i in range(len(lines) - 1, -1, -1) if "##[error]" in lines[i]), None)
    if err is None:
        return {"parsed": False}, body[-WINDOW:]

    col = lines[err].split("\t")
    step = col[1] if len(col) > 2 else ""
    cmd = ""
    for i in range(err, -1, -1):
        c = lines[i].split("\t")
        if (len(c) > 2 and c[1] == step or not step) and RUNCMD in body[i]:
            cmd = body[i].split(RUNCMD, 1)[1].strip()
            break

    cut = body[max(0, err - WINDOW + 1):err + 1]
    checks = [m.group(1).strip() for ln in cut if (m := FAILED.match(ln))]
    tally = next((m.group(0) for ln in reversed(cut) if (m := TALLY.search(ln))), "")
    code = next((m.group(1) for ln in reversed(cut) if (m := EXIT.search(ln))), "")
    hint = ""
    for ln in reversed(cut):
        if m := HINT.search(ln):
            hint = (m.group(1) or m.group(2)).strip()
            break
    return {"parsed": bool(checks or tally or cmd), "failed_step": step,
            "repro_cmd": cmd, "exit_code": code, "tally": tally,
            "fix_hint": hint, "failed_checks": checks}, cut


def emit(meta, cut, out=sys.stdout):
    def q(v):
        return '"%s"' % str(v).replace('\\', '\\\\').replace('"', '\\"') if v else '""'
    for k in ("parsed", "failed_step", "repro_cmd", "exit_code", "tally", "fix_hint"):
        v = meta.get(k, "")
        print(f"  {k}: " + ("true" if v is True else "false" if v is False else q(v)), file=out)
    print("  failed_checks:" + (" []" if not meta.get("failed_checks") else ""), file=out)
    for c in meta.get("failed_checks", [])[:8]:
        print("    - " + q(c), file=out)
    print("---LOG---", file=out)
    print("\n".join(cut), file=out)


def self_test():
    def line(step, msg):
        return f"job\t{step}\t2026-09-09T07:50:43.8607249Z {msg}"
    raw = "\n".join([
        line("check", "##[group]Run python3 fdk/tools/skill-provenance.py check --ci"),
        line("check", "\x1b[1;31m✗\x1b[0m MODIFIED  doyourmagic  — lệch: SKILL.md"),
        line("check", "✗ skill-provenance: 2 vấn đề — chạy `record` để cập nhật sổ."),
        line("check", "##[error]Process completed with exit code 1."),
    ]).encode()
    m, cut = parse(raw)
    assert m["parsed"] and m["failed_step"] == "check", m
    assert m["repro_cmd"] == "python3 fdk/tools/skill-provenance.py check --ci", m
    assert m["exit_code"] == "1" and m["fix_hint"].startswith("chạy `record`"), m
    assert len(m["failed_checks"]) == 2 and m["failed_checks"][0].startswith("MODIFIED"), m

    # ANSI quanh FAIL (bad() của harness/tests/*.sh) vẫn phải nhận ra.
    raw2 = "\n".join([
        line("gate", "##[group]Run bash harness/tests/ge-backcompat-test.sh ."),
        line("gate", "  \x1b[1;31mFAIL\x1b[0m  backcompat loop-runner — rò field mới"),
        line("gate", "  13/14 pass"),
        line("gate", "##[error]Process completed with exit code 2."),
    ]).encode()
    m2, _ = parse(raw2)
    assert m2["failed_checks"] == ["backcompat loop-runner — rò field mới"], m2
    assert m2["tally"] == "13/14 pass" and m2["exit_code"] == "2", m2

    # Màu dạng caret-notation "^[" (hai ký tự) — GitHub trả dạng này ở một số job.
    raw3 = raw2.decode().replace("\x1b", "^[").encode()
    m3, _ = parse(raw3)
    assert m3["failed_checks"] == ["backcompat loop-runner — rò field mới"], m3

    # Byte không UTF-8 không được làm sập (đúng chỗ sed/cut của macOS gãy).
    assert parse(b"job\ts\t2026-09-09T07:50:43.8607249Z \xff\xfe x")[0]["parsed"] is False

    # Không có ##[error] → khai không parse được, KHÔNG bịa.
    assert parse(b"nothing here")[0] == {"parsed": False}
    print("ci-fail-parse self-test: 5/5 pass")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        emit(*parse(sys.stdin.buffer.read()))
