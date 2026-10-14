# BÁO CÁO NHẬT KÝ THAY ĐỔI & HỢP NHẤT DỰ ÁN (README_NHOM2.md)

> **Học phần:** Biểu diễn tri thức và tìm kiếm nâng cao (UET.AI2014)  
> **Dự án 1:** Pacman — Tìm kiếm trong không gian trạng thái và Trò chơi đối kháng  
> **Nhóm thực hiện:** Nhóm 13  
> **Thời gian thực hiện:** Phiên làm việc ngày 14/10/2026  
> **Tài liệu tham chiếu:** [Đề bài Dự án 1 Notion](https://truth-element-426.notion.site/D-n-1-Pacman-T-m-ki-m-v-tr-ch-i-i-kh-ng-3db0e26dc18c818a9f90f6e46b9fd3b1)

---

## MỤC LỤC
1. [Tổng quan phiên làm việc](#1-tổng-quan-phiên-làm-việc)
2. [So sánh toàn diện giữa hai thư mục](#2-so-sánh-toàn-diện-giữa-hai-thư-mục)
3. [Chiến lược và quá trình hợp nhất (Merge)](#3-chiến-lược-và-quá-trình-hợp-nhất-merge)
4. [Thiết kế bản đồ phân biệt Greedy Best-First Search và A* Search](#4-thiết-kế-bản-đồ-phân-biệt-greedy-best-first-search-và-a-search)
5. [Khắc phục triệt để lỗi UI hiển thị "Chiến thắng" trên bản đồ vô nghiệm](#5-khắc-phục-triệt-để-lỗi-ui-hiển-thị-chiến-thắng-trên-bản-đồ-vô-nghiệm)
6. [Mở rộng bộ kiểm thử tự động (14 Unit Tests)](#6-mở-rộng-bộ-kiểm-thử-tự-động-14-unit-tests)
7. [Hướng dẫn chạy và kiểm chứng các tính năng mới](#7-hướng-dẫn-chạy-và-kiểm-chứng-các-tính-năng-mới)

---

## 1. TỔNG QUAN PHIÊN LÀM VIỆC

Trong phiên làm việc này, nhóm đã giải quyết 4 nhiệm vụ kỹ thuật trọng tâm:
1. **So sánh chi tiết 2 thư mục dự án**: Thư mục hiện tại `D:\BDTTTKNC_P1_Nhom13` (nhánh chính, đã hoàn thiện AI Core) và thư mục `D:\BDTTTKNC_P1_Nhom13-emphucdepzai\BDTTTKNC_P1_Nhom13-emphucdepzai` (nhánh đồ họa của thành viên Phúc).
2. **Hợp nhất mã nguồn tối ưu (Smart Merge)**: Đưa giao diện Desktop GUI tương tác cao cấp (1800+ dòng) của Phúc vào dự án chính, đồng thời giữ vững 100% logic thuật toán, engine, bộ unit tests và cải tiến `main.py` thành bộ khởi động đa năng (Hybrid Launcher).
3. **Thiết kế bản đồ độc quyền so sánh thuật toán**: Tạo bản đồ `maps/map_greedy_vs_astar.txt` chỉ ra sự khác biệt trực quan và định lượng giữa Greedy Best-First Search ($f=h$) và A* Search ($f=g+h$).
4. **Sửa lỗi logic UI**: Khắc phục hiện tượng hiển thị overlay "Chiến thắng" khi chạy trên các bản đồ không có lời giải (`map_khong_loi_giai_*.txt`).

---

## 2. SO SÁNH TOÀN DIỆN GIỮA HAI THƯ MỤC

### 2.1. Bối cảnh hai nhánh mã nguồn
* **Nhánh Hiện tại (`D:\BDTTTKNC_P1_Nhom13`)**:
  * Phát triển dựa trên commit `cb34b2f` ("Hoàn thiện nhiều thứ").
  * **Trọng tâm:** Hoàn thiện toàn bộ logic backend: Thuật toán đối kháng Minimax & Alpha-Beta (`src/search/adversarial.py`), hàm đánh giá khoảng cách mê cung BFS (`MazeDistance`), thuật toán Greedy Best-First, bộ 12 Unit Tests tự động, CLI nâng cao có phím Restart `r`, sửa bug tỉa cành `beta <= alpha`.
* **Nhánh Em Phúc (`...-emphucdepzai`)**:
  * Phát triển tách ra từ commit đầu tiên `65904ab` (chưa có các cải tiến AI của commit `cb34b2f`).
  * **Trọng tâm:** Tập trung toàn lực vào **giao diện đồ họa Pygame tương tác (Interactive Desktop GUI)** với 1827 dòng code trong `ui/g_ui.py`, tích hợp Dropdown Menu chọn map/thuật toán/heuristic, nút bấm Play/Pause/Step/Reset, thanh trượt tốc độ (Speed Slider), hoạt ảnh duyệt node (search tree animation).

### 2.2. Bảng phân loại chi tiết 34 files

| STT | Tên file | Trạng thái so sánh | Đánh giá & Quyết định |
|---|---|---|---|
| 1 | `src/search/adversarial.py` | **Chỉ có ở Hiện tại** | **GIỮ CHÍNH**: File cốt lõi đối kháng Minimax/Alpha-Beta, Phúc chưa có. |
| 2 | `tests/test_pacman.py` | **Chỉ có ở Hiện tại** | **GIỮ CHÍNH**: Bộ unit tests tự động của dự án. |
| 3 | `tests/__init__.py` | **Chỉ có ở Hiện tại** | **GIỮ CHÍNH**: Module package test. |
| 4 | `README_NHOM.md` | **Chỉ có ở Hiện tại** | **GIỮ CHÍNH**: Bản báo cáo kỹ thuật giai đoạn 1. |
| 5 | `.vscode/launch.json` | **Chỉ có ở Em Phúc** | **LOẠI BỎ**: File cấu hình C/C++ thừa từ dự án khác (`d:/level-1/level-1`). |
| 6 | `.vscode/c_cpp_properties.json` | **Chỉ có ở Em Phúc** | **LOẠI BỎ**: File cấu hình GCC C/C++ thừa. |
| 7 | `ui/g_ui.py` | Khác biệt lớn | **LẤY CỦA PHÚC & NÂNG CẤP**: GUI 1827 dòng của Phúc vượt trội bản cũ (303 dòng). |
| 8 | `src/agents.py` | Khác biệt | **GIỮ CỦA HIỆN TẠI**: Đã sửa bug tỉa cành Alpha-Beta, thêm `reset()`, hỗ trợ `greedy`. |
| 9 | `src/engine.py` | Khác biệt | **GIỮ CỦA HIỆN TẠI**: Engine đã có cơ chế `reset()` và cờ `is_pacman_move`. |
| 10 | `src/search/algorithms.py` | Khác biệt | **GIỮ CỦA HIỆN TẠI**: Đã cài đặt `greedy` và chuẩn hóa API tìm kiếm. |
| 11 | `ui/cli_ui.py` | Khác biệt | **GIỮ CỦA HIỆN TẠI**: Bản CLI có màu sắc ANSI, hỗ trợ phím restart `r`. |
| 12 | `ui/base_ui.py` | Khác biệt | **GIỮ CỦA HIỆN TẠI**: Kế thừa phương thức `render` có `is_pacman_move`. |
| 13 | `requirements.txt` | Khác biệt | **GIỮ CỦA HIỆN TẠI**: Đã tích hợp thư viện `pygame-ce>=2.5.0` tương thích Python 3.14. |
| 14 | `README.md` | Khác biệt | **GIỮ CỦA HIỆN TẠI**: Bản hướng dẫn chi tiết đầy đủ cờ CLI. |
| 15 | `main.py` | Khác biệt | **HỢP NHẤT LAI GHÉP**: Chạy không tham số mở thẳng GUI, có tham số chạy CLI. |
| 16-25 | `maps/*.txt` (10 files) | Giống nhau 100% | Nội dung đồng nhất giữa 2 bên. |
| 26-30 | `asset/**` (5 files) | Giống nhau 100% | Toàn bộ font và ảnh sprite nhân vật đồng nhất. |
| 31-32 | `src/search/heuristics.py`, `problems.py` | Giống nhau 100% | Nội dung logic đồng nhất (chỉ khác định dạng xuống dòng). |
| 33-34 | `.gitignore`, `.vscode/settings.json` | Giống nhau 100% | Cấu hình workspace giống nhau. |

---

## 3. CHIẾN LƯỢC VÀ QUÁ TRÌNH HỢP NHẤT (MERGE)

Nhóm đã thực hiện tích hợp mã nguồn theo mô hình: **"Lõi AI của Tiến + Giao diện đồ họa của Phúc"**.

### 3.1. Tích hợp và nâng cấp Giao diện Đồ họa (`ui/g_ui.py`)
1. **Thay thế file**: Đưa toàn bộ module giao diện đồ họa Pygame từ nhánh của Phúc sang nhánh chính.
2. **Bổ sung thuật toán Greedy**:
   - Thêm `"Greedy"` vào danh sách `ALGO_SEARCH` và `ALGO_NEEDS_HEURISTIC`.
   - Cập nhật hàm ánh xạ `_algo_name_to_search_key()` để chuyển đổi tên hiển thị `"Greedy"` $\to$ `"greedy"` trong backend.
3. **Hoàn thiện class `GUI_UI` làm cầu nối cho `GameLoop`**:
   - Bổ sung tham số `is_pacman_move=False` trong hàm `render(self, game_state, is_pacman_move=False)` để tương thích 100% với `engine.py`.
4. **Hỗ trợ tham số khởi tạo dòng lệnh trong `run_gui_app()`**:
   - Khai báo hàm `run_gui_app(initial_map=None, initial_algo=None, initial_heuristic=None)`.
   - Nếu người dùng truyền map/thuật toán từ CLI (ví dụ: `-map maps/map_ghost.txt -algo minimax`), ứng dụng tự động chọn đúng giá trị trong Dropdown Menu ngay khi mở cửa sổ.

### 3.2. Cải tiến `main.py` thành Bộ khởi động đa năng (Hybrid Launcher)
Trước khi hợp nhất:
- Nhánh Hiện tại: Bắt buộc phải nhập `-mode` và `-map`, nếu gõ `python main.py` sẽ báo lỗi thiếu tham số.
- Nhánh Phúc: Mặc định mở GUI nhưng thiếu nhiều cờ dòng lệnh quan trọng (`-step`, `-delay`, `-nocolor`, `-seed`, `-max_turns`, `-depth`).

Sau khi hợp nhất:
```python
def main():
    # Tự động chọn GUI nếu người dùng chạy nhanh không truyền tham số
    default_ui = "gui" if len(sys.argv) == 1 else "cli"
    ...
```
* **Khi chạy `python main.py`**: Tự động bật cửa sổ Pygame tương tác chuột, người dùng chỉ cần chọn map và thuật toán trên dropdown rồi ấn **Bắt đầu**.
* **Khi truyền cờ CLI**: Chương trình phân tích đầy đủ các tham số và chạy mượt mà trên Terminal CLI hoặc giao diện đồ họa chỉ định.

---

## 4. THIẾT KẾ BẢN ĐỒ PHÂN BIỆT GREEDY BEST-FIRST SEARCH VÀ A* SEARCH

### 4.1. Bản đồ `maps/map_greedy_vs_astar.txt`
```text
#######################
#.   #  . . . . . .  .#
#  # #  # ######### # #
#. # P  #           # #
#######################
```
* **Kích thước:** $23 \times 5$ ô.
* **Vị trí Pacman:** `P` tại tọa độ `(5, 3)`.
* **Vị trí thức ăn (9 hạt):**
  * 2 hạt bên trái: Nằm sâu trong ngõ cụt tại `(1, 1)` và `(1, 3)`.
  * 7 hạt bên phải: Nối tiếp nhau dọc theo hành lang trên hàng 1 từ `(8, 1)` đến `(21, 1)`.

### 4.2. Cơ chế lý thuyết & So sánh toán học

$$\text{Greedy: } f(n) = h(n) \quad \text{vs} \quad \text{A}^*: f(n) = g(n) + h(n)$$

1. **Tại bước xuất phát từ `P (5, 3)`**:
   * **Greedy Best-First Search:**
     - Greedy chỉ quan tâm đến việc giảm khoảng cách heuristic $h(n)$ tới thức ăn gần nhất.
     - Phía bên phải có một dải 7 hạt thức ăn liên tục, tạo ra gradient heuristic giảm liên tục khi tiến về bên phải.
     - Greedy bị "hấp dẫn" bởi cụm thức ăn này nên lập tức rẽ **`PHẢI`**.
     - Khi ăn xong hạt cuối cùng ở tận cùng bên phải `(21, 1)`, trên bản đồ chỉ còn lại 2 hạt ở góc trái. Lúc này, Pacman **buộc phải quay đầu và đi lùi lại hơn 20 ô trống** để về góc trái.
     - **Tổng quãng đường của Greedy: 44 bước.**
   * **A\* Search (MST Heuristic):**
     - A* đánh giá tổng chi phí $f(n) = g(n) + h(n)$ (chi phí thực tế đã đi cộng với chi phí ước lượng còn lại).
     - Thuật toán nhận ra: Nếu đi sang phải trước, chi phí quay ngược trở lại góc trái là quá đắt đỏ ($g$ tăng cao).
     - Do đó, A* quyết định rẽ **`TRÁI`** ngay từ bước đầu tiên: dọn dẹp sạch sẽ 2 hạt mồi nhử trong ngõ cụt bên trái, sau đó quay ra và lướt thẳng một mạch từ trái sang phải ăn sạch 7 hạt còn lại mà **không phải quay đầu bất kỳ một bước nào**.
     - **Tổng quãng đường của A\*: 34 bước (Tối ưu tuyệt đối).**

### 4.3. Bảng so sánh chỉ số thực nghiệm

| Chỉ số đánh giá | A\* Search (MST) | Greedy Best-First (MST) | Chênh lệch (Suboptimality) |
|---|:---:|:---:|:---:|
| **Hành động bước đầu** | **`LEFT`** | **`RIGHT`** | **Ngược hướng hoàn toàn** |
| **Tổng chi phí (Path Cost)** | **34 bước** | **44 bước** | **Greedy dài hơn 10 bước (+29.4%)** |
| **Số node mở rộng (Expanded)** | 42 | 53 | Greedy phải duyệt nhiều hơn do đi lùi |
| **Tính tối ưu** | **Tối ưu tuyệt đối** | **Dưới tối ưu (Suboptimal)** | Minh chứng rõ ràng lý thuyết AI |

---

## 5. KHẮC PHỤC TRIỆT ĐỂ LỖI UI HIỂN THỊ "CHIẾN THẮNG" TRÊN BẢN ĐỒ VÔ NGHIỆM

### 5.1. Mô tả lỗi ban đầu
Khi chọn các bản đồ không có đường đi tới thức ăn (như `maps/map_khong_loi_giai_pacman.txt` hoặc `maps/map_khong_loi_giai_target.txt`) trên giao diện Pygame:
* Thuật toán không tìm được đường, nhưng Pacman đứng im 0 bước và màn hình lập tức hiện bảng màu xanh: **"🏆 CHIẾN THẮNG! Pacman đã hoàn thành nhiệm vụ!"**.
* Đây là lỗi logic hiển thị rất nghiêm trọng, gây hiểu sai kết quả thuật toán.

### 5.2. Phân tích nguyên nhân gốc rễ (Root Cause)
1. **Lỗi trong hàm `solve_offline()` (`ui/g_ui.py`)**:
   - Khi không tìm thấy đường, `agent.plan` là rỗng (`deque([])`) và `metrics["found"] == False`.
   - Tuy nhiên, đoạn code cũ:
     ```python
     path_rc = []
     if agent.plan is not None:  # deque([]) không phải là None!
         path_rc.append(ui.start_pos) # Tự chèn 1 tọa độ xuất phát vào path
     ```
     khiến `path_rc` có độ dài bằng 1 thay vì rỗng.
2. **Lỗi điều kiện kiểm tra (Logical Bug)**:
   - Tại sự kiện bấm nút Start/Step:
     ```python
     if not m.get("found", False) and not demo_path: # SAI LOGIC
     ```
     Vì `demo_path` có 1 phần tử nên `not demo_path` bằng `False`, làm toàn bộ khối xử lý vô nghiệm bị bỏ qua!
3. **Lỗi mặc định trong pha `MOVING`**:
   - Hàm `advance_move_step()` kết thúc ngay lập tức vì danh sách đường đi hết điểm đến.
   - Khi `still_moving == False`, code cũ mặc định gán:
     ```python
     ui.game_result = "WIN"  # Gán thẳng là thắng mà không kiểm tra thức ăn!
     ```

### 5.3. Các chỉnh sửa kỹ thuật đã áp dụng
1. **Sửa `solve_offline`**:
   ```python
   path_rc = []
   if agent.plan and metrics.get("found", False):  # Chỉ tạo đường khi thực sự tìm thấy
       curr_r, curr_c = ui.start_pos
       path_rc.append((curr_r, curr_c))
       ...
   ```
2. **Sửa điều kiện kiểm tra thành toán tử `or`**:
   ```python
   if not m.get("found", False) or not demo_path:
       ui.phase = "GAME_OVER"
       ui.game_result = "NO_PATH"
       ui.is_running = False
       ui.metrics["status"] = "❌ Bản đồ không có lời giải!"
       continue
   ```
3. **Kiểm tra lượng thức ăn thực tế trước khi kết luận**:
   ```python
   remaining_food = len(ui.food_set) - len(ui.eaten_food)
   if remaining_food == 0 and len(ui.food_set) > 0:
       ui.game_result = "WIN"
       ui.metrics["status"] = "🏆 Hoàn thành! Pacman ăn hết thức ăn!"
   else:
       ui.game_result = "NO_PATH"
       ui.metrics["status"] = "❌ Bản đồ không có lời giải!"
   ```
4. **Cập nhật hiển thị Overlay và Màu sắc**:
   - Khi `game_result == "NO_PATH"`: Vẽ chữ màu đỏ **`❌ KHÔNG CÓ LỜI GIẢI!`**.
   - Cập nhật hàm `GUI_UI.render` để đồng bộ đúng trạng thái `end_reason == "no_solution"` từ engine sang UI.

---

## 6. MỞ RỘNG BỘ KIỂM THỬ TỰ ĐỘNG (14 UNIT TESTS)

Trong file [`tests/test_pacman.py`](file:///D:/BDTTTKNC_P1_Nhom13/tests/test_pacman.py), nhóm đã bổ sung 2 bài test tự động chuyên biệt để đảm bảo không bị lỗi hồi quy (regression):

1. **`test_13_greedy_vs_astar_suboptimality`**:
   - Tải bản đồ `maps/map_greedy_vs_astar.txt`.
   - Chạy cả A* và Greedy với MST Heuristic.
   - Khẳng định `cost(A*) == 34` và `cost(Greedy) == 44`.
   - Khẳng định chắc chắn `cost(A*) < cost(Greedy)`.
2. **`test_14_unsolvable_map_does_not_win`**:
   - Tải bản đồ `maps/map_khong_loi_giai_pacman.txt`.
   - Cho Pacman lấy hành động đầu tiên.
   - Khẳng định Pacman trả về hành động `"STOP"` và lý do bế tắc `"no_solution"`.
   - Khẳng định trạng thái game kết thúc với `is_game_over == True`, `end_reason == "no_solution"` và `is_win() == False`.

### Kết quả chạy kiểm thử:
```bash
python -m unittest discover tests
```
```text
..............
----------------------------------------------------------------------
Ran 14 tests in 0.026s

OK
```
**Toàn bộ 14/14 bài kiểm thử đều PASS 100%.**

---

## 7. HƯỚNG DẪN CHẠY VÀ KIỂM CHỨNG CÁC TÍNH NĂNG MỚI

### 7.1. Khởi động giao diện đồ họa Desktop GUI (Pygame)
```bash
# Mở thẳng giao diện đồ họa tương tác (tự động chọn map, thuật toán qua dropdown)
python main.py
```

### 7.2. So sánh trực quan Greedy vs A* trên bản đồ mới
```bash
# 1. Chạy A* (Đi tối ưu 34 bước - Rẽ TRÁI trước)
python main.py -mode search -map maps/map_greedy_vs_astar.txt -algo astar -ui cli

# 2. Chạy Greedy (Đi dưới tối ưu 44 bước - Rẽ PHẢI trước rồi lùi lại)
python main.py -mode search -map maps/map_greedy_vs_astar.txt -algo greedy -ui cli

# 3. Mở trên Desktop GUI để xem trực quan hoạt ảnh
python main.py -mode search -map maps/map_greedy_vs_astar.txt -algo astar -ui gui
```

### 7.3. Kiểm chứng bản đồ không có lời giải
```bash
# Chạy bản đồ Pacman bị nhốt
python main.py -mode search -map maps/map_khong_loi_giai_pacman.txt -algo astar -ui cli

# Mở trên GUI để kiểm tra thông báo màu đỏ "❌ KHÔNG CÓ LỜI GIẢI!"
python main.py -mode search -map maps/map_khong_loi_giai_pacman.txt -ui gui
```

### 7.4. Chạy toàn bộ bộ kiểm thử tự động
```bash
python -m unittest discover tests
```

---
*Tài liệu được tổng hợp tự động và lưu trữ vào file `README_NHOM2.md` thuộc thư mục gốc dự án.*
