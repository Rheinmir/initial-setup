#!/usr/bin/env python3
"""gen-converters — đọc policy.yaml, SINH wiring cho từng vendor vào out/.

MỘT nguồn (policy.yaml) → nhiều adapter MỎNG. Mỗi file sinh ra có header GENERATED:
đừng sửa tay — sửa policy.yaml rồi chạy lại. Đây chính là "luồng cài đặt" B2/B3:
mỗi vendor được ghi WIRING native, KHÔNG vendor nào cần MCP.

Phân tầng (đã kiểm chứng 2026-06-25):
  deny-được, dùng native + CLI : claude (hook→CLI) · opencode (permission.edit:deny) · antigravity (Deny-rule)
  chỉ-nhắc (advisory text)      : cursor · codex · kiro
  phủ MỌI vendor (sàn đảm bảo)  : pre-commit + CI (gọi CLI files mode)
"""
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("gen-converters: cần pyyaml (pip install pyyaml)")

HERE = os.path.dirname(os.path.abspath(__file__))
POLICY = os.path.join(HERE, "policy.yaml")
OUT = os.path.join(HERE, "out")
# Đường gọi CLI trong các config sinh ra (chỉnh theo vị trí harness thực tế của bạn).
CLI = "harness/poc-vendor-neutral/bin/llmwiki-validate.py"
GEN = "# ⚙️  GENERATED FROM policy.yaml — đừng sửa tay; sửa policy.yaml rồi chạy gen-converters.py"


def write(rel, content):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✎ out/{rel}")


