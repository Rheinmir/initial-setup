---
name: fdk-uat
description: >-
  UAT THẬT cho một bản framework sắp phát hành - dựng một dự án TRỐNG hoàn toàn mới, cài overstack
  đúng đường NGƯỜI MỚI (curl bootstrap từ GitHub raw, không phải file:// working-tree), rồi kiểm chứng
  năng lực MỚI của chính bản đó có tới tay người dùng không (skill reachable, rule CẮN thật, docs khớp).
  HAI PHA - (1) nhánh CANARY trước merge: đẩy lên nhánh tạm uat/<ts>, curl từ raw của chính nhánh đó
  (kèm HARNESS_BASE + REPO_RAW + SKILLS_REF trỏ canary), UAT đầy đủ; FAIL thì xoá canary và nhánh chính
  chưa hề bị bẩn. (2) main-URL smoke NGAY SAU merge: chạy đúng lệnh người mới gõ, KHÔNG override biến
  nào - chỉ pha này kiểm được các giá trị MẶC ĐỊNH (chỗ hardcode tên nhánh); FAIL thì gỡ commit khỏi
  remote (revert hoặc reset --force-with-lease).
  Gọi khi user nói "uat", "test thật", "test downstream", "kiểm tra người mới cài có chạy không",
  "acceptance", "/fdk-uat", hoặc trước khi công bố một bản có năng lực mới. KHÁC medic --ci và
  fresh-install-smoke (cả hai cài từ working-tree qua file:// nên KHÔNG chứng minh được đường remote).
---

# Skill: fdk-uat

## Vấn đề nó giải
`medic --ci` và `fresh-install-smoke --local` cài từ **working-tree** qua `file://`. Chúng chứng minh "code trong máy tôi lành", **không** chứng minh "người lạ `curl` về là chạy được". Hai thứ khác nhau: tarball thiếu file, `.gitignore` nuốt mất thứ cần ship, skill hỏng frontmatter bị CLI bỏ qua trong im lặng, engine global không refresh — mọi lỗi này chỉ lộ ra trên **đường remote thật**.

Đường remote chỉ tồn tại **sau khi push** — nhưng không nhất thiết là push lên **nhánh chính**. Một nhánh tạm cũng có raw URL. Nghịch lý con-gà-quả-trứng biến mất, với một điều kiện: phải override **cả ba** biến nguồn, vì `install.sh` mặc định kéo skill từ nhánh chính.

Và canary vẫn **không đủ**: nó chạy với ref khác + biến override, nên **mù** với chính các giá trị *mặc định* — mà mặc định là chỗ chứa chuỗi tên nhánh hardcode. Nên phải có pha hai: chạy **đúng cái lệnh người mới gõ**, không override gì cả.

## When to use
- Sắp công bố một bản có **năng lực mới** (skill mới, rule mới, engine mới).
- Nghi ngờ "doc hứa mà user không nhận được" (lớp lỗi GH#77).
- Sau khi `medic --ci` đã xanh — UAT là tầng TRÊN nó, không thay thế nó.

## Steps

### 0. Tiền đề — không được bỏ
```bash
python3 fdk/tools/medic.py --ci          # PHẢI xanh. Đỏ mà vẫn push là cố ý đẩy rác lên remote.
git status --short                        # sạch (không untracked lạc)
git log --oneline origin/<nhánh>..HEAD    # in ĐÚNG những commit sắp đẩy — ghi lại, đây là thứ sẽ gỡ nếu fail
```
**Ghi lại `BASE=$(git rev-parse origin/<nhánh>)`** — mốc để quay về.

### 1. Khai năng lực mới của bản này (checklist UAT)
Trước khi push, viết ra **cụ thể** bản này hứa gì mới. Mỗi dòng phải kiểm được bằng lệnh:
- Skill mới → `~/.claude/skills/<tên>/SKILL.md` tồn tại sau khi cài, và có trong `CAPABILITIES.md` của dự án mới.
- Rule mới → phải **CẮN THẬT** trong dự án mới (viết một file BAD → bị chặn; file GOOD → qua).
- Engine/tool mới → reachable trong global harness home.

Không khai được thành lệnh thì **không tính là năng lực** — đó là lời hứa suông.

### 2. PHA 1 — nhánh CANARY (nhánh chính KHÔNG nhận gì cả)
Đường remote chỉ tồn tại sau khi push — nhưng **không nhất thiết phải push lên nhánh chính**. Một nhánh tạm cũng có raw URL, và `curl` không quan tâm nhánh nào.

```bash
CANARY="uat/$(date +%y%m%d-%H%M)"
git push origin HEAD:"$CANARY"
```

Dựng dự án **trống**, cài từ raw của **chính nhánh canary** — phải trỏ **cả ba** biến, không thì nó lặng lẽ kéo nội dung của nhánh chính:

```bash
D=~/orca/overstack-uat-$(date +%y%m%d-%H%M)
mkdir -p "$D" && cd "$D" && git init
RAW="https://raw.githubusercontent.com/<owner>/<repo>/$CANARY"
curl -fsSL "$RAW/harness/poc-vendor-neutral/bootstrap.sh" \
  | HARNESS_BASE="$RAW/harness/poc-vendor-neutral" \
    REPO_RAW="$RAW" \
    SKILLS_REF="<owner>/<repo>#$CANARY" \
    bash
git add -A && git commit -m "fresh overstack install"    # Orca cần ≥1 commit mới nhận repo
```

> **Thiếu `SKILLS_REF` là bài UAT thành ẢO GIÁC.** `install.sh` mặc định cài skill từ `<repo>#<nhánh chính>` — nên nếu không override, canary sẽ cài **skill của nhánh chính**, tức nó chấm bản CŨ rồi báo PASS cho bản MỚI. Một cổng nói dối mà vẫn xanh còn tệ hơn không có cổng.

Chạy checklist bước 3. **PASS** → sang pha 2. **FAIL** → xoá canary, nhánh chính **chưa hề bị bẩn**:
```bash
git push origin --delete "$CANARY"
```

### 3. UAT — chạy checklist bước 1 trong dự án ĐÓ
Tối thiểu, theo `fdk/docs/fresh-install-gate.md`:
1. **3 trụ có mặt:** `harness/poc-vendor-neutral/policy.yaml` · `.claude/settings.json` · `.pre-commit-config.yaml` · `llmwiki/wiki/index.md` · `CAPABILITIES.md`.
2. **Harness cắn thật:** `bash harness/poc-vendor-neutral/test-broad.sh` → PASS (validator GOOD-pass / BAD-block).
3. **Năng lực MỚI tới tay** — phần riêng của bản này (checklist bước 1). Đây là mục hay bị bỏ nhất, và cũng là mục duy nhất chứng minh bản MỚI có giá trị.
4. **Orchestration-ready:** skill `orchestration` / `orca-cli` / `orca-dispatch-reference` reachable.
5. **BẮT BUỘC (không phải tuỳ chọn — feedback 2026-07-24, lần thứ 2 bị nhắc vì skip bước này): dựng workspace Orca thật + TỰ VERIFY nó hiện trong app, đừng chỉ chạy filesystem-level.** Chỉ curl-cài vào một thư mục tạm rồi test bằng CLI KHÔNG tính là UAT hoàn chỉnh — user không thấy được gì, "không visual = không dùng được". Đây là cổng CỨNG: UAT KHÔNG được coi là PASS nếu bỏ qua bước này.
```bash
WT_NAME="uat-$(date +%y%m%d-%H%M)"                          # tên xác định, dùng để verify ở bước sau
REPO_ID=$(orca repo add --path "$D" --json | python3 -c "import json,sys; print(json.load(sys.stdin)['result']['repo']['id'])")
orca worktree create --repo "id:$REPO_ID" --name "$WT_NAME" --setup skip --no-parent --activate --json
```
> Cạm bẫy đã dính: `orca repo add <path>` positional → `Unknown command`. Repo chưa có commit → Orca không nhận. `repo add` **không** làm workspace hiện trong app — phải `worktree create`.

**Cổng verify — chạy NGAY sau lệnh trên, đây không phải bước phụ:**
```bash
orca worktree list --repo "id:$REPO_ID" --json | python3 -c "
import json, sys
d = json.load(sys.stdin)
names = [w['displayName'] for w in d['result']['worktrees']]
assert '$WT_NAME' in names, f'KHÔNG THẤY worktree tên {\"$WT_NAME\"} — UAT KHÔNG ĐƯỢC TÍNH LÀ PASS. Có: {names}'
print(f'✓ worktree \"$WT_NAME\" hiện thật trong Orca — {names}')
"
```
Assertion FAIL ở đây → **DỪNG, không được tiếp tục báo PASS cho user** — quay lại sửa lệnh `worktree create` (thường do `--repo` sai định dạng selector hoặc `repo add` chưa commit) rồi verify lại. Đây chính là gate cấu trúc thay cho việc "phải nhớ tự giác dựng workspace mỗi lần" — nhớ tay đã fail 2 lần liền (2026-07-21, 2026-07-24), giờ ép bằng assert.

### 4. PHA 2 — main-URL smoke, NGAY SAU merge (canary KHÔNG thay được bước này)
Pha 1 chạy với **ref khác** và **ba biến override** → nó **mù** với chính các giá trị **mặc định**. Mà mặc định là chỗ chứa chuỗi nhánh hardcode (`bootstrap.sh` `BASE=`, `install.sh` `REPO_RAW=`, `SKILLS_REF=`). Chỉ pha này kiểm được **đúng cái lệnh người mới thật sự gõ**.

```bash
git push origin HEAD:<nhánh chính>          # merge — bản này ĐÃ qua canary
git push origin --delete "$CANARY"          # dọn nhánh tạm
```

**CHỜ CDN PROPAGATE TRƯỚC KHI ĐO — bắt buộc.** `raw.githubusercontent.com` **không** phục vụ bản mới ngay sau push, và độ trễ **không đồng đều giữa các file**: đã đo được cảnh engine (`bin/llmwiki-validate.py`) đã mới trong khi `policy.yaml` còn cũ → bản cài ra là một thứ **lai**, và cổng báo ĐỎ GIẢ. Nguy hiểm hơn: cùng cơ chế đó có thể cho **XANH GIẢ** nếu file cũ tình cờ vẫn qua được test.

Chốt bằng một sentinel — poll tới khi raw trả đúng nội dung mình vừa đẩy:

```bash
RAW="https://raw.githubusercontent.com/<owner>/<repo>/<nhánh chính>"
MARK="<một chuỗi CHỈ có ở bản mới>"      # vd tên rule/field vừa thêm
  # ⚠ GREP-VERIFY MARK trên file bản mới TRƯỚC (grep "$MARK" <file local>) — chọn pattern đoán
  #   mà không khớp file → vòng lặp chờ hết lượt rồi tưởng raw còn cũ, dù raw ĐÃ mới (p-32).
for i in $(seq 1 30); do
  curl -fsSL "$RAW/harness/poc-vendor-neutral/policy.yaml" | grep -q "$MARK" && break
  echo "  raw còn cũ, chờ CDN… ($i)"; sleep 10
done
```

Rồi mới chạy **đúng lệnh trong README — không override một biến nào**:

```bash
D2=$(mktemp -d) && cd "$D2" && git init -q
curl -fsSL "$RAW/harness/poc-vendor-neutral/bootstrap.sh" | bash
```

Rút gọn (~1 phút): 3 trụ có mặt · `bash harness/poc-vendor-neutral/test-broad.sh` PASS · skill mới reachable trong `~/.claude/skills/`.

**FAIL → gỡ ngay** (bước 5). Cửa sổ rủi ro của nhánh chính thu từ "cả bài UAT dài" xuống "một lần smoke ~1 phút".

### 5. KHÔNG PASS → gỡ commit khỏi remote NGAY
Chỉ dùng khi PHA 2 đỏ (hoặc ai đó đã lỡ push thẳng, bỏ qua canary). Chọn theo tình huống:
```bash
# (a) Nhánh chia sẻ / đã có người kéo → REVERT (không viết lại lịch sử):
git revert --no-edit <sha>..HEAD && git push origin <nhánh>

# (b) Nhánh chỉ mình dùng, vừa đẩy xong, chắc chắn chưa ai kéo → RESET:
git reset --hard "$BASE" && git push --force-with-lease origin <nhánh>
```
`--force-with-lease` chứ **không** `--force`: nếu trong lúc đó có người đẩy lên, lệnh sẽ từ chối thay vì xoá mất việc của họ.

Gỡ xong: ghi lại **vì sao fail** vào `llmwiki/html/fdk-problem-tree.html` (node mới, `status: open`) — thất bại UAT là dữ liệu, không phải chuyện xấu hổ.

### 6. PASS → chốt
- Dọn dự án UAT (hoặc giữ lại `--keep` nếu cần soi).
- Ghi kết quả (số đo thật, không phải lời hứa) vào `wiki/log.md`.
- Bản trên remote coi như đã được nghiệm thu ở tầng "người mới cài".

## Rules
- **Nhánh chính KHÔNG BAO GIỜ nhận bản chưa qua canary.** Pha 1 tồn tại để điều đó đúng.
- **Canary KHÔNG thay được main-URL smoke.** Nó chạy với ref khác + biến override → mù với các giá trị mặc định, mà mặc định chính là chỗ hardcode tên nhánh. Bỏ pha 2 là bỏ đúng thứ người dùng thật chạm vào.
- **Không bao giờ push rồi bỏ mặc.** Đã push để UAT thì phải chạy UAT trong cùng phiên. Push xong đi ngủ là để lại một bản chưa nghiệm thu cho người khác kéo về.
- **Dọn nhánh canary ở CẢ HAI lối ra** (pass và fail). Bước 0 liệt kê `git branch -r | grep uat/` để dọn rác của phiên chết giữa chừng.
- **CDN propagate không đồng đều — CHỜ SENTINEL, đừng đo ngay sau push.** `raw.githubusercontent` có thể trả file A đã mới còn file B còn cũ trong cùng một lần cài → bản lai, và cổng báo đỏ giả (hoặc xanh giả, nguy hiểm hơn). Poll một chuỗi CHỈ có ở bản mới cho tới khi raw trả đúng, rồi mới đo. Đo được thật ngày 2026-07-14: engine mới + policy cũ → test-broad 72/74, luật mới không cắn; chờ vài phút rồi chạy lại → 74/74.
- **Không đếm skill/rule bằng trí nhớ** — đếm LIVE trong dự án vừa cài. Con số trên đĩa repo **không** phải con số tới tay người dùng (đã cháy: doc báo 74 skill, installer giao 67 — 7 skill hỏng frontmatter bị CLI nuốt im lặng).
- **Rule mới phải CẮN, không chỉ có mặt.** File `policy.yaml` có dòng luật ≠ luật chặn được. Luôn test bằng một file BAD thật.
- **Trần (ceiling) cố ý:** UAT headless không spin được model LLM, nên "`/orchestration` chạy được" chỉ kiểm ở mức tất định (cài đủ + reachable + ping runtime). Live-run bằng model thật vẫn là acceptance làm tay.
- Fail thì **gỡ**, không "để đó sửa sau". Remote là thứ người khác kéo về.
- **Workspace Orca hiện thật là BẮT BUỘC, có assert kiểm tên, không phải "tuỳ chọn thấy được bằng mắt".** Bị nhắc lặp lại 2 lần (2026-07-21, 2026-07-24) vì trước đây ghi là tuỳ chọn nên bị bỏ qua khi chạy vội — filesystem-only test KHÔNG tính là UAT hoàn chỉnh dù mọi lệnh CLI khác xanh hết.

## Origin
- Luồng distill từ `fdk/docs/fresh-install-gate.md` (§ "Luồng chuẩn: dựng workspace Orca mới rồi test fresh-install") + yêu cầu của user 2026-07-14: cho phép push trước để test thật, không pass thì gỡ commit khỏi remote.
- **Hai pha** là kết quả của một phản biện của user cùng ngày: "nếu vậy thì nó có test được đúng cái curl của main không?" — không. Canary chứng minh *nội dung* cài được qua remote; chỉ main-URL smoke chứng minh *cái lệnh mặc định* chạy được. Kèm phát hiện `install.sh` hardcode `#orca` không có đường override — thiếu nó thì canary chấm nhầm bản cũ.
