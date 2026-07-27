#!/usr/bin/env bash
# wiki-sync-test.sh — chứng minh neo code→wiki hoạt động đúng (8 assertion).
# Sandbox: git repo tạm trong $TMPDIR, không đụng repo thật.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SYNC="$HERE/../scripts/wiki-sync.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
assert() { # assert <mô tả> <exit-mong-đợi> <exit-thật>
  if [ "$2" = "$3" ]; then pass=$((pass+1)); echo "  ✓ $1"
  else echo "  ✗ $1 (mong exit $2, được $3)"; exit 1; fi
}

cd "$TMP"
git init -q -b main
git config user.email t@t && git config user.name t
mkdir -p llmwiki/wiki/concepts src
cat > llmwiki/wiki/concepts/app-core.md <<'EOF'
---
type: concept
---
# app-core
Xử lý chính nằm ở `src/app.py`.
## Origin
- test fixture
EOF
echo "print('v1')" > src/app.py
git add -A && git -c core.hooksPath=/dev/null commit --no-verify -qm init

# 1. chưa có neo → exit 2 (nhắc --mark-synced)
rc=0; python3 "$SYNC" --check >/dev/null || rc=$?
assert "chưa neo → exit 2" 2 "$rc"

# 2. mark-synced lần đầu → exit 0, tạo .last-sync.json
rc=0; python3 "$SYNC" --mark-synced >/dev/null || rc=$?
assert "mark-synced tạo neo" 0 "$rc"
[ -f llmwiki/wiki/.last-sync.json ] || { echo "  ✗ thiếu .last-sync.json"; exit 1; }

# 3. không gì đổi → no-op exit 0 (cổng 0 token)
rc=0; python3 "$SYNC" --check >/dev/null || rc=$?
assert "không đổi → no-op exit 0" 0 "$rc"

# 4. chỉ wiki đổi (không code) → vẫn no-op (parity openwiki)
echo "- ghi chú thêm" >> llmwiki/wiki/concepts/app-core.md
git add -A && git -c core.hooksPath=/dev/null commit --no-verify -qm "docs: wiki only"
rc=0; python3 "$SYNC" --check >/dev/null || rc=$?
assert "chỉ wiki đổi → vẫn no-op" 0 "$rc"

# 5. code đổi → exit 3 + trang nhắc tới file bị cờ code-drift
echo "print('v2')" > src/app.py
git add -A && git -c core.hooksPath=/dev/null commit --no-verify -qm "feat: change app"
rc=0; out=$(python3 "$SYNC" --check --json) || rc=$?
assert "code đổi → drift exit 3" 3 "$rc"
echo "$out" | python3 -c "
import json,sys
d=json.load(sys.stdin)
assert d['status']=='drift' and 'src/app.py' in d['changed'], d
assert 'concepts/app-core.md' in d['suspects'], d['suspects']"
python3 -c "
import json
s=json.load(open('llmwiki/wiki/stale.json'))
assert s['concepts/app-core.md']['action']=='code-drift', s"
pass=$((pass+1)); echo "  ✓ suspect map + stale.json action=code-drift"

# 6. mark-synced sau rà → exit 0, xoá cờ code-drift, neo mới
rc=0; python3 "$SYNC" --mark-synced >/dev/null || rc=$?
assert "mark-synced sau rà" 0 "$rc"
python3 -c "
import json
s=json.load(open('llmwiki/wiki/stale.json'))
assert not any(v.get('action')=='code-drift' for v in s.values()), s"
rc=0; python3 "$SYNC" --check >/dev/null || rc=$?
assert "sau neo lại → current" 0 "$rc"

echo "wiki-sync-test: $pass/8 assertion XANH"
