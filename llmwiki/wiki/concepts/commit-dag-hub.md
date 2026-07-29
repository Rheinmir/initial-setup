---
type: concept
title: "Commit-DAG hub LOCAL — mỗi thí nghiệm của agent là một commit, tra cứu bằng git ref"
tags: [commit-dag-hub, loop-runner, ratchet, git-notes, opt-in, removable, graph-engineering]
timestamp: 2026-07-29
---

# Commit-DAG hub LOCAL

## Nó giải bài gì

Khi một vòng lặp agent chạy có ratchet (xem `harness/scripts/loop-runner.py`), mỗi lần lặp là một thí nghiệm: agent đổi một thứ, đo điểm, rồi hoặc giữ lại bằng `git commit`, hoặc vứt đi bằng `git reset --hard`. Vấn đề là sau khi vòng lặp kết thúc, thứ duy nhất còn lại là commit cuối cùng. Toàn bộ những nhánh đã thử và đã bỏ biến mất không dấu vết, kèm theo cả lý do vì sao chúng bị bỏ. Lần sau một agent khác lại thử đúng ý tưởng đó, lại đo, lại vứt đi — trả tiền hai lần cho cùng một bài học.

Commit-DAG hub biến mỗi thí nghiệm thành một **node có tên và có metadata** trong chính đồ thị commit của git. Nhờ vậy ta hỏi được những câu mà run-log JSON đơn lẻ không trả lời nổi: *kết quả được giữ lại nào có điểm cao nhất*, *từ trạng thái này đã rẽ ra mấy hướng*, *hướng nào còn chưa ai đi tiếp*, *đường đi từ kết quả tốt nhất về gốc gồm những bước nào*, và *hai thí nghiệm này khác nhau ở chỗ nào*.

## Vì sao bản LOCAL không cần server

Bản gốc trong tài liệu "Graph Engineering" mô tả một dịch vụ hub với bảy lệnh `push · fetch · log · children · leaves · lineage · diff`, tức là một tiến trình riêng có mạng, có xác thực, có hàng đợi merge. Trong bối cảnh của repo này thì phần lớn chi phí đó là thừa: mọi worktree do Orca tạo ra đều dùng chung **một** kho đối tượng `.git`. Commit mà agent A tạo ra đã nhìn thấy được từ agent B ngay lập tức, không có gì để đẩy qua mạng và cũng không có gì để kéo về. Hai lệnh `push` và `fetch` của bản gốc vì thế thu lại thành một thao tác ghi cục bộ duy nhất.

Cái còn lại đúng bằng ba thứ, tất cả đều là nguyên thuỷ có sẵn của git:

1. **Một namespace ref riêng** — `refs/hub/<agent>/<seq>`. Nó nằm ngoài `refs/heads`, nên node hub không phải là nhánh: không hiện trong `git branch`, không cần merge vào đâu, không cần một nhánh chính, và không tạo ra xung đột với công việc thường ngày.
2. **Một sổ ghi chú riêng** — `git notes --ref=refs/notes/hub`. Metadata của node (giả thuyết, điểm số, trạng thái, môi trường) nằm ở đây, gắn theo commit, nên nội dung commit không bị bẩn.
3. **Một CLI mỏng** — `harness/scripts/hub.py`, khoảng 300 dòng Python thuần thư viện chuẩn, chỉ gọi `git` qua `subprocess`.

Chi phí tụt từ "dựng một dịch vụ" xuống "thêm một file script", và đó chính là lý do việc này đủ rẻ để làm ngay dù chưa ai kêu đau.

## Mô hình dữ liệu

Mỗi lần `hub_push` tạo ra một ref trỏ vào một commit có sẵn, kèm một ghi chú JSON gắn vào đúng commit đó:

```json
{
  "agent": "loop-runner",
  "hypothesis": "iter 2: pytest -q",
  "metric": 3.5,
  "status": "kept",
  "ts_utc": "2026-07-29T04:11:07Z",
  "python": "3.13.1",
  "platform": "macOS-15.2-arm64-arm-64bit",
  "deps_sha": null
}
```

