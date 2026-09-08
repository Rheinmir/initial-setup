# 02 — API key, năng lực keyless, và sổ chi phí

**Vì sao dùng:** biết trước *thiếu key thì mất gì* thay vì phát hiện giữa case, và tách hai loại chi phí đừng để nhầm.
**Sinh ra cái gì:** một `.env` ở repo root, và thói quen chạy `capabilities` trước mỗi case.

---

## Không có key vẫn chạy được — đó là thiết kế

Chạy thật trong clone sạch, không `.env`:

```bash
python3 scripts/backend/intel.py capabilities
```

```
WebPivot capability — mode: KEYLESS

  [absent ] FOFA_KEY — FOFA  [critical]  (metered: costs credits)
      LOST:    ... favicon hash hoặc GA4 ID EXTRACT được nhưng không REVERSE được, nên domain anh em
               chia sẻ chúng không bao giờ lộ ra. Cluster rỗng ở chế độ keyless KHÔNG phải bằng chứng
               operator nhỏ.
      instead: crt.sh + Shodan CTL, urlscan ẩn danh, và chuỗi truy vấn Censys/PublicWWW/Shodan
               emit ra để analyst tự dán vào web UI
      get one: https://en.fofa.info/
  ...
```

Đọc kỹ dòng `LOST:` — nó chính là thứ báo cáo của bạn **phải khai** khi kết luận "không tìm thấy liên kết". Đây là chỗ khác biệt giữa "đã tìm và không có" với "không có công cụ để tìm".

## Đặt key

```bash
cd ~/.claude/skills/cti-expert
cp .env.example .env
$EDITOR .env
```

`.env` nằm ở **repo root** (cùng cấp `SKILL.md`), đã gitignore. Các biến có trong `.env.example` (23 key + `INTEL_HOME`):

| Nhóm | Biến |
|---|---|
| Internet-scan | `SHODAN_API_KEY`, `CENSYS_API_KEY` / `CENSYS_ORG_ID` / `CENSYS_API_ID`, `FOFA_KEY` + `FOFA_EMAIL`, `QUAKE_API_KEY`, `ZOOMEYE_API_KEY`, `URLSCAN_API_KEY` |
| DNS / cert / WHOIS | `SECURITYTRAILS_API_KEY` (+ `_FALLBACK`), `WHOISXML_API_KEY`, `CERTSPOTTER_API_KEY`, `ZONECRUNCHER_API_KEY`, `DNSLYTICS_API_KEY` |
| Leak / scam feed | `HUDSONROCK_API_KEY`, `CHONGLUADAO_API_KEY`, `INTELX_API_KEY` |
| On-chain | `BLOCKCHAIR_API_KEY`, `SUBSCAN_API_KEY` |
| Khác | `GITHUB_TOKEN`, `SERPAPI_KEY`, `BRIGHTDATA_SERP_KEY` |
| Override đường dẫn | `INTEL_HOME` (chỉ khi bạn muốn dùng KB chung ở ngoài repo) |

Sau khi điền, chạy lại `capabilities` — mode phải đổi khỏi `KEYLESS` và các dòng `[absent]` tương ứng biến mất.

### Bẫy WhoisXML (đã được code chẩn đoán sẵn)

Whois History và Reverse WHOIS trừ vào ví **Domain Research Suite**, không phải ví WHOIS API. Key có credit WHOIS nhưng DRS bằng 0 sẽ trả `200` cho WHOIS hiện tại và `403` cho hai cái kia. `whois_enrich._explain_403` nói thẳng điều này — **đừng** kết luận là key hỏng (`CLAUDE.md`, mục Cost visibility).

## Hai sổ chi phí, đừng gộp

| Sổ | Ai tiêu | Đọc bằng |
|---|---|---|
| Chi phí model Anthropic | vòng suy luận của agent | `/cost` trong Claude Code (interactive); harness SDK ghi `total_cost_usd` mỗi phase |
| Credit API bên thứ ba | `pivot_extract`, `whois_enrich`, FOFA/urlscan/Shodan/IPinfo... — **0 lời gọi Anthropic** | `python3 scripts/backend/intel.py api-usage` |

Ghi vào `intel_engine/MEMORY/api_usage.jsonl` (đổi chỗ bằng `$API_USAGE_LOG`). Khi báo cáo chi phí, **nói rõ hai phần** — `total_cost_usd` không bao gồm credit API.

## Kiểm ngân sách trước khi tiêu

```bash
python3 scripts/backend/intel.py censys      # có sub-lệnh keycheck/budget
python3 scripts/backend/intel.py api-usage   # đã tiêu bao nhiêu, ở đâu
```

Censys free plan: mỗi lần search trên UI trừ 5 trong 100 credit tháng — nên trình xây truy vấn CenQL chạy **offline** và chỉ emit chuỗi query + link, để việc bấm là quyết định có ý thức chứ không phải mặc định.

## Thứ tự thao tác đề xuất

1. `capabilities` → biết mình mù chỗ nào.
2. Chỉ mua/điền key cho chỗ mù **thực sự chặn** case đang làm (đọc cột `[critical]`/`[high]`).
3. `capabilities` lại → xác nhận.
4. Sau case: `api-usage` → biết đã tiêu gì.
