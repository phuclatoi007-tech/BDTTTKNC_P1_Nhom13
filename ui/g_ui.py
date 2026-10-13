"""
ui/g_ui.py (display.py)
Giao diện trực quan hóa thuật toán tìm kiếm AI và trò chơi Pacman (Pygame).
Thiết kế Dropdown Menu hiện đại, đồng bộ toàn diện với tài nguyên assets/,
hỗ trợ cả chế độ GameLoop và Standalone Demo.
"""
import os
import sys
import time
import math
import random
from collections import deque
import heapq
import pygame

# ──────────────────────────────────────────────────────────────────────────────
# Tương thích với BaseUI (nếu tồn tại)
# ──────────────────────────────────────────────────────────────────────────────
try:
    from ui.base_ui import BaseUI
except ImportError:
    class BaseUI:
        def initialize(self):
            pass

        def render(self, game_state):
            pass

        def show_metrics(self, metrics):
            pass


# ──────────────────────────────────────────────────────────────────────────────
# Quản lý đường dẫn tài nguyên (Assets) an toàn, đa nền tảng
# ──────────────────────────────────────────────────────────────────────────────
def _get_asset_path(*subpaths):
    """Tìm đường dẫn tệp tài nguyên an toàn, hỗ trợ cả 'assets' và 'asset'."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for folder in ["assets", "asset"]:
        target = os.path.join(base_dir, folder, *subpaths)
        if os.path.exists(target):
            return target
    return os.path.join(base_dir, "assets", *subpaths)


_FONT_PATH = _get_asset_path("fonts", "font.ttf")


# ══════════════════════════════════════════════════════════════════════════════
# BẢNG MÀU RGB – Dark Navy / Cyan Accent (Cao cấp, hiện đại)
# ══════════════════════════════════════════════════════════════════════════════

# --- Nền & Khung ---
COLOR_BG              = (15,  18,  30)      # Nền toàn cục – xanh đen tối
COLOR_PANEL_BG        = (20,  24,  40)      # Nền Sidebar – xanh đen tối đồng bộ
COLOR_CARD_BG         = (30,  36,  58)      # Nền thẻ Metrics card
COLOR_DROPDOWN_POPUP  = (22,  28,  48)      # Nền popup danh sách thả xuống
COLOR_BORDER          = (45,  55,  85)      # Viền phân cách panel / card
COLOR_DIVIDER         = (35,  42,  68)      # Đường kẻ ngang mờ giữa các item

# --- Chữ ---
COLOR_TEXT_MAIN       = (235, 240, 245)     # Chữ chính – trắng sáng
COLOR_TEXT_MUTED      = (140, 150, 170)     # Nhãn / thống kê – xám nhạt
COLOR_TEXT_WHITE      = (255, 255, 255)     # Trắng tuyệt đối

# --- Màu nhấn (Accent) ---
COLOR_ACCENT          = (0,  180, 216)      # Xanh ngọc Cyan – tiêu đề, highlight

# --- Bản đồ ---
COLOR_WALL            = (33,  70, 139)      # Tường – Xanh dương trung (Medium Blue)
COLOR_WALL_GRID       = (25,  55, 110)      # Viền lưới mờ ô tường
COLOR_FLOOR           = (15,  18,  30)      # Nền đường đi – đồng nhất với BG
COLOR_FOOD            = (255, 183,   3)     # Thức ăn – Vàng cam nhỏ
COLOR_GOAL            = (230,  57,  70)     # Đích đến – Đỏ nổi bật
COLOR_PACMAN          = (255, 221,   0)     # Pacman fallback – Vàng
COLOR_PACMAN_MOUTH    = (15,  18,  30)     # Miệng Pacman fallback

# --- Lớp màu thuật toán ---
COLOR_VISITED         = (35,  60,  95)      # Đã duyệt (Explored) – xanh tối nhạt
COLOR_VISITED_BORDER  = (50,  80, 120)      # Viền ô đã duyệt
COLOR_FRONTIER        = (180, 110,  20)     # Hàng đợi (Frontier) – cam tối nhạt
COLOR_FRONTIER_BORDER = (220, 145,  40)     # Viền ô frontier
COLOR_PATH            = (46, 204, 113)      # Đường đi tối ưu – xanh lá

# --- Nút bấm & Dropdown ---
COLOR_BTN_DEFAULT     = (38,  48,  78)      # Nút mặc định / Header dropdown
COLOR_BTN_HOVER       = (55,  70,  110)     # Nút hover / Hover item
COLOR_BTN_ACTIVE      = (0,   160, 200)     # Nút đang chọn – xanh ngọc đậm
COLOR_BTN_START       = (40,  167, 69)      # Bắt đầu – Xanh lá
COLOR_BTN_PAUSE       = (240, 150, 0)       # Tạm dừng – Cam
COLOR_BTN_STEP        = (70,  85,  120)     # Từng bước – Xám xanh
COLOR_BTN_RESET       = (220, 53,  69)      # Đặt lại – Đỏ


def _load_font(size, bold=False):
    """Load font từ font.ttf trong assets, fallback sang SysFont nếu không tìm thấy."""
    try:
        if os.path.exists(_FONT_PATH):
            f = pygame.font.Font(_FONT_PATH, size)
            if bold:
                f.set_bold(True)
            return f
    except Exception:
        pass
    return pygame.font.SysFont("Arial", size, bold=bold)


def _load_image(path):
    """Load ảnh an toàn, trả về Surface hoặc None nếu lỗi."""
    try:
        if os.path.exists(path):
            img = pygame.image.load(path)
            return img.convert_alpha() if pygame.display.get_surface() else img
    except Exception as e:
        print(f"[Warning] Khong the tai anh tu {path}: {e}")
    return None


def _prepare_pacman_surface(img):
    """Chuyển đổi pacman.png có nền đen (1, 0, 0) thành Surface có kênh alpha trong suốt tuyệt đối."""
    if img is None:
        return None
    w, h = img.get_size()
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for x in range(w):
        for y in range(h):
            c = img.get_at((x, y))
            # Nếu là màu vàng của Pacman
            if c[0] > 180 and c[1] > 180 and c[2] < 100:
                surf.set_at((x, y), (c[0], c[1], c[2], 255))
            elif c[3] > 0 and (c[0] > 10 or c[1] > 10 or c[2] > 10):
                surf.set_at((x, y), c)
            else:
                surf.set_at((x, y), (0, 0, 0, 0))
    return surf


# ══════════════════════════════════════════════════════════════════════════════
# LỚP GIAO DIỆN CHÍNH: PacmanUI
# ══════════════════════════════════════════════════════════════════════════════

class PacmanUI(BaseUI):
    """Lớp giao diện Pacman chính – vẽ bàn cờ, panel điều khiển, dropdown menu, metrics và sprites."""

    def __init__(self, width=1080, height=720, delay=0.15, step_mode=False, cell_size=None):
        pygame.init()
        pygame.display.set_caption("Pacman AI Search - Nhóm 13")
        self.screen_width = width
        self.screen_height = height
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()

        # Thuộc tính tương thích GameLoop / CLI
        self.delay = delay
        self.step_mode = step_mode
        self.quit_requested = False
        self.turn = 0
        self._game_state = None

        # Font chữ tùy chỉnh từ assets/fonts/font.ttf
        self.font_title = _load_font(20, bold=True)
        self.font_bold  = _load_font(14, bold=True)
        self.font_main  = _load_font(13)
        self.font_small = _load_font(11)

        # Layout: Game board (trái 700px) | Control panel (phải 380px)
        self.panel_x = 700
        self.panel_width = width - self.panel_x
        self.board_rect = pygame.Rect(0, 0, self.panel_x, height)

        # ── Dropdown: Chọn bản đồ ──
        self.map_files = self._scan_maps()
        self.selected_map_idx = 0
        self.map_dropdown_open = False
        self.map_dropdown_rect = None
        self.map_item_rects = []
        self.map_scroll_offset = 0
        self.map_rects = []   # Thuộc tính tương thích ngược

        # ── Dropdown: Thuật toán tìm kiếm ──
        self.algorithms = ["A* Search", "BFS", "DFS", "UCS", "Greedy BFS", "Minimax", "Alpha-Beta"]
        self.selected_algo_idx = 0
        self.algo_dropdown_open = False
        self.algo_dropdown_rect = None
        self.algo_item_rects = []
        self.algo_rects = []  # Thuộc tính tương thích ngược

        # ── Dropdown: Hàm Heuristic (dành cho A* & Greedy BFS) ──
        self.heuristics = [
            ("MST", "MST (Cây khung nhỏ nhất)"),
            ("Manhattan", "Manhattan (Lưới ô)"),
            ("Euclidean", "Euclidean (Đường thẳng)"),
            ("Maze", "Maze Distance (Mê cung)"),
            ("Null", "Null (h = 0)"),
        ]
        self.selected_heuristic_idx = 0
        self.heuristic_dropdown_open = False
        self.heuristic_dropdown_rect = None
        self.heuristic_item_rects = []

        # Trạng thái mô phỏng
        self.is_running = False
        self.is_paused = False
        self.speed = 15
        self.slider_dragging = False

        # Ma trận bản đồ
        self.raw_map = []
        self.map_rows = 0
        self.map_cols = 0
        self.cell_size = cell_size if cell_size is not None else 30
        self.board_offset_x = 20
        self.board_offset_y = 20

        # Vị trí thực thể
        self.pacman_pos = None
        self.start_pos = None
        self.goal_pos = None
        self.ghosts_pos = []
        self.initial_ghosts_pos = []
        self.food_positions = set()
        self.pacman_direction = "RIGHT"

        # Lớp tìm kiếm thuật toán & Đối kháng
        self.visited_nodes = set()
        self.frontier_nodes = set()
        self.final_path = []
        self.planned_trajectory = []
        self.eaten_food = set()
        self.is_game_over = False
        self.game_score = 0

        # State machine:
        # "IDLE"      – Chờ bấm Start
        # "SEARCHING" – Thuật toán đang duyệt, Pacman đứng im tại start_pos
        # "MOVING"    – Pacman di chuyển (theo đường đi tĩnh hoặc theo lượt động)
        self.phase = "IDLE"
        self.current_node = None
        self.move_step_idx = 0
        self._frame_counter = 0

        # Số liệu thống kê
        self.metrics = {
            "status": "Sẵn sàng",
            "expanded": 0,
            "cost": 0,
            "time_ms": 0.0,
            "path_length": 0
        }

        # Nạp sprites từ thư mục assets/
        self._load_sprites()

        # Khởi tạo tọa độ UI và Dropdown rects
        self._init_ui_bounds()

        # Nạp bản đồ mặc định nếu có
        if self.map_files:
            self.load_map_file(self.map_files[self.selected_map_idx])

    # ── Tải và quản lý Sprites ────────────────────────────────────────────────

    def _load_sprites(self):
        """Nạp sprite gốc của Pacman và các Ghost từ assets/."""
        raw_pacman = _load_image(_get_asset_path("images", "pacman", "pacman.png"))
        self.raw_pacman_img = _prepare_pacman_surface(raw_pacman)

        self.raw_ghost_imgs = {
            "blinky": _load_image(_get_asset_path("images", "ghosts", "Blinky.png")),
            "clyde":  _load_image(_get_asset_path("images", "ghosts", "Clyde.png")),
            "inky":   _load_image(_get_asset_path("images", "ghosts", "Inky.png")),
        }

        self.scaled_pacman = {}
        self.scaled_ghosts = {}
        self._update_scaled_sprites()

    def _update_scaled_sprites(self):
        """Scale lại các sprite khớp với cell_size hiện tại và tạo các hướng xoay."""
        cs = self.cell_size
        sprite_size = max(8, int(cs * 0.90))

        if self.raw_pacman_img:
            base_p = pygame.transform.smoothscale(self.raw_pacman_img, (sprite_size, sprite_size))
            self.scaled_pacman = {
                "RIGHT": base_p,
                "LEFT":  pygame.transform.flip(base_p, True, False),
                "UP":    pygame.transform.rotate(base_p, 90),
                "DOWN":  pygame.transform.rotate(base_p, 270)
            }
        else:
            self.scaled_pacman = {}

        self.scaled_ghosts = {}
        for name, img in self.raw_ghost_imgs.items():
            if img:
                self.scaled_ghosts[name] = pygame.transform.smoothscale(img, (sprite_size, sprite_size))

    # ── Quét bản đồ và Khởi tạo Tọa độ UI ─────────────────────────────────────

    def _scan_maps(self):
        """Quét thư mục maps/ lấy danh sách tất cả file .txt."""
        d = "maps"
        if os.path.isdir(d):
            found = sorted(f for f in os.listdir(d) if f.endswith(".txt"))
            if found:
                return [os.path.join(d, f).replace("\\", "/") for f in found]
        return ["maps/map_co_ban.txt"]

    def _init_ui_bounds(self):
        """Khởi tạo tọa độ cho Dropdowns, Buttons, Slider trên Sidebar bên phải."""
        px = self.panel_x + 16
        pw = self.panel_width - 32

        # 1. Map Dropdown (Header & Popup item rects)
        self.map_dropdown_rect = pygame.Rect(px, 72, pw, 32)
        item_h_map = 28
        max_visible_maps = min(10, len(self.map_files))
        self.map_item_rects = [
            pygame.Rect(px, self.map_dropdown_rect.bottom + 2 + i * item_h_map, pw, item_h_map)
            for i in range(max_visible_maps)
        ]

        # 2. Algorithm Dropdown (Header & Popup item rects)
        self.algo_dropdown_rect = pygame.Rect(px, 134, pw, 32)
        item_h_algo = 28
        self.algo_item_rects = [
            pygame.Rect(px, self.algo_dropdown_rect.bottom + 2 + i * item_h_algo, pw, item_h_algo)
            for i in range(len(self.algorithms))
        ]

        # 3. Heuristic Dropdown (Header & Popup item rects)
        self.heuristic_dropdown_rect = pygame.Rect(px, 196, pw, 32)
        item_h_heu = 28
        self.heuristic_item_rects = [
            pygame.Rect(px, self.heuristic_dropdown_rect.bottom + 2 + i * item_h_heu, pw, item_h_heu)
            for i in range(len(self.heuristics))
        ]

        # 4. Điều khiển mô phỏng: Start, Pause, Step, Reset
        y = 258
        cw = (pw - 24) // 4
        self.btn_start = pygame.Rect(px, y, cw, 32)
        self.btn_pause = pygame.Rect(px + (cw + 8), y, cw, 32)
        self.btn_step  = pygame.Rect(px + (cw + 8) * 2, y, cw, 32)
        self.btn_reset = pygame.Rect(px + (cw + 8) * 3, y, cw, 32)

        # 5. Thanh trượt tốc độ & Presets
        self.slider_track = pygame.Rect(px, 318, pw, 8)
        sw = (pw - 24) // 4
        self.speed_presets = [
            (pygame.Rect(px + i * (sw + 8), 334, sw, 20), v, l)
            for i, (v, l) in enumerate([(5, "1x"), (15, "2x"), (30, "5x"), (60, "Max")])
        ]

    # ── Vòng đời & Tương thích BaseUI ─────────────────────────────────────────

    def initialize(self):
        """Khởi tạo vòng đời giao diện (tương thích BaseUI & GameLoop)."""
        self.turn = 0
        self.quit_requested = False
        print("[GUI] Khoi tao giao dien do hoa Pacman (Pygame)...")

    def load_map_file(self, file_path):
        """Đọc file bản đồ .txt và nạp vào giao diện."""
        if not os.path.exists(file_path):
            return False
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [ln.rstrip("\r\n") for ln in f if ln.strip()]
        self.set_map(lines)
        return True

    def set_map(self, map_data):
        """Nạp ma trận bản đồ, nhận diện các thực thể và tự căn giữa ô vẽ."""
        self.raw_map = [list(row) for row in map_data]
        self.map_rows = len(self.raw_map)
        self.map_cols = max((len(r) for r in self.raw_map), default=0)

        self.start_pos = None
        self.pacman_pos = None
        self.goal_pos = None
        self.ghosts_pos = []
        self.food_positions = set()

        for r in range(self.map_rows):
            for c in range(len(self.raw_map[r])):
                ch = self.raw_map[r][c]
                if ch == 'P':
                    self.start_pos = self.pacman_pos = (r, c)
                elif ch == 'G':
                    self.ghosts_pos.append((r, c))
                elif ch in ('.', 'o'):
                    self.food_positions.add((r, c))

        # Lưu vị trí Ghost ban đầu
        self.initial_ghosts_pos = list(self.ghosts_pos)

        # Xác định mục tiêu (Goal):
        # - Nếu có 1 hạt thức ăn: đặt làm mục tiêu chính
        # - Nếu có nhiều hạt thức ăn: chế độ Multi-Food (toàn bộ thức ăn là mục tiêu, không đánh dấu riêng 1 hạt)
        # - Nếu không có thức ăn: lấy vị trí Ghost làm mục tiêu
        if len(self.food_positions) == 1:
            self.goal_pos = sorted(list(self.food_positions))[0]
        elif len(self.food_positions) > 1:
            self.goal_pos = None  # Toàn bộ thức ăn đều là mục tiêu
        elif self.ghosts_pos:
            self.goal_pos = self.ghosts_pos[0]

        # Tự động tính cell_size và căn giữa khu vực vẽ board
        if self.map_cols > 0 and self.map_rows > 0:
            aw = self.board_rect.width - 40
            ah = self.board_rect.height - 40
            self.cell_size = max(12, min(45, aw // self.map_cols, ah // self.map_rows))
            self.board_offset_x = (self.board_rect.width  - self.map_cols * self.cell_size) // 2
            self.board_offset_y = (self.board_rect.height - self.map_rows * self.cell_size) // 2
            self._update_scaled_sprites()

        self.reset_search_state()

    def has_ghosts(self):
        """Kiểm tra bản đồ hiện tại có Ma hay không."""
        return len(getattr(self, "initial_ghosts_pos", self.ghosts_pos)) > 0

    def reset_search_state(self):
        """Đặt lại toàn bộ tiến trình tìm kiếm về trạng thái ban đầu."""
        self.visited_nodes.clear()
        self.frontier_nodes.clear()
        self.final_path = []
        self.planned_trajectory = []
        self.eaten_food.clear()
        self.pacman_pos = self.start_pos
        self.ghosts_pos = list(getattr(self, "initial_ghosts_pos", self.ghosts_pos))
        self.pacman_direction = "RIGHT"
        self.phase = "IDLE"
        self.current_node = None
        self.move_step_idx = 0
        self._frame_counter = 0
        self.is_running = False
        self.is_paused = False
        self.is_game_over = False
        self.game_score = 0
        self.turn = 0
        init_st = "Sẵn sàng (Bản đồ có Ma - Đối kháng theo lượt)" if self.has_ghosts() else "Sẵn sàng (Tìm kiếm tĩnh)"
        self.metrics = {
            "status": init_st,
            "expanded": 0,
            "cost": 0,
            "time_ms": 0.0,
            "path_length": 0
        }

    # ── Điều khiển luồng 2 giai đoạn (Visualization Flow) ────────────────────

    def update_search_step(self, visited=None, frontier=None, current=None):
        """GIAI ĐOẠN 1 (SEARCHING): Cập nhật explored và frontier.
        Pacman đứng im tại start_pos. Đồ ăn chưa bị ăn."""
        self.phase = "SEARCHING"
        if visited is not None:
            self.visited_nodes.update(visited if isinstance(visited, (set, list)) else [visited])
        if frontier is not None:
            self.frontier_nodes = set(frontier if isinstance(frontier, (set, list)) else [frontier])
        if current is not None:
            self.current_node = current

    def set_path(self, path):
        """Thiết lập đường đi tối ưu tìm được."""
        self.final_path = list(path) if path else []
        self.metrics["path_length"] = len(self.final_path)
        self.move_step_idx = 0

    def start_moving_phase(self):
        """Chuyển sang GIAI ĐOẠN 2 (MOVING): Pacman bắt đầu đi theo final_path."""
        self.phase = "MOVING"
        self.move_step_idx = 0
        self.current_node = None
        if self.final_path:
            self.pacman_pos = self.final_path[0]

    def advance_move_step(self):
        """GIAI ĐOẠN 2 (MOVING): Di chuyển Pacman 1 bước trên đường đi tối ưu.
        Tự động quay mặt Pacman và ăn đồ ăn trên đường đi."""
        if self.phase != "MOVING" or not self.final_path:
            return False
        if self.move_step_idx >= len(self.final_path):
            return False

        prev_pos = self.pacman_pos
        pos = self.final_path[self.move_step_idx]
        self.pacman_pos = pos

        # Xác định hướng nhìn của Pacman
        if prev_pos:
            dr = pos[0] - prev_pos[0]
            dc = pos[1] - prev_pos[1]
            if dc > 0:   self.pacman_direction = "RIGHT"
            elif dc < 0: self.pacman_direction = "LEFT"
            elif dr > 0: self.pacman_direction = "DOWN"
            elif dr < 0: self.pacman_direction = "UP"

        # Ăn đồ ăn tại ô đi qua
        r, c = pos
        if 0 <= r < self.map_rows and 0 <= c < len(self.raw_map[r]):
            ch = self.raw_map[r][c]
            if ch in ('.', 'o'):
                self.eaten_food.add(pos)

        # Di chuyển các Ghost hợp lệ (Random Walk tránh tường '#', '%')
        new_ghosts = []
        for gr, gc in self.ghosts_pos:
            legal_moves = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = gr + dr, gc + dc
                if 0 <= nr < self.map_rows and 0 <= nc < len(self.raw_map[nr]):
                    if self.raw_map[nr][nc] not in ('#', '%'):
                        legal_moves.append((nr, nc))
            if legal_moves:
                new_ghosts.append(random.choice(legal_moves))
            else:
                new_ghosts.append((gr, gc))
        self.ghosts_pos = new_ghosts

        self.move_step_idx += 1
        return self.move_step_idx < len(self.final_path)

    def is_moving_done(self):
        """Kiểm tra Pacman đã đi hết đường đi hay chưa."""
        return self.move_step_idx >= len(self.final_path)

    def update_pacman(self, pos):
        """Cập nhật vị trí Pacman và tự động quay mặt theo hướng di chuyển."""
        if self.pacman_pos and pos:
            dr = pos[0] - self.pacman_pos[0]
            dc = pos[1] - self.pacman_pos[1]
            if dc > 0:   self.pacman_direction = "RIGHT"
            elif dc < 0: self.pacman_direction = "LEFT"
            elif dr > 0: self.pacman_direction = "DOWN"
            elif dr < 0: self.pacman_direction = "UP"

        self.pacman_pos = pos
        if self.phase == "MOVING" and pos is not None:
            r, c = pos
            if 0 <= r < self.map_rows and 0 <= c < len(self.raw_map[r]):
                ch = self.raw_map[r][c]
                if ch in ('.', 'o'):
                    self.eaten_food.add(pos)

    def set_metrics(self, expanded=None, cost=None, time_taken=None, status=None):
        """Cập nhật các số liệu thống kê hiệu năng."""
        if expanded is not None:
            self.metrics["expanded"] = expanded
        if cost is not None:
            self.metrics["cost"] = cost
        if time_taken is not None:
            self.metrics["time_ms"] = round(time_taken, 2)
        if status is not None:
            self.metrics["status"] = status

    def is_heuristic_enabled(self):
        """Kiểm tra thuật toán hiện tại có hỗ trợ/sử dụng Heuristic hay không."""
        return self.get_selected_algorithm() in ("A* Search", "Greedy BFS")

    def get_selected_algorithm(self):
        return self.algorithms[self.selected_algo_idx]

    def get_selected_map(self):
        if 0 <= self.selected_map_idx < len(self.map_files):
            return self.map_files[self.selected_map_idx]
        return None

    def get_selected_heuristic(self):
        return self.heuristics[self.selected_heuristic_idx][0]

    def set_selected_algorithm(self, algo_name):
        key = str(algo_name).lower().replace("*", "star").replace("-", "").replace("_", "").replace(" ", "")
        for idx, a in enumerate(self.algorithms):
            a_key = a.lower().replace("*", "star").replace("-", "").replace("_", "").replace(" ", "")
            if key in a_key or a_key in key:
                self.selected_algo_idx = idx
                self.reset_search_state()
                return

    def set_selected_heuristic(self, heuristic_name):
        key = str(heuristic_name).lower()
        for idx, (h_key, _) in enumerate(self.heuristics):
            if key in h_key.lower():
                self.selected_heuristic_idx = idx
                self.reset_search_state()
                return

    def set_selected_map(self, map_path):
        normalized = map_path.replace("\\", "/")
        for idx, m in enumerate(self.map_files):
            if normalized in m or os.path.basename(normalized) == os.path.basename(m):
                self.selected_map_idx = idx
                self.load_map_file(self.map_files[idx])
                return

    # ── Xử lý Sự kiện (Events) ────────────────────────────────────────────────

    def handle_events(self):
        """Lắng nghe sự kiện Pygame, xử lý click dropdown, cuộn chuột và phím tắt."""
        action = None
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.quit_requested = True
                pygame.quit()
                sys.exit(0)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                action = self._handle_click(ev.pos) or action
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self.slider_dragging = False
            elif ev.type == pygame.MOUSEMOTION and self.slider_dragging:
                self._update_slider(ev.pos[0])
                action = {"action": "SPEED_CHANGED", "speed": self.speed}
            elif ev.type == pygame.MOUSEWHEEL:
                # Cuộn chuột khi Map Dropdown có nhiều hơn 10 bản đồ
                if self.map_dropdown_open and len(self.map_files) > 10:
                    max_scroll = len(self.map_files) - 10
                    self.map_scroll_offset = max(0, min(max_scroll, self.map_scroll_offset - ev.y))
            elif ev.type == pygame.KEYDOWN:
                action = self._handle_key(ev.key) or action
        return action

    def _handle_click(self, pos):
        """Xử lý click chuột: ưu tiên tuyệt đối cho Dropdown đang mở để chống click xuyên thấu."""
        mx, my = pos

        # ══════════════════════════════════════════════════════════════════════
        # 1. ƯU TIÊN KIỂM TRA DROPDOWN ĐANG MỞ
        # ══════════════════════════════════════════════════════════════════════

        # A. Algorithm Dropdown đang mở
        if self.algo_dropdown_open:
            if self.algo_dropdown_rect.collidepoint(mx, my):
                self.algo_dropdown_open = False
                return None
            for i, r in enumerate(self.algo_item_rects):
                if r.collidepoint(mx, my):
                    self.selected_algo_idx = i
                    self.algo_dropdown_open = False
                    self.reset_search_state()
                    return {"action": "ALGO_CHANGED", "algo": self.algorithms[i]}
            if self.map_dropdown_rect.collidepoint(mx, my):
                self.algo_dropdown_open = False
                self.map_dropdown_open = True
                return None
            if self.heuristic_dropdown_rect.collidepoint(mx, my) and self.is_heuristic_enabled():
                self.algo_dropdown_open = False
                self.heuristic_dropdown_open = True
                return None
            self.algo_dropdown_open = False
            return None

        # B. Map Dropdown đang mở
        if self.map_dropdown_open:
            if self.map_dropdown_rect.collidepoint(mx, my):
                self.map_dropdown_open = False
                return None
            visible_count = len(self.map_item_rects)
            for idx, r in enumerate(self.map_item_rects):
                if r.collidepoint(mx, my):
                    actual_map_idx = self.map_scroll_offset + idx
                    if actual_map_idx < len(self.map_files):
                        self.selected_map_idx = actual_map_idx
                        self.map_dropdown_open = False
                        self.load_map_file(self.map_files[actual_map_idx])
                        return {"action": "MAP_CHANGED", "map": self.map_files[actual_map_idx]}
            if self.algo_dropdown_rect.collidepoint(mx, my):
                self.map_dropdown_open = False
                self.algo_dropdown_open = True
                return None
            if self.heuristic_dropdown_rect.collidepoint(mx, my) and self.is_heuristic_enabled():
                self.map_dropdown_open = False
                self.heuristic_dropdown_open = True
                return None
            self.map_dropdown_open = False
            return None

        # C. Heuristic Dropdown đang mở
        if self.heuristic_dropdown_open:
            if self.heuristic_dropdown_rect.collidepoint(mx, my):
                self.heuristic_dropdown_open = False
                return None
            for i, r in enumerate(self.heuristic_item_rects):
                if r.collidepoint(mx, my):
                    self.selected_heuristic_idx = i
                    self.heuristic_dropdown_open = False
                    self.reset_search_state()
                    return {"action": "HEURISTIC_CHANGED", "heuristic": self.heuristics[i][0]}
            if self.map_dropdown_rect.collidepoint(mx, my):
                self.heuristic_dropdown_open = False
                self.map_dropdown_open = True
                return None
            if self.algo_dropdown_rect.collidepoint(mx, my):
                self.heuristic_dropdown_open = False
                self.algo_dropdown_open = True
                return None
            self.heuristic_dropdown_open = False
            return None

        # ══════════════════════════════════════════════════════════════════════
        # 2. XỬ LÝ KHI CẢ 3 DROPDOWN ĐỀU ĐANG ĐÓNG
        # ══════════════════════════════════════════════════════════════════════

        # Mở Map Dropdown
        if self.map_dropdown_rect.collidepoint(mx, my):
            self.map_dropdown_open = True
            self.algo_dropdown_open = False
            self.heuristic_dropdown_open = False
            return None

        # Mở Algorithm Dropdown
        if self.algo_dropdown_rect.collidepoint(mx, my):
            self.algo_dropdown_open = True
            self.map_dropdown_open = False
            self.heuristic_dropdown_open = False
            return None

        # Mở Heuristic Dropdown (chỉ khi thuật toán có hỗ trợ Heuristic)
        if self.heuristic_dropdown_rect.collidepoint(mx, my):
            if self.is_heuristic_enabled():
                self.heuristic_dropdown_open = True
                self.map_dropdown_open = False
                self.algo_dropdown_open = False
            return None

        # Nút Bắt đầu / Tiếp tục
        if self.btn_start.collidepoint(mx, my):
            self.is_running = True
            self.is_paused = False
            self.metrics["status"] = "Đang tìm kiếm..."
            return {
                "action": "START",
                "algo": self.get_selected_algorithm(),
                "heuristic": self.get_selected_heuristic(),
                "map": self.get_selected_map()
            }

        # Nút Tạm dừng
        if self.btn_pause.collidepoint(mx, my) and self.is_running:
            self.is_paused = not self.is_paused
            self.metrics["status"] = "Tạm dừng" if self.is_paused else "Đang chạy"
            return {"action": "PAUSE", "paused": self.is_paused}

        # Nút Từng bước
        if self.btn_step.collidepoint(mx, my):
            self.is_paused = True
            self.metrics["status"] = "Chạy từng bước"
            return {
                "action": "STEP",
                "algo": self.get_selected_algorithm(),
                "heuristic": self.get_selected_heuristic(),
                "map": self.get_selected_map()
            }

        # Nút Đặt lại
        if self.btn_reset.collidepoint(mx, my):
            self.reset_search_state()
            return {"action": "RESET"}

        # Slider kéo tốc độ
        if self.slider_track.collidepoint(mx, my):
            self.slider_dragging = True
            self._update_slider(mx)
            return {"action": "SPEED_CHANGED", "speed": self.speed}

        # Presets tốc độ (1x, 2x, 5x, Max)
        for r, val, _ in self.speed_presets:
            if r.collidepoint(mx, my):
                self.speed = val
                return {"action": "SPEED_CHANGED", "speed": self.speed}

        return None

    def _handle_key(self, key):
        """Xử lý phím tắt bàn phím."""
        # Phím ESC đóng dropdown đang mở (nếu có)
        if key == pygame.K_ESCAPE:
            if self.algo_dropdown_open or self.map_dropdown_open or self.heuristic_dropdown_open:
                self.algo_dropdown_open = False
                self.map_dropdown_open = False
                self.heuristic_dropdown_open = False
                return None
            self.quit_requested = True
            return None

        if key == pygame.K_SPACE:
            self.is_paused = not self.is_paused if self.is_running else False
            self.is_running = True
            return {"action": "START" if not self.is_paused else "PAUSE"}
        if key == pygame.K_r:
            self.reset_search_state()
            return {"action": "RESET"}
        if key == pygame.K_s:
            self.is_paused = True
            return {"action": "STEP"}
        if key == pygame.K_q:
            self.quit_requested = True
            return None
        return None

    def _update_slider(self, mx):
        ratio = (max(self.slider_track.left, min(mx, self.slider_track.right))
                 - self.slider_track.left) / self.slider_track.width
        self.speed = max(1, min(60, int(1 + ratio * 59)))

    # ══════════════════════════════════════════════════════════════════════════
    # Vẽ Bàn cờ (Board Rendering)
    # ══════════════════════════════════════════════════════════════════════════

    def draw_board(self):
        """Vẽ khu vực trò chơi: tường ('#' & '%'), đường đi, đồ ăn, explored/frontier, path và sprites."""
        self._frame_counter += 1
        pygame.draw.rect(self.screen, COLOR_BG, self.board_rect)
        cs = self.cell_size

        if self._game_state is not None:
            current_food = {(y, x) for (x, y) in self._game_state.food}
            ghost_list = [(y, x) for (x, y) in self._game_state.ghosts_pos]
        else:
            current_food = self.food_positions - self.eaten_food
            ghost_list = self.ghosts_pos

        # 1. Ô bản đồ cơ sở: Tường, sàn, tập mở/đóng, thức ăn
        for r in range(self.map_rows):
            for c in range(len(self.raw_map[r])):
                cell = self.raw_map[r][c]
                x = self.board_offset_x + c * cs
                y = self.board_offset_y + r * cs
                rect = pygame.Rect(x, y, cs, cs)

                # Tường: Hỗ trợ cả '#' và '%'
                if cell in ('#', '%'):
                    pygame.draw.rect(self.screen, COLOR_WALL, rect, border_radius=2)
                    pygame.draw.rect(self.screen, COLOR_WALL_GRID, rect, 1, border_radius=2)
                    continue

                # Sàn đường đi
                pygame.draw.rect(self.screen, COLOR_FLOOR, rect)

                # Lớp thuật toán (Explored / Frontier)
                if (r, c) in self.visited_nodes:
                    pygame.draw.rect(self.screen, COLOR_VISITED, rect)
                    pygame.draw.rect(self.screen, COLOR_VISITED_BORDER, rect, 1)
                elif (r, c) in self.frontier_nodes:
                    pygame.draw.rect(self.screen, COLOR_FRONTIER, rect)
                    pygame.draw.rect(self.screen, COLOR_FRONTIER_BORDER, rect, 1)

                # Thức ăn: Hiển thị nếu chưa bị ăn
                if (r, c) in current_food or (cell in ('.', 'o') and (r, c) not in self.eaten_food):
                    is_goal = ((r, c) == self.goal_pos)
                    if is_goal:
                        pulse = 0.8 + 0.3 * math.sin(self._frame_counter * 0.15)
                        glow_r = int(cs * 0.35 * pulse)
                        pygame.draw.circle(self.screen, (255, 215, 0), rect.center, glow_r, 1)

                    dot_radius = max(2, cs // 7 if is_goal else cs // 8)
                    pygame.draw.circle(self.screen, COLOR_FOOD, rect.center, dot_radius)

                # Điểm đích không phải thức ăn (nếu có)
                elif (r, c) == self.goal_pos and (r, c) not in ghost_list:
                    pygame.draw.circle(self.screen, COLOR_GOAL, rect.center, cs // 3, 2)
                    pygame.draw.circle(self.screen, (255, 100, 100), rect.center, max(2, cs // 8))

        # 2. Highlight node đang duyệt (SEARCHING phase): Hình thoi nhấp nháy
        if self.phase == "SEARCHING" and self.current_node is not None:
            cr, cc = self.current_node
            cx = self.board_offset_x + cc * cs + cs // 2
            cy = self.board_offset_y + cr * cs + cs // 2
            pulse = 0.7 + 0.3 * math.sin(self._frame_counter * 0.18)
            ms = int(cs * 0.35 * pulse)
            diamond = [
                (cx, cy - ms),
                (cx + ms, cy),
                (cx, cy + ms),
                (cx - ms, cy),
            ]
            pygame.draw.polygon(self.screen, COLOR_ACCENT, diamond)
            pygame.draw.polygon(self.screen, COLOR_TEXT_WHITE, diamond, 2)

        # 3. Vẽ đường đi tối ưu (Optimal Path)
        if len(self.final_path) > 1:
            if self.phase == "MOVING" and self.move_step_idx > 0:
                if self.move_step_idx > 1:
                    done_pts = [
                        (self.board_offset_x + c * cs + cs // 2,
                         self.board_offset_y + r * cs + cs // 2)
                        for r, c in self.final_path[:self.move_step_idx]
                    ]
                    lw = max(3, cs // 6)
                    pygame.draw.lines(self.screen, (30, 140, 75), False, done_pts, lw)

                remaining = self.final_path[max(0, self.move_step_idx - 1):]
                if len(remaining) > 1:
                    rem_pts = [
                        (self.board_offset_x + c * cs + cs // 2,
                         self.board_offset_y + r * cs + cs // 2)
                        for r, c in remaining
                    ]
                    lw = max(3, cs // 6)
                    pygame.draw.lines(self.screen, COLOR_PATH, False, rem_pts, lw)
            else:
                pts = [
                    (self.board_offset_x + c * cs + cs // 2,
                     self.board_offset_y + r * cs + cs // 2)
                    for r, c in self.final_path
                ]
                lw = max(3, cs // 6)
                pygame.draw.lines(self.screen, COLOR_PATH, False, pts, lw)
                for pt in pts:
                    pygame.draw.circle(self.screen, COLOR_PATH, pt, max(2, lw // 2))

        # 3b. Vẽ Vùng cảnh báo nguy hiểm quanh Ma (Hazard Zone) khi bản đồ có Ma
        if self.has_ghosts():
            for gr, gc in ghost_list:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    hr, hc = gr + dr, gc + dc
                    if 0 <= hr < self.map_rows and 0 <= hc < len(self.raw_map[hr]):
                        if self.raw_map[hr][hc] not in ('#', '%') and (hr, hc) not in ghost_list:
                            hx = self.board_offset_x + hc * cs
                            hy = self.board_offset_y + hr * cs
                            pulse = 0.5 + 0.3 * math.sin(self._frame_counter * 0.15)
                            h_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
                            h_surf.fill((255, 60, 60, int(45 * pulse)))
                            self.screen.blit(h_surf, (hx, hy))
                            pygame.draw.rect(self.screen, (255, 90, 90), pygame.Rect(hx, hy, cs, cs), 1)

        # 3c. Vẽ Quỹ đạo dự kiến ngắn hạn của Pacman (Local Planned Trajectory)
        if self.has_ghosts() and getattr(self, "planned_trajectory", None):
            traj_pts = [(self.board_offset_x + c * cs + cs // 2, self.board_offset_y + r * cs + cs // 2)
                        for r, c in [self.pacman_pos] + self.planned_trajectory if r is not None and c is not None]
            if len(traj_pts) > 1:
                pygame.draw.lines(self.screen, COLOR_ACCENT, False, traj_pts, 2)
                for pt in traj_pts[1:]:
                    pygame.draw.circle(self.screen, COLOR_ACCENT, pt, max(3, cs // 7))

        # 4. Vẽ Ghost bằng Asset Sprite (Blinky, Clyde, Inky)
        ghost_names = ["blinky", "inky", "clyde"]
        for idx, (gr, gc) in enumerate(ghost_list):
            if 0 <= gr < self.map_rows and 0 <= gc < self.map_cols:
                gx = self.board_offset_x + gc * cs + cs // 2
                gy = self.board_offset_y + gr * cs + cs // 2
                gname = ghost_names[idx % len(ghost_names)]
                sprite = self.scaled_ghosts.get(gname)

                if sprite:
                    srect = sprite.get_rect(center=(gx, gy))
                    self.screen.blit(sprite, srect)
                else:
                    grad = max(6, int(cs * 0.42))
                    col = (230, 50, 50) if gname == "blinky" else ((50, 200, 240) if gname == "inky" else (240, 140, 40))
                    pygame.draw.circle(self.screen, col, (gx, gy - 2), grad)
                    pygame.draw.rect(self.screen, col, (gx - grad, gy - 2, grad * 2, grad))
                    pygame.draw.circle(self.screen, COLOR_TEXT_WHITE, (gx - grad // 2, gy - 3), max(2, grad // 3))
                    pygame.draw.circle(self.screen, COLOR_TEXT_WHITE, (gx + grad // 2, gy - 3), max(2, grad // 3))
                    pygame.draw.circle(self.screen, (30, 30, 180), (gx - grad // 2, gy - 3), max(1, grad // 5))
                    pygame.draw.circle(self.screen, (30, 30, 180), (gx + grad // 2, gy - 3), max(1, grad // 5))

        # 5. Vẽ Pacman bằng Asset Sprite (pacman.png) với hướng xoay thực tế
        if self.pacman_pos:
            pr, pc = self.pacman_pos
            px = self.board_offset_x + pc * cs + cs // 2
            py = self.board_offset_y + pr * cs + cs // 2
            sprite = self.scaled_pacman.get(self.pacman_direction, self.scaled_pacman.get("RIGHT"))

            if sprite:
                srect = sprite.get_rect(center=(px, py))
                self.screen.blit(sprite, srect)
            else:
                rad = max(6, int(cs * 0.42))
                pygame.draw.circle(self.screen, COLOR_PACMAN, (px, py), rad)
                mouth_pts = [(px, py)]
                if self.pacman_direction == "RIGHT":
                    mouth_pts.extend([(px + rad, py - rad // 2), (px + rad, py + rad // 2)])
                elif self.pacman_direction == "LEFT":
                    mouth_pts.extend([(px - rad, py - rad // 2), (px - rad, py + rad // 2)])
                elif self.pacman_direction == "UP":
                    mouth_pts.extend([(px - rad // 2, py - rad), (px + rad // 2, py - rad)])
                else:
                    mouth_pts.extend([(px - rad // 2, py + rad), (px + rad // 2, py + rad)])
                pygame.draw.polygon(self.screen, COLOR_PACMAN_MOUTH, mouth_pts)

    # ══════════════════════════════════════════════════════════════════════════
    # Vẽ Sidebar Điều khiển & Thống kê (Panel Rendering)
    # ══════════════════════════════════════════════════════════════════════════

    def draw_panel(self):
        """Vẽ bảng điều khiển bên phải. Các Dropdown Popup BẮT BUỘC được vẽ sau cùng (Z-Index top)."""
        panel = pygame.Rect(self.panel_x, 0, self.panel_width, self.screen_height)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel)
        pygame.draw.line(self.screen, COLOR_BORDER,
                         (self.panel_x, 0), (self.panel_x, self.screen_height), 2)

        px = self.panel_x + 16
        pw = self.panel_width - 32
        mpos = pygame.mouse.get_pos()

        # Tiêu đề
        title_surf = self.font_title.render("PACMAN AI - NHÓM 13", True, COLOR_ACCENT)
        self.screen.blit(title_surf, (px, 14))
        sub_surf = self.font_small.render("Đề án Trực quan hóa Thuật toán Tìm kiếm", True, COLOR_TEXT_MUTED)
        self.screen.blit(sub_surf, (px, 36))

        # ── 1. Map Dropdown (Header đóng) ──
        self.screen.blit(self.font_bold.render("1. Chọn bản đồ:", True, COLOR_TEXT_MAIN), (px, 54))
        cur_map_name = os.path.basename(self.get_selected_map() or "None")
        self._draw_dropdown_header(
            rect=self.map_dropdown_rect,
            text=f"{cur_map_name} ({self.selected_map_idx + 1}/{len(self.map_files)})",
            is_open=self.map_dropdown_open,
            mpos=mpos,
            enabled=True
        )

        # ── 2. Algorithm Dropdown (Header đóng) ──
        self.screen.blit(self.font_bold.render("2. Thuật toán tìm kiếm:", True, COLOR_TEXT_MAIN), (px, 116))
        self._draw_dropdown_header(
            rect=self.algo_dropdown_rect,
            text=self.get_selected_algorithm(),
            is_open=self.algo_dropdown_open,
            mpos=mpos,
            enabled=True
        )

        # ── 3. Heuristic Dropdown (Header đóng) ──
        self.screen.blit(self.font_bold.render("3. Hàm Heuristic (cho A* & Greedy):", True, COLOR_TEXT_MAIN), (px, 178))
        self._draw_dropdown_header(
            rect=self.heuristic_dropdown_rect,
            text=self.get_selected_heuristic(),
            is_open=self.heuristic_dropdown_open,
            mpos=mpos,
            enabled=self.is_heuristic_enabled()
        )

        # ── 4. Điều khiển mô phỏng ──
        self.screen.blit(self.font_bold.render("4. Điều khiển mô phỏng:", True, COLOR_TEXT_MAIN), (px, 238))
        label_start = "Tiếp tục" if self.is_paused else "Bắt đầu"
        self._draw_btn(self.btn_start, label_start, COLOR_BTN_START,  mpos)
        self._draw_btn(self.btn_pause, "Tạm dừng",  COLOR_BTN_PAUSE,  mpos)
        self._draw_btn(self.btn_step,  "Từng bước", COLOR_BTN_STEP,   mpos)
        self._draw_btn(self.btn_reset, "Đặt lại",   COLOR_BTN_RESET,  mpos)

        # ── 5. Tốc độ thực thi ──
        self.screen.blit(self.font_bold.render(f"5. Tốc độ: {self.speed} bước/s", True, COLOR_TEXT_MAIN), (px, 298))
        pygame.draw.rect(self.screen, COLOR_BTN_DEFAULT, self.slider_track, border_radius=4)
        fill_w = int(((self.speed - 1) / 59) * self.slider_track.width)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.slider_track.x, self.slider_track.y, fill_w, 8)
            pygame.draw.rect(self.screen, COLOR_ACCENT, fill_rect, border_radius=4)
        knob_x = self.slider_track.x + fill_w
        pygame.draw.circle(self.screen, COLOR_TEXT_WHITE, (knob_x, self.slider_track.centery), 8)
        pygame.draw.circle(self.screen, COLOR_ACCENT, (knob_x, self.slider_track.centery), 5)

        for r, val, lbl in self.speed_presets:
            is_active = (self.speed == val)
            bg = COLOR_BTN_ACTIVE if is_active else COLOR_BTN_DEFAULT
            pygame.draw.rect(self.screen, bg, r, border_radius=3)
            if is_active:
                pygame.draw.rect(self.screen, COLOR_ACCENT, r, 1, border_radius=3)
            t_col = COLOR_TEXT_WHITE if is_active else COLOR_TEXT_MUTED
            t = self.font_small.render(lbl, True, t_col)
            self.screen.blit(t, t.get_rect(center=r.center))

        # ── 6. Metrics ──
        self._draw_metrics(px, pw)

        # ── 7. Legend & Shortcuts ──
        self._draw_legend(px)

        # ══════════════════════════════════════════════════════════════════════
        # 8. VẼ DROPDOWN POPUP SAU CÙNG (LAYER RENDERING / Z-INDEX TOPMOST)
        # ══════════════════════════════════════════════════════════════════════
        # Danh sách thả xuống BẮT BUỘC được vẽ đè lên trên cùng để không bị các nút bên dưới che
        if self.map_dropdown_open:
            self._draw_map_dropdown_popup(mpos)
        elif self.algo_dropdown_open:
            self._draw_algo_dropdown_popup(mpos)
        elif self.heuristic_dropdown_open and self.is_heuristic_enabled():
            self._draw_heuristic_dropdown_popup(mpos)

    # ── Vẽ Hộp chọn Dropdown (Header & Popup) ─────────────────────────────────

    def _draw_dropdown_header(self, rect, text, is_open, mpos, enabled=True):
        """Vẽ hộp chọn chính của Dropdown kèm mũi tên chỉ hướng (▲ / ▼)."""
        is_hover = rect.collidepoint(mpos) and enabled
        if not enabled:
            bg = (24, 30, 44)
            border_col = (45, 52, 70)
            text_col = COLOR_TEXT_MUTED
        elif is_open:
            bg = (45, 58, 92)
            border_col = COLOR_ACCENT
            text_col = COLOR_TEXT_WHITE
        elif is_hover:
            bg = COLOR_BTN_HOVER
            border_col = COLOR_ACCENT
            text_col = COLOR_TEXT_WHITE
        else:
            bg = COLOR_BTN_DEFAULT
            border_col = COLOR_BORDER
            text_col = COLOR_TEXT_WHITE

        pygame.draw.rect(self.screen, bg, rect, border_radius=5)
        pygame.draw.rect(self.screen, border_col, rect, 1, border_radius=5)

        # Nhãn text của giá trị đang chọn
        disp_text = text if enabled else f"{text} (Không áp dụng)"
        t_surf = self.font_bold.render(disp_text, True, text_col)
        self.screen.blit(t_surf, (rect.x + 12, rect.centery - t_surf.get_height() // 2))

        # Biểu tượng mũi tên tam giác vẽ sắc nét bằng polygon (chỉ vẽ khi enabled)
        if enabled:
            arrow_cx = rect.right - 18
            arrow_cy = rect.centery
            arrow_col = COLOR_ACCENT if (is_open or is_hover) else COLOR_TEXT_MUTED
            if is_open:
                arrow_pts = [
                    (arrow_cx - 5, arrow_cy + 3),
                    (arrow_cx + 5, arrow_cy + 3),
                    (arrow_cx,     arrow_cy - 3),
                ]
            else:
                arrow_pts = [
                    (arrow_cx - 5, arrow_cy - 3),
                    (arrow_cx + 5, arrow_cy - 3),
                    (arrow_cx,     arrow_cy + 3),
                ]
            pygame.draw.polygon(self.screen, arrow_col, arrow_pts)

    def _draw_algo_dropdown_popup(self, mpos):
        """Vẽ popup danh sách mở rộng của Algorithm Dropdown."""
        total_h = len(self.algorithms) * 28
        popup_rect = pygame.Rect(self.algo_dropdown_rect.x, self.algo_dropdown_rect.bottom + 2,
                                 self.algo_dropdown_rect.width, total_h)

        pygame.draw.rect(self.screen, COLOR_DROPDOWN_POPUP, popup_rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_ACCENT, popup_rect, 2, border_radius=6)

        for i, (algo_name, r) in enumerate(zip(self.algorithms, self.algo_item_rects)):
            is_selected = (i == self.selected_algo_idx)
            is_hover = r.collidepoint(mpos)

            if is_selected:
                pygame.draw.rect(self.screen, (35, 60, 95), r)
                pygame.draw.circle(self.screen, COLOR_ACCENT, (r.x + 14, r.centery), 4)
                t_surf = self.font_bold.render(algo_name, True, COLOR_ACCENT)
            elif is_hover:
                pygame.draw.rect(self.screen, COLOR_BTN_HOVER, r)
                t_surf = self.font_bold.render(algo_name, True, COLOR_TEXT_WHITE)
            else:
                t_surf = self.font_main.render(algo_name, True, COLOR_TEXT_MUTED)

            self.screen.blit(t_surf, (r.x + 28, r.centery - t_surf.get_height() // 2))

            if i < len(self.algorithms) - 1:
                pygame.draw.line(self.screen, COLOR_DIVIDER, (r.left + 8, r.bottom), (r.right - 8, r.bottom), 1)

    def _draw_map_dropdown_popup(self, mpos):
        """Vẽ popup danh sách mở rộng của Map Dropdown kèm thanh cuộn (scrollbar)."""
        item_h = 28
        visible_count = len(self.map_item_rects)
        total_h = visible_count * item_h
        popup_rect = pygame.Rect(self.map_dropdown_rect.x, self.map_dropdown_rect.bottom + 2,
                                 self.map_dropdown_rect.width, total_h)

        pygame.draw.rect(self.screen, COLOR_DROPDOWN_POPUP, popup_rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_ACCENT, popup_rect, 2, border_radius=6)

        for idx, r in enumerate(self.map_item_rects):
            map_idx = self.map_scroll_offset + idx
            if map_idx >= len(self.map_files):
                break
            mpath = self.map_files[map_idx]
            is_selected = (map_idx == self.selected_map_idx)
            is_hover = r.collidepoint(mpos)
            name = os.path.basename(mpath)

            if is_selected:
                pygame.draw.rect(self.screen, (35, 60, 95), r)
                pygame.draw.circle(self.screen, COLOR_ACCENT, (r.x + 14, r.centery), 4)
                t_surf = self.font_bold.render(name, True, COLOR_ACCENT)
            elif is_hover:
                pygame.draw.rect(self.screen, COLOR_BTN_HOVER, r)
                t_surf = self.font_bold.render(name, True, COLOR_TEXT_WHITE)
            else:
                t_surf = self.font_main.render(name, True, COLOR_TEXT_MUTED)

            self.screen.blit(t_surf, (r.x + 28, r.centery - t_surf.get_height() // 2))

            if idx < visible_count - 1:
                pygame.draw.line(self.screen, COLOR_DIVIDER, (r.left + 8, r.bottom), (r.right - 8, r.bottom), 1)

        # Thanh cuộn mỏng (scrollbar) nếu số bản đồ vượt quá hiển thị
        if len(self.map_files) > visible_count:
            sb_w = 4
            sb_x = popup_rect.right - sb_w - 4
            sb_h = max(20, int((visible_count / len(self.map_files)) * total_h))
            sb_max_y = total_h - sb_h
            sb_y = popup_rect.y + int((self.map_scroll_offset / (len(self.map_files) - visible_count)) * sb_max_y)
            pygame.draw.rect(self.screen, COLOR_ACCENT, pygame.Rect(sb_x, sb_y, sb_w, sb_h), border_radius=2)

    def _draw_heuristic_dropdown_popup(self, mpos):
        """Vẽ popup danh sách mở rộng của Heuristic Dropdown."""
        item_h = 28
        total_h = len(self.heuristics) * item_h
        popup_rect = pygame.Rect(self.heuristic_dropdown_rect.x, self.heuristic_dropdown_rect.bottom + 2,
                                 self.heuristic_dropdown_rect.width, total_h)

        pygame.draw.rect(self.screen, COLOR_DROPDOWN_POPUP, popup_rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_ACCENT, popup_rect, 2, border_radius=6)

        for i, ((h_code, h_name), r) in enumerate(zip(self.heuristics, self.heuristic_item_rects)):
            is_selected = (i == self.selected_heuristic_idx)
            is_hover = r.collidepoint(mpos)

            if is_selected:
                pygame.draw.rect(self.screen, (35, 60, 95), r)
                pygame.draw.circle(self.screen, COLOR_ACCENT, (r.x + 14, r.centery), 4)
                t_surf = self.font_bold.render(h_name, True, COLOR_ACCENT)
            elif is_hover:
                pygame.draw.rect(self.screen, COLOR_BTN_HOVER, r)
                t_surf = self.font_bold.render(h_name, True, COLOR_TEXT_WHITE)
            else:
                t_surf = self.font_main.render(h_name, True, COLOR_TEXT_MUTED)

            self.screen.blit(t_surf, (r.x + 28, r.centery - t_surf.get_height() // 2))

            if i < len(self.heuristics) - 1:
                pygame.draw.line(self.screen, COLOR_DIVIDER, (r.left + 8, r.bottom), (r.right - 8, r.bottom), 1)

    # ── Vẽ Thống kê & Chú thích ───────────────────────────────────────────────

    def _draw_metrics(self, px, pw):
        """Vẽ thẻ thống kê hiệu năng (Metrics Card)."""
        y = 368
        self.screen.blit(self.font_bold.render("6. Thống kê hiệu năng (Metrics):", True, COLOR_TEXT_MAIN), (px, y))
        card = pygame.Rect(px, y + 20, pw, 185)
        pygame.draw.rect(self.screen, COLOR_CARD_BG, card, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_BORDER, card, 1, border_radius=6)

        st = str(self.metrics["status"])
        if "Hoàn thành" in st or "Tìm thấy" in st or "CHIẾN THẮNG" in st:
            status_color = COLOR_PATH
        elif "Đang" in st or "Lượt" in st:
            status_color = (243, 156, 18)
        elif "Tạm dừng" in st:
            status_color = COLOR_BTN_PAUSE
        elif "GAME OVER" in st or "Không tìm thấy" in st or "THUA" in st:
            status_color = (230, 57, 70)
        else:
            status_color = COLOR_TEXT_MAIN

        if self.is_heuristic_enabled():
            algo_disp = f"{self.get_selected_algorithm()} ({self.get_selected_heuristic()})"
        else:
            algo_disp = self.get_selected_algorithm()

        map_disp = os.path.basename(self.get_selected_map() or "None")

        cost_title = "Điểm số (Score):" if self.has_ghosts() else "Chi phí đường đi (Cost):"
        steps_title = "Số lượt đã đi (Turns):" if self.has_ghosts() else "Độ dài đường đi (Steps):"

        items = [
            ("Trạng thái:",              st,                                status_color),
            ("Bản đồ:",                  map_disp,                          COLOR_TEXT_WHITE),
            ("Thuật toán:",              algo_disp,                         COLOR_ACCENT),
            ("Số nút duyệt (Expanded):", str(self.metrics["expanded"]),    (255, 221, 0)),
            (cost_title,                 str(self.metrics["cost"]),        COLOR_FOOD),
            (steps_title,                str(self.metrics["path_length"]), COLOR_PATH),
            ("Thời gian tính toán:",     f"{self.metrics['time_ms']} ms",  COLOR_TEXT_MUTED),
        ]

        ry = card.y + 10
        for lbl, val, c in items:
            lbl_surf = self.font_main.render(lbl, True, COLOR_TEXT_MUTED)
            self.screen.blit(lbl_surf, (card.x + 10, ry))
            val_surf = self.font_bold.render(val, True, c)
            self.screen.blit(val_surf, (card.right - val_surf.get_width() - 10, ry))
            ry += 24

    def _draw_legend(self, px):
        """Vẽ chú thích màu sắc và thực thể (Legend)."""
        y = 585
        self.screen.blit(self.font_bold.render("7. Chú thích màu sắc (Legend):", True, COLOR_TEXT_MAIN), (px, y))

        legends = [
            (COLOR_VISITED,  "Đã duyệt"),
            (COLOR_FRONTIER, "Hàng đợi"),
            (COLOR_PATH,     "Đường đi"),
            (COLOR_PACMAN,   "Pacman"),
            (COLOR_GOAL,     "Ghost / Đích"),
        ]
        lx = px
        for col, desc in legends:
            pygame.draw.rect(self.screen, col, (lx, y + 24, 12, 12), border_radius=2)
            pygame.draw.rect(self.screen, COLOR_TEXT_WHITE, (lx, y + 24, 12, 12), 1, border_radius=2)
            self.screen.blit(self.font_small.render(desc, True, COLOR_TEXT_MUTED), (lx + 18, y + 23))
            lx += 68

        shortcut_text = "Phím tắt: [Space] Chạy/Dừng | [S] Bước | [R] Đặt lại | [Esc] Đóng Dropdown"
        self.screen.blit(self.font_small.render(shortcut_text, True, (100, 110, 130)), (px, self.screen_height - 24))

    def _draw_btn(self, rect, text, color, mpos):
        """Vẽ nút bấm kèm hiệu ứng hover."""
        if rect.collidepoint(mpos):
            c = tuple(min(255, v + 25) for v in color)
        else:
            c = color
        pygame.draw.rect(self.screen, c, rect, border_radius=5)
        t = self.font_bold.render(text, True, COLOR_TEXT_WHITE)
        self.screen.blit(t, t.get_rect(center=rect.center))

    # ── Render Tổng hợp & Tương thích GameLoop ───────────────────────────────

    def render(self, game_state=None):
        """Vẽ lại toàn bộ khung hình.
        Hỗ trợ cả luồng GameLoop (nhận game_state) và luồng Standalone (game_state=None)."""
        if game_state is not None:
            self._game_state = game_state

            # Đồng bộ kích thước bản đồ nếu có thay đổi
            if self.map_rows != game_state.height or self.map_cols != game_state.width:
                self.map_rows = game_state.height
                self.map_cols = game_state.width

                # Tạo ma trận raw_map từ GameState
                self.raw_map = [[' ' for _ in range(self.map_cols)] for _ in range(self.map_rows)]
                for (wx, wy) in game_state.walls:
                    if 0 <= wy < self.map_rows and 0 <= wx < self.map_cols:
                        self.raw_map[wy][wx] = '#'

                # Căn giữa bàn cờ
                if self.map_cols > 0 and self.map_rows > 0:
                    aw = self.board_rect.width - 40
                    ah = self.board_rect.height - 40
                    self.cell_size = max(12, min(45, aw // self.map_cols, ah // self.map_rows))
                    self.board_offset_x = (self.board_rect.width  - self.map_cols * self.cell_size) // 2
                    self.board_offset_y = (self.board_rect.height - self.map_rows * self.cell_size) // 2
                    self._update_scaled_sprites()

            # Đồng bộ vị trí Pacman và xác định hướng xoay
            if game_state.pacman_pos:
                new_pos = (game_state.pacman_pos[1], game_state.pacman_pos[0])
                if self.pacman_pos:
                    dr = new_pos[0] - self.pacman_pos[0]
                    dc = new_pos[1] - self.pacman_pos[1]
                    if dc > 0:   self.pacman_direction = "RIGHT"
                    elif dc < 0: self.pacman_direction = "LEFT"
                    elif dr > 0: self.pacman_direction = "DOWN"
                    elif dr < 0: self.pacman_direction = "UP"
                self.pacman_pos = new_pos

            # Đồng bộ trạng thái kết thúc
            self.turn += 1
            self.metrics["cost"] = game_state.score
            self.metrics["expanded"] = len(game_state.food)

            if game_state.is_game_over:
                if game_state.win:
                    self.metrics["status"] = "CHIẾN THẮNG!"
                elif game_state.lose:
                    self.metrics["status"] = "GAME OVER (Bị bắt)!"
                else:
                    self.metrics["status"] = f"Kết thúc: {game_state.end_reason}"
            else:
                self.metrics["status"] = f"Lượt {self.turn} | Điểm: {game_state.score}"

            # Vẽ khung hình
            self.draw_board()
            self.draw_panel()
            pygame.display.flip()

            # Xử lý sự kiện và độ trễ ở chế độ GameLoop
            self._handle_gameloop_interaction(game_state)
            return

        # Luồng gọi thông thường không đối số
        self.draw_board()
        self.draw_panel()
        pygame.display.flip()

    def _handle_gameloop_interaction(self, state):
        """Xử lý sự kiện bàn phím/chuột khi chạy trong vòng lặp GameLoop."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_requested = True
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    self.quit_requested = True
                elif event.key == pygame.K_SPACE:
                    self.step_mode = not self.step_mode
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    self.delay = max(0.01, self.delay / 1.5)
                elif event.key == pygame.K_MINUS:
                    self.delay = min(2.0, self.delay * 1.5)

        if self.step_mode and not state.is_game_over:
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit_requested = True
                        pygame.quit()
                        sys.exit(0)
                    elif event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_n):
                            waiting = False
                        elif event.key == pygame.K_a:
                            self.step_mode = False
                            waiting = False
                        elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                            self.quit_requested = True
                            waiting = False
                self.clock.tick(30)
        else:
            time.sleep(self.delay)

    def show_metrics(self, metrics):
        """Hiển thị số liệu thống kê chi tiết từ thuật toán lên màn hình (Modal Dialog)."""
        if not metrics:
            return

        # Cập nhật các chỉ số chính
        if "expanded_nodes" in metrics:
            self.metrics["expanded"] = metrics["expanded_nodes"]
        elif "expanded" in metrics:
            self.metrics["expanded"] = metrics["expanded"]

        if "path_cost" in metrics:
            self.metrics["cost"] = metrics["path_cost"]
        elif "cost" in metrics:
            self.metrics["cost"] = metrics["cost"]

        if "plan_length" in metrics:
            self.metrics["path_length"] = metrics["plan_length"]

        search_time = metrics.get("search_time", metrics.get("total_time", metrics.get("time_taken", 0)))
        if search_time:
            self.metrics["time_ms"] = round(search_time * 1000, 2) if search_time < 50 else round(search_time, 2)

        if metrics.get("found", True):
            self.metrics["status"] = "Hoàn thành! Tìm thấy giải pháp."
        else:
            self.metrics["status"] = "Vô nghiệm (Không có đường đi)!"

        # Vẽ lại background board và panel
        self.draw_board()
        self.draw_panel()

        # Modal Overlay làm mờ nền
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((10, 14, 25, 215))
        self.screen.blit(overlay, (0, 0))

        # Khung thẻ kết quả ở giữa màn hình
        box_w, box_h = 520, 360
        box_x = (self.screen_width - box_w) // 2
        box_y = (self.screen_height - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(self.screen, COLOR_CARD_BG, box_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_ACCENT, box_rect, 2, border_radius=10)

        # Tiêu đề kết quả
        t_surf = self.font_title.render("=== KẾT QUẢ TÌM KIẾM AI ===", True, COLOR_ACCENT)
        self.screen.blit(t_surf, t_surf.get_rect(center=(box_x + box_w // 2, box_y + 35)))

        # Danh sách các chỉ số
        label_map = {
            "algorithm":        "Thuật toán",
            "heuristic":        "Hàm Heuristic",
            "found":            "Tìm thấy đường đi",
            "path_cost":        "Chi phí đường đi (Cost)",
            "plan_length":      "Độ dài đường đi (Steps)",
            "expanded_nodes":   "Số node đã mở rộng",
            "generated_nodes":  "Số node đã sinh",
            "max_frontier":     "Tập biên cực đại (Frontier)",
            "search_time":      "Thời gian tìm kiếm",
            "preprocess_time":  "Thời gian tiền xử lý",
            "total_time":       "Tổng thời gian"
        }

        cur_y = box_y + 70
        count = 0
        for k, v in metrics.items():
            if count >= 9:
                break
            lbl = label_map.get(k, str(k))
            if isinstance(v, float):
                val_str = f"{v:.6f} s" if "time" in k else f"{v:.2f}"
            else:
                val_str = str(v)

            l_surf = self.font_main.render(lbl + ":", True, COLOR_TEXT_MUTED)
            v_surf = self.font_bold.render(val_str, True, COLOR_TEXT_WHITE)
            self.screen.blit(l_surf, (box_x + 30, cur_y))
            self.screen.blit(v_surf, (box_x + box_w - v_surf.get_width() - 30, cur_y))
            cur_y += 24
            count += 1

        hint_surf = self.font_small.render("Nhan phim bat ky hoac click chuot de dong...", True, COLOR_ACCENT)
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(box_x + box_w // 2, box_y + box_h - 25)))
        pygame.display.flip()

        if os.environ.get("SDL_VIDEODRIVER") == "dummy":
            return

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False
            self.clock.tick(30)

    def tick(self, fps=None):
        """Khống chế tốc độ vòng lặp game."""
        self.clock.tick(fps if fps is not None else self.speed)


# Alias tương thích ngược tuyệt đối với main.py và các module khác
GUI_UI = PacmanUI


# ══════════════════════════════════════════════════════════════════════════════
# LOGIC RA QUYẾT ĐỊNH ĐỘNG & VÒNG LẶP THEO LƯỢT (KHI BẢN ĐỒ CÓ MA)
# ══════════════════════════════════════════════════════════════════════════════

def _compute_dynamic_pacman_move(ui, algo, heuristic):
    """
    Tính toán nước đi tiếp theo (duy nhất 1 ô) cho Pacman khi bản đồ có Ma:
    - Minimax / Alpha-Beta: Sử dụng cây trò chơi đối kháng với độ sâu giới hạn,
      đánh giá khoảng cách mồi và né tránh Ma.
    - Search động (A* Search, Greedy BFS, BFS, UCS, DFS):
      Coi vị trí các con Ma và vùng nguy hiểm lân cận (bán kính 1-2 ô) là chướng ngại
      vật hoặc chi phí phạt rất cao, chỉ lấy bước đầu tiên của lộ trình an toàn nhất.
    Trả về: (next_pos, planned_trajectory, expanded_nodes)
    """
    pr, pc = ui.pacman_pos
    rows, cols = ui.map_rows, ui.map_cols
    ghost_set = set(ui.ghosts_pos)
    remaining_food = ui.food_positions - ui.eaten_food

    # Danh sách các ô đi hợp lệ xung quanh Pacman (không đâm tường '#', '%')
    legal_neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = pr + dr, pc + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            if ui.raw_map[nr][nc] not in ('#', '%'):
                legal_neighbors.append((nr, nc))

    if not legal_neighbors:
        return (pr, pc), [], 0

    # ──────────────────────────────────────────────────────────────────────────
    # NHÁNH 1: THUẬT TOÁN ĐỐI KHÁNG (MINIMAX / ALPHA-BETA)
    # ──────────────────────────────────────────────────────────────────────────
    if algo in ("Minimax", "Alpha-Beta"):
        try:
            from src.engine import GameState
            from src.agents import MinimaxAgent, AlphaBetaAgent

            s = GameState()
            s.width = cols
            s.height = rows
            s.walls = set()
            for r in range(rows):
                for c in range(len(ui.raw_map[r])):
                    if ui.raw_map[r][c] in ('#', '%'):
                        s.walls.add((c, r))
            s.pacman_pos = (pc, pr)  # (col, row)
            s.ghosts_pos = [(gc, gr) for gr, gc in ui.ghosts_pos]
            s.food = {(fc, fr) for fr, fc in remaining_food}
            s.score = getattr(ui, "game_score", 0)

            depth = 3 if algo == "Alpha-Beta" else 2
            agent = AlphaBetaAgent(depth=depth) if algo == "Alpha-Beta" else MinimaxAgent(depth=depth)
            action = agent.get_action(s)

            dir_map = {
                'UP': (-1, 0),
                'DOWN': (1, 0),
                'LEFT': (0, -1),
                'RIGHT': (0, 1),
                'STOP': (0, 0)
            }
            dr, dc = dir_map.get(action, (0, 0))
            cand = (pr + dr, pc + dc)
            if cand in legal_neighbors:
                return cand, [cand], getattr(agent, "expanded_nodes", 0)
        except Exception:
            pass  # Fallback sang dynamic search an toàn bên dưới nếu có ngoại lệ

    # ──────────────────────────────────────────────────────────────────────────
    # NHÁNH 2: SEARCH ĐỘNG (A* / GREEDY / BFS / UCS / DFS RE-PLANNING)
    # ──────────────────────────────────────────────────────────────────────────
    # Xây dựng các vùng nguy hiểm (Hazard Zones):
    # - Vùng nguy hiểm cấp 1: Bán kính 1 ô xung quanh Ma
    hazard_1 = set()
    for gr, gc in ui.ghosts_pos:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            hr, hc = gr + dr, gc + dc
            if 0 <= hr < rows and 0 <= hc < cols and ui.raw_map[hr][hc] not in ('#', '%'):
                hazard_1.add((hr, hc))

    # - Vùng nguy hiểm cấp 2: Bán kính 2 ô xung quanh Ma
    hazard_2 = set()
    for gr, gc in ui.ghosts_pos:
        for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            hr, hc = gr + dr, gc + dc
            if 0 <= hr < rows and 0 <= hc < cols and ui.raw_map[hr][hc] not in ('#', '%'):
                hazard_2.add((hr, hc))

    def manhattan(p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def calc_h(p):
        if not remaining_food:
            return 0
        if heuristic == "Euclidean":
            return min(math.hypot(p[0] - f[0], p[1] - f[1]) for f in remaining_food)
        elif heuristic == "Null":
            return 0
        return min(manhattan(p, f) for f in remaining_food)

    def search_path(blocked_set, penalty_map):
        expanded = 0
        if not remaining_food:
            return [], expanded

        pq = []
        counter = 0
        start_pos = (pr, pc)
        visited_costs = {start_pos: 0}

        init_h = calc_h(start_pos) if algo in ("A* Search", "Greedy BFS") else 0
        heapq.heappush(pq, (init_h, counter, 0, start_pos, [start_pos]))

        while pq:
            prio, _, cur_cost, curr, path = heapq.heappop(pq)
            expanded += 1

            if curr in remaining_food:
                return path, expanded

            if expanded > 1000:
                break

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = curr[0] + dr, curr[1] + dc
                nxt = (nr, nc)
                if 0 <= nr < rows and 0 <= nc < cols:
                    if ui.raw_map[nr][nc] in ('#', '%') or nxt in blocked_set:
                        continue

                    step_cost = 1 + penalty_map.get(nxt, 0)
                    new_cost = cur_cost + step_cost
                    if nxt not in visited_costs or new_cost < visited_costs[nxt]:
                        visited_costs[nxt] = new_cost
                        counter += 1
                        h_val = calc_h(nxt) if algo in ("A* Search", "Greedy BFS") else 0
                        if algo == "A* Search":
                            priority = new_cost + h_val
                        elif algo == "Greedy BFS":
                            priority = h_val + penalty_map.get(nxt, 0)
                        elif algo == "UCS":
                            priority = new_cost
                        else:  # BFS / DFS
                            priority = len(path) if algo == "BFS" else -len(path)
                        heapq.heappush(pq, (priority, counter, new_cost, nxt, path + [nxt]))

        return [], expanded

    # Cấp 1: Né triệt để Ma và vùng bán kính 1 ô
    path_safe, exp_nodes = search_path(blocked_set=(ghost_set | hazard_1), penalty_map={})
    if len(path_safe) > 1:
        return path_safe[1], path_safe[1:6], exp_nodes

    # Cấp 2: Chỉ Ma là chướng ngại vật; Hazard 1 bị phạt +45, Hazard 2 bị phạt +15
    penalties = {}
    for h in hazard_1:
        penalties[h] = 45
    for h in hazard_2:
        penalties[h] = 15
    path_cautious, exp2 = search_path(blocked_set=ghost_set, penalty_map=penalties)
    if len(path_cautious) > 1:
        return path_cautious[1], path_cautious[1:6], exp_nodes + exp2

    # Cấp 3: Chế độ sinh tồn (Flee Mode) - Chủ động chọn ô cách xa Ma nhất
    best_neighbor = None
    best_score = -float('inf')
    for nr, nc in legal_neighbors:
        if (nr, nc) in ghost_set:
            continue
        min_g_dist = min(manhattan((nr, nc), g) for g in ui.ghosts_pos) if ui.ghosts_pos else 99
        score = min_g_dist * 20 + (5 if (nr, nc) in remaining_food else 0)
        if score > best_score:
            best_score = score
            best_neighbor = (nr, nc)

    if best_neighbor:
        return best_neighbor, [best_neighbor], exp_nodes + exp2

    return (pr, pc), [], exp_nodes


def _move_ghosts(ui):
    """
    Di chuyển từng con Ma 1 ô:
    - 75% xác suất: Chaser AI (đi ô thu hẹp khoảng cách tới Pacman nhiều nhất)
    - 25% xác suất: Tuần tra ngẫu nhiên (tạo cơ hội cho Pacman luồn lách)
    """
    new_ghosts = []
    pr, pc = ui.pacman_pos
    rows, cols = ui.map_rows, ui.map_cols

    for gr, gc in ui.ghosts_pos:
        legal_moves = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = gr + dr, gc + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if ui.raw_map[nr][nc] not in ('#', '%'):
                    legal_moves.append((nr, nc))

        if not legal_moves:
            new_ghosts.append((gr, gc))
            continue

        if random.random() < 0.25:
            new_ghosts.append(random.choice(legal_moves))
        else:
            best_dist = float('inf')
            best_moves = []
            for mr, mc in legal_moves:
                d = abs(mr - pr) + abs(mc - pc)
                if d < best_dist:
                    best_dist = d
                    best_moves = [(mr, mc)]
                elif d == best_dist:
                    best_moves.append((mr, mc))
            new_ghosts.append(random.choice(best_moves))

    return new_ghosts


def _execute_turn(ui, algo, heuristic):
    """
    Thực hiện 1 lượt chơi hoàn chỉnh trong chế độ Turn-by-Turn:
    1. Pacman tính toán quyết định và đi 1 ô
    2. Kiểm tra va chạm lượt Pacman & ăn thức ăn
    3. Các con Ma lần lượt đi 1 ô
    4. Kiểm tra va chạm lượt Ma
    5. Cập nhật điểm số, cảnh báo thời gian thực và thống kê
    """
    if ui.is_game_over:
        ui.is_running = False
        return

    prev_pacman = ui.pacman_pos
    prev_ghosts = list(ui.ghosts_pos)

    # 1. Pacman ra quyết định và đi 1 ô
    t0 = time.time()
    next_pos, trajectory, expanded = _compute_dynamic_pacman_move(ui, algo, heuristic)
    decision_time_ms = (time.time() - t0) * 1000

    ui.update_pacman(next_pos)
    ui.planned_trajectory = trajectory
    ui.turn += 1
    ui.game_score -= 1  # Mỗi bước đi -1 điểm

    # Kiểm tra ăn thức ăn
    if next_pos in (ui.food_positions - ui.eaten_food):
        ui.eaten_food.add(next_pos)
        ui.game_score += 10  # Ăn mồi +10 điểm

    # 2. Kiểm tra va chạm sau khi Pacman đi
    if next_pos in prev_ghosts:
        ui.is_game_over = True
        ui.is_running = False
        ui.metrics["status"] = "GAME OVER! Pacman đâm trúng Ma!"
        ui.set_metrics(expanded=expanded, cost=ui.game_score, time_taken=decision_time_ms)
        ui.metrics["path_length"] = ui.turn
        return

    # 3. Lượt Ma di chuyển
    new_ghosts = _move_ghosts(ui)
    ui.ghosts_pos = new_ghosts

    # 4. Kiểm tra va chạm sau khi Ma đi
    # A. Ma đi vào vị trí Pacman
    if ui.pacman_pos in new_ghosts:
        ui.is_game_over = True
        ui.is_running = False
        ui.metrics["status"] = "GAME OVER! Ma đã bắt được Pacman!"
        ui.set_metrics(expanded=expanded, cost=ui.game_score, time_taken=decision_time_ms)
        ui.metrics["path_length"] = ui.turn
        return

    # B. Va chạm đối đầu (crossover / swap vị trí cùng lượt)
    for pg, ng in zip(prev_ghosts, new_ghosts):
        if prev_pacman == ng and next_pos == pg:
            ui.is_game_over = True
            ui.is_running = False
            ui.metrics["status"] = "GAME OVER! Bị Ma bắt (Va chạm đối đầu)!"
            ui.set_metrics(expanded=expanded, cost=ui.game_score, time_taken=decision_time_ms)
            ui.metrics["path_length"] = ui.turn
            return

    # 5. Kiểm tra điều kiện thắng
    if ui.food_positions and len(ui.eaten_food) == len(ui.food_positions):
        ui.is_game_over = True
        ui.is_running = False
        ui.game_score += 500  # Bonus chiến thắng
        ui.metrics["status"] = f"CHIẾN THẮNG! Đã ăn hết {len(ui.food_positions)} thức ăn và né thoát Ma!"
        ui.set_metrics(expanded=expanded, cost=ui.game_score, time_taken=decision_time_ms)
        ui.metrics["path_length"] = ui.turn
        return

    # 6. Cập nhật cảnh báo trạng thái thời gian thực
    min_g_dist = min((abs(ui.pacman_pos[0] - gr) + abs(ui.pacman_pos[1] - gc) for gr, gc in ui.ghosts_pos), default=99)
    if min_g_dist <= 2:
        status_msg = f"CẢNH BÁO: Ma đang áp sát (khoảng cách {min_g_dist} ô)! Đang né tránh..."
    else:
        eaten_cnt = len(ui.eaten_food)
        total_food = len(ui.food_positions)
        status_msg = f"Lượt {ui.turn}: Đang tìm mồi (Đã ăn {eaten_cnt}/{total_food})"

    ui.set_metrics(
        expanded=expanded,
        cost=ui.game_score,
        time_taken=decision_time_ms,
        status=status_msg
    )
    ui.metrics["path_length"] = ui.turn


# ══════════════════════════════════════════════════════════════════════════════
# Ứng dụng GUI Tương tác – Khởi chạy trực tiếp từ main.py hoặc ui/g_ui.py
# ══════════════════════════════════════════════════════════════════════════════

def run_gui_app(initial_map=None, initial_algo=None, initial_heuristic=None):
    """Khởi chạy ứng dụng đồ họa Pacman AI GUI (Pygame).
    Cho phép điều khiển tương tác trực tiếp qua hệ thống Dropdown Menu trên giao diện:
    - Chọn bản đồ từ dropdown (quét động maps/)
    - Chọn thuật toán tìm kiếm (A*, BFS, DFS, UCS, Greedy, Minimax, Alpha-Beta)
    - Chọn Heuristic (MST, Manhattan, Euclidean, Maze, Null)
    - Tự động chuyển đổi giữa chế độ Tìm kiếm tĩnh (không có Ma) và Đối kháng theo lượt (có Ma).
    """
    print("=== Pacman AI Visualization GUI - Nhom 13 ===")
    ui = PacmanUI(width=1080, height=720)

    # Nạp cấu hình ban đầu nếu được truyền (không khóa, người dùng có thể đổi bất kỳ lúc nào qua Dropdown)
    if initial_map:
        ui.set_selected_map(initial_map)
    if initial_algo:
        ui.set_selected_algorithm(initial_algo)
    if initial_heuristic:
        ui.set_selected_heuristic(initial_heuristic)

    search_steps = []
    demo_path = []
    search_step_idx = 0
    search_time_ms = 0.0

    def calc_dist(p1, p2, h_type):
        if h_type == "Manhattan":
            return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
        elif h_type == "Euclidean":
            return math.hypot(p1[0] - p2[0], p1[1] - p2[1])
        elif h_type == "Null":
            return 0
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def calc_mst_weight(pts):
        if len(pts) <= 1:
            return 0
        if len(pts) > 15:
            min_r = min(p[0] for p in pts)
            max_r = max(p[0] for p in pts)
            min_c = min(p[1] for p in pts)
            max_c = max(p[1] for p in pts)
            return (max_r - min_r) + (max_c - min_c) + len(pts) - 1

        visited = [False] * len(pts)
        min_dist = [float('inf')] * len(pts)
        min_dist[0] = 0
        total_w = 0

        for _ in range(len(pts)):
            u = -1
            best_d = float('inf')
            for i in range(len(pts)):
                if not visited[i] and min_dist[i] < best_d:
                    best_d = min_dist[i]
                    u = i
            if u == -1:
                break
            visited[u] = True
            total_w += best_d
            for v in range(len(pts)):
                if not visited[v]:
                    d = abs(pts[u][0] - pts[v][0]) + abs(pts[u][1] - pts[v][1])
                    if d < min_dist[v]:
                        min_dist[v] = d

        return total_w

    def solve(algo, heuristic):
        """Thuật toán tìm kiếm tĩnh dùng cho bản đồ KHÔNG có Ma."""
        if not ui.start_pos:
            return [], [], 0.0

        has_multiple_foods = len(ui.food_positions) > 1

        if not has_multiple_foods:
            target_goal = ui.goal_pos
            if not target_goal:
                if ui.food_positions:
                    target_goal = sorted(list(ui.food_positions))[0]
                elif ui.ghosts_pos:
                    target_goal = ui.ghosts_pos[0]
            if not target_goal:
                return [], [], 0.0

            start, goal = ui.start_pos, target_goal
            t0 = time.time()
            steps = []
            par = {start: None}
            vis = set()
            fs = {start}
            cost_so_far = {start: 0}

            def h_single(pos):
                if algo not in ("A* Search", "Greedy BFS"):
                    return 0
                return calc_dist(pos, goal, heuristic)

            if algo == "BFS":
                q = deque([start])
            elif algo == "DFS":
                q = [start]
            else:
                counter = 0
                prio = 0 if algo == "UCS" else h_single(start)
                pq = [(prio, counter, start, 0)]

            found = False
            while True:
                if algo in ("BFS", "DFS"):
                    if not q: break
                    cur = q.popleft() if algo == "BFS" else q.pop()
                else:
                    if not pq: break
                    prio, _, cur, cur_cost = heapq.heappop(pq)
                    if cur in vis and algo != "UCS":
                        continue

                fs.discard(cur)
                vis.add(cur)

                steps.append({
                    "visited": set(vis),
                    "frontier": set(fs),
                    "current": cur
                })

                if cur == goal:
                    found = True
                    break

                for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
                    nr, nc = cur[0] + dr, cur[1] + dc
                    nxt = (nr, nc)
                    if 0 <= nr < ui.map_rows and 0 <= nc < len(ui.raw_map[nr]):
                        if ui.raw_map[nr][nc] in ('#', '%'):
                            continue

                        new_cost = cost_so_far.get(cur, 0) + 1

                        if algo in ("BFS", "DFS"):
                            if nxt not in vis and nxt not in fs:
                                par[nxt] = cur
                                q.append(nxt)
                                fs.add(nxt)
                        elif algo == "UCS":
                            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                                cost_so_far[nxt] = new_cost
                                par[nxt] = cur
                                counter += 1
                                heapq.heappush(pq, (new_cost, counter, nxt, new_cost))
                                fs.add(nxt)
                        elif algo == "A* Search":
                            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                                cost_so_far[nxt] = new_cost
                                par[nxt] = cur
                                counter += 1
                                priority = new_cost + h_single(nxt)
                                heapq.heappush(pq, (priority, counter, nxt, new_cost))
                                fs.add(nxt)
                        elif algo == "Greedy BFS":
                            if nxt not in vis and nxt not in fs:
                                par[nxt] = cur
                                counter += 1
                                priority = h_single(nxt)
                                heapq.heappush(pq, (priority, counter, nxt, new_cost))
                                fs.add(nxt)

            elapsed = (time.time() - t0) * 1000
            path = []
            if found:
                n = goal
                while n is not None:
                    path.append(n)
                    n = par.get(n)
                path.reverse()
            return steps, path, elapsed

        else:
            t0 = time.time()
            remaining = set(ui.food_positions)
            curr = ui.start_pos
            full_path = [curr]
            steps = []
            total_visited = set()

            while remaining:
                par = {curr: None}
                vis = set()
                fs = {curr}
                cost_so_far = {curr: 0}

                def h_multi(pos):
                    if algo not in ("A* Search", "Greedy BFS") or not remaining:
                        return 0
                    if heuristic == "Null":
                        return 0
                    if heuristic == "MST":
                        pts = list(remaining)
                        min_to_f = min(abs(pos[0] - f[0]) + abs(pos[1] - f[1]) for f in pts)
                        return min_to_f + calc_mst_weight(pts)
                    elif heuristic == "Euclidean":
                        return min(math.hypot(pos[0] - f[0], pos[1] - f[1]) for f in remaining)
                    else:
                        return min(abs(pos[0] - f[0]) + abs(pos[1] - f[1]) for f in remaining)

                if algo == "BFS":
                    q = deque([curr])
                elif algo == "DFS":
                    q = [curr]
                else:
                    counter = 0
                    prio = 0 if algo == "UCS" else h_multi(curr)
                    pq = [(prio, counter, curr, 0)]

                found_target = None
                while True:
                    if algo in ("BFS", "DFS"):
                        if not q: break
                        c_node = q.popleft() if algo == "BFS" else q.pop()
                    else:
                        if not pq: break
                        prio, _, c_node, cur_cost = heapq.heappop(pq)
                        if c_node in vis and algo != "UCS":
                            continue

                    fs.discard(c_node)
                    vis.add(c_node)

                    if len(steps) < 250:
                        total_visited.add(c_node)
                        steps.append({
                            "visited": set(total_visited),
                            "frontier": set(fs),
                            "current": c_node
                        })

                    if c_node in remaining:
                        found_target = c_node
                        break

                    for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
                        nr, nc = c_node[0] + dr, c_node[1] + dc
                        nxt = (nr, nc)
                        if 0 <= nr < ui.map_rows and 0 <= nc < len(ui.raw_map[nr]):
                            if ui.raw_map[nr][nc] in ('#', '%'):
                                continue

                            new_cost = cost_so_far.get(c_node, 0) + 1

                            if algo in ("BFS", "DFS"):
                                if nxt not in vis and nxt not in fs:
                                    par[nxt] = c_node
                                    q.append(nxt)
                                    fs.add(nxt)
                            elif algo == "UCS":
                                if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                                    cost_so_far[nxt] = new_cost
                                    par[nxt] = c_node
                                    counter += 1
                                    heapq.heappush(pq, (new_cost, counter, nxt, new_cost))
                                    fs.add(nxt)
                            elif algo == "A* Search":
                                if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                                    cost_so_far[nxt] = new_cost
                                    par[nxt] = c_node
                                    counter += 1
                                    priority = new_cost + h_multi(nxt)
                                    heapq.heappush(pq, (priority, counter, nxt, new_cost))
                                    fs.add(nxt)
                            elif algo == "Greedy BFS":
                                if nxt not in vis and nxt not in fs:
                                    par[nxt] = c_node
                                    counter += 1
                                    priority = h_multi(nxt)
                                    heapq.heappush(pq, (priority, counter, nxt, new_cost))
                                    fs.add(nxt)

                if not found_target:
                    break

                segment = []
                n = found_target
                while n is not None:
                    segment.append(n)
                    n = par.get(n)
                segment.reverse()

                for pt in segment[1:]:
                    full_path.append(pt)
                    remaining.discard(pt)
                curr = found_target

            elapsed = (time.time() - t0) * 1000
            return steps, full_path, elapsed

    # ══════════════════════════════════════════════════════════════════════════
    # Vòng lặp chính (Main Game Loop)
    # ══════════════════════════════════════════════════════════════════════════
    while True:
        ev = ui.handle_events()

        if ev:
            act = ev.get("action")

            if act == "START":
                if ui.has_ghosts():
                    # Chế độ theo lượt khi có Ma
                    if ui.is_game_over:
                        ui.reset_search_state()
                    ui.is_running = True
                    ui.is_paused = False
                    ui.phase = "MOVING"
                else:
                    # Chế độ tìm kiếm tĩnh khi không có Ma
                    ui.reset_search_state()
                    cur_algo = ui.get_selected_algorithm()
                    cur_heu  = ui.get_selected_heuristic()
                    search_steps, demo_path, search_time_ms = solve(cur_algo, cur_heu)
                    search_step_idx = 0
                    ui.is_running = True
                    ui.is_paused = False
                    ui.phase = "SEARCHING"
                    ui.metrics["time_ms"] = round(search_time_ms, 2)

            elif act in ("ALGO_CHANGED", "HEURISTIC_CHANGED", "MAP_CHANGED"):
                ui.reset_search_state()
                search_steps, demo_path = [], []
                search_step_idx = 0

            elif act == "RESET":
                ui.reset_search_state()
                search_steps, demo_path = [], []
                search_step_idx = 0

            elif act == "STEP":
                if ui.has_ghosts():
                    # Thực hiện chính xác 1 lượt di chuyển trong chế độ có Ma
                    if ui.is_game_over:
                        ui.reset_search_state()
                    ui.is_running = True
                    ui.is_paused = True
                    ui.phase = "MOVING"
                    cur_algo = ui.get_selected_algorithm()
                    cur_heu  = ui.get_selected_heuristic()
                    _execute_turn(ui, cur_algo, cur_heu)
                else:
                    # Chế độ tìm kiếm tĩnh
                    if ui.phase == "IDLE":
                        cur_algo = ui.get_selected_algorithm()
                        cur_heu  = ui.get_selected_heuristic()
                        search_steps, demo_path, search_time_ms = solve(cur_algo, cur_heu)
                        search_step_idx = 0
                        ui.is_running = True
                        ui.is_paused = True
                        ui.phase = "SEARCHING"
                        ui.metrics["time_ms"] = round(search_time_ms, 2)
                    elif ui.phase == "SEARCHING":
                        if search_step_idx < len(search_steps):
                            s = search_steps[search_step_idx]
                            ui.update_search_step(s["visited"], s["frontier"], s["current"])
                            ui.set_metrics(
                                expanded=len(s["visited"]),
                                status=f"Đang duyệt ({search_step_idx + 1}/{len(search_steps)})"
                            )
                            search_step_idx += 1
                        else:
                            ui.set_path(demo_path)
                            ui.set_metrics(
                                cost=len(demo_path) - 1 if demo_path else 0,
                                status="Tìm thấy đường! Đang di chuyển..." if demo_path else "Không tìm thấy đường (Vô nghiệm)!"
                            )
                            if demo_path:
                                ui.current_node = None
                                ui.start_moving_phase()
                            else:
                                ui.phase = "IDLE"
                                ui.is_running = False
                    elif ui.phase == "MOVING":
                        still_moving = ui.advance_move_step()
                        step = ui.move_step_idx
                        total = len(ui.final_path)
                        if still_moving:
                            if ui.food_positions:
                                ui.set_metrics(
                                    status=f"Di chuyển ({step}/{total}) | Đã ăn {len(ui.eaten_food)}/{len(ui.food_positions)}"
                                )
                            else:
                                ui.set_metrics(
                                    status=f"Di chuyển ({step}/{total})"
                                )
                        else:
                            ui.phase = "IDLE"
                            ui.is_running = False
                            if ui.food_positions and len(ui.eaten_food) == len(ui.food_positions):
                                ui.set_metrics(
                                    status=f"Hoàn thành! Pacman đã ăn sạch toàn bộ {len(ui.food_positions)} thức ăn!"
                                )
                            else:
                                ui.set_metrics(
                                    status="Hoàn thành! Pacman đã đến đích!"
                                )

        # ══════════════════════════════════════════════════════════════════════
        # CẬP NHẬT THEO FRAME
        # ══════════════════════════════════════════════════════════════════════
        if ui.has_ghosts():
            # VÒNG LẶP CHO BẢN ĐỒ CÓ MA (DYNAMIC / TURN-BY-TURN ADVERSARIAL)
            if ui.is_running and not ui.is_paused and not ui.is_game_over:
                cur_algo = ui.get_selected_algorithm()
                cur_heu  = ui.get_selected_heuristic()
                _execute_turn(ui, cur_algo, cur_heu)

        else:
            # VÒNG LẶP CHO BẢN ĐỒ TĨNH KHÔNG CÓ MA (OFFLINE SEARCH 2 GIAI ĐOẠN)
            if ui.phase == "SEARCHING" and ui.is_running and not ui.is_paused:
                if search_step_idx < len(search_steps):
                    s = search_steps[search_step_idx]
                    ui.update_search_step(s["visited"], s["frontier"], s["current"])
                    ui.set_metrics(
                        expanded=len(s["visited"]),
                        status=f"Đang duyệt ({search_step_idx + 1}/{len(search_steps)})"
                    )
                    search_step_idx += 1
                else:
                    ui.set_path(demo_path)
                    ui.set_metrics(
                        cost=len(demo_path) - 1 if demo_path else 0,
                        status="Tìm thấy đường! Đang di chuyển..." if demo_path else "Không tìm thấy đường (Vô nghiệm)!"
                    )
                    if demo_path:
                        ui.current_node = None
                        ui.start_moving_phase()
                    else:
                        ui.phase = "IDLE"
                        ui.is_running = False

            elif ui.phase == "MOVING" and ui.is_running and not ui.is_paused:
                still_moving = ui.advance_move_step()
                step = ui.move_step_idx
                total = len(ui.final_path)
                if still_moving:
                    if ui.food_positions:
                        ui.set_metrics(
                            status=f"Di chuyển ({step}/{total}) | Đã ăn {len(ui.eaten_food)}/{len(ui.food_positions)}"
                        )
                    else:
                        ui.set_metrics(
                            status=f"Di chuyển ({step}/{total})"
                        )
                else:
                    ui.phase = "IDLE"
                    ui.is_running = False
                    if ui.food_positions and len(ui.eaten_food) == len(ui.food_positions):
                        ui.set_metrics(
                            status=f"Hoàn thành! Pacman đã ăn sạch toàn bộ {len(ui.food_positions)} thức ăn!"
                        )
                    else:
                        ui.set_metrics(
                            status="Hoàn thành! Pacman đã đến đích!"
                        )

        ui.render()
        ui.tick()


# Alias tương thích ngược
run_standalone_demo = run_gui_app


if __name__ == "__main__":
    run_gui_app()