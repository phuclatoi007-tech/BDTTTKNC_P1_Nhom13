# BÁO CÁO TỔNG HỢP TOÀN BỘ LỖI VÀ HẠNG MỤC CÒN THIẾU (README4.md)

> **Học phần:** Biểu diễn tri thức và tìm kiếm nâng cao (UET.AI2014)  
> **Dự án 1:** Pacman — Tìm kiếm trong không gian trạng thái và Trò chơi đối kháng  
> **Nhóm thực hiện:** Nhóm 13  
> **Tài liệu tham chiếu:** [Đề bài Dự án 1 Notion](https://truth-element-426.notion.site/D-n-1-Pacman-T-m-ki-m-v-tr-ch-i-i-kh-ng-3db0e26dc18c818a9f90f6e46b9fd3b1)  
> **Ngày rà soát:** 14/10/2026  

---

## MỤC LỤC
1. [Tổng quan hiện trạng mã nguồn so với đề bài Notion](#1-tổng-quan-hiện-trạng-mã-nguồn-so-với-đề-bài-notion)
2. [Chi tiết các lỗi logic và bug tiềm ẩn trong mã nguồn (Bugs & Code Issues)](#2-chi-tiết-các-lỗi-logic-và-bug-tiềm-ẩn-trong-mã-nguồn)
3. [Chi tiết các yêu cầu đề bài còn thiếu (Missing Requirements)](#3-chi-tiết-các-yêu-cầu-đề-bài-còn-thiếu)
4. [Các hạng mục hồ sơ nộp bài chưa hoàn thiện (Submission Checklist)](#4-các-hạng-mục-hồ-sơ-nộp-bài-chưa-hoàn-thiện)
5. [Kế hoạch hành động cụ thể để đạt điểm tối đa (10/10)](#5-kế-hoạch-hành-động-cụ-thể-để-đạt-điểm-tối-đa)

---

## 1. TỔNG QUAN HIỆN TRẠNG MÃ NGUỒN SO VỚI ĐỀ BÀI NOTION

Hệ thống mã nguồn của Nhóm 13 hiện tại đã hoàn thiện hầu hết các phần khung kiến trúc cốt lõi:
- Đã cài đặt đầy đủ **5 thuật toán tìm kiếm**: BFS, DFS, UCS, Greedy Best-First Search, A* Search (kết hợp MST Heuristic).
- Đã cài đặt đầy đủ **2 thuật toán trò chơi đối kháng**: Minimax và Alpha-Beta Pruning có giới hạn độ sâu `depth` và hàm lượng giá trạng thái mê cung BFS.
- Đã có **2 giao diện hoàn chỉnh**: Desktop GUI đồ họa tương tác cao cấp (Pygame) và CLI tương tác Terminal (ANSI color).
- Đã có **14 bài Unit Test tự động** (`tests/test_pacman.py`) vượt chỉ tiêu tối thiểu 10 test của đề bài (14/14 PASS).

Tuy nhiên, khi đối chiếu từng câu chữ của đề bài trên trang Notion chính thức, dự án vẫn còn tồn tại **một số lỗi logic trong code**, **thiếu các phần thực nghiệm bắt buộc** và **chưa chuẩn hóa cấu trúc hồ sơ nộp bài**.

---

## 2. CHI TIẾT CÁC LỖI LOGIC VÀ BUG TIỀM ẨN TRONG MÃ NGUỒN

### 🔴 Lỗi 1: Sai điều kiện thông báo "Bị ma bắt" trên Desktop GUI
* **Vị trí:** File [`ui/g_ui.py`](file:///d:/BDTTTKNC_P1_Nhom13/ui/g_ui.py), dòng 963–967 trong hàm `_check_game_over_turn()`:
  ```python
  ui.game_result = "WIN" if turn_game_state.end_reason == "win" else "LOSE"
  msg = ("🏆 Pacman chiến thắng!" if ui.game_result == "WIN"
         else "💀 Pacman bị ma bắt!" if turn_game_state.end_reason == "ghost"
         else "Hết lượt đi tối đa!")
  ```
* **Hiện tượng lỗi:** Khi chơi đối kháng trên GUI và Pacman bị Ghost bắt, màn hình thông báo: `"Hết lượt đi tối đa!"` thay vì `"💀 Pacman bị ma bắt!"`.
* **Nguyên nhân:** Trong [`src/engine.py`](file:///d:/BDTTTKNC_P1_Nhom13/src/engine.py#L112), khi Pacman va chạm với Ghost, biến trạng thái được gán là:
  ```python
  self.lose = True
  self.is_game_over = True
  self.end_reason = "lose"  # <-- Giá trị là "lose", KHÔNG PHẢI "ghost"!
  ```
  Do đó, điều kiện `turn_game_state.end_reason == "ghost"` luôn bị `False`, dẫn đến GUI luôn rơi vào nhánh `else` ("Hết lượt đi tối đa!").
* **Cách khắc phục:** Sửa điều kiện thành:
  ```python
  else "💀 Pacman bị ma bắt!" if turn_game_state.end_reason == "lose"
  ```

---

### 🟡 Lỗi 3: Chưa xuất "Đường đi / Danh sách hành động" trong Metrics tìm kiếm
* **Vị trí:** [`src/agents.py`](file:///d:/BDTTTKNC_P1_Nhom13/src/agents.py#L68-L81) và [`ui/cli_ui.py`](file:///d:/BDTTTKNC_P1_Nhom13/ui/cli_ui.py#L65-L73).
* **Vấn đề:**
  - **Mục 4 đề bài Notion** quy định rõ:
    > *"Với mỗi lần chạy tìm đường, chương trình cần hiển thị hoặc lưu: Thuật toán đã sử dụng, Trạng thái tìm thấy hoặc không tìm thấy lời giải, **Đường đi hoặc danh sách hành động**, Số bước, Tổng chi phí, Số trạng thái đã mở rộng, Thời gian chạy."*
  - Hiện tại, `SearchAgent.metrics` chỉ lưu: `path_cost`, `plan_length`, `expanded_nodes`, `search_time`... mà **không lưu trường `actions`** (danh sách các nước đi cụ thể như `['UP', 'LEFT', 'LEFT', 'DOWN', ...]`).
  - Kết thúc ván trên Terminal CLI, người chấm chỉ thấy số bước và chi phí chứ không nhìn thấy chuỗi hành động mà Pacman đã thực hiện.
* **Cách khắc phục:**
  1. Thêm `"actions": list(result.actions)` vào `self.metrics` trong `SearchAgent._plan_path()`.
  2. Trong `CLI_UI.show_metrics()`, in đường đi / danh sách hành động (nếu quá dài thì hiển thị tóm tắt chuỗi bước đi `UP -> RIGHT -> ...`).

---

### 🟡 Lỗi 4: Phân biệt hành vi của Ghost trên bản đồ trong chế độ Search
* **Hiện tượng:** Khi chạy chế độ tìm kiếm (`-mode search`) trên các map có chứa ký tự `G` (như `map_arena.txt` hay `map_dac_biet.txt` cũ), Pacman chỉ lập kế hoạch ăn thức ăn mà không coi Ghost là vật cản, dẫn đến việc đi xuyên vào Ghost và bị thua cuộc.
* **Yêu cầu đề bài (Mục 1 & 2):**
  - Chế độ tìm đường (Search): Pacman tìm đường tới mục tiêu hoặc thu thập nhiều thức ăn trong môi trường tĩnh.
  - Chế độ đối kháng (Adversarial): Pacman đối đầu khi Ghost di chuyển.
* **Khuyến nghị chuẩn hóa:**
  - Trong các bản đồ dành riêng cho Search (như `map1`, `map2`, `map3`, `map4`, `map_co_ban`), không nên bố trí Ghost `G` để tránh gây hiểu nhầm cho người chấm.
  - Đã có cảnh báo rõ ràng trong README và GUI: Map có Ghost chỉ chạy chế độ `adversarial`.

---

## 3. CHI TIẾT CÁC YÊU CẦU ĐỀ BÀI CÒN THIẾU (MISSING REQUIREMENTS)

### ❌ Phần thiếu 1: THƯ MỤC `results/` VÀ SCRIPT THỰC NGHIỆM TỰ ĐỘNG (RẤT QUAN TRỌNG)
* **Đề bài quy định (Mục 5 & Mục 6):**
  - Phải có thư mục: `results/ ← kết quả thực nghiệm` nằm ngay tại thư mục gốc.
  - Phải thực hiện đầy đủ 3 nội dung thực nghiệm bắt buộc:
    1. **Mục 5.1:** So sánh 5 thuật toán tìm đường (**DFS vs BFS vs UCS vs Greedy vs A\***) trên nhiều bản đồ (nhỏ/lớn, ít/nhiều vật cản, có/không lời giải, 1/nhiều mục tiêu) theo 5 tiêu chí: *Khả năng tìm thấy lời giải, Số bước, Tổng chi phí, Số trạng thái mở rộng, Thời gian chạy*.
    2. **Mục 5.2:** Đánh giá Heuristic: So sánh **UCS (A\* với h=0) vs A\* với MST vs A\* với Farthest Food (Maze)** để phân tích khi nào heuristic mang lại lợi ích rõ rệt và khi nào không.
    3. **Mục 5.3:** Đánh giá đối kháng: So sánh **Minimax vs Alpha-Beta** tại ít nhất 2 mức độ sâu (`depth=2` và `depth=3`) theo: *Hành động được chọn, Số trạng thái đã xét, Thời gian ra quyết định, Điểm số/kết quả*.
* **Hiện trạng dự án:**
  - Thư mục `results/` **chưa tồn tại**.
  - **Chưa có script tự động** (như `benchmark.py` hoặc `run_experiments.py`) để chạy tự động qua toàn bộ các kịch bản trên và xuất ra các bảng Markdown / CSV tổng hợp số liệu cho file báo cáo `report.pdf`.

---

### ❌ Phần thiếu 2: TẬP TIN PHÂN CÔNG CÔNG VIỆC `CONTRIBUTIONS.md`
* **Đề bài quy định (Mục 6):**
  - Bắt buộc phải có file `CONTRIBUTIONS.md` trong gói nộp bài zip.
  - Nội dung cần thể hiện:
    - Bảng phân công chi tiết công việc cho từng thành viên (nhóm 4 sinh viên).
    - Tỷ lệ đóng góp của từng người (%).
    - Chữ ký xác nhận hoặc cam kết hoàn thành nhiệm vụ của các thành viên.
* **Hiện trạng dự án:** File này hiện **chưa có trong thư mục**.

---

### ❌ Phần thiếu 3: THIẾU CÁC MỤC BẮT BUỘC TRONG `README.md` THEO MỤC 6.2
* **Đề bài quy định (Mục 6.2):** `README.md` cần ghi rõ 10 mục:
  1. Danh sách thành viên (Họ tên, MSSV, vai trò) $\to$ **Hiện chưa có thông tin thành viên nhóm 13**.
  2. Phiên bản Python và hệ điều hành đã sử dụng $\to$ **Mới ghi chung chung Python >= 3.8, cần ghi rõ Python 3.10/3.11/3.12/3.14 trên Windows/Linux/macOS**.
  3. Cách cài đặt $\to$ Đã có.
  4. Cấu trúc chương trình $\to$ Đã có.
  5. Cách khởi động và sử dụng giao diện $\to$ Đã có.
  6. Cách chạy từng thuật toán $\to$ Đã có.
  7. Cách thay đổi bản đồ và tham số $\to$ Đã có.
  8. Cách chạy test $\to$ Đã có.
  9. **Các lệnh tái tạo kết quả chính (Reproduction Commands)** $\to$ Cần bổ sung các lệnh cụ thể để người chấm tái hiện trực tiếp các bảng so sánh trong báo cáo.
  10. **Các giới hạn hoặc lỗi đã biết (Known Limitations)** $\to$ Hiện chưa có mục này.

---

### ❌ Phần thiếu 4: LÀM RÕ "PHẦN PHÁT TRIỂN CỦA NHÓM" (MỤC 3.7 ĐỀ BÀI)
* **Đề bài quy định (Mục 3.7):**
  > *"Mỗi nhóm lựa chọn ít nhất một nội dung mở rộng: Iterative Deepening Search, Expectimax, Một heuristic thứ hai, Evaluation function cải tiến, Sinh bản đồ tự động, Trực quan hóa quá trình mở rộng trạng thái, Tối ưu thời gian hoặc bộ nhớ... Phần mở rộng phải có mã nguồn, kiểm thử và phân tích kết quả."*
* **Hiện trạng dự án:**
  Nhóm thực chất **đã xây dựng 3 phần mở rộng kỹ thuật rất tốt**:
  1. **Heuristic thứ hai:** Đã có `farthest_food_heuristic` (Maze distance tới thức ăn xa nhất) bên cạnh `mst_heuristic`.
  2. **Trực quan hóa không gian tìm kiếm:** GUI Pygame có animation duyệt node `visited` và `frontier` trực quan trước khi đi.
  3. **Tối ưu thời gian và bộ nhớ:** Xây dựng `MazeDistanceCache` chạy BFS tiền xử lý tính APSP cho phép tra cứu khoảng cách $O(1)$, Memoization Prim MST, và tối ưu `GameState.copy()` tránh nghẽn `deepcopy`.
* **Điểm thiếu:**
  - Chưa viết riêng Unit Test để kiểm thử độ admissible và tính đúng đắn cho Heuristic thứ 2 (`farthest_food_heuristic`).
  - Chưa có mục tổng kết riêng trong `README.md` và `tests/` để giảng viên nhận diện đây là **"Phần mở rộng của nhóm"**, tránh bị chấm sót điểm thưởng sáng tạo.

---

### ❌ Phần thiếu 5: CHI PHÍ DI CHUYỂN KHÔNG ĐỒNG NHẤT (MỤC 5)
* **Đề bài quy định (Mục 5):**
  > *"Nhóm cần thực nghiệm trên nhiều bản đồ có đặc điểm khác nhau: ... Chi phí di chuyển đồng nhất và không đồng nhất."*
* **Hiện trạng dự án:**
  - Trong [`src/search/problems.py`](file:///d:/BDTTTKNC_P1_Nhom13/src/search/problems.py#L94-L100), lớp `MultiFoodSearchProblem` đã hỗ trợ tham số `cost_fn` và `min_step_cost`.
  - Tuy nhiên, dự án chưa có map mẫu hoặc tham số dòng lệnh để bật chi phí di chuyển không đồng nhất (ví dụ: đi vào vùng bùn lầy/cát tốn 2 hoặc 3 cost).

---

## 4. CÁC HẠNG MỤC HỒ SƠ NỘP BÀI CHƯA HOÀN THIỆN

Đối chiếu với cấu trúc gói nộp bài chuẩn trong **Mục 6 đề bài Notion**:

```text
P1_NhomXX.zip
└── P1_NhomXX/
    ├── src/                    ← ĐÃ HOÀN THIỆN
    ├── ui/                     ← ĐÃ HOÀN THIỆN
    ├── assets/                 ← CẦN ĐỔI TÊN TỪ "asset" THÀNH "assets"
    ├── tests/                  ← ĐÃ VƯỢT CHỈ TIÊU (14 Tests)
    ├── maps/                   ← ĐÃ ĐẦY ĐỦ (13 Maps)
    ├── results/                ← ĐANG THIẾU
    ├── main.py                 ← ĐÃ HOÀN THIỆN
    ├── requirements.txt        ← ĐÃ HOÀN THIỆN
    ├── README.md               ← CẦN BỔ SUNG THÔNG TIN THÀNH VIÊN & LỆNH TÁI TẠO
    ├── CONTRIBUTIONS.md        ← ĐANG THIẾU
    └── report.pdf              ← CẦN BIÊN SOẠN BÁO CÁO THEO DỮ LIỆU RESULTS
```

> [!CAUTION]
> **Lưu ý vệ sinh mã nguồn khi nén file zip nộp bài:**
> - Cần xóa thư mục `__pycache__/` và các thư mục `.vscode/`.
> - Các file báo cáo nội bộ (`README_NHOM.md`, `README_NHOM2.md`, `README_NHOM3.md`, `README4.md`) là tài liệu làm việc của nhóm, trước khi nộp chính thức nên gom vào một thư mục tài liệu riêng hoặc chuyển các thông tin quan trọng nhất vào `README.md` chính để tránh vi phạm quy định: *"Không chứa môi trường ảo, cache, dữ liệu không liên quan"*.

---

## 5. KẾ HOẠCH HÀNH ĐỘNG CỤ THỂ ĐỂ ĐẠT ĐIỂM TỐI ĐA (10/10)

Dưới đây là 6 bước kỹ thuật cụ thể cần triển khai:

### Bước 1: Sửa các lỗi code và chuẩn hóa tên thư mục
1. Đổi tên thư mục `asset/` $\to$ `assets/`.
2. Sửa đường dẫn `_ASSET_DIR` trong `ui/g_ui.py` để hỗ trợ cả `assets` và `asset`.
3. Sửa bug hiển thị `"💀 Pacman bị ma bắt!"` tại dòng 965 trong `ui/g_ui.py`.
4. Bổ sung trường `"actions"` vào `metrics` trong `src/agents.py` và cập nhật hàm in `show_metrics()` trong `ui/cli_ui.py`.

### Bước 2: Bổ sung Unit Test cho Phần phát triển của nhóm
* Thêm test case số 15 vào `tests/test_pacman.py`:
  - `test_15_farthest_food_heuristic_admissible`: Kiểm tra tính hợp lệ và admissible của Heuristic thứ 2 (`farthest_food_heuristic`).
  - Nâng tổng số test cases lên **15/15 tests**.

### Bước 3: Xây dựng công cụ thực nghiệm tự động (`benchmark.py`)
* Viết script `benchmark.py` chạy tự động và tạo thư mục `results/` gồm 3 báo cáo:
  1. `results/search_comparison.md`: Bảng so sánh DFS vs BFS vs UCS vs Greedy vs A* trên 5 map đại diện.
  2. `results/heuristic_comparison.md`: Bảng so sánh A* h=0 (UCS) vs A* Farthest vs A* MST.
  3. `results/adversarial_comparison.md`: Bảng so sánh Minimax vs Alpha-Beta ở depth=2 và depth=3 (thời gian, số node duyệt, tỷ lệ cắt tỉa).

### Bước 4: Khởi tạo file `CONTRIBUTIONS.md`
* Soạn thảo bảng phân công nhiệm vụ chi tiết cho 4 thành viên theo mẫu của môn học.

### Bước 5: Cập nhật toàn diện `README.md`
* Điền danh sách thành viên nhóm 13.
* Bổ sung các lệnh tái tạo kết quả thực nghiệm một dòng lệnh (1-click reproduction).
* Bổ sung phần Giới hạn và Lỗi đã biết (Known limitations).
* Nêu bật các tính năng thuộc "Phần mở rộng của nhóm".

### Bước 6: Biên soạn báo cáo `report.pdf`
* Sử dụng dữ liệu thực nghiệm đã xuất trong thư mục `results/` để vẽ biểu đồ và viết báo cáo theo đúng 11 mục yêu cầu tại Mục 6.3 của đề bài.