Ba field cuối là **field môi trường**, và chúng có mặt ngay từ commit đầu tiên một cách có chủ ý. Một số đo không kèm môi trường sinh ra nó thì không tái lập được: điểm 3.5 đo trên Python 3.13 với một tập dependency nhất định có thể không lặp lại được ở nơi khác, và khi đó cả node lẫn kết luận rút ra từ nó đều mất giá trị. Nếu thêm ba field này sau, mọi thí nghiệm đã ghi trước đó sẽ vĩnh viễn không có môi trường — không có cách nào truy ngược. Đây là lý do chúng nằm trong schema từ dòng code đầu tiên chứ không phải trong danh sách việc-sẽ-làm.

`deps_sha` là sha1 rút gọn của file khoá dependency đầu tiên tìm thấy trong `uv.lock`, `poetry.lock`, `requirements.txt`; repo nào không có file nào trong ba file đó thì giá trị là `null` — trung thực hơn là bịa ra một giá trị giả.

## Bốn truy vấn DAG, với ví dụ chạy thật

Các đoạn dưới đây là output thật, lấy từ một sandbox git tạm gồm một commit cha chung và hai nhánh con rẽ ra từ nó.

**`children <rev>` — từ trạng thái này đã rẽ ra những hướng nào.** Câu trả lời được giới hạn trong tập node hub, nên nó cho ra cây *thí nghiệm* chứ không phải toàn bộ lịch sử repo:

```
$ python3 harness/scripts/hub.py children 1d18f202fc10
8e86766193daeebb79fcf9a244ab455ffa1abcf0  refs/hub/alpha/0002
be3dbdf41eb4ba9403793057e07e1b2a15ae33da  refs/hub/beta/0001
```

**`leaves` — biên chưa khám phá.** Một node hub chưa từng làm cha của node hub nào khác nghĩa là chưa ai đi tiếp từ đó. Node cha chung ở ví dụ trên đã có hai con nên bị loại khỏi danh sách:

```
$ python3 harness/scripts/hub.py leaves
8e86766193daeebb79fcf9a244ab455ffa1abcf0
be3dbdf41eb4ba9403793057e07e1b2a15ae33da
```

**`lineage <rev>` — đường đi từ một kết quả về gốc**, theo thứ tự con trước, tổ tiên sau, dùng `git rev-list --topo-order`:

```
$ python3 harness/scripts/hub.py lineage nhanh1
8e86766193daeebb79fcf9a244ab455ffa1abcf0
1d18f202fc10fe7bbb7fe8ea3fabe5c3ebc410d2
```

**`diff <a> <b>` — hai thí nghiệm khác nhau ở đâu.** Đây là passthrough thẳng sang `git diff --stat`, cố ý không thêm định dạng riêng:

```
$ python3 harness/scripts/hub.py diff 1d18f202fc10 nhanh1
 a.txt | 1 +
 1 file changed, 1 insertion(+)
```

Ngoài bốn truy vấn đó, `log --by-metric` trả lời đúng câu hỏi chữ ký của mô hình này — *kết quả giữ lại nào có metric tốt nhất*:

```
$ python3 harness/scripts/hub.py log --by-metric
ref                                agent                metric  status     hypothesis
refs/hub/alpha/0002                alpha                   3.5  kept       nhanh 1: dung lru-cache
refs/hub/beta/0001                 beta                   2.25  discarded  nhanh 2: bo cache, tang batch
refs/hub/alpha/0001                alpha                     1  kept       goc: dung map thuong
```

Node có `status: discarded` được giữ lại có chủ ý: một thay đổi đã bị vứt vẫn dạy được agent sau rằng ý tưởng đó hỏng trong điều kiện nào.

## Cách bật

Hub **mặc định tắt**. Bật bằng một trong hai cách, và cả hai đều chỉ có tác dụng khi ratchet đang chạy (tức là đã có `--metric-cmd`):

```bash
# cách 1 — bật cho MỘT lần chạy
python3 harness/scripts/loop-runner.py run --verify "pytest -q" --metric-cmd "./bench.sh" --hub

# cách 2 — bật thường trực: sửa hub.enabled thành true trong harness/loop-runner.config.yaml
```

Cờ `--no-hub` ép tắt cho một lần chạy bất kể config nói gì. Các ngưỡng riêng của hub (giữ lại bao nhiêu node khi dọn) nằm ở `harness/hub.config.yaml`.

## Cách tắt và cách gỡ bỏ hoàn toàn

Đây là mục quan trọng nhất của trang này. Tính năng chỉ đáng thêm vào nếu việc bỏ nó ra cũng rẻ như việc thêm vào, và ba tầng dưới đây tăng dần theo mức độ dứt khoát. Chọn tầng thấp nhất đủ dùng.

