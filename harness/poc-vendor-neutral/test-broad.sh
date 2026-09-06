#!/usr/bin/env bash
# test-broad.sh — bộ test RỘNG cho lõi: false-positive, normalize, bash bypass,
# require_origin biên, files-mode, claude-hook hỏng, và KNOWN GAPS (chứng minh vì sao cần CI).
set -uo pipefail
cd "$(dirname "$0")"
CLI="bin/llmwiki-validate.py"
T=0; P=0; F=0
assert(){ local want="$1" desc="$2" got="$3"; T=$((T+1))
  if [ "$got" = "$want" ]; then P=$((P+1)); printf '  \033[1;32mok\033[0m  %s\n' "$desc"
  else F=$((F+1)); printf '  \033[1;31mNO\033[0m  %s \033[2m(want %s got %s)\033[0m\n' "$desc" "$want" "$got"; fi; }
pm(){ python3 "$CLI" path "$1" >/dev/null 2>&1; }                 # path mode
hk(){ printf '%s' "$1" | python3 "$CLI" claude-hook >/dev/null 2>&1; }  # claude-hook mode

echo "── A. no_write_raw · path (block=2) ──"
pm "llmwiki/raw/x.md";                 assert 2 "raw/ trực tiếp" $?
pm "raw/x.md";                         assert 2 "raw/ không prefix" $?
pm "./llmwiki/raw/x.md";               assert 2 "leading ./" $?
pm "llmwiki/raw/a/b/c.md";             assert 2 "raw/ lồng sâu" $?
pm "/Users/me/p/llmwiki/raw/x.md";     assert 2 "đường tuyệt đối" $?
pm "wiki/sources/draft/raw/x.md";      assert 2 "raw/ nằm sâu trong cây" $?
pm 'llmwiki\raw\x.md';                 assert 2 "backslash (Windows) normalize" $?

echo "── A'. FALSE-POSITIVE guard (phải KHÔNG chặn = 0) ──"
pm "llmwiki/wiki/concepts/coleslaw.md"; assert 0 "coleslaw.md (chứa 'raw')" $?
pm "llmwiki/wiki/concepts/draw.md";     assert 0 "draw.md (chứa 'raw')" $?
pm "llmwiki/raws/x.md";                 assert 0 "raws/ (không phải raw)" $?
pm "myraw/x.md";                        assert 0 "myraw/ (raw dính từ khác)" $?
pm "src/app.ts";                        assert 0 "file thường" $?

echo "── B. bash ghi raw/ (claude-hook, block=2) ──"
hk '{"tool_name":"Bash","tool_input":{"command":"echo hi > llmwiki/raw/x.md"}}';   assert 2 "redirect >" $?
hk '{"tool_name":"Bash","tool_input":{"command":"echo hi >> llmwiki/raw/x.md"}}';  assert 2 "append >>" $?
hk '{"tool_name":"Bash","tool_input":{"command":"tee llmwiki/raw/x.md"}}';         assert 2 "tee" $?
hk '{"tool_name":"Bash","tool_input":{"command":"tee -a llmwiki/raw/x.md"}}';      assert 2 "tee -a" $?
hk '{"tool_name":"Bash","tool_input":{"command":"touch llmwiki/raw/x.md"}}';       assert 2 "touch" $?
hk '{"tool_name":"Bash","tool_input":{"command":"cp a.md llmwiki/raw/"}}';         assert 2 "cp đích raw/" $?
hk '{"tool_name":"Bash","tool_input":{"command":"sed -i.bak llmwiki/raw/x.md"}}'; assert 2 "sed -i.bak <file raw> (file ngay sau -i)" $?

echo "── B'. bash hợp lệ (đọc / ghi nơi khác / mv RA khỏi raw = 0) ──"
hk '{"tool_name":"Bash","tool_input":{"command":"cat llmwiki/raw/x.md"}}';          assert 0 "cat (đọc raw)" $?
hk '{"tool_name":"Bash","tool_input":{"command":"grep foo llmwiki/raw/x.md"}}';     assert 0 "grep (đọc raw)" $?
hk '{"tool_name":"Bash","tool_input":{"command":"ls llmwiki/raw/"}}';               assert 0 "ls raw/" $?
hk '{"tool_name":"Bash","tool_input":{"command":"mv llmwiki/raw/x.md /tmp/out.md"}}'; assert 0 "mv RA khỏi raw" $?
hk '{"tool_name":"Bash","tool_input":{"command":"echo hi > llmwiki/wiki/notes.md"}}'; assert 0 "redirect nơi khác" $?

