# BÁO CÁO CẬP NHẬT DỰ ÁN – NHÓM 13 (PHIÊN BẢN V3.0)
> **Tài liệu ghi nhận chi tiết các thay đổi nâng cấp từ việc chắt lọc tinh hoa giữa phiên bản chính và phiên bản rút gọn.**

---

## 1. Mục tiêu và Định hướng Cập nhật

Sau quá trình phân tích đối chiếu chuyên sâu giữa mã nguồn dự án chính (`BDTTTKNC_P1_Nhom13`) và phiên bản gửi bổ sung (`BDTTTKNC_P1_Nhom13-rutgongui`), nhóm nhận thấy:
- **Bản rút gọn có ưu điểm vượt trội** về mặt kiến trúc giao diện đồ họa: loại bỏ trùng lặp mã nguồn (DRY), tái cấu trúc các hàm xử lý bước duyệt, tối ưu hóa kích thước code và sở hữu bộ bản đồ thử nghiệm phong phú hơn.
- **Bản chính có ưu điểm vượt trội** về tính chuẩn mực giải thuật: hỗ trợ đầy đủ thuật toán `Greedy`, tách biệt module đối kháng `adversarial.py`, sở hữu 14 bài Unit Test tự động, cơ chế `reset()` ván chơi và khả năng nhận cờ tham số CLI khởi tạo thẳng vào GUI.

**Quyết định nâng cấp v3.0:** Tích hợp toàn bộ các điểm cải tiến kiến trúc và bộ bản đồ mới vào dự án chính, đồng thời bảo toàn 100% tính đúng đắn thuật toán và độ bao phủ kiểm thử.

---

## 2. Chi tiết các thay đổi theo từng file

### 2.1. File `ui/g_ui.py` (Tái cấu trúc GUI theo chuẩn DRY & Modular)

| Thành phần trước đây | Cải tiến sau khi cập nhật | Lợi ích mang lại |
| :--- | :--- | :--- |
| **Logic bước duyệt (Step)**: Bị viết lặp lại 2 lần (một lần trong xử lý nút `STEP`, một lần trong vòng lặp tự động). | Tách thành các hàm helper dùng chung:<br>• `advance_search_step()`<br>• `advance_moving_step()` | Loại bỏ hoàn toàn hơn 80 dòng code trùng lặp; bảo đảm tính nhất quán 100% giữa chế độ chạy tự động và bấm từng bước. |
| **Khởi tạo tìm kiếm**: Code phân nhánh giải thuật viết trực tiếp trong vòng lặp sự kiện. | Tách thành hàm `start_offline_search()` trả về boolean thành công/thất bại. | Giúp code bắt sự kiện `START` và `STEP` khi đang ở trạng thái `IDLE` trở nên ngắn gọn, dễ kiểm soát lỗi. |
| **Kiểm tra trạng thái đối kháng**: Logic thắng/thua/hết lượt được phân tán. | Tách thành `_check_game_over_turn()`. | Tự động đồng bộ sang UI và chuyển phase `GAME_OVER` chuẩn xác ngay khi có va chạm với Ghost. |
| **Dọn dẹp phiên**: Thủ công gán biến rải rác. | Đóng gói vào hàm `reset_session()`. | Đảm bảo giải phóng sạch sẽ hàng đợi, lộ trình khi người chơi ấn Reset hoặc đổi sang bản đồ khác. |
| **Hàm `set_metrics`**: Nhận danh sách tham số cố định `(expanded=None, cost=None,...)`. | Chuyển sang `set_metrics(**kwargs)`. | Linh hoạt truyền bất kỳ chỉ số thống kê nào mà không sợ lỗi chữ ký hàm. |
| **Bảo toàn tính năng nâng cao**: | • Giữ nguyên `run_gui_app(initial_map, initial_algo, initial_heuristic)` để CLI mở thẳng map/thuật toán tương ứng.<br>• Giữ trọn vẹn thuật toán **`Greedy`** trong Dropdown và logic tìm kiếm.<br>• Giữ lớp `GUI_UI(BaseUI)` để tương thích hoàn toàn với GameLoop. | Không làm gãy tính tương thích ngược với hệ thống dòng lệnh và Game Engine. |

---

### 2.2. Thư mục `maps/` (Thay thế toàn diện bằng bộ bản đồ mới)

Toàn bộ thư mục `maps/` đã được thay thế bằng bộ bản đồ mới, bổ sung các cấu trúc mê cung đa dạng:

