# Đối chiếu gói day12-goi-6-tv — TV2

> Cập nhật: đã tìm thấy gói `02_TV2_Ducbaynao` và tích hợp Gather v1.1. Xem [bàn giao mới](../README.md). Nội dung dưới đây là kết quả kiểm tra gói TV6 trước khi có gói TV2.

Ngày kiểm tra: 2026-11-21. Chỉ đối chiếu file cục bộ, chưa commit/push.

## Nguồn và phạm vi

`turn_meta.json` xác định gói là lượt **TV6 Laurent2526, Phase 4**. Ba manifest chỉ chứa thay đổi của lượt release, không phải toàn bộ code của sáu thành viên. Hướng dẫn yêu cầu có sẵn main sau PR #5 và tag phase-3; repo hiện tại chưa có các module Phase 2/3 đó. Không chạy `apply_turn.py` vì script chép toàn bộ file và tạo ba commit TV6.

TV2 là Phạm Lý Ngọc Đức (`Ducbaynao`), Dev Lead Gather theo `TEAM.md`.

| Phần liên quan TV2 trong gói | Đối chiếu code bên ngoài | Xử lý |
|---|---|---|
| `commit_1/files/chonoi/contract.py`: hằng nguyên liệu, `_validate_gather`, `_validate_monsters` | Validator hiện hành chỉ hỗ trợ Phase 1; validator mới đồng thời yêu cầu cấu hình ngày/shop và các thay đổi quán của thành viên khác | Chưa chép vào runtime vì thiếu triển khai phụ thuộc |
| `commit_1/files/game.contract.json`: `tuning.gather` | Thêm `keo_neo`, `ca_keo`, cá bơi/sinh và cá sấu; `fish_initial` đổi từ mảng 6 đàn thành số 8 | Trích nguyên khối Gather vào [gather-v11-reference.json](gather-v11-reference.json), chỉ làm dữ liệu tham chiếu; giữ contract khóa hiện hành |
| `commit_3/files/docs/members/Ducbaynao.md` | Tuyên bố đã hoàn thành Gather v1.1 và dẫn đến file test không tồn tại | Giữ phản tư hiện hành đã có bằng chứng Phase 1; chưa nhận tuyên bố hoàn thành Phase 2 |
| Dòng TV2 trong `ai-usage-log.md` và `standup.md` | Gộp thành quả TV1/TV2 và kết quả 84 test từ nguồn khác | Chưa nhập kết quả chưa tái chạy được |
| Bench, soak, leaderboard, HUD, proof release | Phần TV6, phụ thuộc DaySim và schema kho cá thể chưa có trong repo | Ngoài phạm vi TV2 |

## Vì sao chưa sửa runtime

`GatherSim.__init__` đang lặp qua `tuning.gather.fish_initial` như danh sách object. Giá trị số `8` từ gói sẽ gây lỗi khởi tạo. `scenario.py` và kho hiện hành cũng chưa hỗ trợ đầy đủ nguyên liệu mới, quái và schema Phase 3 mà headless/live của gói đòi hỏi. Chép riêng validator không triển khai hành vi cá bơi hoặc cá sấu và sẽ khiến contract Phase 1 bị từ chối.

Gói **không chứa** `chonoi/sim/gather.py`, `chonoi/scenario.py`, `tests/test_gather_v11.py`, PRD/TICKET-02. Vì vậy chưa có đủ nguồn để nhặt và hiệu chỉnh phần triển khai TV2 được nhắc trong phản tư. Cần gói TV2/Phase 2 cùng ticket gốc để xác nhận thứ tự event, luật RNG, va chạm và fixture, thay vì suy ra luật từ văn bản phản tư.

## Kiểm chứng code hiện hành

- Toàn bộ suite: **70/70 test qua**.
- Headless Gather và Quán: **600 ticks, seed 1, exit 0** cho mỗi mode.
- `tools/check_team.py`: **exit 1**, TV6 trong `TEAM.md` còn placeholder. Đây là vấn đề hồ sơ có sẵn.
- [checks.txt](checks.txt) lưu đầu ra thực chạy. Windows dùng bản sao Python tạm tên `python3.exe`, `PYTHONHOME` và UTF-8 để chạy đúng lệnh CLI trong contract; không sửa contract hay môi trường người dùng lâu dài.

Các file trong thư mục báo cáo này độc lập với folder gói. Có thể đọc báo cáo và dữ liệu Gather tham chiếu sau khi xóa gói; các phần TV6 chưa được lưu hay tích hợp lại ở đây. Chưa kết luận Gather v1.1 hoặc release v1.0.0 đã hoàn thành.
