#!/usr/bin/env bash
# openclaude-install-test.sh — installer --global detect/merge/idempotency cho OpenClaude.
# Mọi HOME và executable đều nằm trong mktemp; không đụng settings thật của user.
set -uo pipefail

SRC="${1:?usage: openclaude-install-test.sh <repo-root>}"
SRC="$(cd "$SRC" && pwd)"
INST="$SRC/harness/scripts/install-harness.sh"
PASS=0; FAIL=0; N=0
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
check() { if "$@"; then ok "$DESC"; else bad "$DESC" "assertion failed"; fi; }

run_global() {
  env HOME="$1" PATH="$2:$NO_OC_PATH" bash "$INST" --global >"$1/install.log" 2>&1
}

BASE_PATH="$PATH"
NO_OC_PATH=""
IFS=:
for d in $BASE_PATH; do
  [ -x "$d/openclaude" ] && continue
  NO_OC_PATH="${NO_OC_PATH:+$NO_OC_PATH:}$d"
done
unset IFS
NO_OC_HOME="$TMP/no-openclaude"
mkdir -p "$NO_OC_HOME/bin"
run_global "$NO_OC_HOME" "$NO_OC_HOME/bin:$NO_OC_PATH"
DESC="OpenClaude vắng: installer không tạo settings scope OpenClaude" check test ! -e "$NO_OC_HOME/.openclaude/settings.json"
DESC="OpenClaude vắng: Claude settings vẫn được cài" check test -f "$NO_OC_HOME/.claude/settings.json"

HOME_OC="$TMP/with-openclaude"
BIN="$HOME_OC/bin"
SETTINGS="$HOME_OC/.openclaude/settings.json"
mkdir -p "$BIN" "$HOME_OC/.openclaude"
printf '#!/bin/sh\nexit 0\n' > "$BIN/openclaude"
chmod +x "$BIN/openclaude"
cat > "$SETTINGS" <<'JSON'
{
  "theme": "dark",
  "env": {
    "KEEP_ME": "yes",
    "CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS": "45000"
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "/tmp/orca-hook.sh", "timeout": 10},
          {"type": "command", "command": "if [ -d \"${CLAUDE_PROJECT_DIR:-.}/llmwiki\" ]; then python3 \"$HOME/.claude/harness/hooks/pre_tool_use.py\"; fi", "timeout": 5}
        ]
      }
    ],
    "Notification": [
      {"matcher": "*", "hooks": [{"type": "command", "command": "/tmp/notify.sh"}]},
      {"matcher": "metadata-only", "description": "keep definition without hooks"}
    ],
    "PostToolUseFailure": [
      {"matcher": "Bash", "hooks": [
        {"type": "command", "command": "printf %s \"$HOME/.claude/harness/hooks\" > /tmp/user-audit.log"},
        {"type": "command", "command": "printf '%s\\n' 'then python3 \"$HOME/.claude/harness/hooks/user-reference.py\"'"},
        {"type": "command", "command": "printf '%s\\n' then python3 \"$HOME/.claude/harness/hooks/unquoted-reference.py\""}
      ]}
    ]
  }
}
JSON

run_global "$HOME_OC" "$BIN"
DESC="OpenClaude có mặt: settings JSON hợp lệ" check python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$SETTINGS"
DESC="merge giữ nguyên setting và env user" check python3 - "$SETTINGS" <<'PY'
import json, sys
x=json.load(open(sys.argv[1]))
assert x["theme"] == "dark" and x["env"]["KEEP_ME"] == "yes"
assert x["env"]["CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS"] == "45000"
PY
DESC="merge giữ hook Orca, hook user nhắc path và definition metadata-only" check python3 - "$SETTINGS" <<'PY'
import json, sys
x=json.load(open(sys.argv[1]))
commands=[h["command"] for defs in x["hooks"].values() for d in defs for h in d.get("hooks", [])]
assert "/tmp/orca-hook.sh" in commands and "/tmp/notify.sh" in commands
assert 'printf %s "$HOME/.claude/harness/hooks" > /tmp/user-audit.log' in commands
assert 'printf \'%s\\n\' \'then python3 "$HOME/.claude/harness/hooks/user-reference.py"\'' in commands
assert 'printf \'%s\\n\' then python3 "$HOME/.claude/harness/hooks/unquoted-reference.py"' in commands
assert any(d.get("matcher") == "metadata-only" and "hooks" not in d
           for d in x["hooks"]["Notification"])
