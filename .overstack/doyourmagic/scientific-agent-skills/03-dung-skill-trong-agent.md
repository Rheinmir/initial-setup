# 03 — Dùng skill trong agent (CHỈ prompt, không phải lệnh shell)

> **Mọi thứ trong file này gõ vào ô chat của agent, không gõ vào terminal.** Lệnh shell nằm ở [04-chay-script-bundled-tu-shell.md](04-chay-script-bundled-tu-shell.md). Lẫn hai file này là nguồn lỗi copy-paste phổ biến nhất.

**Vì sao dùng:** skill đã cài rồi vẫn có thể không được agent chọn, hoặc chọn nhầm skill anh em. File này là cách gọi trúng, và cách viết prompt để agent chạy được nhiều bước.
**Sinh ra cái gì:** các artifact do skill định nghĩa — bảng, hình, báo cáo markdown/PDF, file dữ liệu — trong workspace của bạn.

---

## Skill được chọn thế nào

Host so khớp yêu cầu của bạn với trường `description` trong frontmatter mỗi `SKILL.md`. Không có lệnh `/skill-name` — bạn **gọi tên skill trong câu văn**.

```text
Dùng skill depmap. Gene nào là dependency chọn lọc trong dòng tế bào ung thư
tuỵ so với toàn bộ panel DepMap?
```

Khi hai skill phủ nhau, nêu đích danh cái bạn muốn. Chính repo lấy ví dụ: `phylogenetics` **dựng** cây, `etetoolkit` **phân tích** cây có sẵn; `scanpy` **chạy** phân tích, `anndata` **định nghĩa** format. Nêu tên xoá được mơ hồ thay vì trông chờ router đoán đúng.

Xem agent đang có skill nào (vẫn là prompt):

```text
Liệt kê các skill bạn đang nạp có liên quan tới genomics, kèm description của từng cái.
```

## Khung prompt 5 phần (lấy từ `docs/examples.md`)

Repo chỉ rõ 5 yếu tố tách một workflow agent chạy tốt khỏi một workflow agent chạy mơ hồ:

1. **Gọi tên skill bạn muốn.**
2. **Nêu tiêu chí quyết định, không chỉ các bước.** "Lọc variant" là thiếu; "giữ QUAL > 30 và DP > 20, rồi báo mỗi bộ lọc loại bao nhiêu variant" là chạy được và kiểm toán được.
3. **Khai hợp đồng output trước khi làm.** Nói trước "bảng xếp hạng, mỗi dòng một ứng viên, có cột pIC50 dự đoán, khoảng 90%, và láng giềng gần nhất trong tập huấn luyện".
4. **Đòi provenance và đòi cả kết quả âm.** Hỏi database nào, tham số gì, ngày nào — và hỏi thẳng phân tích **không** tìm thấy gì. Workflow chỉ biết báo hit thì sẽ chỉ báo hit.
5. **Tách kế hoạch khỏi hành động không thể hoàn tác.** Bất kỳ việc gì ghi lên hệ thống từ xa, tiêu tiền, chuyển dữ liệu ra ngoài, hoặc điều khiển thiết bị vật lý phải nằm ở prompt riêng, sau khi bạn đã đọc kế hoạch.

Khung để copy:

```text
Dùng các skill <tên skill>. Giữ output có tổ chức và lưu các kết quả trung gian.

Mục tiêu: <một câu, kèm quyết định mà kết quả này phục vụ>
Dữ liệu: <ở đâu, được phép dùng tới đâu, cái gì không được rời khỏi máy>
Tiêu chí: <ngưỡng, bộ lọc, thế nào là hit, cái gì sẽ bác bỏ kết quả>
Bàn giao: <artifact chính xác, định dạng, cột/hình bắt buộc có>
Báo cáo: <provenance cho mọi dữ kiện truy xuất; độ bất định cho mọi ước lượng;
          cái gì không xác định được và vì sao>
Không được: <các hành động không hoàn tác, để dành cho một lượt duyệt riêng>
```

Hai thói quen phụ đáng giá trong các lượt chạy dài: **checkpoint** (ghi kết quả trung gian ra đĩa và đặt tên, để lỗi ở bước 9 không đốt luôn bước 1–8) và **kiểm bằng thứ rẻ mà bạn đã tin** (một ca giải được chính xác, một positive control, một benchmark đã công bố, một ước lượng bậc độ lớn) trước khi tin kết quả đắt tiền.

## Prompt mẫu nhiều skill

Pipeline drug discovery (lấy nguyên từ README):

```text
Use available skills you have access to whenever possible. Query ChEMBL for EGFR
inhibitors (IC50 < 50nM), analyze structure-activity relationships with RDKit,
generate improved analogs with datamol, perform virtual screening with DiffDock
against AlphaFold EGFR structure, search PubMed for resistance mechanisms, check
COSMIC for mutations, and create visualizations and a comprehensive report.
```

