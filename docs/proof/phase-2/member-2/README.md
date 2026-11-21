# Bàn giao TV2 — Gather v1.1

Ngày: 2026-11-21. Nguồn: `C:/Users/Admin/Downloads/02_TV2_Ducbaynao`, ba manifest; dùng bản cuối `commit_3/files/chonoi/sim/gather.py`. Đã tích hợp trực tiếp vào repo, chưa commit/push. Không chạy script tạo commit của gói. Code và kiểm thử không đọc hay import từ folder Downloads hoặc `day12-goi-6-tv`.

## Phần được tích hợp

- `game.contract.json` lên v1.1 theo gói TV2: sáu nguyên liệu, sáu món, hai bếp/bốn bàn, dữ liệu `day_plan` và `shop`. Kho vẫn là map số lượng; không đổi sang schema cá thể Phase 3.
- `contract.py`, `inventory.py`: kiểm tuning mới và nhận `ca_keo`, `keo_neo`.
- `scenario.py`: chỉ ghép validator Gather, bổ sung quái và tuổi cá; giữ validator Quán hiện tại. Gói có validator Quán dựa trên payload món/khách từ bản nền khác, nên không chép toàn file.
- `GatherSim`: tám đàn cá theo seed, vị trí ban đầu không trùng; bơi/đổi hướng/phản xạ/sinh theo tuning; `random_fish: false` đóng băng cá và tắt sinh; M1 từ ngày 1, M2 từ ngày 3; tuần tra/đuổi/hit/rơi LIFO/bất tử/recoil/ngất. Nhận tham số ngày và nâng cấp để TV1 nối sau.
- `web/index.html`: vẽ quái theo trạng thái và cảnh báo, đọc bán kính từ tuning qua `meta`; giữ phần render Quán hiện tại.

## Hiệu chỉnh so với gói

- Validator mới từ chối tọa độ sinh cá ngoài vùng, cấu trúc độ sâu sai, số không hữu hạn, spawn quái sai kiểu và độ sâu quái/waypoint ngoài vùng loài. `scenario.monsters[].target_idx` bắt buộc là số nguyên.
- Không chép `test_quan_customers.py` trong gói: file đó kiểm payload Quán chưa có trong repo. Giữ kỳ vọng kiểm thử cũ và khóa fixture một bàn; test thanh toán tắt khách tự sinh để tập trung vào khách đang được phục vụ. Lần chạy đầu ghi nhận hai lỗi fixture do số bàn mặc định mới, xem [initial-tests.txt](initial-tests.txt).
- Nhập sửa fixture `random_fish: false` của test bắt cá để tránh chuyển động thay đổi tình huống kiểm hòa ID/cooldown. Test smoke đọc số đàn từ tuning v1.1.
- Bổ sung test từ chối tuning/scenario sai và test CLI ngất do quái: thứ tự event, rơi LIFO, kho rỗng và JSONL giống từng byte khi chạy lặp. Các kiểm thử Gather Core Phase 1 giữ nguyên kỳ vọng và đều qua.
- Giữ kế hoạch của TV4 trong `docs/plan/phase-2.md`, bổ sung phần TV2 thay vì ghi đè. Không nhập các tuyên bố 78/84 test hay thành quả review từ nguồn nếu chưa kiểm chứng tại đây.

## Kết quả thực chạy

Chạy từ gốc repo: `python docs/proof/phase-2/member-2/verify.py`.

- **78/78 test qua**, gồm năm test từ gói và ba test bổ sung.
- Headless Gather/Quán: seed 1, 600 ticks mỗi mode, exit 0.
- Hai phiên Gather 600 ticks giống từng byte.
- JavaScript trong HTML qua `node --check`; chưa kiểm trực quan trên trình duyệt.
- `tools/check_team.py`: exit 1 vì TV6 trong TEAM còn placeholder; không sửa danh tính thay thành viên đó.

[checks.txt](checks.txt), [summary.json](summary.json), [gather.jsonl](gather.jsonl), [quan.jsonl](quan.jsonl) là bằng chứng lần tích hợp này. Script dùng launcher Python tạm trên Windows để chạy đúng `python3` trong contract, không cài hay đổi alias hệ thống.

## Giới hạn và bàn giao

Chưa có PRD/TICKET-02 gốc trong hai gói; việc đối chiếu v1.1 dựa trên code, tuning, kế hoạch và test của gói TV2. Không khẳng định đã kiểm toàn bộ yêu cầu gốc hoặc DoD nhóm. Vòng lặp D1–D5, shop, pause và CLI `--mode day` thuộc lượt TV1, chưa nằm trong repo. Hiện CLI Gather chạy ngày 1; M2/ngày 3 và nâng cấp được gọi qua API `GatherSim`. Contract chung và các file starter được sửa vì đây là phụ thuộc của Gather v1.1; Integrator cần review các phần này trước khi merge/tag.

Báo cáo [package-review](package-review/README.md) là lần kiểm tra trước với gói TV6 thiếu code TV2, được giữ làm lịch sử. Có thể xóa các folder gói sau khi giữ bản sao cần thiết cho những lượt thành viên khác; phần TV2 đã tích hợp không phụ thuộc chúng.
