# BÁO CÁO CẬP NHẬT & NHẬT KÝ THAY ĐỔI DỰ ÁN (README_NHOM.md)

> **Học phần:** Biểu diễn tri thức và tìm kiếm nâng cao (UET.AI2014)  
> **Dự án 1:** Pacman — Tìm kiếm trong không gian trạng thái và Trò chơi đối kháng  
> **Nhóm thực hiện:** Nhóm 13  
> **Tài liệu tham chiếu:** [Đề bài Dự án 1 Notion](https://truth-element-426.notion.site/D-n-1-Pacman-T-m-ki-m-v-tr-ch-i-i-kh-ng-3db0e26dc18c818a9f90f6e46b9fd3b1)

---

# PHẦN I: NHẬT KÝ THAY ĐỔI TỪ CÁC PHIÊN LÀM VIỆC TRƯỚC

## 1. TỔNG QUAN CÁC THAY ĐỔI ĐÃ THỰC HIỆN

Kể từ khi đưa mã nguồn vào hệ thống hỗ trợ, nhóm đã rà soát, sửa lỗi logic cốt lõi và bổ sung toàn diện các tính năng còn thiếu theo yêu cầu đề bài. Dưới đây là tóm tắt các hạng mục chính:

1. **Sửa lỗi đếm bước (Turn Counter) trên giao diện Desktop GUI & Terminal CLI.**
2. **Cài đặt thuật toán Greedy Best-First Search (`greedy` / `gbfs`).**
3. **Bổ sung chỉ số "Giá trị đánh giá" (Evaluation Value / Utility) trong Metrics đối kháng.**
4. **Bổ sung tính năng Khởi động lại ván chơi (Restart - phím `r`) trên cả GUI và CLI.**
5. **Xây dựng bộ kiểm thử tự động (Unit Tests) gồm 12 bài test trong thư mục `tests/`.**
6. **Giải thích chi tiết nguyên nhân hiện tượng Pacman nhảy vào Ghost trong chế độ Search.**
7. **Cập nhật tài liệu hướng dẫn `README.md` chuẩn hóa theo yêu cầu đề bài.**

---

## 2. CHI TIẾT CÁC THAY ĐỔI & GIẢI PHÁP KỸ THUẬT

### 2.1. Sửa lỗi số bước hiển thị không khớp với số bước đi thật của Pacman
- **Vấn đề ban đầu:** 
  - Trước khi game chạy, hàm `ui.render()` bị gọi 1 lần khiến số bước nhảy lên `1` dù Pacman chưa di chuyển.
  - Vòng lặp `for agent_index, agent in enumerate(self.agents)` trong `GameLoop` gọi `render()` sau lượt đi của **tất cả các tác tử** (Pacman + từng Ghost).
  - Với bản đồ có $G$ con ma, mỗi lần Pacman đi 1 bước thì biến đếm `self.turn` tăng vọt thêm $1 + G$ (ví dụ: trên `map_arena.txt` có 2 Ghost, Pacman đi 19 bước thì GUI hiển thị `Bước: 56`).
- **Giải pháp đã thực hiện:**
  - Cập nhật phương thức `render(self, game_state, is_pacman_move=False)` trong `ui/base_ui.py`, `ui/g_ui.py` và `ui/cli_ui.py`.
  - Chỉ tăng `self.turn += 1` khi `is_pacman_move == True`.
  - Trong `src/engine.py`, truyền cờ `is_pacman_move=(agent_index == 0)`.
- **Kết quả:** Khi mở game hiển thị `Bước: 0`; mỗi bước chân của Pacman số bước tăng đúng `+1`; kết thúc ván số bước hiển thị khớp 100% với `plan_length` / `moves` trong Metrics.

---

### 2.2. Bổ sung thuật toán Greedy Best-First Search (`greedy`)
- **Yêu cầu đề bài (Mục 3.3 & 5.1):** Hệ thống bắt buộc phải cài đặt Greedy Best-First Search và A* Search.
- **Giải pháp đã thực hiện:**
  - Thêm hàm `greedy(problem, heuristic="mst")` vào `src/search/algorithms.py`. Thuật toán sử dụng `PriorityQueueFrontier` với độ ưu tiên $f(n) = h(n)$ (ưu tiên trạng thái có khoảng cách ước lượng tới đích nhỏ nhất).
  - Đăng ký `greedy` và `gbfs` vào từ điển `ALGORITHMS`, hàm chuẩn hóa `normalize_algo_name()` và hàm điều phối `run_search()`.
  - Cập nhật `SearchAgent` trong `src/agents.py` và tham số dòng lệnh `-algo` trong `main.py`.
- **Lệnh chạy:**
  ```bash
  python main.py -mode search -map maps/map_co_ban.txt -algo greedy -heuristic mst
  ```

---

### 2.3. Bổ sung chỉ số "Giá trị đánh giá" (Evaluation Value) cho đối kháng
- **Yêu cầu đề bài (Mục 4):** Kết quả chế độ đối kháng bắt buộc cung cấp: Tác tử, Độ sâu, Hành động được chọn, **Giá trị đánh giá**, Số trạng thái đã xét, Thời gian ra quyết định.
- **Giải pháp đã thực hiện:**
  - Cập nhật `AdversarialAgent` trong `src/agents.py` để lưu lại `self.last_eval_value` (điểm số minimax/utility của nước đi tối ưu được chọn tại mỗi lượt).
  - Bổ sung trường `"last_eval_value"` vào kết quả trả về của hàm `get_metrics()`.
  - Chỉ số này tự động hiển thị trong bảng thống kê metrics ở cuối trận trên cả CLI và GUI.

---

### 2.4. Bổ sung tính năng Khởi động lại (Restart - phím `r`)
- **Yêu cầu đề bài (Mục 2 & 3.6):** Giao diện phải cho phép bắt đầu, tạm dừng, chạy từng bước và **khởi động lại**.
- **Giải pháp đã thực hiện:**
  - Trong `src/engine.py`: Thêm phương thức `reset()` cho lớp `GameLoop` để khôi phục trạng thái bản đồ ban đầu, nạp lại thức ăn, đưa Pacman và Ghost về vị trí xuất phát, đồng thời reset trạng thái của các Agent (`SearchAgent.reset()`, `AdversarialAgent.reset()`).
  - Vòng lặp chính `GameLoop.run()` được bọc trong vòng lặp kiểm tra `restart_requested` để chơi lại ván mà không cần tắt/mở lại tiến trình.
  - Trong `ui/g_ui.py`: Bắt sự kiện phím `r` khi đang chơi hoặc khi màn hình báo kết thúc (Chiến thắng / Game Over) để chơi lại.
  - Trong `ui/cli_ui.py`: Bổ sung lệnh `r` vào danh sách phím điều khiển tương tác.

---

### 2.5. Xây dựng bộ kiểm thử tự động (Unit Tests) với 12 test cases
- **Yêu cầu đề bài (Mục 6.1):** Phải có ít nhất 10 test do nhóm tự xây dựng trong thư mục `tests/`.
- **Giải pháp đã thực hiện:**
  - Tạo thư mục `tests/` cùng module kiểm thử `tests/test_pacman.py` dựa trên thư viện chuẩn `unittest`.
  - Xây dựng **12 bài kiểm thử tự động** bao phủ toàn bộ các nội dung lý thuyết và thực hành của môn học:
    1. `test_01_bfs_shortest_path`: BFS tìm đường đi có số bước ngắn nhất trên bản đồ dạng lưới.
    2. `test_02_dfs_finds_solution`: DFS tìm được lời giải hợp lệ trên bản đồ có nghiệm.
    3. `test_03_ucs_optimal_cost`: UCS tìm đường đi có chi phí tối thiểu.
    4. `test_04_greedy_best_first_search`: Greedy Best-First Search tìm được đường đi tới thức ăn.
    5. `test_05_astar_mst_optimal`: A* kết hợp MST Heuristic tìm đường đi tối ưu thu thập thức ăn.
    6. `test_06_heuristic_admissible`: Kiểm tra tính chấp nhận được (Admissibility: $h(s) \le h^*(s)$).
    7. `test_07_heuristic_goal_state_is_zero`: Giá trị Heuristic tại trạng thái đích bằng 0 ($h(G) = 0$).
    8. `test_08_unsolvable_map_detection`: Phát hiện chính xác bản đồ không có lời giải (`is_solvable() == False`).
    9. `test_09_minimax_alphabeta_equivalence`: Minimax và Alpha-Beta đưa ra hành động tương đương trên cùng trạng thái và độ sâu.
    10. `test_10_alphabeta_pruning_efficiency`: Alpha-Beta Pruning mở rộng ít hơn hoặc bằng số node so với Minimax.
    11. `test_11_ghost_collision_loses_game`: Luật va chạm: Pacman chạm Ghost thì thua cuộc (`lose = True`).
    12. `test_12_food_collection_wins_game`: Luật hoàn thành: Pacman ăn hết thức ăn thì chiến thắng (`win = True`).
- **Lệnh chạy kiểm thử:**
  ```bash
  python -m unittest discover tests
  # Hoặc xem chi tiết từng test:
  python -m unittest -v tests/test_pacman.py
  ```
  *(Hiện tại 12/12 bài test đều vượt qua thành công trong ~0.02s).*

---

### 2.6. Làm rõ hành vi Pacman nhảy vào Ghost trong Search Mode
- **Hiện tượng:** Khi chạy `python main.py -mode search -map maps/map_arena.txt -algo dfs -ui gui`, Pacman đi thẳng vào con ma ở bước 19 và thua.
- **Nguyên nhân:**
  1. Trong `-mode search`, bài toán là `MultiFoodSearchProblem` chỉ tập trung tìm đường ăn hết thức ăn và chỉ nhận `walls`, `start_pos`, `food`. Vị trí của Ghost **hoàn toàn không được đưa vào bài toán tìm kiếm**, thuật toán coi ô có ma là ô trống bình thường.
  2. Thuật toán DFS sử dụng ngăn xếp LIFO, khi đến ô `(11, 2)` đã ưu tiên rẽ `LEFT` vào `(10, 2)` (đúng vị trí con ma đang đứng yên) để khám phá tiếp.
  3. `map_arena.txt` vốn được thiết kế cho chế độ đối kháng `-mode adversarial` (trong đó Pacman dùng Minimax/Alpha-Beta có tính khoảng cách né ma).

---

## 3. CẤU TRÚC THƯ MỤC DỰ ÁN

```text
D:\BDTTTKNC_P1_Nhom13\
├── main.py                     # Điểm vào chính của chương trình, đọc CLI arguments
├── README.md                   # Hướng dẫn sử dụng chung của dự án
├── README_NHOM.md              # Báo cáo nhật ký các thay đổi và cập nhật của nhóm
├── requirements.txt            # Danh sách thư viện (pygame phục vụ giao diện GUI)
├── maps/                       # Các bản đồ kiểm thử (.txt)
│   ├── map_co_ban.txt          # Bản đồ cơ bản 1 thức ăn
│   ├── map_dac_biet.txt        # Bản đồ nhiều thức ăn
│   ├── map_arena.txt           # Bản đồ đối kháng arena có 2 ma
│   ├── map_ghost.txt           # Bản đồ đối kháng 3 ma
│   ├── map_khong_loi_giai_*.txt# Các bản đồ không có lời giải
│   └── ...
├── src/                        # Mã nguồn logic cốt lõi
│   ├── engine.py               # GameState (luật chơi) + GameLoop (vòng lặp game & restart)
│   ├── agents.py               # SearchAgent, MinimaxAgent, AlphaBetaAgent, GhostAgent
│   └── search/                 # Module thuật toán AI
│       ├── algorithms.py       # DFS, BFS, UCS, Greedy, A* (Graph Search)
│       ├── adversarial.py      # Minimax & Alpha-Beta Pruning cho Game Tree
│       ├── heuristics.py       # Heuristic MST, Maze distance, Null
│       └── problems.py         # MultiFoodSearchProblem + BFS MazeDistanceCache
├── tests/                      # Thư mục kiểm thử tự động (12 Unit Tests)
│   ├── __init__.py
│   └── test_pacman.py          # 12 bài unit test bao phủ toàn diện các yêu cầu
├── ui/                         # Mã nguồn giao diện người dùng
│   ├── base_ui.py              # Interface BaseUI
│   ├── cli_ui.py               # Giao diện dòng lệnh tương tác trên Terminal
│   └── g_ui.py                 # Giao diện đồ họa Desktop Pygame
└── asset/                      # Hình ảnh Pacman, Ghost và Font chữ
    ├── fonts/
    └── images/
```

---

## 4. CÁC VIỆC CẦN HOÀN THIỆN TIẾP CHO HỒ SƠ NỘP BÀI (MỤC 6 ĐỀ BÀI)

Để hoàn thiện 100% hồ sơ nộp bài:
1. **Tạo file `CONTRIBUTIONS.md`**: Ghi rõ bảng phân công công việc cụ thể cho các thành viên trong nhóm.
2. **Tạo thư mục `results/`**: Lưu lại bảng số liệu thực nghiệm so sánh (DFS vs BFS vs UCS vs Greedy vs A*, và Minimax vs Alpha-Beta) để đưa vào file `report.pdf`.
3. **Đổi tên thư mục `asset/` thành `assets/`** (nếu muốn đúng 100% theo quy ước đề bài yêu cầu).

---
---

# PHẦN II: CÁC THAY ĐỔI & BỔ SUNG TRONG PHIÊN LÀM VIỆC HIỆN TẠI

Trong phiên làm việc này, nhóm tiếp tục xử lý các vấn đề được đặt ra:
1. **Kiểm tra khả năng chạy của mã nguồn, phát hiện và khắc phục toàn bộ các lỗi khởi động.**
2. **Thêm thuật toán đối kháng Minimax (và Alpha-Beta) cho module search.**
3. **Kích hoạt và hoàn thiện hiển thị giao diện Desktop GUI (Pygame).**

Dưới đây là chi tiết toàn bộ các chỉnh sửa đã thực hiện trong phiên này:

---

## 5. KIỂM TRA MÃ NGUỒN VÀ KHẮC PHỤC CÁC LỖI KHỞI ĐỘNG

Khi chạy kiểm tra thực tế, chương trình ban đầu **không thể chạy được** do gặp các lỗi sau:

### 5.1. Lỗi `ModuleNotFoundError: No module named 'pygame'`
- **Hiện tượng:** Chạy bất kỳ lệnh nào (kể cả chỉ chạy Terminal CLI cơ bản) đều bị crash ngay lập tức.
- **Nguyên nhân:** Tại [main.py](file:///d:/BDTTTKNC_P1_Nhom13/main.py#L5) có lệnh `from ui.g_ui import GUI_UI` đặt ngay đầu file. Trong khi [ui/g_ui.py](file:///d:/BDTTTKNC_P1_Nhom13/ui/g_ui.py#L13) import `pygame`. Mặc dù dự án cam kết trong [README.md](file:///d:/BDTTTKNC_P1_Nhom13/README.md) là chạy trên terminal không cần cài thư viện ngoài, người dùng vẫn bị văng lỗi.
- **Khắc phục:** Chuyển `GUI_UI` sang cơ chế **Lazy Import** (chỉ nạp thư viện đồ họa khi người dùng truyền tham số `-ui gui`).

### 5.2. Chế độ đối kháng (`adversarial`) bị bỏ dở (TODO)
- **Hiện tượng:** Chạy `-mode adversarial` bị thoát game với thông báo `[LỖI] Cần cài đặt lớp cho thuật toán ... trong file agents.py!`.
- **Nguyên nhân:** Trong `main.py`, khối `elif args.mode == "adversarial":` chỉ in thông báo rồi `return`, chưa import và khởi tạo Agent thực tế (dù trong `src/agents.py` đã viết sẵn `MinimaxAgent`, `AlphaBetaAgent`, `ChaserGhostAgent`).
- **Khắc phục:** Kết nối đầy đủ `MinimaxAgent`, `AlphaBetaAgent`, `ChaserGhostAgent` vào `main.py`, cho phép chạy hoàn chỉnh chế độ đối kháng.

### 5.3. Thiếu hàng loạt tham số dòng lệnh CLI
- **Hiện tượng:** Chạy các lệnh mẫu trong `README.md` bị văng lỗi `unrecognized arguments`.
- **Nguyên nhân:** `argparse` trong `main.py` thiếu các cờ: `-depth`, `-delay`, `-step`, `-nocolor`, `-seed`, `-max_turns`.
- **Khắc phục:** Bổ sung đầy đủ tất cả các tham số trên vào `argparse`, đồng thời truyền đúng cấu hình vào `ui` và `GameLoop`.

### 5.4. Lỗi gán cứng Ghost Agent (`Hardcoded Ghost Agent`)
- **Hiện tượng:** Trên map không có Ghost (như `map_co_ban.txt`), vẫn có 1 Ghost ma chạy lượt làm chậm và nháy hình; trên map có nhiều Ghost (như `map_ghost.txt` có 3 Ghost, `map_arena.txt` có 2 Ghost), các Ghost từ thứ 2 trở đi không có Agent điều khiển.
- **Nguyên nhân:** `main.py` luôn gán cố định `agents.append(DummyGhostAgent(index=1))` mà không dùng `ghost_factory`.
- **Khắc phục:** Áp dụng tham số `ghost_factory` của `GameLoop`, tự động sinh đúng số lượng tác tử Ghost tương ứng với số ma trên từng bản đồ (`DummyGhostAgent` cho search, `ChaserGhostAgent` cho adversarial).

### 5.5. Lỗi mã hóa tiếng Việt trên Windows Console (`UnicodeEncodeError: 'charmap'`)
- **Hiện tượng:** Khi chạy trên PowerShell/CMD của Windows, in tiếng Việt có dấu bị lỗi `UnicodeEncodeError: 'charmap' codec can't encode character...`.
- **Khắc phục:** Bổ sung đoạn mã tự động cấu hình UTF-8 `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` ngay đầu file `main.py`.

### 5.6. Hiển thị Metrics chỉ chạy cho chế độ Search
- **Hiện tượng:** Kết thúc trận đối kháng không in bảng thống kê Metrics.
- **Nguyên nhân:** `main.py` kiểm tra `if args.mode == "search" and hasattr(...)`.
- **Khắc phục:** Bỏ ràng buộc `args.mode == "search"`, cho phép in đầy đủ metrics cho cả hai chế độ.

### 5.7. Chuẩn hóa điều kiện cắt tỉa Alpha-Beta
- **Hiện tượng:** Trong `src/agents.py`, điều kiện cắt tỉa ban đầu là `beta < alpha`.
- **Khắc phục:** Đổi thành `beta <= alpha` theo đúng lý thuyết chuẩn của thuật toán Minimax Alpha-Beta Pruning, giúp thuật toán tận dụng tối đa cơ hội cắt tỉa khi các nhánh bằng điểm nhau.

---

## 6. THÊM THUẬT TOÁN ĐỐI KHÁNG MINIMAX CHO SEARCH

Nhóm đã thiết kế và tích hợp Minimax theo mô hình modular:

### 6.1. Tạo mới module tìm kiếm đối kháng [src/search/adversarial.py](file:///d:/BDTTTKNC_P1_Nhom13/src/search/adversarial.py)
Bao gồm:
- **`minimax_search(state, depth, evaluation_fn, maze_distance)`:** Duyệt toàn bộ cây trò chơi đa tác tử (Pacman là MAX, lần lượt các Ghost là MIN). Độ sâu giảm 1 đơn vị sau khi Pacman và toàn bộ Ghost đi xong 1 vòng.
- **`alphabeta_search(...)`:** Minimax kết hợp cắt tỉa Alpha-Beta (`beta <= alpha`), cho kết quả tương đương Minimax nhưng duyệt ít hơn 50% số trạng thái.
- **`default_evaluation_fn(state, maze_distance)`:** Hàm đánh giá heuristic (thưởng thắng +500, phạt thua -500, điểm game, số thức ăn còn lại, khoảng cách mê cung BFS tới thức ăn gần nhất, phạt nặng khi ma áp sát $\le 2$ ô).
- **`AdversarialSearchResult`:** Đóng gói kết quả: nước đi tốt nhất (`action`), giá trị đánh giá (`value`), số node đã mở rộng (`expanded_nodes`) và thời gian tính toán (`search_time`).
- **`MazeDistance`:** Module tính toán khoảng cách mê cung BFS nhớ lại (memoized) để hàm đánh giá tra cứu nhanh $O(1)$.

### 6.2. Đăng ký vào Search Engine [src/search/algorithms.py](file:///d:/BDTTTKNC_P1_Nhom13/src/search/algorithms.py)
- Đăng ký `minimax` và `alphabeta` vào từ điển `ALGORITHMS` và hàm chuẩn hóa `normalize_algo_name()`.
- Cài đặt `problem_adversarial_search()` để hỗ trợ chạy Minimax tìm kiếm trên cả đối tượng `SearchProblem` lẫn `GameState`.

### 6.3. Cập nhật `SearchAgent` trong [src/agents.py](file:///d:/BDTTTKNC_P1_Nhom13/src/agents.py) và [main.py](file:///d:/BDTTTKNC_P1_Nhom13/main.py)
Cho phép chạy thuật toán Minimax ở cả 2 trường hợp:
- **Chế độ `adversarial`:** `python main.py -mode adversarial -map maps/map_ghost.txt -algo minimax -depth 3` (Pacman dùng Minimax đối đầu với Ghost đuổi theo có AI).
- **Chế độ `search`:** `python main.py -mode search -map maps/map_co_ban.txt -algo minimax` (Pacman dùng Minimax để tìm đường ăn mồi và né vật cản / ma đứng yên).

---

## 7. KÍCH HOẠT VÀ HOÀN THIỆN HIỂN THỊ GIAO DIỆN DESKTOP GUI

Nhóm đã hoàn thiện giải pháp hiển thị cửa sổ game đồ họa trực tiếp trên Desktop:

### 7.1. Cài đặt thư viện đồ họa tương thích
- Cài đặt thư viện `pygame-ce` (phiên bản tương thích với mọi bản Python, kể cả Python 3.12, 3.13, 3.14).
- Cập nhật hướng dẫn trong [requirements.txt](file:///d:/BDTTTKNC_P1_Nhom13/requirements.txt) và [README.md](file:///d:/BDTTTKNC_P1_Nhom13/README.md).

### 7.2. Nâng cấp toàn diện [ui/g_ui.py](file:///d:/BDTTTKNC_P1_Nhom13/ui/g_ui.py)
- **Nạp hình ảnh Sprites:** Tự động nạp sprite Pacman và các Ghost (`Blinky.png`, `Inky.png`, `Clyde.png`) từ thư mục `asset/images/`.
- **Nạp Font chữ Retro:** Tự động nạp font từ `asset/fonts/font.ttf`.
- **Căn chỉnh Responsive:** Tự động căn giữa bản đồ trong cửa sổ game; thiết lập kích thước cửa sổ tối thiểu `480x480` pixel để các bản đồ nhỏ không làm co cụm giao diện.
- **Banner kết thúc trận:** Hiển thị chữ nổi bật khi ván kết thúc (*CHIẾN THẮNG!*, *GAME OVER!*, *BẢN ĐỒ KHÔNG CÓ LỜI GIẢI!*).
- **Bảng Metrics Overlay:** Khi kết thúc ván, tự động hiển thị màn hình phủ mờ (overlay) liệt kê toàn bộ thông số thống kê kết quả tìm kiếm.

### 7.3. Cách mở giao diện Desktop và phím điều khiển
Chỉ cần thêm tham số **`-ui gui`** vào câu lệnh chạy:
```bash
# Đối kháng Minimax trên Desktop GUI
python main.py -mode adversarial -map maps/map_ghost.txt -algo minimax -depth 3 -ui gui

# Tìm kiếm A* trên Desktop GUI
python main.py -mode search -map maps/map_co_ban.txt -algo astar -ui gui
```

**Bảng phím điều khiển trên cửa sổ Desktop (GUI):**
- `Space` / `Enter` / `n`: Đi tiếp 1 bước (chế độ từng bước).
- `a`: Chuyển sang chạy tự động.
- `s`: Tạm dừng và quay lại chế độ từng bước.
- `r`: Khởi động lại ván chơi (Restart).
- `+` / `-`: Tăng / giảm tốc độ di chuyển.
- `q` / `Esc`: Thoát game.

---

## 8. BẢNG TỔNG KẾT TẤT CẢ CÁC FILE ĐÃ CHỈNH SỬA & TẠO MỚI

| STT | Tên file | Trạng thái | Nội dung chỉnh sửa chính |
|:---:|---|:---:|---|
| 1 | `main.py` | Chỉnh sửa | Bổ sung các tham số CLI, Lazy import GUI, liên kết Minimax/AlphaBeta/ChaserGhost, dùng ghost_factory, cấu hình UTF-8 console. |
| 2 | `src/search/adversarial.py` | Tạo mới | Module tìm kiếm đối kháng: `minimax_search`, `alphabeta_search`, hàm đánh giá `default_evaluation_fn`, lớp `AdversarialSearchResult`. |
| 3 | `src/search/algorithms.py` | Chỉnh sửa | Tích hợp `greedy`, `minimax`, `alphabeta` vào từ điển `ALGORITHMS`, hàm `run_search` và `problem_adversarial_search`. |
| 4 | `src/agents.py` | Chỉnh sửa | Hỗ trợ Greedy và Minimax trong `SearchAgent`, chuẩn hóa cắt tỉa `beta <= alpha`, bổ sung `last_eval_value` và phương thức `reset()`. |
| 5 | `src/engine.py` | Chỉnh sửa | Bổ sung phương thức `reset()` trong `GameLoop`, truyền cờ `is_pacman_move` vào `ui.render()`, hỗ trợ chơi lại ván (Restart). |
| 6 | `ui/g_ui.py` | Chỉnh sửa | Nâng cấp toàn diện Desktop GUI: nạp sprite từ `asset/`, căn giữa bản đồ, kích thước tối thiểu $480 \times 480$, sửa đếm bước, phím restart `r`. |
| 7 | `ui/cli_ui.py` | Chỉnh sửa | Sửa logic đếm bước (chỉ tăng khi Pacman đi), bổ sung lệnh restart `r`. |
| 8 | `ui/base_ui.py` | Chỉnh sửa | Chuẩn hóa phương thức `render(self, game_state, is_pacman_move=False)`. |
| 9 | `tests/test_pacman.py` | Tạo mới | Xây dựng 12 bài Unit Test Cases tự động kiểm thử toàn diện mọi chức năng. |
| 10 | `requirements.txt` | Chỉnh sửa | Bổ sung gói `pygame-ce` phục vụ giao diện Desktop GUI. |
| 11 | `README.md` | Chỉnh sửa | Bổ sung hướng dẫn tham số `-ui gui`, các thuật toán mới `greedy`, `minimax`, `alphabeta`. |
| 12 | `README_NHOM.md` | Cập nhật | Báo cáo đầy đủ, toàn diện mọi thay đổi của dự án qua các phiên làm việc. |