Skill dùng: `database-lookup`, `rdkit`, `datamol`, `diffdock`, `paper-lookup`, `scientific-visualization`.

Còn ~40 workflow đã viết sẵn nữa nằm trong `docs/examples.md` của repo — mỗi cái có mục "Skills Used" và "Expected Output". Đọc thẳng file đó khi cần mẫu cho lĩnh vực của bạn (cancer genomics, single-cell, protein structure, toxicology, clinical trial, PK/PD…).

## 25 skill cần credential

Skill nào cần key thì khai trong `metadata.openclaw.envVars`. Đặt biến vào môi trường (hoặc `.env` nếu skill đọc `python-dotenv`) **trước khi** khởi động agent.

| Skill | Biến môi trường | Có bắt buộc |
|---|---|---|
| `autoskill` | `SCREENPIPE_TOKEN`, `ANTHROPIC_API_KEY`, `FOUNDRY_API_KEY` | 1 bắt buộc |
| `benchling-integration` | `BENCHLING_TENANT_URL`, `BENCHLING_API_KEY`, `BENCHLING_CLIENT_ID`, `BENCHLING_CLIENT_SECRET`, + biến prod/staging | 1 bắt buộc |
| `biopython` | `NCBI_EMAIL`, `NCBI_API_KEY` | tuỳ chọn |
| `bioservices` | `NCBI_EMAIL` | tuỳ chọn |
| `citation-management` | `NCBI_EMAIL`, `NCBI_API_KEY`, `OPENALEX_EMAIL` | tuỳ chọn |
| `exa-search` | `EXA_API_KEY` | bắt buộc |
| `generate-image` | `OPENROUTER_API_KEY` | bắt buộc |
| `genomic-intelligence` | `GI_API_KEY` | tuỳ chọn |
| `infographics` | `OPENROUTER_API_KEY` | tuỳ chọn |
| `latex-posters` | `OPENROUTER_API_KEY` | tuỳ chọn |
| `literature-review` | `OPENROUTER_API_KEY` | tuỳ chọn |
| `modal` | `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, `DATABASE_URL` | 2 bắt buộc |
| `neuropixels-analysis` | `ANTHROPIC_API_KEY` | tuỳ chọn |
| `omero-integration` | `OMERO_HOST`, `OMERO_PORT`, `OMERO_USER`, `OMERO_PASSWORD`, `OMERO_SESSION_KEY`, `OMERO_SECURE` | 1 bắt buộc |
| `open-notebook` | `OPEN_NOTEBOOK_URL`, `OPEN_NOTEBOOK_PASSWORD`, `OPEN_NOTEBOOK_ENCRYPTION_KEY` | 1 bắt buộc |
| `paperclip` | `PAPERCLIP_API_KEY` | tuỳ chọn |
| `parallel-web` | `PARALLEL_API_KEY` | bắt buộc |
| `protocolsio-integration` | `PROTOCOLS_IO_ACCESS_TOKEN` | tuỳ chọn |
| `pyzotero` | `ZOTERO_API_KEY`, `ZOTERO_LIBRARY_ID`, `ZOTERO_LIBRARY_TYPE` | 2 bắt buộc |
| `research-lookup` | `PARALLEL_API_KEY`, `OPENROUTER_API_KEY` | tuỳ chọn |
| `rowan` | `ROWAN_API_KEY` | bắt buộc |
| `scientific-schematics` | `OPENROUTER_API_KEY` | tuỳ chọn |
| `scientific-slides` | `OPENROUTER_API_KEY` | tuỳ chọn |
| `tamarind` | `TAMARIND_API_KEY` | bắt buộc |
| `waypoint-bio` | `HF_TOKEN` | bắt buộc |

Tự dựng lại bảng trên bản mới hơn (lệnh shell, chạy trong repo đã clone):

```bash
grep -l 'envVars' skills/*/SKILL.md | while read -r f; do
  echo "== $(basename "$(dirname "$f")")"
  sed -n '/^---$/,/^---$/p' "$f" | grep -E 'name: [A-Z0-9_]+|required:'
done
```

## Cạm bẫy

- **Gate `requires` thất bại sẽ *ẩn* skill.** `AGENTS.md` nói rõ: nếu block `metadata.openclaw`/`metadata.hermes` gate vào một credential mà bạn chưa đặt, host có thể không hiện skill — nó biến mất chứ không báo lỗi. Không thấy skill thì kiểm env trước khi kết luận cài hỏng.
- **163 skill = rất nhiều context thường trú.** Cài nhiều làm router chọn kém đi, không phải tốt lên. Cài theo chủ đề.
- **Skill là điểm khởi đầu đã review, không phải kết quả đã kiểm định.** Repo diễn đạt là "tested examples with explicit validation, provenance, and safety boundaries; verify them in the target environment". Với các skill lâm sàng/quy chuẩn, chúng sinh ra **bản nháp cho người đủ thẩm quyền duyệt** — không phải quyết định.
