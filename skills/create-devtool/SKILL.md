---
name: create-devtool
description: "Sinh 1 dev toolkit xuyên suốt app cho project Next.js/React đích: burger icon global (mount ở root layout, không riêng 1 trang) mở overlay chứa console-log + network-fetch capture (ring buffer 100 dòng), toggle 'Break on error' (chèn debugger; khi có lỗi), tuỳ chọn role-override (giả lập UI theo role) và dev-login bypass (nếu project có endpoint bypass riêng), tuỳ chọn nút clear cache React Query. Tự phát hiện Tailwind/shadcn-radix component có sẵn để tái dùng (Sheet/Checkbox/Switch/Badge/Accordion), sinh bản vanilla-CSS nếu project không có. Chỉ hiện khi 1 biến env gate = có set (không set trên PRD). Gọi khi user nói: 'thêm dev toolkit', 'thêm devtool', 'burger debug', 'panel debug xuyên app', 'console/network capture', 'break on error', 'giả lập role UI', hoặc gọi đích danh /create-devtool. Distill từ implementation thật đã build + verify (click CDP thật) trong payroll-frontend (Next.js App Router)."
version: 1.0.0
---

# Skill: create-devtool

## Purpose

Sinh 1 dev toolkit — 1 icon burger cố định góc màn hình, mount ở ROOT LAYOUT (có mặt ở MỌI trang, không riêng 1 route), mở overlay chứa các công cụ debug: xem 100 log console gần nhất, 100 request network gần nhất, bật/tắt dừng ở DevTools khi có lỗi, và (tuỳ chọn) giả lập role để xem UI theo quyền khác, và (tuỳ chọn) đăng nhập nhanh qua đường bypass riêng của project. Chỉ tồn tại khi 1 biến env "gate" có set — build production không set biến này thì toolkit **không vào bundle** (tự loại, không phải ẩn bằng CSS).

Không phải npm package — skill này ĐỌC project đích rồi VIẾT code trực tiếp vào đúng project đó (giống cách skill khác trong hệ này generate code), theo đúng convention (component library, token màu) đã có sẵn ở project đích, không đè lên bằng style lạ.

## Khi nào KHÔNG dùng

- Project không phải Next.js/React (Vue/Svelte/vanilla) — v1 chưa hỗ trợ, dừng và báo rõ thay vì generate sai.
- User chỉ cần 1 nút debug đơn giản (ví dụ chỉ cần xem 1 giá trị state) — việc đó nhỏ hơn cả component-scope, làm tay nhanh hơn gọi skill.

## Bước 0 — Pre-flight scan (đọc trước khi hỏi, giống nguyên tắc của skill `hallmark`)

Đọc, KHÔNG sửa gì ở bước này:

1. **Framework**: `package.json` có `next`? App Router (`app/layout.tsx` tồn tại) hay Pages Router (`pages/_app.tsx`)? Nếu không phải Next.js — kiểm `react` + tự hỏi entry point tương đương (root component bọc toàn app).
2. **Styling**: có Tailwind (`tailwind.config.*` hoặc `@import "tailwindcss"` trong CSS entry)? Có OKLCH/hex token nào ở `:root`/`@theme` không (để biết dùng token nào cho màu cảnh báo — KHÔNG bao giờ tự chế `amber-*`/màu Tailwind mặc định nếu project đã có token semantic riêng như `warning`/`danger`).
3. **Component library**: grep `components/` (hoặc `src/components/`) tìm các file/export tên gần đúng `Sheet`, `Checkbox`, `Switch`, `Badge`, `Accordion`, `ScrollArea`, `Button`, `Label` (thường là shadcn/radix nếu có `radix-ui`/`@radix-ui/*` trong `package.json`). Với MỖI component tìm được — đọc props thật (checked/onCheckedChange hay checked/onChange? open/onOpenChange?) trước khi dùng, ĐỪNG đoán API.
4. **Data layer**: có `@tanstack/react-query` trong deps? Có `@tanstack/react-query-devtools` đã cài nhưng CHƯA mount ở đâu (rất thường gặp — kiểm bằng grep `ReactQueryDevtools` toàn repo, 0 kết quả nghĩa là chưa mount)? Nếu có QueryClientProvider nhưng client instance không export — dùng `useQueryClient()` hook trong component mới, không export lại biến module.
5. **Auth**: có sẵn 1 cơ chế "dev bypass login" nào chưa (biến env dạng `*_DEV_*`, endpoint `/me`/`/whoami`, header `Authorization: Bearer dev` hay tương tự)? Nếu KHÔNG có — mục "Đăng nhập nhanh" sẽ bị bỏ qua ở Bước 1 (không tự chế 1 cơ chế bypass mới, quá nhạy cảm để tự quyết).

