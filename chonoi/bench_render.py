"""Phần VẼ của benchmark (Ticket-04 mục 1). KHUNG rỗng — E viết. Khung đo ở `chonoi/bench.py`.

Giao diện bench.py cần:

    r = Renderer()
    r.open(1280, 720)            # mở cửa sổ 1280×720; không mở được thì ném lỗi (bench thoát mã 1)
    r.draw(snapshot) -> bool     # vẽ MỘT khung từ snapshot gather (cùng trường với JSONL / GET /state);
                                 # trả False nếu người dùng đóng cửa sổ, True nếu vẽ xong
    r.close()

Gợi ý (E quyết, ghi docs/clarify.md): Tkinter (thư viện chuẩn) vẽ cảnh lặn bằng hình khối trên Canvas: nước, mặt
nước, bến, nút hái, đàn cá (`snapshot["fish"]`), quái (`snapshot["monsters"]`), Út Sen (`snapshot["player"]`), HUD oxy,
Máu, giỏ kèm độ tươi. Mỗi khung xóa và vẽ lại rồi gọi `root.update()` (không dùng mainloop) để bench tự đo thời gian.
Linux không có màn hình: chạy qua `xvfb-run python3 -m chonoi.bench ...` (ghi trong README).
"""


class Renderer:
    def open(self, width, height):
        raise NotImplementedError("TODO(E): mở cửa sổ render cho benchmark (chonoi/bench_render.py)")

    def draw(self, snapshot) -> bool:
        raise NotImplementedError("TODO(E): vẽ một khung cảnh lặn từ snapshot")

    def close(self):
        pass
