---
type: issue
kind: architecture
title: "Orca-independence — tự-build orchestration optional làm Plan B"
status: open
assignee: phiên /fdk kế (framework-dev)
dispatch: Claude
entry: /fdk
priority: P3
tags: [issue, orchestration, orca, optionality, plan-b, adapter]
timestamp: 2026-07-03
id: 030726-orca-independence-planb
source_session: "Phiên 2026-07-03 — nhận xét: orca chỉ cung cấp orchestration mà ta tự làm được"
---

# Issue: Orca-independence — orchestration tự-chủ làm Plan B

## Vấn đề (một câu)
Overstack đang phụ thuộc **orca** cho tầng orchestration (dispatch worker, ask/reply, wait worker_done, task DAG) — nhưng phần lớn cơ chế này ta *tự làm được*; nếu một môi trường có ràng buộc kỹ thuật **cấm dùng orca**, hiện chưa có fallback, cả loop dừng.

## Bối cảnh & bằng chứng
- Nhận xét user (phiên 2026-07-03): "orca lý thuyết chỉ cung cấp orchestration mà chúng ta thực ra cũng tự làm được". Đúng: council-026 vừa chạy protocol 3-stage **không cần orca** — `harness/scripts/council.py` làm phần tất định, còn generation có thể do bất kỳ CLI (opencode/claude) đảm nhận.
- Tiền lệ kiến trúc trong repo: **build-now-adapt-later** + adapter boundary — orca đã là một "unknown/vendor" quarantine được. `harness/council.config.yaml` (`verified:false`) là ví dụ tách vendor khỏi engine.
- Skill `orchestration` + `orca-cli` hiện là đường chính; đây KHÔNG đề xuất bỏ orca — orca vẫn là default khi có. Chỉ cần **optionality**: một backend orchestration nội bộ thay thế được.
- Liên quan: `ADR-005` (thứ cần travel đi theo harness), poc-vendor-neutral (`harness/poc-vendor-neutral/`) — tinh thần vendor-neutral đã có sẵn.

## Phạm vi
- Định nghĩa một **interface orchestration tối thiểu** mà cả orca-backend lẫn self-backend cùng thoả: `task-create`, `dispatch(task,to)`, `check --wait --types`, `worker_done`. 
- Self-backend Plan B: điều phối qua tmux/PTY hoặc process pool + file-based mailbox (dispatch-verify.py đã có mầm mống), không cần orca daemon.
- Adapter chọn backend bằng cấu hình (`orchestration.backend: orca | self`), engine không branch theo vendor.

## Không thuộc phạm vi
- KHÔNG bỏ hay thay orca ở đường mặc định — orca vẫn ưu tiên khi khả dụng.
- KHÔNG làm full-feature parity ngay (task DAG phức tạp) — Plan B chỉ cần đủ chạy council + dispatch tuần tự/song song cơ bản.
- KHÔNG tối ưu hiệu năng ở vòng đầu.

## Hướng gợi ý (không bắt buộc)
- Trích interface từ chỗ `orca-workflow`/`orchestration` đang gọi orca → một `orchestration_backend.py` với 2 impl.
- Self-backend: dùng `orca-cli`-shape API nhưng nền tmux/subprocess; mailbox JSON trong scratchpad; poll worker_done bằng sentinel file.
- Conformance test: cùng một "council wave" chạy được trên cả 2 backend, transcript byte-identical (engine đã tất định).

## Tiêu chí HOÀN THÀNH
1. Có `orchestration.backend` config; đặt `self` → một wave dispatch 2-worker chạy trọn không cần orca daemon.
2. Council-026 tái chạy được trên self-backend, ra transcript tương đương.
3. Adapter boundary tài liệu hoá (build-now-adapt-later): orca vẫn default, self là fallback verified.
4. Không regression: đường orca hiện tại không đổi hành vi.

## Assign & lý do
- **assignee**: phiên `/fdk` kế — framework-dev đụng tầng orchestration lõi + adapter.
- **dispatch Claude**: thiết kế interface + boundary cần hiểu cả hệ; phần mechanical (tmux/mailbox) có thể sub cho opencode sau.
- **entry /fdk**: framework-dev, mở bằng front-door.
- **priority P3**: optionality/hedge — chưa cháy, chỉ kích hoạt khi có ràng buộc cấm orca. Đúng tinh thần Taleb ở council-026: mua quyền-chọn rẻ cho kịch bản đuôi.

## Origin
Raise bởi skill `/raise-issue` phiên 2026-07-03, từ nhận xét user về sự phụ thuộc orca. Bằng chứng self-orchestration khả thi: council-026 chạy protocol không cần orca (`harness/scripts/council.py`, `harness/council.config.yaml`). Chưa thực hiện — defer cho phiên /fdk kế.