**In ra 1 khối tóm tắt** trước khi hỏi gì, theo mẫu:
```
Pre-flight: Next.js App Router · Tailwind (token: warning-500/danger-500 tại app/globals.css @theme)
· Component có sẵn: Sheet, Checkbox, Switch, Badge, Accordion, ScrollArea (components/core/*, radix-ui)
· React Query: có (chưa mount ReactQueryDevtools) · Dev-login bypass: có (Bearer dev, /api/v1/me)
```

## Bước 1 — Hỏi cấu hình (tối đa 1 lượt, có thể bỏ qua từng mục)

Hỏi 1 lần, cho phép trả lời từng phần hoặc "bỏ qua X":

1. **Tên biến env gate** — mặc định gợi ý `NEXT_PUBLIC_DEV_TOOLKIT` (hoặc theo convention project nếu Bước 0 đã thấy pattern `NEXT_PUBLIC_*_DEV_*`). Đây là biến DUY NHẤT quyết định toolkit có build vào bundle hay không.
2. **Role-override** — nếu project có RBAC rõ ràng (tìm thấy 1 danh sách role cố định, ví dụ enum/const), hỏi user xác nhận danh sách role thật (không tự đoán role từ code, dễ sai/thiếu). Không có RBAC hoặc user nói "bỏ qua" → skip mục này hoàn toàn (không sinh `role-override.ts`, không có AccordionItem "Vai trò").
3. **Đăng nhập nhanh** — chỉ hỏi nếu Bước 0 đã tìm thấy cơ chế bypass sẵn có. Hỏi endpoint + tên header/token bypass thật (không tự chế). Không có → skip mục này.
4. **Cache** — chỉ hỏi/sinh nếu Bước 0 xác nhận có React Query. Không có React Query → mục Cache chỉ còn nút "Xoá console/network log đã ghi" (bỏ nút clear query cache).

Console log + Network + Break-on-error **luôn sinh, không hỏi** — đây là phần generic 100%, giá trị chính của skill.

## Bước 2 — Sinh file

Tạo thư mục `components/dev-toolkit/` (hoặc theo convention thư mục component thật của project, xem Bước 0) với các file sau. **Luôn sinh `capture.ts` gần như nguyên văn** (đã test kỹ, generic 100% — không viết lại logic ring-buffer/monkey-patch từ đầu):

### `capture.ts` — LUÔN sinh, không đổi logic cốt lõi