echo "── B''. layout dot .llmwiki/ + deny_write theo GLOB CỦA RULE (GH#111/112/113) ──"
hk '{"tool_name":"Bash","tool_input":{"command":"echo hi > .llmwiki/raw/a.md"}}';      assert 2 "bash ghi .llmwiki/raw/" $?
hk '{"tool_name":"Write","tool_input":{"file_path":".llmwiki/raw/a.md","content":"x"}}'; assert 2 "Write .llmwiki/raw/" $?
# R14 patterns-protected: trước GH#113 nhánh Bash chỉ grep chuỗi "raw/" nên đích THẬT của R14 lọt
hk '{"tool_name":"Bash","tool_input":{"command":"echo x > llmwiki/patterns/p.md"}}';   assert 2 "bash ghi patterns/ (R14)" $?
hk '{"tool_name":"Bash","tool_input":{"command":"echo x > .llmwiki/patterns/p.md"}}';  assert 2 "bash ghi .llmwiki/patterns/ (R14)" $?
hk '{"tool_name":"Write","tool_input":{"file_path":".llmwiki/patterns/p.md","content":"x"}}'; assert 2 "Write .llmwiki/patterns/ (R14)" $?
# và KHÔNG được báo R14 trên lệnh ghi raw/ (dương tính giả cũ). grep -q: 1 = không thấy = đúng.
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"echo hi > llmwiki/raw/x.md"}}' \
  | python3 "$CLI" claude-hook 2>&1 | grep -q 'R14'
assert 1 "không có R14 thừa khi ghi raw/ (chỉ R1)" $?

echo "── C. KNOWN GAPS — lõi session soi bề mặt, KHÔNG bắt (đúng như đã verify) ──"
echo "      → đây là LÝ DO sàn đảm bảo phải ở CI/sandbox, không phải hook regex."
hk '{"tool_name":"Bash","tool_input":{"command":"python3 -c \"open('llmwiki/raw/x.md','w')\""}}'; assert 0 "GAP: python -c open(w) né regex" $?
hk '{"tool_name":"Bash","tool_input":{"command":"rm llmwiki/raw/x.md"}}';           assert 0 "GAP: rm raw/ (xóa không phải write)" $?
hk '{"tool_name":"Bash","tool_input":{"command":"sed -i s/a/b/ llmwiki/raw/x.md"}}'; assert 0 "GAP: sed -i <expr> trước path" $?

echo "── D. require_origin (claude-hook Write/Edit) ──"
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/concepts/a.md","content":"---\ntype: concept\n---\n# a\n## Origin\n- s"}}'; assert 0 "concept CÓ Origin + frontmatter" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/concepts/b.md","content":"# b"}}';                assert 2 "concept THIẾU Origin" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/concepts/c.md","content":"---\ntype: concept\n---\n# c\n##  Origin\n"}}';  assert 0 "## + 2 space Origin (linh hoạt)" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/concepts/d.md","content":"# d\n## Origins\n"}}';  assert 2 "## Origins (≠ Origin, chặt biên)" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/concepts/e.md","content":"# e\n### Origin\n"}}';  assert 2 "### Origin (h3 không tính)" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/entities/f.md","content":"# f"}}';               assert 2 "entities thiếu Origin" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/sources/draft/g.md","content":"# g"}}';          assert 2 "sources/draft thiếu Origin" $?
hk '{"tool_name":"Edit","tool_input":{"file_path":"llmwiki/wiki/concepts/h.md","content":"# h"}}';                assert 2 "Edit (không chỉ Write) cũng soi" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/concepts/README.md","content":"x"}}';            assert 0 "README.md miễn trừ" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/concepts/index.md","content":"x"}}';             assert 0 "index.md miễn trừ" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/architecture/z.md","content":"x"}}';             assert 2 "architecture/ thuộc R9 → thiếu frontmatter bị chặn" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/concepts/note.txt","content":"x"}}';             assert 0 ".txt ngoài *.md → bỏ qua" $?

