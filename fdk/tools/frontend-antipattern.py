#!/usr/bin/env python3
"""frontend-antipattern — soi anti-pattern FRONTEND ở HTML sinh (0 token, no-LLM).

Cổng chất-lượng-HTML mà p_docs (medic) KHÔNG bắt: p_docs chỉ so generator↔đĩa (anti-drift),
không nhìn NỘI DUNG lỗi. Bắt các bẫy rẻ-tiền, tất định làm hỏng copy-paste / gây hiểu nhầm:

  [FAIL] ligature chưa tắt: file có <pre>/<code> mà thiếu `font-variant-ligatures:none`
         → mono-font ligate '--'/'-' thành em-dash: người đọc gõ sai lệnh (bug đã gặp 07/2026).
  [WARN] prose lọt code block: <pre>…</pre> chứa chữ tiếng Việt có dấu ở dòng KHÔNG phải
         comment (#) → câu văn lẫn vào lệnh, copy ra chạy lỗi. Heuristic → warn, người soi lại.

  Cổng slop-test hallmark, nhóm UNIVERSAL (chưng cất design-foundation, hấp thụ 07/2026):
  [FAIL] gradient TEXT (background-clip:text) — dấu hiệu AI kinh điển. Gradient NỀN vẫn hợp lệ.
  [FAIL] italic header (<h_> chứa <em>/<i>, hoặc h_{font-style:italic}) — AI-tell đáng tin nhất.
  [WARN] fake browser chrome vẽ tay (≥3 màu traffic-light) — cấm re-drawn chrome.
  [WARN] số liệu marketing bịa (`Nx faster`, `+NN% conversion`, `trusted by N,000+`) — honest-copy.
  Nhóm genre-scoped (Inter/system làm display, pure đen-trắng) KHÔNG ở đây — false-positive trên
  chính seq.html của ta. Để model xử lúc dựng UI sản phẩm qua skills/hallmark.

  Cổng SVG (hấp thụ diagram-design `self_check.py`, 09/2026) — ta sinh SVG bằng code ở 37 chỗ
  mà trước nay không gác gì trên output:
  [FAIL] SVG tham chiếu remote http → trang tự-chứa mở offline khuyết hình.
  [FAIL] <title>/<desc> RỖNG → screen reader đọc khoảng trắng rồi bỏ qua hình.
  [WARN] sơ đồ thiếu role="img" · thiếu <title> · <title> không phải con đầu.
         WARN vì nợ cũ (20/33 và 17/33 lúc cắm); icon trang trí (aria-hidden hoặc thân <400B) được tha.

  Neo bằng chứng cho node sơ đồ (hấp thụ archify `repository-evidence.mjs`, 09/2026):
  [FAIL] node khai `data-src="path"` / `data-src="path:line"` mà đường dẫn không resolve,
         hoặc số dòng vượt độ dài file → sơ đồ đang NÓI DỐI về code. Fail-closed có chủ ý:
         không khai thì không bị hỏi; đã khai thì phải đúng.

Exit: 0 sạch · 1 có FAIL · 2 chỉ WARN (medic map: 1→fail, 2→warn, 0→ok). Fail-open:
thiếu file → sạch (không chặn). Mặc định quét llmwiki/html/overstack.html; nhận path khác qua arg.

Usage:
  frontend-antipattern.py [file.html ...]   # mặc định overstack.html
  frontend-antipattern.py --json
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = [ROOT / "llmwiki" / "html" / "overstack.html"]
# chữ Việt có dấu (precomposed) — tín hiệu chắc: lệnh shell ASCII thuần không khớp
VN = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
    r"ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
)
PRE = re.compile(r"<pre\b[^>]*>(.*?)</pre>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")

# ── Cổng slop-test hallmark, nhóm UNIVERSAL (chưng cất design-foundation) ──
# CHỈ những dấu hiệu KHÔNG BAO GIỜ hợp lệ, kể cả ở artifact kỹ thuật (seq/report).
# Nhóm genre-scoped (Inter/system làm display, pure đen-trắng, 3-cột-icon-tile) KHÔNG ở đây —
# chúng false-positive trên chính seq.html của ta (dùng system font + gradient NỀN). Để model
# xử lúc dựng UI sản phẩm qua skills/hallmark. Xem [[design-foundation]] § phạm vi.

# gradient TEXT (background-clip:text + gradient) — dấu hiệu AI kinh điển; gradient NỀN thì hợp lệ.
GRAD_TEXT = re.compile(
    r"(background-clip\s*:\s*text|-webkit-background-clip\s*:\s*text)", re.I)
# italic header: <h1..h6> chứa <em>/<i>, hoặc rule CSS cho heading + font-style:italic
ITALIC_H_EM = re.compile(r"<h[1-6]\b[^>]*>[^<]*<(?:em|i)\b", re.I)
ITALIC_H_CSS = re.compile(r"\bh[1-6]\b[^{}]*\{[^}]*font-style\s*:\s*italic", re.I)
# fake browser chrome: 3 chấm traffic-light vẽ tay (đỏ/vàng/lục cạnh nhau) — cấm re-drawn chrome
TRAFFIC = re.compile(
    r"(#ff5f5[06]|#febc2e|#28c840|#ff605c|#ffbd44|#00ca4e)", re.I)
# số liệu MARKETING bịa (honest-copy). Khớp mẫu quảng cáo, KHÔNG khớp số kỹ thuật (74/74, ~2.3k token).
FAKE_METRIC = re.compile(
    r"(\b\d+\s*[x×]\s*(?:faster|better|more)\b"
    r"|\+\s*\d+\s*%\s*(?:conversion|growth|faster|revenue|increase)"
    r"|\btrusted by\s+[\d,]+\+?\b"
    r"|\b[\d,]+\+\s*(?:teams|companies|customers|users)\s+(?:trust|use|love)\b)", re.I)


# ── Cổng SVG: accessibility + self-containment (hấp thụ diagram-design self_check.py, 09/2026) ──
# Ta tự viết SVG bằng code ở 37 chỗ trong build-overstack-docs.py / build-wiki-graph.py mà KHÔNG
# gác gì trên output. diagram-design gác đúng bốn thứ này; port sang vì nó tất định, 0 token, và
# áp được cho SVG do code sinh (khác các luật khác ở đây vốn nhắm CSS).
SVG_TAG = re.compile(r"<svg\b[^>]*>(.*?)</svg>", re.S | re.I)
SVG_REMOTE = re.compile(
    r"(?:href|xlink:href)\s*=\s*[\"']https?://|url\(\s*[\"']?https?://", re.I)
SVG_TITLE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.S | re.I)
SVG_DESC = re.compile(r"<desc\b[^>]*>(.*?)</desc>", re.S | re.I)
SVG_FIRST_EL = re.compile(r"\s*<(\w+)")
# Icon trang trí không cần nhãn: đã khai aria-hidden, HOẶC thân quá nhỏ để là sơ đồ.
# Đo 2026-09-04 trên 86 <svg> của repo: 53 rơi vào nhóm này, 33 là sơ đồ thật.
SVG_DECORATIVE_MAX = 400
SVG_ARIA_HIDDEN = re.compile(r"aria-hidden\s*=\s*[\"']true", re.I)


# Neo bằng chứng cho NODE sơ đồ (hấp thụ archify `repository-evidence.mjs`, 09/2026).
# archify từ chối RENDER khi sources[] của một component không verify được — fail-closed.
# Bản của ta gọn hơn vì SVG do chính code ta sinh: node khai `data-src="path"` hoặc
# `data-src="path:line"`, và cổng FAIL nếu đường dẫn không resolve trên đĩa. Cùng nguyên
# lý với claim-receipts (ref phải tồn tại), khác chỗ áp: đây là node HÌNH, không phải câu văn.
SVG_DATA_SRC = re.compile(r'data-src\s*=\s*"([^"]+)"')


def scan_svg_evidence(html: str, rel: str, root) -> list:
    """FAIL khi node sơ đồ khai bằng chứng mà bằng chứng không tồn tại.

    Fail-closed có chủ ý: một node trỏ vào file đã bị đổi tên/xoá là sơ đồ đang NÓI DỐI
    về code — tệ hơn node không khai gì. Không khai thì không bị hỏi.
    """
    out = []
    for m in SVG_DATA_SRC.finditer(html):
        ref = m.group(1)
        path_part, _, line_part = ref.partition(":")
        target = root / path_part
        if not target.exists():
            out.append({"level": "FAIL", "file": rel,
                        "msg": f"node sơ đồ khai bằng chứng `{ref}` nhưng đường dẫn KHÔNG tồn tại "
                               "— sơ đồ đang nói dối về code. Sửa neo hoặc bỏ data-src.",
                        "snippet": ref[:70]})
            continue
        if line_part.isdigit():
            try:
                n = sum(1 for _ in target.open(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
            if int(line_part) > n:
                out.append({"level": "FAIL", "file": rel,
                            "msg": f"node sơ đồ neo `{ref}` nhưng file chỉ có {n} dòng — neo trôi.",
                            "snippet": ref[:70]})
    return out


# ── Cổng HÌNH HỌC cho SVG (hấp thụ archify `check-render-output.mjs`, 09/2026) ──
# archify có 9 check hình học có tên (orthogonal_arrows, relationship_crossings,
# label_route_clearance, legend_clearance…) và TỪ CHỐI giao artifact khi chúng đỏ. Ta vẽ SVG
# bằng code ở 37 chỗ mà không kiểm hình học lần nào — cổng SVG hiện có chỉ soi a11y và
# tự-chứa. Một sơ đồ có ô đè nhau hay chữ tràn viền vẫn qua cổng trót lọt.
#
# Đo trên 5 sơ đồ thật của overstack trước khi chọn luật (cùng kỷ luật đã dùng cho em-dash):
#   · rect đè nhau          0 vi phạm → nhận, FAIL
#   · phần tử ngoài viewBox 0 vi phạm → nhận, FAIL
#   · chữ tràn/sát viền ô   0 vi phạm → nhận, FAIL
#   · mũi tên phải thẳng ngang/dọc — LOẠI: sơ đồ của ta cố ý toả nan quạt từ một node
#     (6·4·10 đường chéo hợp lệ ở 3 sơ đồ). Đó là ràng buộc phong cách CỦA archify,
#     không phải lỗi của ta. Bê nguyên là lặp lại lỗi genre-scoped.
SVG_VIEWBOX = re.compile(r'viewBox\s*=\s*"([\d.\-\s]+)"', re.I)
SVG_RECT = re.compile(
    r'<rect\b[^>]*?x="([\d.]+)"[^>]*?y="([\d.]+)"[^>]*?width="([\d.]+)"[^>]*?height="([\d.]+)"[^>]*>', re.I)
SVG_TEXT = re.compile(r"<text\b([^>]*)>([^<]*)</text>", re.I)
SVG_ATTR = re.compile(r'(\w[\w-]*)\s*=\s*"([^"]*)"')
# Bề rộng chữ ước lượng: ký tự × cỡ chữ × hệ số. 0.55 là xấp xỉ chuẩn cho font sans tỉ lệ.
# Cố ý ước lượng RỘNG RÃI (ngưỡng 2px) — cổng này bắt lỗi bố cục thật, không phải trọng tài
# kerning. Muốn đo chính xác thì đó là việc của visual-receipt.py (trình duyệt thật).
SVG_CHAR_W = 0.55
SVG_EDGE_PAD = 2.0
SVG_GEOM_MIN_BOX = 400   # cùng ngưỡng "là sơ đồ thật" với luật a11y ở trên


def _svg_attrs(blob: str) -> dict:
    return {k.lower(): v for k, v in SVG_ATTR.findall(blob)}


def scan_svg_geometry(html: str, rel: str) -> list:
    """Ba lỗi bố cục mà mắt thấy ngay nhưng cổng tĩnh hiện tại mù hoàn toàn."""
    out = []
    for m in SVG_TAG.finditer(html):
        whole, body = m.group(0), m.group(1)
        if len(body) < SVG_GEOM_MIN_BOX:
            continue                      # icon trang trí — không có bố cục để hỏng
        vb = SVG_VIEWBOX.search(whole[: whole.find(">") + 1])
        rects = [tuple(map(float, r)) for r in SVG_RECT.findall(body)]

        for a, b in ((i, j) for i in range(len(rects)) for j in range(i + 1, len(rects))):
            x1, y1, w1, h1 = rects[a]
            x2, y2, w2, h2 = rects[b]
            # Ô LỒNG hẳn trong ô khác là bố cục hợp lệ (khung bao, nền nhóm) — chỉ bắt ĐÈ MỘT PHẦN.
            inner = (x1 >= x2 and y1 >= y2 and x1 + w1 <= x2 + w2 and y1 + h1 <= y2 + h2) or \
                    (x2 >= x1 and y2 >= y1 and x2 + w2 <= x1 + w1 and y2 + h2 <= y1 + h1)
            if inner:
                continue
            if x1 < x2 + w2 and x2 < x1 + w1 and y1 < y2 + h2 and y2 < y1 + h1:
                out.append({"level": "FAIL", "file": rel,
                            "msg": "hai ô sơ đồ ĐÈ NHAU một phần — bố cục hỏng, người đọc không "
                                   "phân biệt được node. Giãn toạ độ hoặc thu ô.",
                            "snippet": f"({x1:g},{y1:g},{w1:g}×{h1:g}) ∩ ({x2:g},{y2:g},{w2:g}×{h2:g})"})
                break

        if vb:
            try:
                vx, vy, vw, vh = (float(n) for n in vb.group(1).split()[:4])
            except ValueError:
                vx = vy = vw = vh = None
            if vw:
                for x, y, w, h in rects:
                    if x < vx - 0.5 or y < vy - 0.5 or x + w > vx + vw + 0.5 or y + h > vy + vh + 0.5:
                        out.append({"level": "FAIL", "file": rel,
                                    "msg": "ô sơ đồ nằm NGOÀI viewBox — phần đó không bao giờ hiện "
                                           "ra. Nới viewBox hoặc kéo ô vào trong.",
                                    "snippet": f"ô ({x:g},{y:g},{w:g}×{h:g}) vs viewBox {vw:g}×{vh:g}"})
                        break

        for blob, label in SVG_TEXT.findall(body):
            at = _svg_attrs(blob)
            if not {"x", "y", "font-size"} <= at.keys() or not label.strip():
                continue
            try:
                tx, ty, fs = float(at["x"]), float(at["y"]), float(at["font-size"])
            except ValueError:
                continue
            host = next((r for r in rects
                         if r[0] <= tx <= r[0] + r[2] and r[1] - 14 <= ty <= r[1] + r[3] + 4), None)
            if not host:
                continue                  # chữ tự do ngoài ô — không có viền để tràn
            tw = len(label) * fs * SVG_CHAR_W
            left = tx - tw / 2 if at.get("text-anchor") == "middle" else tx
            if min(left - host[0], host[0] + host[2] - (left + tw)) < -SVG_EDGE_PAD:
                out.append({"level": "FAIL", "file": rel,
                            "msg": "chữ TRÀN RA NGOÀI ô chứa nó — nhãn bị cắt hoặc đè lên node "
                                   "bên cạnh. Rút ngắn nhãn, giảm cỡ chữ, hoặc nới ô.",
                            "snippet": f'"{label[:28]}" rộng ~{tw:.0f}px trong ô {host[2]:g}px'})
                break
    return out


def scan_svg(html: str, rel: str) -> list:
    """Bốn luật của diagram-design, chia mức theo NỢ ĐANG CÓ chứ không theo cảm tính.

    FAIL cho hai luật hôm nay đang 0 vi phạm (remote ref, title/desc rỗng) — gác ngay
    không tốn gì, và chặn đúng thứ làm hỏng offline/screen-reader.
    WARN cho hai luật đang có nợ thật (20 thiếu role, 17 thiếu title trên 33 sơ đồ) —
    FAIL ngay sẽ làm đỏ cổng vì code CŨ, biến medic thành thứ người ta tắt đi.
    # ponytail: WARN là bậc thang, nâng lên FAIL khi nợ về 0.
    """
    out = []
    for m in SVG_TAG.finditer(html):
        whole = m.group(0)
        head = whole[: whole.find(">") + 1]
        body = m.group(1)
        if SVG_REMOTE.search(body):
            out.append({"level": "FAIL", "file": rel,
                        "msg": "SVG tham chiếu tài nguyên REMOTE (http) — trang tự-chứa mà mở "
                               "offline sẽ khuyết hình. Nhúng data: URI hoặc vẽ thẳng.",
                        "snippet": (SVG_REMOTE.search(body).group(0))[:60]})
        for tag, rx in (("title", SVG_TITLE), ("desc", SVG_DESC)):
            el = rx.search(body)
            if el and not el.group(1).strip():
                out.append({"level": "FAIL", "file": rel,
                            "msg": f"SVG có <{tag}> RỖNG — tệ hơn không có: screen reader đọc ra "
                                   f"khoảng trắng và bỏ qua hình. Điền nội dung hoặc xoá thẻ.",
                            "snippet": f"<{tag}></{tag}>"})
        if SVG_ARIA_HIDDEN.search(head) or len(body) < SVG_DECORATIVE_MAX:
            continue  # icon trang trí — không đòi nhãn
        if "role=" not in head:
            out.append({"level": "WARN", "file": rel,
                        "msg": "SVG sơ đồ thiếu role=\"img\" — screen reader coi nó là nhóm hình "
                               "vô nghĩa. Icon trang trí thì khai aria-hidden=\"true\" thay vì bỏ trống.",
                        "snippet": head[:70]})
        elif not SVG_TITLE.search(body):
            out.append({"level": "WARN", "file": rel,
                        "msg": "SVG sơ đồ có role nhưng thiếu <title> — role=img mà không tên thì "
                               "vẫn câm. <title> phải là CON ĐẦU TIÊN của <svg>.",
                        "snippet": head[:70]})
        else:
            first = SVG_FIRST_EL.match(body)
            if first and first.group(1).lower() != "title":
                out.append({"level": "WARN", "file": rel,
                            "msg": "SVG có <title> nhưng KHÔNG phải con đầu tiên — một số screen "
                                   "reader chỉ đọc con đầu, đặt sau là mất tên.",
                            "snippet": f"con đầu đang là <{first.group(1)}>"})
    return out


def _unesc(s: str) -> str:
    return (s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
             .replace("&#39;", "'").replace("&amp;", "&"))


def scan(path: Path) -> list:
    """Trả list finding dict: {level, file, msg, snippet}."""
    out = []
    try:
        html = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return out  # fail-open: đọc không được → coi như sạch
    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    has_code = ("<pre" in html) or ("<code" in html)
    # [FAIL] ligature — chỉ bắt khi CÓ code block
    if has_code and "font-variant-ligatures:none" not in html:
        out.append({"level": "FAIL", "file": str(rel),
                    "msg": "có <pre>/<code> nhưng thiếu `font-variant-ligatures:none` "
                           "(mono ligate '-' thành em-dash → gõ sai lệnh)",
                    "snippet": "pre,code{font-variant-ligatures:none;font-feature-settings:\"liga\" 0,\"calt\" 0}"})
    # ── Cổng slop-test hallmark (UNIVERSAL) — dấu hiệu AI không bao giờ hợp lệ ──
    # CHỈ quét trong <style> (+ inline style=""), KHÔNG quét cả trang: văn xuôi nhắc
    # `background-clip:text` để GIẢI THÍCH cổng thì không phải vi phạm (bài học R7-d, p-32).
    styles = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", html, re.S | re.I))
    styles += "\n".join(re.findall(r'style\s*=\s*"([^"]*)"', html, re.I))
    if GRAD_TEXT.search(styles):
        out.append({"level": "FAIL", "file": str(rel),
                    "msg": "gradient TEXT (background-clip:text) — dấu hiệu AI kinh điển (slop-test #2). "
                           "Gradient NỀN thì hợp lệ; nhấn chữ bằng weight/màu đặc, không gradient.",
                    "snippet": "background-clip:text  ← bỏ"})
    if ITALIC_H_EM.search(html) or ITALIC_H_CSS.search(styles):
        out.append({"level": "FAIL", "file": str(rel),
                    "msg": "italic header — một trong những AI-tell đáng tin nhất (slop-test #38a). "
                           "Heading luôn roman; nhấn bằng weight/màu/underline, italic chỉ trong body.",
                    "snippet": "<h_>…<em> hoặc h_{font-style:italic}  ← bỏ"})
    if len(set(TRAFFIC.findall(styles))) >= 3:
        out.append({"level": "WARN", "file": str(rel),
                    "msg": "nghi fake browser chrome vẽ tay (≥3 màu traffic-light) — cấm re-drawn chrome "
                           "(discipline #4). Dùng screenshot thật trong <figure>, hoặc bỏ chrome.",
                    "snippet": "3 chấm đỏ/vàng/lục cạnh nhau"})
    for m in FAKE_METRIC.finditer(TAG.sub(" ", html)):
        out.append({"level": "WARN", "file": str(rel),
                    "msg": "nghi số liệu marketing BỊA (honest-copy, slop-test #46) — nếu không có nguồn thật, "
                           "dùng placeholder có nhãn hoặc đổi macrostructure.",
                    "snippet": m.group(0)[:60]})
        break
    out += scan_svg(html, str(rel))
    out += scan_svg_evidence(html, str(rel), ROOT)
    out += scan_svg_geometry(html, str(rel))
    # [WARN] prose lọt <pre> — chữ Việt có dấu ở dòng không-comment
    for block in PRE.findall(html):
        text = _unesc(TAG.sub("", block))
        for ln in text.splitlines():
            s = ln.strip()
            if not s or s.startswith("#"):
                continue  # dòng trống / comment shell → cho phép
            code_part = s.split("#", 1)[0]  # bỏ comment inline (`lệnh  # chú thích VN` hợp lệ)
            if VN.search(code_part):
                out.append({"level": "WARN", "file": str(rel),
                            "msg": "prose tiếng Việt lọt code block (copy ra chạy lỗi)",
                            "snippet": s[:80]})
                break  # 1 cảnh báo / block là đủ
    return out


def _scan_text(html: str) -> list:
    """scan() nhưng trên chuỗi (cho self-test, không cần file thật)."""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        tmp = Path(f.name)
    try:
        return scan(tmp)
    finally:
        tmp.unlink()


def self_test() -> int:
    """Bite-test: cổng slop hallmark phải BẮT bản BAD và THA bản GOOD. Exit 0 pass / 1 fail."""
    BAD = ("<html><head><style>.h1{background:linear-gradient(135deg,#0a84ff,#5856d6);"
           "-webkit-background-clip:text;color:transparent} h2{font-style:italic}</style></head>"
           "<body><h1>x</h1><h2>Built to <em>think</em></h2>"
           "<p>10x faster than the competition, trusted by 50,000+ teams</p></body></html>")
    GOOD = ("<html><head><style>.h1{color:#0a2540;font-weight:800}"
            "code{font-variant-ligatures:none}</style></head>"
            "<body><h1>x</h1><p>đo thật: 74/74 test PASS, cắt ~2.307 token</p></body></html>")
    # Cổng SVG (hấp thụ diagram-design): BAD phải bị bắt, GOOD phải sạch.
    SVG_BAD = ('<html><body><svg viewBox="0 0 10 10"><desc></desc>'
               '<image href="https://cdn.example.com/x.png"/>' + "<path d='M0 0'/>" * 40
               + '</svg></body></html>')
    SVG_GOOD = ('<html><body><svg role="img" viewBox="0 0 10 10"><title>Sơ đồ luồng</title>'
                + "<path d='M0 0'/>" * 40 + '</svg>'
                '<svg aria-hidden="true" viewBox="0 0 4 4">' + "<path d='M1 1'/>" * 40
                + '</svg></body></html>')
    EV_BAD = '<html><body><svg role="img"><title>x</title>' + "<path d='M0 0'/>" * 40 + \
             '<rect data-src="harness/scripts/khong-he-ton-tai.py"/></svg></body></html>'
    EV_GOOD = '<html><body><svg role="img"><title>x</title>' + "<path d='M0 0'/>" * 40 + \
              '<rect data-src="harness/scripts/fdk-gate.py"/></svg></body></html>'
    ev_bad = _scan_text(EV_BAD)
    ev_good = [f for f in _scan_text(EV_GOOD) if "bằng chứng" in f["msg"] or "neo" in f["msg"]]
    PAD = "<path d='M0 0'/>" * 40
    GEO_OVERLAP = ('<html><body><svg role="img" viewBox="0 0 200 100"><title>t</title>' + PAD +
                   '<rect x="10" y="10" width="80" height="40"/>'
                   '<rect x="50" y="20" width="80" height="40"/></svg></body></html>')
    GEO_OUTSIDE = ('<html><body><svg role="img" viewBox="0 0 200 100"><title>t</title>' + PAD +
                   '<rect x="180" y="10" width="80" height="40"/></svg></body></html>')
    GEO_OVERFLOW = ('<html><body><svg role="img" viewBox="0 0 200 100"><title>t</title>' + PAD +
                    '<rect x="10" y="10" width="40" height="30"/>'
                    '<text x="30" y="28" font-size="12" text-anchor="middle">'
                    'nhãn dài quá khổ so với ô</text></svg></body></html>')
    GEO_GOOD = ('<html><body><svg role="img" viewBox="0 0 200 100"><title>t</title>' + PAD +
                '<rect x="10" y="10" width="80" height="40"/>'
                '<rect x="100" y="10" width="80" height="40"/>'
                # ô LỒNG hẳn trong ô khác = khung bao hợp lệ, KHÔNG được coi là đè
                '<rect x="15" y="15" width="20" height="10"/>'
                '<text x="140" y="34" font-size="10" text-anchor="middle">vừa</text>'
                '<line x1="90" y1="30" x2="100" y2="44"/></svg></body></html>')
    geo_ov = _scan_text(GEO_OVERLAP); geo_out = _scan_text(GEO_OUTSIDE)
    geo_of = _scan_text(GEO_OVERFLOW)
    geo_good = [f for f in _scan_text(GEO_GOOD) if f["level"] == "FAIL"]
    svg_bad = _scan_text(SVG_BAD)
    svg_good = [f for f in _scan_text(SVG_GOOD) if "SVG" in f["msg"]]
    bad = _scan_text(BAD)
    good = _scan_text(GOOD)
    bad_kinds = {f["msg"][:20] for f in bad}
    ok = True
    checks = [
        ("BAD bắt gradient-text", any("gradient TEXT" in f["msg"] for f in bad)),
        ("BAD bắt italic-header (em)", any("italic header" in f["msg"] for f in bad)),
        ("BAD bắt số liệu marketing", any("marketing" in f["msg"] for f in bad)),
        ("GOOD sạch (0 finding)", len(good) == 0),
        ("SVG BAD bắt remote ref (FAIL)",
         any("REMOTE" in f["msg"] and f["level"] == "FAIL" for f in svg_bad)),
        ("SVG BAD bắt <desc> rỗng (FAIL)",
         any("RỖNG" in f["msg"] and f["level"] == "FAIL" for f in svg_bad)),
        ("SVG BAD bắt thiếu role (WARN)",
         any("role=" in f["msg"] and f["level"] == "WARN" for f in svg_bad)),
        ("SVG GOOD sạch — icon aria-hidden được tha", len(svg_good) == 0),
        ("neo data-src trỏ file KHÔNG tồn tại → FAIL",
         any("KHÔNG tồn tại" in f["msg"] and f["level"] == "FAIL" for f in ev_bad)),
        ("neo data-src trỏ file có thật → sạch", len(ev_good) == 0),
        ("hình học: hai ô ĐÈ NHAU → FAIL", any("ĐÈ NHAU" in f["msg"] for f in geo_ov)),
        ("hình học: ô NGOÀI viewBox → FAIL", any("NGOÀI viewBox" in f["msg"] for f in geo_out)),
        ("hình học: chữ TRÀN ô → FAIL", any("TRÀN RA NGOÀI" in f["msg"] for f in geo_of)),
        ("hình học: bố cục lành + ô LỒNG + đường chéo → sạch", len(geo_good) == 0),
    ]
    for label, passed in checks:
        print(f"  {'✓' if passed else '✗'} {label}")
        ok = ok and passed
    print("self-test: PASS" if ok else "self-test: FAIL")
    return 0 if ok else 1


def main() -> None:
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    args = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv
    targets = [Path(a) for a in args] if args else DEFAULT
    findings = []
    for t in targets:
        findings += scan(t)
    fails = [f for f in findings if f["level"] == "FAIL"]
    warns = [f for f in findings if f["level"] == "WARN"]
    if as_json:
        import json
        print(json.dumps({"fail": len(fails), "warn": len(warns), "findings": findings},
                         ensure_ascii=False))
    else:
        for f in findings:
            mark = "\033[1;31m✗\033[0m" if f["level"] == "FAIL" else "\033[1;33m⚠\033[0m"
            print(f"  {mark} {f['file']}: {f['msg']}\n      → {f['snippet']}")
        n = len([t for t in targets if t.exists()])
        if not findings:
            print(f"  \033[1;32m✓\033[0m {n} file HTML sạch anti-pattern frontend")
        else:
            print(f"\n  {len(fails)} FAIL · {len(warns)} WARN trên {n} file")
    sys.exit(1 if fails else (2 if warns else 0))


if __name__ == "__main__":
    main()