PY
DESC="hook harness canonical được cài đủ, timeout 30s" check python3 - "$SETTINGS" <<'PY'
import json, sys
x=json.load(open(sys.argv[1]))
expected={
 "pre_tool_use.py", "orca_guard.py", "post_tool_use.py", "stop.py",
 "session_end.py", "session_start.py", "code_graph_keeper.py", "user_prompt_submit.py"
}
owned=[]
for defs in x["hooks"].values():
    for d in defs:
        for h in d.get("hooks", []):
            if ".harness-stamp" in h.get("command", "") and "$HOME/.claude/harness/hooks/" in h.get("command", ""):
                owned.append(h)
assert len(owned) == len(expected)
assert {h["command"].split("/hooks/",1)[1].split('"',1)[0] for h in owned} == expected
assert all(h["timeout"] == 30 for h in owned)
assert all(".harness-stamp" in h["command"] for h in owned)
pre_matchers=[d.get("matcher", "") for d in x["hooks"]["PreToolUse"]]
post_matchers=[d.get("matcher", "") for d in x["hooks"]["PostToolUse"]]
assert any("MultiEdit" in m for m in pre_matchers)
assert any("MultiEdit" in m for m in post_matchers)
PY
DESC="installer thay hook harness-owned canonical cũ thay vì nhân đôi" check python3 - "$SETTINGS" <<'PY'
import json, sys
x=json.load(open(sys.argv[1]))
commands=[h["command"] for defs in x["hooks"].values() for d in defs for h in d.get("hooks", [])]
canonical='if [ -f "${CLAUDE_PROJECT_DIR:-.}/llmwiki/.harness-stamp" ]; then python3 "$HOME/.claude/harness/hooks/pre_tool_use.py"; fi'
legacy='if [ -d "${CLAUDE_PROJECT_DIR:-.}/llmwiki" ]; then python3 "$HOME/.claude/harness/hooks/pre_tool_use.py"; fi'
assert commands.count(canonical) == 1
assert legacy not in commands
PY

FIRST=$(python3 - "$SETTINGS" <<'PY'
import json, sys
x=json.load(open(sys.argv[1]))
print(sum(".harness-stamp" in h.get("command", "") and "$HOME/.claude/harness/hooks/" in h.get("command", "") for ds in x["hooks"].values() for d in ds for h in d.get("hooks", [])))
PY
)
run_global "$HOME_OC" "$BIN"
SECOND=$(python3 - "$SETTINGS" <<'PY'
import json, sys
x=json.load(open(sys.argv[1]))
print(sum(".harness-stamp" in h.get("command", "") and "$HOME/.claude/harness/hooks/" in h.get("command", "") for ds in x["hooks"].values() for d in ds for h in d.get("hooks", [])))
PY
)
[ "$FIRST" = "8" ] && [ "$SECOND" = "8" ] && ok "re-run idempotent: vẫn đúng 8 hook harness" || bad "re-run idempotent" "first=$FIRST second=$SECOND"
BACKUPS=$(python3 - "$HOME_OC/.openclaude" <<'PY'
import pathlib, sys
print(len(list(pathlib.Path(sys.argv[1]).glob("settings.json.bak.*"))))
PY
)
[ "$BACKUPS" -ge 2 ] && ok "re-run cùng giây giữ backup riêng, không ghi đè" || bad "backup unique" "chỉ có $BACKUPS backup"

BROKEN_HOME="$TMP/broken-json"
BROKEN_BIN="$BROKEN_HOME/bin"
BROKEN_SETTINGS="$BROKEN_HOME/.openclaude/settings.json"
mkdir -p "$BROKEN_BIN" "$BROKEN_HOME/.openclaude"
printf '#!/bin/sh\nexit 0\n' > "$BROKEN_BIN/openclaude"; chmod +x "$BROKEN_BIN/openclaude"
printf '{not json\n' > "$BROKEN_SETTINGS"
if run_global "$BROKEN_HOME" "$BROKEN_BIN"; then
  ok "OpenClaude JSON hỏng không làm hỏng cài đặt Claude global"
else
  bad "OpenClaude JSON hỏng" "installer global exit≠0"
