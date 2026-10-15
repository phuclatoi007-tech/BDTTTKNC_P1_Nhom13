# Pacman AI - Nhóm 13

# Thành viên 
Cao Thế Nhật - 25022970
Lê Minh Quân - 25022993
Nguyễn Hoàng Phúc - 25022981
Kiều Việt Tiến -25023025

Trò chơi Pacman chạy trên terminal, có hai chế độ:

| Chế độ | Thuật toán | Ghost |
|---|---|---|
| `search` | `bfs`, `dfs`, `ucs`, `greedy`, `astar` (heuristic: `mst`, `maze`, `null`) | |
| `adversarial` | `minimax`, `alphabeta` | đuổi theo Pacman (có xác suất đi ngẫu nhiên) |

## Yêu cầu

- Python 3.12, **không cần cài thư viện ngoài** cho CLI (xem `requirements.txt`).
- Terminal hỗ trợ mã màu ANSI để hiển thị màu (có thể tắt bằng `-nocolor`).
- Cài đặt `pygame` nếu muốn sử dụng giao diện đồ họa Desktop GUI: `pip install pygame`.

## Cấu trúc thư mục

```
main.py                  điểm vào, đọc tham số dòng lệnh
maps/                    các bản đồ kiểm thử
tests/                   bộ kiểm thử tự động (12 unit tests)
src/engine.py            GameState (luật chơi) + GameLoop (vòng lặp game)
src/agents.py            SearchAgent, MinimaxAgent, AlphaBetaAgent, Ghost agents
src/search/algorithms.py general_graph_search + Frontier (DFS/BFS/UCS/Greedy/A*)
src/search/adversarial.py Minimax và Alpha-Beta Pruning cho GameTree
src/search/heuristics.py heuristic: mst, maze, null
src/search/problems.py   MultiFoodSearchProblem + cache khoảng cách mê cung (BFS)
ui/base_ui.py            BaseUI trừu tượng
ui/cli_ui.py             Giao diện Terminal (CLI)
ui/g_ui.py               Giao diện Đồ họa Desktop (GUI Pygame)
```

### Tham số

| Tham số | Ý nghĩa | Mặc định |
|---|---|---|
| `-mode` | `search` hoặc `adversarial` | `search` |
| `-map` | đường dẫn file map | `maps/map_co_ban.txt` |
| `-algo` | thuật toán (`bfs`, `dfs`, `ucs`, `greedy`, `astar`, `minimax`, `alphabeta`) | `astar` / `alphabeta` |
| `-heuristic` | heuristic cho A* và Greedy: `mst`, `maze`, `null` | `mst` |
| `-depth` | độ sâu của minimax / alphabeta | `3` |
| `-ui` | `cli` (Terminal) hoặc `gui` (Cửa sổ Desktop Pygame) | `gui` (nếu không truyền tham số) / `cli` |
| `-delay` | giây nghỉ giữa các bước ở chế độ tự động | `0.15` |
| `-step` | bắt đầu ở chế độ từng bước | tắt |
| `-nocolor` | tắt màu ANSI | tắt |
| `-seed` | seed ngẫu nhiên của Ghost (để tái lập kết quả) | ngẫu nhiên |
| `-max_turns` | số vòng tối đa của chế độ adversarial | `200` |

``
## Cách chạy

```bash
# Khởi chạy nhanh: mở thẳng giao diện đồ họa tương tác (GUI)
python main.py

# Chạy bằng terminal
python main.py -mode <mode_type> -map <map_url> -algo <algorithm> -heuristic <heuristic_type> -depth <do_sau> -ui <gui/cli> 
    # Các tham số khác không cần thiết phải điều chỉnh

# Chạy thực nghiệm
  Chạy file run_experiments.py  
    
    # Trường hợp đặc biệt
    python main.py -mode search -map maps/map_co_ban.txt -algo bfs -ui cli
    python main.py -mode search -map maps/map_dac_biet.txt -algo bfs -ui cli
    python main.py -mode adversarial -map maps/map_dac_biet.txt -algo minimax -ui cli

# Chạy kiểm tra tính đúng đắn của chương trình
python -m unittest discover tests
```

## Ký hiệu bản đồ

`#` tường - `P` Pacman - `G` Ghost - `.` thức ăn - khoảng trắng: ô trống.

Các map trong `maps/`: `map_co_ban`, `map_hep`, `map_dac_biet`, `map_lon_1`, `map_lon_2`,
`map_ghost`, `map_ghost_lon`, `map_arena`, và hai map **không có lời giải**
(`map_khong_loi_giai_pacman`, `map_khong_loi_giai_target`).


### Điều khiển giao diện (CLI & GUI)

| Phím | Tác dụng |
|---|---|
| `Enter` / `n` / `Space` | đi 1 bước (chế độ từng bước) |
| `a` | chạy tự động |
| `s` | quay lại chế độ từng bước (tạm dừng) |
| `r` | khởi động lại ván chơi (Restart) |
| `+` / `-` | tăng / giảm tốc độ |
| `q` / `Esc` | thoát |
| `Ctrl+C` | tạm dừng khi đang chạy tự động trong CLI |

Khi không chạy trong terminal thật (pipe, file) giao diện tự chạy tự động, không chờ nhập.

## Kết thúc ván chơi

Ván kết thúc khi: thắng (ăn hết thức ăn), thua (chạm Ghost), **bản đồ không có lời giải**
(search báo `no_solution`, không bị treo), hết `-max_turns`, hoặc người chơi bấm `q`.


## Ghi chú thiết kế

- **Search**: trạng thái = `(vị trí Pacman, tập thức ăn còn lại)`; mọi thuật toán dùng chung
  `general_graph_search`, chỉ khác cấu trúc Frontier. A* + MST là admissible và consistent.
  BFS/DFS/UCS trên map có rất nhiều thức ăn (vd `map_arena`, 41 thức ăn) sẽ bùng nổ không gian
  trạng thái - hãy dùng `astar` hoặc chế độ `adversarial` cho map đó.
- **Adversarial**: Pacman là MAX, các Ghost là MIN; một độ sâu = Pacman + toàn bộ Ghost đi một lượt.
  `alphabeta` cho kết quả giống `minimax` nhưng mở rộng ít node hơn. Hàm đánh giá dùng điểm,
  số thức ăn còn lại, khoảng cách mê cung tới thức ăn gần nhất và phạt khi Ghost quá gần.

# Hạn chế
- Chưa xử lí các map với chi phí di chuyển đồng không đồng nhất.
- Hàm đánh giá thuật toán đối kháng chưa tốt.