### Tầng 1 — Tắt (giữ nguyên code và dữ liệu)

Đặt `enabled: false` trong khối `hub:` của `harness/loop-runner.config.yaml`, hoặc thêm `--no-hub` vào lệnh chạy:

```bash
python3 harness/scripts/loop-runner.py run --verify "pytest -q" --metric-cmd "./bench.sh" --no-hub
```

Khi tắt, `loop-runner.py` không nạp `hub.py`, không tạo ref nào, và run-log JSON không thêm field nào — nó trở lại giống hệt bản trước khi có tính năng này. Dữ liệu hub đã ghi vẫn còn nguyên và tra cứu được bằng CLI, chỉ là không có gì ghi thêm nữa.

### Tầng 2 — Xoá sạch dữ liệu (giữ code)

Khi muốn bỏ toàn bộ cây thí nghiệm đã tích, chạy kill-switch. Không có `--yes` thì lệnh chỉ liệt kê thứ *sẽ* bị xoá và không đụng vào gì:

```bash
python3 harness/scripts/hub.py purge            # dry-run, in ra danh sách sẽ xoá
python3 harness/scripts/hub.py purge --yes      # thi hành thật
git for-each-ref refs/hub                        # kiểm chứng: phải không in ra dòng nào
```

Lệnh này xoá toàn bộ `refs/hub/*` **và** `refs/notes/hub`. Nếu chỉ muốn dọn bớt thay vì xoá hết, dùng `prune` để giữ lại K node điểm cao nhất — đây cũng là cách chặn nợ "đồ thị phình vô hạn":

```bash
python3 harness/scripts/hub.py prune --keep-top 20             # dry-run
python3 harness/scripts/hub.py prune --keep-top 20 --yes       # thi hành thật
```

Lưu ý: `purge` chỉ xoá **ref và ghi chú**, không xoá commit. Các commit do ratchet tạo ra vẫn nằm trong lịch sử nhánh làm việc như trước — hub chưa bao giờ sở hữu chúng.

### Tầng 3 — Gỡ code hoàn toàn

Sau khi đã purge, gỡ bản thân tính năng. Cách sạch nhất là revert đúng commit đã thêm nó. Một commit không thể chứa mã băm của chính nó, nên hãy lấy sha thật bằng `git log` — lệnh dưới đây in ra commit đầu tiên đã tạo `hub.py`:

```bash
# in ra sha thật + tiêu đề của commit T7 (dòng duy nhất):
git log --oneline --diff-filter=A -- harness/scripts/hub.py
#   <sha> feat(hub): commit-DAG hub local opt-in, mặc định tắt, gỡ được sạch

# revert bằng sha vừa đọc, hoặc để git tự tra cho khỏi chép tay:
git revert "$(git log --format=%H --diff-filter=A -- harness/scripts/hub.py)"
```

Nếu không muốn revert (chẳng hạn commit đó đã bị gộp chung với việc khác), gỡ tay theo đúng bốn thao tác sau — không còn chỗ nào khác trong repo nhắc tới hub:

```bash
rm harness/scripts/hub.py harness/hub.config.yaml
rm llmwiki/wiki/concepts/commit-dag-hub.md   # nhớ gỡ dòng tương ứng trong llmwiki/wiki/index.md
```

Rồi xoá khối `hub:` trong `harness/loop-runner.config.yaml`, và xoá dòng `hub.py --self-test` khỏi bước "BNAL feature self-tests" trong `harness/scripts/fdk-gate.py`.

Riêng `harness/scripts/loop-runner.py` thì **không bắt buộc phải sửa**. Đây là điểm thiết kế cốt lõi: file đó không có dòng `import hub` nào ở đầu. Nó nạp module theo đường dẫn, lười, và chỉ khi hub đã được bật — nên khi `hub.py` không còn tồn tại, hàm nạp trả về `None`, nhánh hub im lặng trở thành thao tác rỗng, và vòng lặp chạy y hệt như chưa từng có tính năng này. Điều đó đã được kiểm bằng cách chuyển tạm `hub.py` ra khỏi thư mục rồi chạy `python3 harness/scripts/loop-runner.py selftest`: kết quả vẫn `ALL PASS`. Muốn dọn cho gọn thì xoá thêm hàm `_load_hub()`, hai tham số `hub_enabled`/`hub_agent`, khối gọi hub trong `run_loop()`, và hai cờ `--hub`/`--no-hub`.