1. **Bộ bản đồ mới bổ sung (7 maps):**
   - [`map1.txt`](file:///d:/BDTTTKNC_P1_Nhom13/maps/map1.txt): Mê cung 10x10 có nhiều lối rẽ và chướng ngại vật phức tạp.
   - [`map2.txt`](file:///d:/BDTTTKNC_P1_Nhom13/maps/map2.txt): Mê cung thử thách năng lực tìm kiếm của BFS, UCS và A*.
   - [`map3.txt`](file:///d:/BDTTTKNC_P1_Nhom13/maps/map3.txt): Mê cung kích thước trung bình với mật độ thức ăn dày đặc.
   - [`map4.txt`](file:///d:/BDTTTKNC_P1_Nhom13/maps/map4.txt): Bản đồ hành lang dài kiểm tra khả năng quay lui của DFS.
   - [`map_1ghost.txt`](file:///d:/BDTTTKNC_P1_Nhom13/maps/map_1ghost.txt): Đấu trường không gian rộng có 1 Ghost (Blinky) đuổi theo Pacman.
   - [`map_2ghost_1.txt`](file:///d:/BDTTTKNC_P1_Nhom13/maps/map_2ghost_1.txt): Bản đồ đối kháng kích thước 13x6 với 2 Ghost (Blinky, Inky).
   - [`map_2ghost_2.txt`](file:///d:/BDTTTKNC_P1_Nhom13/maps/map_2ghost_2.txt): Bản đồ đối kháng 2 Ghost với lối đi hành lang hẹp, thách thức thuật toán Alpha-Beta Pruning.

2. **Bộ bản đồ cơ bản được nâng cấp (5 maps):**
   - [`map_co_ban.txt`](file:///d:/BDTTTKNC_P1_Nhom13/maps/map_co_ban.txt): Nâng cấp từ 5x5 lên 9x9 với hệ thống thức ăn phân bố đối xứng và các khối tường ngăn cách rõ ràng.
   - [`map_dac_biet.txt`](file:///d:/BDTTTKNC_P1_Nhom13/maps/map_dac_biet.txt): Bản đồ 10x5 thử nghiệm tình huống Pacman và Ghost cùng xuất hiện trong không gian hẹp.
   - [`map_hep.txt`](file:///d:/BDTTTKNC_P1_Nhom13/maps/map_hep.txt): Bản đồ 11x6 dạng mê cung chữ S.
   - [`map_khong_loi_giai_pacman.txt`](file:///d:/BDTTTKNC_P1_Nhom13/maps/map_khong_loi_giai_pacman.txt): Bản đồ tường kín ngăn cách Pacman với thức ăn, phục vụ kiểm thử bài toán vô nghiệm.
   - [`map_khong_loi_giai_target.txt`](file:///d:/BDTTTKNC_P1_Nhom13/maps/map_khong_loi_giai_target.txt): Bản đồ tường kín bao quanh toàn bộ thức ăn.

3. **Bản đồ chuyên dụng được bảo tồn:**
   - [`map_greedy_vs_astar.txt`](file:///d:/BDTTTKNC_P1_Nhom13/maps/map_greedy_vs_astar.txt): Giữ lại bản đồ này để bảo đảm tính đúng đắn cho bài Unit Test so sánh độ lệch đường đi giữa Greedy Best-First Search và A*.

---

### 2.3. File `.vscode/launch.json` (Cấu hình Debug VS Code chuyên nghiệp)

Đã bổ sung cấu hình [`.vscode/launch.json`](file:///d:/BDTTTKNC_P1_Nhom13/.vscode/launch.json) chuẩn cho Python, hỗ trợ các thao tác chạy 1-click (F5):
1. **Python: Run GUI App (Interactive)**: Mở giao diện đồ họa Pygame đầy đủ tính năng.
2. **Python: Run CLI Search (A\* MST)**: Chạy bài toán tìm kiếm tối ưu trên Terminal.
3. **Python: Run CLI Adversarial (Alpha-Beta)**: Chạy đối kháng với Ghost trên Terminal.
4. **Python: Run Unit Tests**: Tự động phát hiện và chạy toàn bộ 14 test cases.

---

### 2.4. File `README.md`

- Cập nhật các dòng lệnh ví dụ trong mục **Cách chạy** để trỏ chính xác đến các file bản đồ mới (`map1.txt`, `map2.txt`, `map_1ghost.txt`).
- Giúp người dùng hoặc giảng viên chấm bài có thể copy-paste lệnh chạy trực tiếp mà không gặp lỗi `FileNotFoundError`.

---

## 3. Kết quả Kiểm thử & Đánh giá Chất lượng

Toàn bộ hệ thống đã được kiểm tra nghiêm ngặt sau khi cập nhật:

```bash
# 1. Chạy toàn bộ 14 bài kiểm thử tự động
python -m unittest discover tests
# Kết quả: Ran 14 tests in 0.025s -> OK (100% PASS)

# 2. Kiểm tra chế độ CLI tìm kiếm với map mới
python main.py -mode search -map maps/map_co_ban.txt -algo astar -heuristic mst -ui cli
# Kết quả: Hoàn thành 35 bước, thu thập toàn bộ thức ăn, đạt điểm 215 -> THÀNH CÔNG!

# 3. Kiểm tra nạp module GUI
python -c "import ui.g_ui; print('GUI loaded successfully!')"
# Kết quả: pygame-ce 2.5.8 khởi tạo hoàn tất, không có lỗi cú pháp -> THÀNH CÔNG!
```

---

## 4. Tổng kết

Bản cập nhật **v3.0** đã giải quyết triệt để sự phân mảnh giữa hai phiên bản:
- Đạt được độ tinh gọn, sạch sẽ, cấu trúc DRY chuẩn mực từ bản rút gọn.
- Giữ vững toàn bộ sức mạnh học thuật, sự đa dạng thuật toán (`Greedy`, `Minimax`, `Alpha-Beta`), tính chính xác của các điều kiện cắt tỉa, và hệ thống kiểm thử tự động của bản gốc.