```typescript
// Dev toolkit — capture console log + fetch network, ring buffer 100 dòng gần nhất.
//
// Cố ý KHÔNG dùng React state cho buffer (chỉ 1 array module-scope) — nếu để console.log
// đẩy state React mỗi lần gọi, mọi nơi gọi console.log sẽ re-render toàn app. UI chỉ đọc
// snapshot (.slice()) khi panel mở hoặc bấm "Làm mới" — không subscribe realtime.
//
// patchOnce() phải gọi ĐÚNG 1 LẦN (module-scope guard) — Next.js dev mode remount component
// nhiều lần (Fast Refresh) sẽ patch console.log lồng nhau nếu không có guard, in log trùng N lần.

export interface ConsoleEntry {
  ts: number;
  level: "log" | "info" | "warn" | "error";
  args: string[];
}

export interface NetworkEntry {
  ts: number;
  method: string;
  url: string;
  status: number | "error";
  durationMs: number;
}

const MAX_ENTRIES = 100;
const consoleBuf: ConsoleEntry[] = [];
const networkBuf: NetworkEntry[] = [];

function pushCapped<T>(buf: T[], entry: T) {
  buf.push(entry);
  if (buf.length > MAX_ENTRIES) buf.shift();
}

function safeStringify(a: unknown): string {
  if (typeof a === "string") return a;
  try {
    return JSON.stringify(a);
  } catch {
    return String(a);
  }
}

let breakOnErrorEnabled = false;
export function setBreakOnError(enabled: boolean) {
  breakOnErrorEnabled = enabled;
}
export function isBreakOnErrorEnabled() {
  return breakOnErrorEnabled;
}

let patched = false;

/** Gọi 1 lần ở component UI (client component, useEffect) — no-op nếu gọi lại. */
export function patchOnce() {
  if (patched || typeof window === "undefined") return;
  patched = true;

  const levels: ConsoleEntry["level"][] = ["log", "info", "warn", "error"];
  for (const level of levels) {
    const original = console[level].bind(console);
    console[level] = (...args: unknown[]) => {
      pushCapped(consoleBuf, { ts: Date.now(), level, args: args.map(safeStringify) });
      // eslint-disable-next-line no-debugger
      if (level === "error" && breakOnErrorEnabled) debugger;
      original(...args);
    };
  }

  // Lỗi CHƯA CATCH không đi qua console.error — bắt riêng, nếu không sẽ bỏ sót đúng loại lỗi
  // nghiêm trọng nhất (crash render, promise vỡ).
  window.addEventListener("error", (e) => {
    pushCapped(consoleBuf, { ts: Date.now(), level: "error", args: [`Uncaught: ${e.message}`, `${e.filename}:${e.lineno}`] });
    // eslint-disable-next-line no-debugger
    if (breakOnErrorEnabled) debugger;
  });
  window.addEventListener("unhandledrejection", (e) => {
    pushCapped(consoleBuf, { ts: Date.now(), level: "error", args: [`Unhandled rejection: ${safeStringify(e.reason)}`] });
    // eslint-disable-next-line no-debugger
    if (breakOnErrorEnabled) debugger;
  });

  const originalFetch = window.fetch.bind(window);
  window.fetch = async (...args: Parameters<typeof fetch>) => {
    const started = performance.now();
    const req = args[0];
    const url = typeof req === "string" ? req : req instanceof URL ? req.toString() : req.url;
    const method = (typeof req === "object" && "method" in req && req.method) || args[1]?.method || "GET";
    try {
      const res = await originalFetch(...args);
      pushCapped(networkBuf, { ts: Date.now(), method: String(method), url, status: res.status, durationMs: Math.round(performance.now() - started) });
      // eslint-disable-next-line no-debugger
      if (res.status >= 400 && breakOnErrorEnabled) debugger;
      return res;
    } catch (err) {
      pushCapped(networkBuf, { ts: Date.now(), method: String(method), url, status: "error", durationMs: Math.round(performance.now() - started) });
      // eslint-disable-next-line no-debugger
      if (breakOnErrorEnabled) debugger;
      throw err;
    }
  };
}

export function getConsoleLogs(): ConsoleEntry[] {
  return consoleBuf.slice();
}
export function getNetworkLogs(): NetworkEntry[] {
  return networkBuf.slice();
}
export function clearCaptured() {
  consoleBuf.length = 0;
  networkBuf.length = 0;
}
```

### `role-override.ts` — CHỈ sinh nếu Bước 1 xác nhận có role list

Template (thay `KNOWN_ROLES` bằng danh sách thật user xác nhận, thay `NEXT_PUBLIC_DEV_TOOLKIT` bằng tên biến gate thật đã chọn):

```typescript
// Dev toolkit — giả lập vai trò để xem UI theo role khác, KHÔNG đổi quyền thật ở backend.
// Chỉ có tác dụng khi <TÊN_BIẾN_GATE> có set — build production luôn trả null.

const KEY = "dev_role_override";
export const KNOWN_ROLES = [/* ĐIỀN role thật của project, user xác nhận ở Bước 1 */] as const;

export function getRoleOverride(): string[] | null {
  if (!process.env.<TÊN_BIẾN_GATE> || typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : null;
  } catch {
    return null;
  }
}

export function setRoleOverride(roles: string[] | null) {
  if (typeof window === "undefined") return;
  if (!roles || roles.length === 0) localStorage.removeItem(KEY);
  else localStorage.setItem(KEY, JSON.stringify(roles));
}
```

Sau khi sinh file này, tìm hàm `hasRole()` (hoặc tương đương) thật của project trong file auth/context, và patch nó đọc override TRƯỚC role thật — **đọc kỹ implementation thật trước khi patch, đừng đoán tên hàm/field**. Ví dụ pattern đã verify:

```typescript
const hasRole = (role: string) => (getRoleOverride() ?? user?.roles ?? []).includes(role);
```

### `DevToolkit.tsx` — LUÔN sinh, cấu trúc theo Bước 0+1

Cấu trúc cố định: burger `<Button>` (hoặc `<button>` thô nếu project không có component Button) cố định 1 góc màn hình (`fixed`, `z-50` hoặc cao hơn mọi overlay khác của project) → mở overlay (component `Sheet` nếu có, nếu không thì 1 `<div>` fixed side-panel tự viết với backdrop) → 1 toggle "Break on error" LUÔN hiện không cần mở accordion (dùng `Switch` nếu có, `<input type="checkbox">` styled tối thiểu nếu không) → các mục còn lại dạng Accordion (hoặc `<details>` thuần nếu project không có Accordion component): Đăng nhập nhanh (nếu Bước 1 không skip) · Vai trò (nếu không skip) · Console log · Network · Cache.

