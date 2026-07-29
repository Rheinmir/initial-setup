#!/usr/bin/env bash
# smoke-test.sh — BỘ TEST CHUẨN của dây chuyền /br: chạy selftest MỌI tool cốt lõi.
# Xanh hết = hệ khoẻ, bắt đầu workflow được. Chạy: bash getting-started/smoke-test.sh
# (đứng ở gốc repo). Không cần app/data — chỉ kiểm tool tất định.
set -u
cd "$(dirname "$0")/.." || exit 2
ROOT="$(pwd)"
pass=0; fail=0; miss=0; warn=0

run() { # <nhãn> <lệnh...>  — test LOGIC tất định (đỏ = chặn)
  local label="$1"; shift
  if "$@" >/tmp/smoke.out 2>&1; then
    echo "  ✓ $label"; pass=$((pass+1))
  else
    echo "  ✗ $label"; tail -2 /tmp/smoke.out | sed 's/^/      /'; fail=$((fail+1))
  fi
}
run_int() { # test INTEGRATION (git worktree/loop end-to-end) — đỏ = CẢNH BÁO, không chặn
  local label="$1"; shift
  if "$@" >/tmp/smoke.out 2>&1; then echo "  ✓ $label"; pass=$((pass+1))
  else echo "  ⚠ $label (integration — env-dependent, xem README §Troubleshoot)"; warn=$((warn+1)); fi
}

echo "== BỘ TEST CHUẨN dây chuyền /br (selftest tất định) =="
echo "-- gác & lõi --"
run "frame-lint (9 luật R1-R9 + manifest)" python3 fdk/tools/frame-lint.py selftest
run "loop-runner (6 phanh)"                python3 harness/scripts/loop-runner.py selftest
echo "-- mode /br --"
run_int "br-run (integration: git worktree + loop)" python3 fdk/tools/br-run.py selftest
run "br-queue"      python3 fdk/tools/br-queue.py selftest
run "br-revise"     python3 fdk/tools/br-revise.py selftest
run "br-prompts"    python3 fdk/tools/br-prompts.py selftest
run "br-find"       python3 fdk/tools/br-find.py selftest
run "br-contract (UI Contract)"  python3 fdk/tools/br-contract.py selftest
run "br-sync (GitHub issue)"     python3 fdk/tools/br-sync.py selftest
run "loop-cost"     python3 fdk/tools/loop-cost.py selftest
run "build-line-status (status)" python3 fdk/tools/build-line-status.py selftest
run "checkpoint (rollback)"      python3 fdk/tools/checkpoint.py selftest
echo "-- công tắc & phụ trợ --"
run "br-rail (toggle harness)"   python3 fdk/tools/br-rail.py selftest
run "unknown (ledger mơ hồ)"     python3 fdk/tools/unknown.py selftest
echo "-- sức khoẻ tổng --"
run "harness-doctor (17 rail)"   python3 harness/scripts/harness-doctor.py --ci

echo "------------------------------------------------------------"
echo "  KẾT: $pass pass · $fail fail · $warn warn(integration)"
[ "$fail" -eq 0 ] && { echo "  ✅ HỆ KHOẺ (logic tất định xanh) — bắt đầu workflow được (xem getting-started/README.md)"; [ "$warn" -gt 0 ] && echo "     (⚠ $warn integration-test env-dependent — không chặn)"; exit 0; }
echo "  ❌ CÓ TOOL LOGIC ĐỎ — sửa trước khi chạy workflow"; exit 1
