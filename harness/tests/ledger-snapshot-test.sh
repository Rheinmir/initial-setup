#!/usr/bin/env bash
# ledger-snapshot-test — ký ức máy-local phải SỐNG SÓT round-trip, và backup phải TỰ chạy.
# Maintainer #2: ledger gitignored một máy = mất máy mất não. 4 chiều:
#   round-trip (export→restore ra dữ liệu y nguyên) · dedupe (restore 2 lần không nhân đôi)
#   · loại baseline (không chở rác regen được) · SessionEnd có wire (backup không chờ ai nhớ).
set -u
ROOT="$(cd "${1:-.}" && pwd)"
SNAP="$ROOT/harness/scripts/ledger-snapshot.py"
fail=0
ok(){ printf '  \033[1;32m✓\033[0m %s\n' "$1"; }
bad(){ printf '  \033[1;31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }

# 1-3. round-trip + dedupe + loại-baseline: chính self-test của tool (tất định, tmp)
python3 "$SNAP" --self-test >/dev/null 2>&1 \
  && ok "self-test: round-trip + dedupe + loại baseline" || bad "self-test FAIL"

# 4. export trên repo THẬT (đích tmp — không đụng snapshot thật) chứa đúng ledger lõi
SD="$(mktemp -d)"
OVERSTACK_SNAPSHOT_DIR="$SD" python3 "$SNAP" export --quiet --root "$ROOT"
TAR=$(ls "$SD"/snap-*.tar.gz 2>/dev/null | head -1)
if [ -n "$TAR" ]; then
  ok "export repo thật ra tarball ($(du -k "$TAR" | cut -f1)KB)"
  # failures.jsonl là ledger LOCAL gitignored — fresh clone (CI) không có là ĐÚNG;
  # chỉ khi máy này CÓ ledger mà tarball thiếu mới là bug.
  if [ -f "$ROOT/harness/metrics/failures.jsonl" ]; then
    tar -tzf "$TAR" | grep -q "harness/metrics/failures.jsonl" \
      && ok "chứa flywheel failures.jsonl (ký ức đắt nhất)" || bad "thiếu failures.jsonl"
  else
    ok "repo không có failures.jsonl (fresh clone) — miễn assert nội dung"
  fi
  tar -tzf "$TAR" | grep -q "baseline" \
    && bad "chở cả baseline (rác regen được)" || ok "không chở baseline"
else
  bad "export không ra tarball"
fi
rm -rf "$SD"

# 5. SessionEnd hook có wire snapshot (backup tự chạy, không chờ ai nhớ)
grep -q "ledger-snapshot" "$ROOT/llmwiki/.claude/hooks/session_end.py" \
  && ok "SessionEnd wire snapshot_ledgers (fail-open)" \
  || bad "SessionEnd KHÔNG gọi snapshot — backup lại thành việc phải nhớ"

[ "$fail" -eq 0 ] && { printf '\n\033[1m═══ ledger-snapshot: \033[1;32mPASS\033[0m\033[0m\n'; exit 0; }
printf '\n\033[1m═══ ledger-snapshot: \033[1;31m%d VI PHẠM\033[0m\033[0m\n' "$fail"; exit 1