echo "── E. files mode (layer=repo) ──"
tmp="$(mktemp -d)"; mkdir -p "$tmp/llmwiki/raw" "$tmp/llmwiki/wiki/concepts" "$tmp/llmwiki/wiki/entities"
printf 'human inbox\n'        > "$tmp/llmwiki/raw/human.md"
printf '%b' '---\ntype: concept\n---\n# g\n## Origin\n- s\n' > "$tmp/llmwiki/wiki/concepts/good.md"
printf '# b no origin\n'      > "$tmp/llmwiki/wiki/concepts/bad.md"
printf '# e no origin\n'      > "$tmp/llmwiki/wiki/entities/bad.md"
python3 "$CLI" files "$tmp/llmwiki/raw/human.md" >/dev/null 2>&1;            assert 0 "repo: raw/ con người commit OK (R1 session-only)" $?
python3 "$CLI" files "$tmp/llmwiki/wiki/concepts/good.md" >/dev/null 2>&1;   assert 0 "repo: concept tốt" $?
python3 "$CLI" files "$tmp/llmwiki/wiki/concepts/bad.md" >/dev/null 2>&1;    assert 1 "repo: concept thiếu Origin fail" $?
python3 "$CLI" files "$tmp/llmwiki/wiki/concepts/good.md" "$tmp/llmwiki/wiki/entities/bad.md" >/dev/null 2>&1; assert 1 "repo: lô [tốt,xấu] → fail" $?
python3 "$CLI" files "$tmp/llmwiki/wiki/concepts/nope.md" >/dev/null 2>&1;   assert 0 "repo: file không tồn tại → bỏ qua" $?
rm -rf "$tmp"

echo "── F. claude-hook robustness (fail-open / không áp dụng = 0) ──"
hk '{';                                                              assert 0 "JSON hỏng → fail-open" $?
printf '' | python3 "$CLI" claude-hook >/dev/null 2>&1;             assert 0 "stdin rỗng → fail-open" $?
hk '{"tool_name":"Read","tool_input":{"file_path":"llmwiki/raw/x.md"}}'; assert 0 "tool Read (không phải write) → 0" $?
hk '{"tool_name":"Write"}';                                         assert 0 "thiếu tool_input → 0" $?
hk '{"tool_name":"MultiEdit","tool_input":{"file_path":"llmwiki/raw/x.md"}}'; assert 2 "MultiEdit→raw/ vẫn chặn" $?

echo "── G. mode/policy robustness ──"
python3 "$CLI" frobnicate x >/dev/null 2>&1;                        assert 0 "mode lạ → fail-open" $?
python3 "$CLI" --policy /no/such.yaml path llmwiki/raw/x.md >/dev/null 2>&1; assert 0 "policy thiếu → fail-open" $?
python3 "$CLI" path "" >/dev/null 2>&1;                             assert 0 "path rỗng → 0" $?

echo "── H. reason đúng rule (grep stderr) ──"
r=$(hk_err(){ printf '%s' "$1" | python3 "$CLI" claude-hook 2>&1 >/dev/null; }; hk_err '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/raw/x.md","content":"x"}}')
case "$r" in *R1*) assert 0 "raw/ báo đúng [R1]" 0;; *) assert 0 "raw/ báo đúng [R1]" 1;; esac
r=$(hk_err2(){ printf '%s' "$1" | python3 "$CLI" claude-hook 2>&1 >/dev/null; }; hk_err2 '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/concepts/x.md","content":"# x"}}')
case "$r" in *R2*) assert 0 "thiếu Origin báo đúng [R2]" 0;; *) assert 0 "thiếu Origin báo đúng [R2]" 1;; esac