**Quy tắc bắt buộc khi sinh JSX — chống AI slop (bài học thật, đã bị bắt bằng audit `hallmark` ở lần build gốc):**
- KHÔNG dùng `<input type="checkbox">`/`<input type="radio">` thô nếu project đã có `Checkbox`/`Switch`/`RadioGroup` — luôn ưu tiên component có sẵn, nó đã có đủ 8 state (default/hover/focus-visible/active/disabled/checked...).
- KHÔNG tự chế màu Tailwind mặc định (`amber-*`, `yellow-*`...) cho trạng thái cảnh báo — dùng ĐÚNG token semantic đã tìm ở Bước 0 (`warning-*`/`caution-*`/tên tương đương project đặt). Nếu project không có token semantic nào — dùng đúng 1 màu trung tính (ví dụ viền `border-2 border-dashed`) thay vì đoán màu.
- Mỗi dòng log console/network phải có phân cấp thị giác tối thiểu: timestamp mờ + badge level/status màu theo mức độ (dùng `Badge` nếu có) + nội dung — không phải 1 dòng text phẳng đồng màu.

### Wiring vào root layout — LUÔN làm, đây là bước hay bị quên

Next.js App Router: mở `app/layout.tsx`, import `DevToolkit`, mount **BÊN TRONG mọi Provider cần (Auth/QueryClient) nhưng bên NGOÀI đủ để render ở mọi trang** — thường đặt làm sibling cuối cùng của `{children}` trong provider trong cùng. Next.js Pages Router: mount trong `pages/_app.tsx` tương tự.

### Nếu project build qua Docker — kiểm tra Dockerfile, đây là bug thật đã gặp

Nếu project có `Dockerfile` build Next.js: kiểm `ARG`/`ENV` cho biến gate đã chọn ở Bước 1 CÓ được khai báo trong Dockerfile không. **Bug thật đã xảy ra ở lần build gốc**: `docker-compose.yml` truyền đúng `build.args`, nhưng Dockerfile thiếu khai `ARG <tên biến>` → Docker âm thầm bỏ qua, biến luôn rỗng dù `.env` đúng, toolkit không bao giờ vào bundle. Nếu thiếu — thêm cả `ARG <TÊN>=` (default rỗng, để PRD không set vẫn build được) và `ENV <TÊN>=$<TÊN>` ngay cạnh các `ARG`/`ENV` `NEXT_PUBLIC_*` khác đã có.

## Bước 3 — Verify (bắt buộc, không chỉ đọc code)

1. `tsc --noEmit` (hoặc lệnh typecheck thật của project) — phải sạch cho các file mới.
2. Build thật (`next build` hoặc lệnh build/dev thật của project) — xác nhận không lỗi runtime.
3. **Xác nhận bundle có nhận biến gate**: sau build, grep file JS đã build tìm 1 chuỗi đặc trưng từ giá trị biến gate (nếu build local có set giá trị thật) — nếu không tìm thấy, dừng lại, đây chính là bug Dockerfile ở trên, đừng báo "xong" khi chưa xác nhận.
4. Nếu có cách chạy trình duyệt thật (headless Chrome CLI + CDP, hoặc browser tool sẵn có) — mở trang, click burger thật, chụp ảnh xác nhận panel mở đúng. Đọc code kỹ không thay được 1 lần click thật — bug UI (ví dụ token màu sai, spacing vỡ) chỉ thấy được qua ảnh.

## Rules

- KHÔNG tự chế cơ chế dev-login bypass nếu project chưa có sẵn — đây là quyết định bảo mật, không phải quyết định UI, phải để user tự thêm ở backend trước.
- KHÔNG hardcode role list nếu Bước 1 không xác nhận — hỏi, không đoán từ code.
- Capture console/network LUÔN chạy (không cần bật gì) — chỉ "Break on error" là toggle riêng, mặc định OFF (bật mặc định sẽ dừng app liên tục, rất khó chịu).
- Mọi giá trị màu/spacing trong component mới PHẢI truy được về 1 token/class đã tồn tại trong project đích — không có giá trị "tự tay chọn cho đẹp".
- Touch only what the task requires — không sửa code khác ngoài phạm vi toolkit.

## Origin

Distill từ implementation thật đã build + verify bằng CDP thật (click burger, mở panel, đăng nhập, chụp ảnh) trong `payroll-frontend-develop` (Next.js 14 App Router) — bao gồm 1 bug thật đã gặp và sửa (Dockerfile thiếu `ARG` cho biến gate) và 1 lần audit `hallmark` bắt AI-slop (checkbox thô + màu tự chế) rồi sửa lại đúng component/token có sẵn. Raised làm skill qua `raise-issue` (`290726-generalize-dev-toolkit-skill`), giải quyết trong cùng phiên theo yêu cầu user.