## Bốn khoản nợ đã biết, và khoản nào đã chặn

Tài liệu gốc §IX.C liệt kê những chỗ mà một hub như thế này thường mục ruỗng theo thời gian. Bảng dưới ghi thẳng tình trạng hiện tại, kể cả những chỗ chưa giải.

| Nợ đã biết | Trạng thái | Cách đã chặn (hoặc điều kiện phải giải) |
|---|---|---|
| Đồ thị phình vô hạn, không ai dọn | **Đã chặn** | `prune --keep-top K [--older-than N]` giữ lại K node điểm cao nhất; mặc định dry-run nên không bao giờ xoá ngoài ý muốn. Có thêm `purge --yes` là kill-switch dứt điểm. |
| Không tái lập được thí nghiệm cũ | **Đã chặn** | Ba field môi trường `python`/`platform`/`deps_sha` nằm trong ghi chú ngay từ commit đầu — thêm sau là mất vĩnh viễn. |
| Nén / gộp lịch sử làm mất node | **Đã chặn một phần** | Ref trong `refs/hub/*` giữ commit sống, nên `git gc` không thu gom chúng. Chỗ chưa giải: sau khi `purge`, các commit mất ref có thể bị gc dọn — đó là hành vi mong muốn, nhưng phải purge một cách có ý thức. |
| Cần đánh chỉ mục khi số node lớn | **Chưa giải, có chủ ý** | Mọi truy vấn hiện quét tuyến tính danh sách ref. Với vài trăm node thì `git for-each-ref` nhanh hơn bất cứ chỉ mục tự viết nào. Điều kiện mở lại: khi `hub.py log` mất hơn một giây trên dữ liệu thật, hoặc số node vượt vài nghìn. |

Một hạn chế nữa nằm ngoài bốn khoản trên: ghi chú gắn theo **commit**, nên hai ref trỏ vào cùng một commit sẽ dùng chung một ghi chú và lần push sau ghi đè lần trước. Trong cách dùng bình thường thì mỗi Trial là một commit riêng nên không gặp; nếu về sau có luồng ghi nhiều node lên cùng một commit, đây là chỗ phải sửa trước.

## Kiểm chứng

```bash
python3 harness/scripts/hub.py --self-test          # dựng sandbox git thật, assert cả 14 điểm
python3 harness/scripts/loop-runner.py selftest     # 8 kịch bản cũ vẫn ALL PASS khi hub tắt
```

Self-test của hub tự dựng repo git tạm, đẩy ba node thành hai nhánh từ một cha chung, rồi kiểm `children`/`leaves`/`lineage`/`diff`/`log --by-metric`/`prune`/`purge`, kiểm cả đường fail-open (đẩy vào thư mục không phải repo git phải trả về `None` chứ không ném lỗi), và kiểm luôn nhánh opt-in bằng cách chạy thật `loop-runner` với hub bật. Nó cũng được nối vào bước "BNAL feature self-tests" của `harness/scripts/fdk-gate.py` nên không thể lặng lẽ chết.

## Liên quan

- [[log-model]] — ranh giới giữa các sổ ghi trong repo; hub là một sổ nữa, nhưng ghi vào git ref chứ không vào file JSONL, nên nó không tranh chỗ với sổ nào đang có.
- Sổ bài học phản tỉnh của vòng lặp (`reflexion.episodic_memory_page` trong `harness/loop-runner.config.yaml`, tạo lười khi verify đỏ lần đầu) ghi bài học dưới dạng câu chữ. Hub bổ sung chiều cấu trúc — ai rẽ từ đâu, điểm bao nhiêu — mà một sổ chữ không có.

## Origin
- **PLAN:** `llmwiki/wiki/sources/draft/290726-graph-engineering-PLAN.md` — "Task 7: Commit-DAG hub LOCAL — opt-in, gỡ được sạch"
- **PDF nguồn:** `~/Downloads/Graph-Engineering-Athropic-Karpathy-Loop.pdf` (§III.C bảy lệnh hub, §III.D "the DAG is the graph", §IX.C nợ đã biết của AgentHub)
- **Code:** `harness/scripts/hub.py`, adapter `harness/hub.config.yaml`, điểm nối `harness/scripts/loop-runner.py::run_loop`
- **Nhánh thi hành:** `ge-t7`
- **Commit:** _(verify-before-commit điền)_
- **Date promoted:** _(verify-before-commit điền)_