fi
VALUE=$(python3 - "$BROKEN_SETTINGS" <<'PY'
import pathlib, sys
print(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"), end="")
PY
)
[ "$VALUE" = "{not json" ] && ok "OpenClaude JSON hỏng được giữ nguyên" || bad "giữ JSON hỏng" "file bị thay đổi"

SHAPE_CASES=(
  'nonstandard-number|{"theme":NaN}'
  'root|[]'
  'env|{"env":"bad"}'
  'hooks|{"hooks":"bad"}'
  'event|{"hooks":{"PreToolUse":"bad"}}'
  'definition|{"hooks":{"PreToolUse":["bad"]}}'
  'entry|{"hooks":{"PreToolUse":[{"hooks":[{"command":7}]}]}}'
)
for spec in "${SHAPE_CASES[@]}"; do
  label=${spec%%|*}
  value=${spec#*|}
  home="$TMP/broken-shape-$label"
  bin="$home/bin"
  settings="$home/.openclaude/settings.json"
  original="$home/original.json"
  mkdir -p "$bin" "$home/.openclaude"
  printf '#!/bin/sh\nexit 0\n' > "$bin/openclaude"; chmod +x "$bin/openclaude"
  printf '%s\n' "$value" > "$settings"
  cp "$settings" "$original"
  if run_global "$home" "$bin" \
      && cmp -s "$settings" "$original" \
      && test -f "$home/.claude/settings.json" \
      && compgen -G "$home/.openclaude/settings.json.bak.*" >/dev/null; then
    ok "OpenClaude cấu trúc sai ($label): bỏ qua an toàn, giữ file + backup, Claude vẫn cài"
  else
    bad "OpenClaude cấu trúc sai ($label)" "installer lỗi, file đổi, thiếu backup, hoặc Claude chưa cài"
  fi
done

SURROGATE_HOME="$TMP/lone-surrogate"
SURROGATE_BIN="$SURROGATE_HOME/bin"
SURROGATE_SETTINGS="$SURROGATE_HOME/.openclaude/settings.json"
mkdir -p "$SURROGATE_BIN" "$SURROGATE_HOME/.openclaude"
printf '#!/bin/sh\nexit 0\n' > "$SURROGATE_BIN/openclaude"; chmod +x "$SURROGATE_BIN/openclaude"
printf '{"label":"\\ud800"}\n' > "$SURROGATE_SETTINGS"
if run_global "$SURROGATE_HOME" "$SURROGATE_BIN" \
    && python3 - "$SURROGATE_SETTINGS" <<'PY'
import json, sys
x=json.load(open(sys.argv[1], encoding="utf-8"))
assert x["label"] == "\ud800"
assert len(x["hooks"]) == 6
PY
then
  ok "OpenClaude lone surrogate: merge atomic không truncate settings"
else
  bad "OpenClaude lone surrogate" "installer lỗi, settings bị truncate, hoặc hook chưa merge"
fi

# settings.json là file NGƯỜI sửa tay: merge không được siết quyền file, không được escape
# chữ có dấu thành \uXXXX. (mkstemp đẻ 0600 + ensure_ascii=True làm cả hai — đo 2026-08-02.)
PRESERVE_HOME="$TMP/preserve"
PRESERVE_BIN="$PRESERVE_HOME/bin"
PRESERVE_SETTINGS="$PRESERVE_HOME/.openclaude/settings.json"
mkdir -p "$PRESERVE_BIN" "$PRESERVE_HOME/.openclaude"
printf '#!/bin/sh\nexit 0\n' > "$PRESERVE_BIN/openclaude"; chmod +x "$PRESERVE_BIN/openclaude"
printf '{"greeting":"Chào bạn — hook tiếng Việt"}\n' > "$PRESERVE_SETTINGS"
chmod 644 "$PRESERVE_SETTINGS"
run_global "$PRESERVE_HOME" "$PRESERVE_BIN"
if python3 - "$PRESERVE_SETTINGS" <<'PY'
import json, os, stat, sys
p=sys.argv[1]
raw=open(p, encoding="utf-8").read()
assert "Chào bạn — hook tiếng Việt" in raw, "chữ có dấu bị escape thành \\uXXXX"
assert json.loads(raw)["greeting"] == "Chào bạn — hook tiếng Việt"
mode=stat.S_IMODE(os.stat(p).st_mode)
assert mode == 0o644, oct(mode)
PY
then
  ok "merge giữ nguyên quyền file (644) và chữ có dấu không bị escape"
else
  bad "giữ quyền + UTF-8" "mode bị siết hoặc chữ có dấu bị escape"
fi

# Fresh: openclaude có mặt nhưng máy chưa từng có ~/.openclaude — phải TỰ tạo settings đủ 8 hook.
FRESH_HOME="$TMP/fresh"
FRESH_BIN="$FRESH_HOME/bin"
FRESH_SETTINGS="$FRESH_HOME/.openclaude/settings.json"
mkdir -p "$FRESH_BIN"
printf '#!/bin/sh\nexit 0\n' > "$FRESH_BIN/openclaude"; chmod +x "$FRESH_BIN/openclaude"
if run_global "$FRESH_HOME" "$FRESH_BIN" \
    && python3 - "$FRESH_SETTINGS" <<'PY'
import json, sys
x=json.load(open(sys.argv[1]))
owned=[h for ds in x["hooks"].values() for d in ds for h in d.get("hooks", [])
       if ".harness-stamp" in h.get("command", "")]
assert len(owned) == 8, owned
assert x["env"]["CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS"] == "30000"
PY
then
  ok "chưa có ~/.openclaude: installer tạo settings đủ 8 hook + timeout 30000ms"
else
  bad "fresh ~/.openclaude" "settings chưa được tạo đúng"
fi

# ~/.openclaude là FILE: mkdir -p đỏ. Không guard thì set -e giết installer NGAY SAU khi
# ~/.claude/settings.json đã merge và TRƯỚC smoke validator → user nhận bản cài dở, cổng tự kiểm im.
FILE_HOME="$TMP/openclaude-is-file"
FILE_BIN="$FILE_HOME/bin"
mkdir -p "$FILE_BIN"
printf '#!/bin/sh\nexit 0\n' > "$FILE_BIN/openclaude"; chmod +x "$FILE_BIN/openclaude"
printf 'not a directory\n' > "$FILE_HOME/.openclaude"
if run_global "$FILE_HOME" "$FILE_BIN" \
    && grep -q "GLOBAL smoke OK" "$FILE_HOME/install.log" \
    && [ "$(cat "$FILE_HOME/.openclaude")" = "not a directory" ] \
    && test -f "$FILE_HOME/.claude/settings.json"; then
  ok "~/.openclaude là file: warn rồi bỏ qua, Claude global vẫn cài xong + chạy smoke"
else
  bad "~/.openclaude là file" "installer lỗi, smoke không chạy, file bị đổi, hoặc Claude chưa cài"
fi

# ~/.openclaude không ghi được: cp backup và ghi atomic đều đỏ — cùng lớp lỗi với case trên.
# Bỏ qua khi chạy dưới root: root ghi xuyên mode 555 nên case này không dựng được.
RO_HOME="$TMP/openclaude-readonly"
RO_BIN="$RO_HOME/bin"
RO_SETTINGS="$RO_HOME/.openclaude/settings.json"
mkdir -p "$RO_BIN" "$RO_HOME/.openclaude"
printf '#!/bin/sh\nexit 0\n' > "$RO_BIN/openclaude"; chmod +x "$RO_BIN/openclaude"
printf '{"theme":"dark"}\n' > "$RO_SETTINGS"
if [ "$(id -u)" = "0" ]; then
  printf '  \033[1;33mSKIP\033[0m  ~/.openclaude read-only (chạy dưới root)\n'
else
  chmod 555 "$RO_HOME/.openclaude"
  if run_global "$RO_HOME" "$RO_BIN" \
      && grep -q "GLOBAL smoke OK" "$RO_HOME/install.log" \
      && [ "$(cat "$RO_SETTINGS")" = '{"theme":"dark"}' ]; then
    ok "~/.openclaude read-only: warn rồi bỏ qua, Claude global vẫn cài xong + chạy smoke"
  else
    bad "~/.openclaude read-only" "installer lỗi, smoke không chạy, hoặc settings bị đổi"
  fi
  chmod 755 "$RO_HOME/.openclaude"
fi

LOW_HOME="$TMP/low-timeout"
LOW_BIN="$LOW_HOME/bin"
LOW_SETTINGS="$LOW_HOME/.openclaude/settings.json"
mkdir -p "$LOW_BIN" "$LOW_HOME/.openclaude"
printf '#!/bin/sh\nexit 0\n' > "$LOW_BIN/openclaude"; chmod +x "$LOW_BIN/openclaude"
printf '{"env":{"CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS":"1000"}}\n' > "$LOW_SETTINGS"
run_global "$LOW_HOME" "$LOW_BIN"
VALUE=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["env"]["CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS"])' "$LOW_SETTINGS")
[ "$VALUE" = "30000" ] && ok "SessionEnd parent timeout thấp được nâng lên 30000ms" || bad "SessionEnd timeout" "got $VALUE"

# Cùng khoá nhưng kiểu số (JSON number, không phải string) và đã cao hơn ngưỡng — không được hạ.
HIGH_HOME="$TMP/high-timeout-int"
HIGH_BIN="$HIGH_HOME/bin"
HIGH_SETTINGS="$HIGH_HOME/.openclaude/settings.json"
mkdir -p "$HIGH_BIN" "$HIGH_HOME/.openclaude"
printf '#!/bin/sh\nexit 0\n' > "$HIGH_BIN/openclaude"; chmod +x "$HIGH_BIN/openclaude"
printf '{"env":{"CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS":45000}}\n' > "$HIGH_SETTINGS"
run_global "$HIGH_HOME" "$HIGH_BIN"
VALUE=$(python3 -c 'import json,sys; print(repr(json.load(open(sys.argv[1]))["env"]["CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS"]))' "$HIGH_SETTINGS")
[ "$VALUE" = "45000" ] && ok "SessionEnd timeout kiểu số đã cao hơn 30000ms được giữ nguyên" || bad "SessionEnd timeout cao" "got $VALUE"

printf '\n%d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 2