echo "── I. RULE MỚI PORT (R5 folder · R9 frontmatter · R7 proposal) ──"
pm "llmwiki/wiki/foo.md";                              assert 2 "R5: wiki/ root .md bị chặn" $?
pm "llmwiki/wiki/index.md";                            assert 0 "R5: index.md ở root miễn trừ" $?
pm "llmwiki/wiki/concepts/foo.md";                     assert 0 "R5: trong subdir concepts/ ok" $?
# R5 NỚI (khớp global): subdir NGOÀI allow_subdirs cũng bị chặn, không chỉ root
pm "llmwiki/wiki/junk/x.md";                           assert 2 "R5: subdir lạ 'junk' bị chặn" $?
pm "llmwiki/wiki/architecture/a.md";                   assert 0 "R5: subdir architecture/ hợp lệ" $?
pm "llmwiki/wiki/tours/t.md";                          assert 0 "R5: subdir tours/ hợp lệ" $?
# R2 NỚI: architecture/tours nay cũng phải có Origin (có frontmatter để R9 qua, thiếu Origin → chỉ R2)
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/architecture/arch1.md","content":"---\ntype: architecture\n---\n# a"}}'; assert 2 "R2: architecture thiếu Origin bị chặn (scope mới)" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/concepts/n1.md","content":"# n\n## Origin\n- s"}}';                         assert 2 "R9: concept KHÔNG frontmatter bị chặn" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/concepts/n2.md","content":"---\ntype: concept\n---\n# n\n## Origin\n- s"}}';  assert 0 "R9: có frontmatter + type qua" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/concepts/n3.md","content":"---\nname: x\n---\n# n\n## Origin\n- s"}}';        assert 2 "R9: frontmatter THIẾU type bị chặn" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/sources/draft/p1.md","content":"---\ntype: draft\n---\n# p\n## Origin\n- x\n## Plan\n- [ ] t\nStatus: proposed"}}';                                          assert 2 "R7: proposal thiếu Agent Task/Sequence bị chặn" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/sources/draft/p2.md","content":"---\ntype: draft\n---\n# p\n## Origin\n- x\n## Plan\n## Agent Task Assignment\n| a |\n**Sequence diagram**: x\n## Global constraints\n- y\nStatus: proposed"}}'; assert 0 "R7: proposal đủ mục qua" $?
# R7-h: ràng buộc bao trùm là BẮT BUỘC — agent thi hành chỉ được bơm task của nó, luật chung phải đi kèm
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/sources/draft/p4.md","content":"---\ntype: draft\n---\n# p\n## Origin\n- x\n## Plan\n## Agent Task Assignment\n| a |\n**Sequence diagram**: x\nStatus: proposed"}}'; assert 2 "R7-h: proposal thiếu '## Global constraints' bị chặn" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/sources/draft/p3.md","content":"---\ntype: draft\n---\n# p\n## Origin\n- x\n## Plan\nStatus: done"}}';  assert 0 "R7: không 'proposed' → R7 không áp" $?
# R18 plan-executable — PLAN là thứ bơm thẳng vào agent context=0; thiếu Files/Interfaces = agent phải đoán
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/sources/draft/f-PLAN.md","content":"---\ntype: draft\n---\n# f — PLAN\n## Origin\n- spec\n## Global constraints\n- x\n### Task 1: a\n- [ ] step"}}';                                                                        assert 2 "R18: PLAN thiếu Files/Interfaces bị chặn" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/sources/draft/g-PLAN.md","content":"---\ntype: draft\n---\n# g — PLAN\n## Origin\n- spec\n## Global constraints\n- x\n### Task 1: a\n**Thoả:** FR-001\n**Files:**\n- Tao: `src/a.py`\n**Interfaces:**\n- Produces: `a() -> int`\n- [ ] step"}}';  assert 0 "R18: PLAN đủ Files+Interfaces+Global constraints qua" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/sources/draft/h.md","content":"---\ntype: draft\n---\n# h\n## Origin\n- x\n### Task 1: a\n- [ ] step"}}';                                                                                              assert 0 "R18: file KHÔNG phải *-PLAN.md → R18 không áp" $?
# R7 forbid_contains — unknown NGUY HIỂM chưa trả lời KHÔNG được mang ra cổng duyệt
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/sources/draft/p5.md","content":"---\ntype: draft\n---\n# p\n## Origin\n- x\n## Plan\n## Agent Task Assignment\n| a |\n**Sequence diagram**: x\n## Global constraints\n- y\n## Requirements (FR)\n- FR-001: xac thuc bang [CẦN LÀM RÕ: SSO hay OAuth?]\nStatus: proposed"}}'; assert 2 "R7: SPEC còn '[CẦN LÀM RÕ]' chưa trả lời bị chặn" $?
# R18 — PLAN phải khai '**Thoả:**' (truy vết ngược về FR của SPEC)
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/sources/draft/i-PLAN.md","content":"---\ntype: draft\n---\n# i — PLAN\n## Origin\n- spec\n## Global constraints\n- x\n### Task 1: a\n**Files:**\n- Tao: `src/a.py`\n**Interfaces:**\n- Produces: `a() -> int`\n- [ ] step"}}'; assert 2 "R18: PLAN thiếu '**Thoả:**' bị chặn" $?
# R9 NỚI (khớp global): sources/draft cũng cần frontmatter — file có Origin nhưng THIẾU frontmatter → chặn
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/wiki/sources/draft/q.md","content":"# q\n## Origin\n- x"}}';                       assert 2 "R9 nới: draft có Origin nhưng thiếu frontmatter bị chặn" $?

echo
printf '\033[1mTỔNG: %d test · %d PASS · %d FAIL\033[0m\n' "$T" "$P" "$F"
[ "$F" = 0 ] || exit 1