def main():
    with open(POLICY, encoding="utf-8") as f:
        policy = yaml.safe_load(f)
    rules = policy.get("rules", {})
    deny = {n: r for n, r in rules.items() if r.get("kind") == "deny_write"}
    deny_globs = [g for r in deny.values() for g in r.get("deny_write_globs", [])]
    statements = [f"- ({r.get('id')}) {r.get('statement')}" for r in rules.values()]

    print("gen-converters: sinh wiring từ policy.yaml →")

    # ---- 1. Claude — PreToolUse (lõi chặn) + 4 hook sự kiện R3/R4/R8/R10 ----
    import json
    EVT = "harness/poc-vendor-neutral/bin/harness-events.py"
    def _ev(c, t=15): return [{"type": "command", "command": c, "timeout": t}]
    # CHẶN-ĐƯỢC (PreToolUse/Stop): exec giữ exit 2 khi script chặn; file THIẾU → exit 0 (fail-open, không khoá cứng)
    def _block(f, a): return f'[ -f "$CLAUDE_PROJECT_DIR/{f}" ] && exec python3 "$CLAUDE_PROJECT_DIR/{f}" {a} || exit 0'
    # KHÔNG-CHẶN (PostToolUse/SessionStart/UserPromptSubmit): LUÔN exit 0 — file thiếu/lỗi KHÔNG bao giờ chặn input
    def _info(f, a): return f'python3 "$CLAUDE_PROJECT_DIR/{f}" {a} 2>/dev/null || true'
    # R3/R4/R8/R10 — SINH hook từ hook_event rules trong policy.yaml (policy-drives-wiring).
    # Trước đây hardcode; giờ policy là nguồn DUY NHẤT cho cả semantics LẪN wiring.
    # blocking=true → _block (giữ exit 2); false → _info (luôn exit 0). matcher/timeout optional.
    hook_events = {}
    for r in rules.values():
        if r.get("kind") != "hook_event":
            continue
        ev, action = r.get("event"), r.get("event_action")
        if not ev or not action:
            continue   # hook_event thiếu field máy → bỏ qua; drift-test sẽ bắt (event không wired)
        cmd = _block(EVT, action) if r.get("blocking") else _info(EVT, action)
        entry = {"hooks": _ev(cmd, r.get("timeout", 15))}
        if r.get("matcher"):
            entry["matcher"] = r["matcher"]
        hook_events.setdefault(ev, []).append(entry)
    claude = {
        "_generated": GEN,
        "hooks": {
            # PreToolUse = cổng content-rule (validator claude-hook), gộp R1/R2/R5/R7/R9 — giữ hardcode
            "PreToolUse": [{"matcher": "Write|Edit|MultiEdit|Bash", "hooks": _ev(_block(CLI, "claude-hook"))}],
            **hook_events,   # Stop(R3)/PostToolUse(R4)/SessionStart(R8)/UserPromptSubmit(R10) ← policy
        },
    }
    write("claude/settings.snippet.json", json.dumps(claude, ensure_ascii=False, indent=2) + "\n")

    # ---- 2. opencode (deny: permission.edit:deny NATIVE — không cần CLI lúc chạy) ----
    perm = {"*": "allow"}
    for g in deny_globs:
        perm[g] = "deny"
    opencode = {
        "$schema": "https://opencode.ai/config.json",
        "_generated": GEN,
        "permission": {"edit": perm},
    }
    write("opencode/opencode.json", json.dumps(opencode, ensure_ascii=False, indent=2) + "\n")
    # plugin gọi CLI (cho luật permission-glob không diễn tả được, vd require_origin)
    plugin = f"""// {GEN}
// opencode plugin: gọi CÙNG CLI lõi cho các luật mà permission.edit không biểu diễn được.
export const HarnessPlugin = async ({{ $ }}) => ({{
  "tool.execute.before": async (input, output) => {{
    if (!["edit", "write", "patch"].includes(input.tool)) return;
    const path = (output.args && (output.args.filePath || output.args.path)) || "";
    const res = await $`python3 {CLI} path ${{path}}`.quiet().nothrow();
    if (res.exitCode === 2) throw new Error(res.stderr.toString() || "harness deny");
  }},
}});
"""
    write("opencode/plugin/harness.js", plugin)

    # ---- 3. Antigravity (deny: Permission Deny-rule theo path) ----
    ag = [GEN.replace("# ", "# "), "# Antigravity — Permissions › Deny tier (Deny > Ask > Allow).",
          "# Dán vào cấu hình Permissions của project; chặn TRƯỚC khi ghi.", "Deny:"]
    for g in deny_globs:
        ag.append(f"  - write_file({g})")
    write("antigravity/permissions.snippet.txt", "\n".join(ag) + "\n")

    # ---- 4. advisory (chỉ-nhắc): cursor / codex / kiro ----
    body = "\n".join(statements)
    cursor = f"""---
description: llmwiki harness rules (advisory — KHÔNG enforce; sàn đảm bảo là CI)
alwaysApply: true
---
{GEN}

# Quy tắc harness (bắt buộc tuân)
{body}

> ⚠️ Cursor không có hook chặn ghi-file trực tiếp → đây chỉ là NHẮC. Đảm bảo thật ở CI + pre-commit.
"""
    write("cursor/.cursor/rules/harness.mdc", cursor)
    write("codex/AGENTS.snippet.md",
          f"<!-- {GEN} -->\n\n## Harness rules (advisory)\n{body}\n\n"
          f"> Codex: AGENTS.md hay drift giữa phiên → đây chỉ là NHẮC. Đảm bảo thật ở CI.\n")
    write("kiro/.kiro/steering/harness.md",
          f"<!-- {GEN} -->\n---\ninclusion: always\n---\n\n# Harness rules (advisory)\n{body}\n\n"
          f"> Kiro steering hay bị bỏ qua → NHẮC thôi. Đảm bảo thật ở CI.\n")

    # ---- 5. SÀN: CI (gọi CLI files mode = layer repo) ----
    # v4 (GH#63 Phase 3): repo downstream KHÔNG mang engine — runner TỰ CÀI harness global
    # (install-harness --global từ clone pin theo HARNESS_REF) rồi validate từ ~/.claude/harness/
    # (giải U8 version-skew: đổi HARNESS_REF sang tag/commit để pin cứng). Đây là SÀN đảm bảo —
    # không fail-open: clone/cài lỗi thì CI đỏ đúng nghĩa (mất sàn phải thấy được).
    ci = f"""# {GEN.lstrip('# ')}
name: harness
on: [pull_request, push]
env:
  HARNESS_REPO: https://github.com/Rheinmir/setup.git
  HARNESS_REF: orca            # pin phiên bản harness: nhánh / tag / commit SHA
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: {{ fetch-depth: 0 }}
      - uses: actions/setup-python@v5
        with: {{ python-version: '3.x' }}
      - run: pip install pyyaml
      - name: self-install harness global trên runner (v4 — repo không mang engine)
        run: |
          git clone --depth 1 -b "$HARNESS_REF" "$HARNESS_REPO" "$RUNNER_TEMP/harness-src"
          bash "$RUNNER_TEMP/harness-src/harness/scripts/install-harness.sh" --global
      - name: harness-doctor fire-drill — chứng ref đang pin còn cắn (không dark rail)
        # chạy từ CHECKOUT ĐẦY ĐỦ vừa clone, KHÔNG từ global: global thiếu hooks/pre-commit
        # của repo nên side-effect rail (R4/R8/R10/R17) báo missing = dark-rail GIẢ. Bản
        # $RUNNER_TEMP/harness-src là full repo → 18/18 thật. Mỗi PR tự chứng 18 luật gốc
        # mà downstream đang bị gác vẫn còn cắn — dark rail của framework nổi đỏ TẠI downstream.
        run: python3 "$RUNNER_TEMP/harness-src/harness/scripts/harness-doctor.py" --ci
      - name: harness-local fire-drill — rule RIÊNG dự án còn cắn? (engine mới + rules repo)
        # phủ nốt lỗ harness-doctor không chạm: rule tuỳ biến của downstream. Chạy ENGINE
        # luôn-mới từ harness-src (run.py của repo có thể là bản cũ chưa có firedrill — nếu
        # gọi nó, mode lạ rơi về check và CI degrade ÂM THẦM), trỏ HARNESS_LOCAL_DIR vào
        # rules của repo. Vắng harness-local thì skip (đa số dự án). Rule có validator mà
        # thiếu fixtures bad/good thì đỏ (blind-spot). Bad không chặn thì rule chết, đỏ.
        run: |
          [ -d harness-local ] || {{ echo "no harness-local — skip"; exit 0; }}
          HARNESS_LOCAL_DIR="$PWD/harness-local" python3 "$RUNNER_TEMP/harness-src/harness-local/run.py" firedrill
      - name: harness validator (layer=repo, từ global) trên file .md đổi
        run: |
          base="${{{{ github.event.pull_request.base.sha || github.event.before }}}}"
          files=$(git diff --name-only "$base" HEAD 2>/dev/null | grep -E '\\.md$' || true)
          [ -z "$files" ] && {{ echo "no changed .md"; exit 0; }}
          python3 "$HOME/.claude/harness/{CLI}" files $files
"""
    write("ci/harness.yml", ci)

    # ---- 5b. CRON: wiki-refresh (distill openwiki 2026-07-06) ----
    # Giữ wiki khớp code KHÔNG cần người trông: cổng no-op TẤT ĐỊNH (wiki-sync.py,
    # 0 token) chạy trước — không drift thì kết thúc miễn phí; có drift thì (tuỳ chọn,
    # cần secret ANTHROPIC_API_KEY) gọi LLM sửa surgical, rồi mở PR CHỈ diff wiki cho
    # người review. Không có key vẫn hữu ích: PR mang cờ code-drift trong stale.json
    # để phiên làm việc kế tiếp rà (degrade tử tế, không fail-open im lặng).
    wr = f"""# {GEN.lstrip('# ')}
name: wiki-refresh
on:
  workflow_dispatch:
  schedule:
    - cron: "0 1 * * *"        # 08:00 VN hằng ngày — chỉnh theo nhịp dự án
permissions:
  contents: write
  pull-requests: write
env:
  HARNESS_REPO: https://github.com/Rheinmir/setup.git
  HARNESS_REF: orca            # pin phiên bản harness: nhánh / tag / commit SHA
jobs:
  refresh:
    runs-on: ubuntu-latest
    env:
      ANTHROPIC_API_KEY: ${{{{ secrets.ANTHROPIC_API_KEY }}}}   # không đặt secret → bước LLM tự bỏ qua
    steps:
      - uses: actions/checkout@v4
        with: {{ fetch-depth: 0 }}
      - uses: actions/setup-python@v5
        with: {{ python-version: '3.x' }}
      - name: self-install harness global trên runner (v4 — repo không mang engine)
        run: |
          git clone --depth 1 -b "$HARNESS_REF" "$HARNESS_REPO" "$RUNNER_TEMP/harness-src"
          bash "$RUNNER_TEMP/harness-src/harness/scripts/install-harness.sh" --global
      - name: cổng no-op tất định (0 token) — code có đổi kể từ neo wiki?
        id: drift
        run: |
          set +e
          python3 "$HOME/.claude/harness/harness/scripts/wiki-sync.py" --check --json --root .
          rc=$?
          set -e
          case "$rc" in
            0) echo "status=current" >> "$GITHUB_OUTPUT" ;;
            2|3) echo "status=drift" >> "$GITHUB_OUTPUT" ;;
            *) exit "$rc" ;;
          esac
      - name: LLM sửa wiki surgical (/lint) — chỉ chạy khi có drift VÀ có key
        if: steps.drift.outputs.status == 'drift' && env.ANTHROPIC_API_KEY != ''
        run: |
          npm install -g @anthropic-ai/claude-code
          claude -p "Chạy skill /lint: bước 0 wiki-sync đã cờ code-drift trong llmwiki/wiki/stale.json. Lập docs-impact-plan rồi sửa SURGICAL đúng trang bị ảnh hưởng (soft diff budget, cấm formatting-only). Xong chạy: python3 ~/.claude/harness/harness/scripts/wiki-sync.py --mark-synced --root ." \\
            --allowedTools "Read,Write,Edit,Bash,Grep,Glob"
      - name: mở PR chỉ diff wiki (người review là chốt cuối)
        if: steps.drift.outputs.status == 'drift'
        uses: peter-evans/create-pull-request@v7
        with:
          add-paths: llmwiki/wiki
          branch: wiki-refresh/update
          commit-message: "docs(wiki): wiki-refresh tự động (neo wiki-sync)"
          title: "docs(wiki): wiki-refresh — đồng bộ wiki với code"
          body: |
            PR tự động từ workflow wiki-refresh.
            - Có `ANTHROPIC_API_KEY`: wiki đã được LLM rà + sửa surgical, neo đã chốt.
            - Không có key: PR chỉ mang cờ `code-drift` trong `stale.json` — mở phiên
              Claude local chạy /lint để rà, hoặc thêm secret để tự động hoá trọn.
"""
    write("ci/wiki-refresh.yml", wr)

    # ---- 6. SÀN: pre-commit (gọi CLI files mode) ----
    pc = f"""# {GEN.lstrip('# ')}
# Thêm vào .pre-commit-config.yaml của project:
- repo: local
  hooks:
    - id: llmwiki-harness
      name: llmwiki harness validator (layer=repo)
      entry: python3 {CLI} files
      language: system
      files: '\\.md$'
"""
    write("pre-commit-snippet.yaml", pc)

    print("Xong. Tất cả sinh từ 1 policy.yaml. Sửa luật ở policy.yaml → chạy lại file này.")


if __name__ == "__main__":
    main()
