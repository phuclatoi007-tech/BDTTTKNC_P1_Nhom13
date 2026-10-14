"""
ui/g_ui.py
Giao diện đồ họa Pygame cho đồ án Pacman AI – Nhóm 13.

Tính năng chính:
  1. Dropdown Menu tương tác: Map / Algorithm / Heuristic.
  2. Hai chế độ vận hành:
     • Map KHÔNG có Ma -> Offline Search (Duyệt tìm kiếm -> Di chuyển ăn đồ ăn).
     • Map CÓ Ma        -> Turn-by-Turn Game Loop (Pacman và Ghost luân phiên).
  3. Quản lý tài nguyên: Tự động nạp sprite và font tùy chỉnh (fallback an toàn).
  4. Tương thích 100% với BaseUI, SearchAgent, AdversarialAgent và GameLoop.
"""

import math
import os
import sys
import time
import pygame

# Đảm bảo thư mục gốc dự án nằm trong sys.path để import src.*
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ui.base_ui import BaseUI

# ── ĐƯỜNG DẪN TÀI NGUYÊN & BẢNG MÀU RGB (Dark Navy & Cyan Accent) ─────────────
_ASSET_DIR = os.path.join(_PROJECT_ROOT, "asset")
_FONT_PATH = os.path.join(_ASSET_DIR, "fonts", "font.ttf")
_IMG_DIR = os.path.join(_ASSET_DIR, "images")
_PACMAN_IMG = os.path.join(_IMG_DIR, "pacman", "pacman.png")
_GHOST_IMGS = {
    "Blinky": os.path.join(_IMG_DIR, "ghosts", "Blinky.png"),
    "Inky":   os.path.join(_IMG_DIR, "ghosts", "Inky.png"),
    "Clyde":  os.path.join(_IMG_DIR, "ghosts", "Clyde.png"),
}
_GHOST_NAMES = ["Blinky", "Inky", "Clyde"]

COLOR_BG, COLOR_PANEL_BG, COLOR_CARD_BG = (15, 18, 30), (20, 24, 40), (30, 36, 58)
COLOR_BORDER, COLOR_DIVIDER = (45, 55, 85), (38, 46, 72)
COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_TEXT_WHITE = (235, 240, 245), (140, 150, 170), (255, 255, 255)
COLOR_ACCENT = (0, 180, 216)
COLOR_WALL, COLOR_WALL_GRID, COLOR_FLOOR = (33, 70, 139), (25, 55, 110), (15, 18, 30)
COLOR_FOOD, COLOR_GOAL = (255, 183, 3), (230, 57, 70)
COLOR_VISITED, COLOR_VISITED_BORDER = (35, 60, 95), (50, 80, 120)
COLOR_FRONTIER, COLOR_FRONTIER_BORDER = (180, 110, 20), (220, 145, 40)
COLOR_PATH = (46, 204, 113)

COLOR_BTN_DEFAULT, COLOR_BTN_HOVER, COLOR_BTN_ACTIVE = (38, 48, 78), (55, 70, 110), (0, 160, 200)
COLOR_BTN_START, COLOR_BTN_PAUSE = (40, 167, 69), (240, 150, 0)
COLOR_BTN_STEP, COLOR_BTN_RESET = (70, 85, 120), (220, 53, 69)
COLOR_DD_BG, COLOR_DD_HOVER = (28, 34, 56), (45, 58, 95)
COLOR_DD_BORDER, COLOR_DD_SELECTED = (60, 75, 115), (0, 140, 180)
COLOR_GAME_OVER, COLOR_WIN, COLOR_OVERLAY = (220, 53, 69), (46, 204, 113), (0, 0, 0, 150)

_ALGO_KEY_MAP = {"BFS": "bfs", "DFS": "dfs", "UCS": "ucs", "A*": "astar"}
_HEURISTIC_KEY_MAP = {"MST": "mst", "Maze (Farthest)": "maze", "Null": "null"}


# ── HÀM TIỆN ÍCH NẠP TÀI NGUYÊN ───────────────────────────────────────────────

def _load_font(size, bold=False):
    """Nạp font tùy chỉnh từ asset, tự động fallback sang SysFont Arial nếu thiếu file."""
    try:
        f = pygame.font.Font(_FONT_PATH, size)
        if bold:
            f.set_bold(True)
        return f
    except (FileNotFoundError, OSError):
        return pygame.font.SysFont("Arial", size, bold=bold)


def _load_sprite(path, size):
    """Nạp sprite từ đường dẫn và scale thành kích thước vuông (size, size); trả về None nếu lỗi."""
    if not os.path.exists(path):
        return None
    try:
        return pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), (size, size))
    except pygame.error:
        return None


# ── DROPDOWN MENU ─────────────────────────────────────────────────────────────

class DropdownMenu:
    """Hộp chọn dạng thả xuống tương tác cho Pygame:
    Hỗ trợ cuộn chuột, mutual exclusive, tự động rút gọn nhãn text và vẽ top Z-index.
    """

    def __init__(self, x, y, w, h, items, label="", font=None, font_small=None, max_visible=8):
        self.rect = pygame.Rect(x, y, w, h)
        self.items = list(items)
        self.label = label
        self.font = font
        self.font_small = font_small or font
        self.max_visible = max_visible
        self.selected_idx = 0
        self.is_open = False
        self.hovered_idx = -1
        self.scroll_offset = 0
        self.enabled = True

    @property
    def value(self):
        """Giá trị chuỗi của mục hiện đang được chọn."""
        return self.items[self.selected_idx] if 0 <= self.selected_idx < len(self.items) else None

    def set_items(self, new_items, keep_selection=False):
        """Cập nhật danh sách mục chọn; giữ lại lựa chọn cũ nếu còn tồn tại."""
        old_val = self.value
        self.items = list(new_items)
        self.selected_idx = self.items.index(old_val) if (keep_selection and old_val in self.items) else 0
        self.scroll_offset, self.is_open, self.hovered_idx = 0, False, -1

    def select_by_value(self, value):
        """Chọn mục theo tên giá trị chuỗi."""
        if value in self.items:
            self.selected_idx = self.items.index(value)

    def _dropdown_rect(self):
        """Tính toán khung bao quanh danh sách mở dựa trên số mục hiển thị tối đa."""
        visible = min(len(self.items), self.max_visible)
        return pygame.Rect(self.rect.x, self.rect.bottom + 2, self.rect.width, visible * self.rect.height + 4)

    def handle_click(self, mx, my):
        """Xử lý sự kiện click chuột. Trả về True nếu giá trị lựa chọn thay đổi."""
        if not self.enabled:
            return False

        if self.rect.collidepoint(mx, my):
            self.is_open = not self.is_open
            self.scroll_offset = 0
            return False

        if self.is_open:
            dd_rect = self._dropdown_rect()
            if dd_rect.collidepoint(mx, my):
                idx = self.scroll_offset + int((my - dd_rect.y - 2) / self.rect.height)
                if 0 <= idx < len(self.items):
                    self.selected_idx = idx
                    self.is_open = False
                    return True
            self.is_open = False
        return False

    def handle_scroll(self, direction):
        """Cuộn danh sách thả xuống khi danh sách dài vượt max_visible."""
        if self.is_open:
            max_offset = max(0, len(self.items) - self.max_visible)
            self.scroll_offset = max(0, min(max_offset, self.scroll_offset - direction))

    def draw_header(self, surface, mpos):
        """Vẽ header dropdown ở trạng thái bình thường/hover/disabled."""
        if not self.enabled:
            bg, border, tc = COLOR_BTN_DEFAULT, COLOR_BORDER, (80, 90, 110)
        elif self.is_open:
            bg, border, tc = COLOR_DD_SELECTED, COLOR_ACCENT, COLOR_TEXT_WHITE
        elif self.rect.collidepoint(mpos):
            bg, border, tc = COLOR_BTN_HOVER, COLOR_ACCENT, COLOR_TEXT_MAIN
        else:
            bg, border, tc = COLOR_DD_BG, COLOR_DD_BORDER, COLOR_TEXT_MAIN

        pygame.draw.rect(surface, bg, self.rect, border_radius=5)
        pygame.draw.rect(surface, border, self.rect, 1, border_radius=5)

        display_text = f"{self.label}: {self.value or '—'}" if self.label else (self.value or "—")
        max_w = self.rect.width - 28
        t = self.font.render(display_text, True, tc)
        while len(display_text) > 3 and t.get_width() > max_w:
            display_text = display_text[:-2] + "…"
            t = self.font.render(display_text, True, tc)
        surface.blit(t, (self.rect.x + 10, self.rect.centery - t.get_height() // 2))

        arrow = self.font.render("▲" if self.is_open else "▼", True, tc)
        surface.blit(arrow, (self.rect.right - arrow.get_width() - 8, self.rect.centery - arrow.get_height() // 2))

    def draw_dropdown_list(self, surface, mpos):
        """Vẽ danh sách các lựa chọn khi mở dropdown (gọi sau cùng để có Z-index cao nhất)."""
        if not self.is_open or not self.items:
            return

        dd_rect, item_h = self._dropdown_rect(), self.rect.height
        pygame.draw.rect(surface, COLOR_DD_BG, dd_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_DD_BORDER, dd_rect, 1, border_radius=4)

        for i in range(min(len(self.items), self.max_visible)):
            idx = self.scroll_offset + i
            if idx >= len(self.items):
                break
            r = pygame.Rect(dd_rect.x + 2, dd_rect.y + 2 + i * item_h, dd_rect.width - 4, item_h)
            ibg, itc = ((COLOR_DD_SELECTED, COLOR_TEXT_WHITE) if idx == self.selected_idx
                        else (COLOR_DD_HOVER, COLOR_TEXT_MAIN) if r.collidepoint(mpos)
                        else (COLOR_DD_BG, COLOR_TEXT_MUTED))
            pygame.draw.rect(surface, ibg, r, border_radius=3)
            t = self.font_small.render(self.items[idx], True, itc)
            surface.blit(t, (r.x + 10, r.centery - t.get_height() // 2))

        if len(self.items) > self.max_visible:
            scroll_h = max(10, int(dd_rect.height * self.max_visible / len(self.items)))
            scroll_y = dd_rect.y + int((dd_rect.height - scroll_h) * self.scroll_offset / (len(self.items) - self.max_visible))
            pygame.draw.rect(surface, COLOR_ACCENT, pygame.Rect(dd_rect.right - 6, scroll_y, 4, scroll_h), border_radius=2)

    def contains_point(self, mx, my):
        """Kiểm tra một tọa độ chuột có nằm trong vùng header hoặc danh sách mở hay không."""
        return self.rect.collidepoint(mx, my) or (self.is_open and self._dropdown_rect().collidepoint(mx, my))


# ── GIAO DIỆN CHÍNH – PacmanUI ────────────────────────────────────────────────

class PacmanUI(BaseUI):
    """Giao diện đồ họa chính cho Pacman AI (Pygame).
    Hỗ trợ trực quan hóa thuật toán tìm kiếm đường đi và mô phỏng game đối kháng với Ma.
    """

    ALGO_SEARCH = ["A*", "BFS", "DFS", "UCS"]
    ALGO_ADVERSARIAL = ["Minimax", "Alpha-Beta"]
    ALGORITHMS = ALGO_SEARCH + ALGO_ADVERSARIAL
    ALGO_NEEDS_HEURISTIC = {"A*"}
    HEURISTICS = ["MST", "Maze (Farthest)", "Null"]

    def __init__(self, width=1100, height=740):
        pygame.init()
        pygame.display.set_caption("Pacman AI Search – Nhóm 13")
        self.screen_width, self.screen_height = width, height
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()

        # Typography & Bố cục
        self.font_title, self.font_bold = _load_font(20, bold=True), _load_font(13, bold=True)
        self.font_main, self.font_small = _load_font(12), _load_font(11)
        self.panel_width = 360
        self.panel_x = width - self.panel_width
        self.board_rect = pygame.Rect(0, 0, self.panel_x, height)

        # Trạng thái điều khiển & Tốc độ
        self.map_files = self._scan_maps()
        self.is_running, self.is_paused, self.speed, self.slider_dragging = False, False, 10, False

        # Bản đồ & Tọa độ thực thể
        self.raw_map, self.map_rows, self.map_cols, self.cell_size = [], 0, 0, 30
        self.board_offset_x, self.board_offset_y = 20, 20
        self.pacman_pos, self.start_pos = None, None
        self.ghost_positions, self.initial_ghost_positions = [], []
        self.food_set, self.eaten_food = set(), set()

        # Thuật toán & State Machine
        self.visited_nodes, self.frontier_nodes = set(), set()
        self.final_path, self.current_node = [], None
        self.phase, self.move_step_idx = "IDLE", 0
        self._frame_counter, self.game_result = 0, ""

        self.metrics = {
            "status": "Sẵn sàng", "algorithm": "", "expanded": 0,
            "cost": 0, "time_ms": 0.0, "path_length": 0, "turn": 0,
        }
        self._pacman_sprite, self._ghost_sprites = None, {}

        self._init_dropdowns()
        self._init_ui_buttons()

        if self.map_files:
            self._dd_map.selected_idx = 0
            self.load_map_file(self.map_files[0])
            self.update_available_algorithms()

    # ── Khởi tạo UI Widgets ──

    def _scan_maps(self):
        """Quét và trả về danh sách các tệp bản đồ (.txt) trong thư mục maps/."""
        maps_dir = os.path.join(_PROJECT_ROOT, "maps")
        if os.path.isdir(maps_dir):
            found = sorted(f for f in os.listdir(maps_dir) if f.endswith(".txt"))
            return [os.path.join("maps", f).replace("\\", "/") for f in found]
        return []

    def _init_dropdowns(self):
        """Khởi tạo 3 menu thả xuống: Bản đồ, Thuật toán và Heuristic."""
        px, pw = self.panel_x + 16, self.panel_width - 32
        map_names = [os.path.basename(m).replace(".txt", "") for m in self.map_files]
        self._dd_map = DropdownMenu(px, 80, pw, 30, map_names or ["(Không có map)"], font=self.font_bold, font_small=self.font_main)
        self._dd_algo = DropdownMenu(px, 145, pw, 30, self.ALGORITHMS, font=self.font_bold, font_small=self.font_main)
        self._dd_heuristic = DropdownMenu(px, 210, pw, 30, self.HEURISTICS, font=self.font_bold, font_small=self.font_main, max_visible=6)
        self._update_heuristic_state()
        self._dropdowns = [self._dd_map, self._dd_algo, self._dd_heuristic]

    def _init_ui_buttons(self):
        """Khởi tạo vị trí các nút điều khiển và thanh trượt tốc độ."""
        px, pw = self.panel_x + 16, self.panel_width - 32
        bw, y_btn = (pw - 24) // 4, 280
        self.btn_start = pygame.Rect(px, y_btn, bw, 34)
        self.btn_pause = pygame.Rect(px + bw + 8, y_btn, bw, 34)
        self.btn_step = pygame.Rect(px + (bw + 8) * 2, y_btn, bw, 34)
        self.btn_reset = pygame.Rect(px + (bw + 8) * 3, y_btn, bw, 34)

        self.slider_track = pygame.Rect(px, 355, pw, 8)
        sw = (pw - 24) // 4
        self.speed_presets = [
            (pygame.Rect(px + i * (sw + 8), 375, sw, 22), v, l)
            for i, (v, l) in enumerate([(3, "0.5x"), (10, "1x"), (25, "3x"), (60, "Max")])
        ]

    def _update_heuristic_state(self):
        """Kích hoạt Dropdown Heuristic chỉ khi chạy chế độ A* trên map không Ma."""
        self._dd_heuristic.enabled = (not self.has_ghosts()) and (self._dd_algo.value in self.ALGO_NEEDS_HEURISTIC)

    def get_valid_algorithms_for_current_map(self):
        """Trả về danh sách thuật toán hợp lệ theo đặc trưng map (có Ma vs không Ma)."""
        return list(self.ALGO_ADVERSARIAL if self.has_ghosts() else self.ALGO_SEARCH)

    def update_available_algorithms(self):
        """Đồng bộ danh sách thuật toán tương ứng khi người dùng thay đổi bản đồ."""
        valid_algos = self.get_valid_algorithms_for_current_map()
        self._dd_algo.set_items(valid_algos, keep_selection=True)
        if self._dd_algo.value not in valid_algos:
            self._dd_algo.selected_idx = 0
        self._update_heuristic_state()

    def _load_sprites(self):
        """Nạp và điều chỉnh kích cỡ sprite của Pacman và Ghost theo cell_size hiện tại."""
        sprite_size = max(12, int(self.cell_size * 0.85))
        self._pacman_sprite = _load_sprite(_PACMAN_IMG, sprite_size)
        self._ghost_sprites = {
            name: spr for name, path in _GHOST_IMGS.items()
            if (spr := _load_sprite(path, sprite_size)) is not None
        }

    # ── Quản lý Trạng thái & Bản đồ (BaseUI Interface) ──

    def initialize(self):
        """Giao diện BaseUI: Khởi tạo hoàn tất trong constructor."""
        pass

    def load_map_file(self, file_path):
        """Đọc và nạp dữ liệu bản đồ từ đường dẫn tương đối hoặc tuyệt đối."""
        full_path = file_path if os.path.isabs(file_path) else os.path.join(_PROJECT_ROOT, file_path)
        if not os.path.exists(full_path):
            return False
        with open(full_path, "r", encoding="utf-8") as f:
            lines = [ln.rstrip("\r\n") for ln in f if ln.strip()]
        self.set_map(lines)
        return True

    def set_map(self, map_data):
        """Phân tích cấu trúc ký tự bản đồ, căn chỉnh vị trí thực thể và tính toán viewport."""
        self.raw_map = [list(row) for row in map_data]
        self.map_rows, self.map_cols = len(self.raw_map), max((len(r) for r in self.raw_map), default=0)
        self.start_pos = None
        self.ghost_positions, self.initial_ghost_positions = [], []
        self.food_set = set()

        for r, row in enumerate(self.raw_map):
            for c, ch in enumerate(row):
                if ch == 'P': self.start_pos = self.pacman_pos = (r, c)
                elif ch == 'G':
                    self.ghost_positions.append((r, c))
                    self.initial_ghost_positions.append((r, c))
                elif ch == '.': self.food_set.add((r, c))

        if self.map_cols > 0 and self.map_rows > 0:
            aw, ah = self.board_rect.width - 40, self.board_rect.height - 40
            self.cell_size = max(12, min(48, aw // self.map_cols, ah // self.map_rows))
            self.board_offset_x = (self.board_rect.width - self.map_cols * self.cell_size) // 2
            self.board_offset_y = (self.board_rect.height - self.map_rows * self.cell_size) // 2

        self._load_sprites()
        if hasattr(self, "_dd_algo"): self.update_available_algorithms()
        self.reset_search_state()

    def reset_search_state(self):
        """Khôi phục trạng thái ban đầu của bản đồ, vị trí nhân vật và số liệu thống kê."""
        self.visited_nodes.clear()
        self.frontier_nodes.clear()
        self.eaten_food.clear()
        self.final_path, self.current_node = [], None
        self.pacman_pos, self.ghost_positions = self.start_pos, list(self.initial_ghost_positions)
        self.phase, self.move_step_idx, self._frame_counter = "IDLE", 0, 0
        self.is_running, self.is_paused, self.game_result = False, False, ""
        self.metrics = {
            "status": "Sẵn sàng", "algorithm": "", "expanded": 0,
            "cost": 0, "time_ms": 0.0, "path_length": 0, "turn": 0,
        }

    def sync_from_engine(self, gs):
        """Đồng bộ trạng thái từ GameState của engine (x=col, y=row) sang UI (row, col)."""
        if not gs: return
        if gs.pacman_pos: self.pacman_pos = (gs.pacman_pos[1], gs.pacman_pos[0])
        self.ghost_positions = [(gy, gx) for gx, gy in gs.ghosts_pos]
        self.eaten_food = self.food_set - {(fy, fx) for fx, fy in gs.food}

    def update_search_step(self, visited=None, frontier=None, current=None):
        """Cập nhật các tập nút đã duyệt và biên trong giai đoạn tìm kiếm đường đi."""
        self.phase = "SEARCHING"
        if visited is not None:
            self.visited_nodes.update(visited if isinstance(visited, (set, list)) else [visited])
        if frontier is not None:
            self.frontier_nodes = set(frontier if isinstance(frontier, (set, list)) else [frontier])
        if current is not None:
            self.current_node = current

    def set_path(self, path):
        """Lưu trữ đường đi tìm kiếm tối ưu và chuẩn bị di chuyển."""
        self.final_path = list(path) if path else []
        self.metrics["path_length"] = len(self.final_path)
        self.move_step_idx = 0

    def start_moving_phase(self):
        """Chuyển giao diện sang giai đoạn Pacman di chuyển theo hành trình đã lập."""
        self.phase = "MOVING"
        self.move_step_idx, self.current_node = 0, None
        if self.final_path: self.pacman_pos = self.final_path[0]

    def advance_move_step(self):
        """Di chuyển Pacman một bước trên đường đi và cập nhật đồ ăn đã ăn."""
        if self.phase != "MOVING" or not self.final_path or self.move_step_idx >= len(self.final_path):
            return False
        pos = self.final_path[self.move_step_idx]
        self.pacman_pos = pos
        if pos in self.food_set: self.eaten_food.add(pos)
        self.move_step_idx += 1
        return self.move_step_idx < len(self.final_path)

    def is_moving_done(self):
        """Kiểm tra Pacman đã đi hết toàn bộ các bước trong đường đi hay chưa."""
        return self.move_step_idx >= len(self.final_path)

    def update_pacman(self, pos):
        """Cập nhật vị trí Pacman trực tiếp (dùng cho các bản đồ không Ma)."""
        self.pacman_pos = pos
        if self.phase == "MOVING" and pos and pos in self.food_set:
            self.eaten_food.add(pos)

    def set_metrics(self, **kwargs):
        """Cập nhật linh hoạt các chỉ số hiệu năng thông qua keyword arguments."""
        key_alias = {"time_taken": "time_ms"}
        for k, v in kwargs.items():
            if v is not None:
                tk = key_alias.get(k, k)
                self.metrics[tk] = round(v, 2) if tk == "time_ms" else v

    def get_selected_algorithm(self):
        """Lấy tên thuật toán đang được lựa chọn trên UI."""
        return self._dd_algo.value or "BFS"

    def get_selected_map(self):
        """Lấy đường dẫn tệp bản đồ đang được lựa chọn."""
        idx = self._dd_map.selected_idx
        return self.map_files[idx] if 0 <= idx < len(self.map_files) else None

    def get_selected_heuristic(self):
        """Lấy tên heuristic đang chọn cho A*."""
        return self._dd_heuristic.value or "MST"

    def has_ghosts(self):
        """Kiểm tra bản đồ hiện tại có chứa Ghost hay không."""
        return len(self.initial_ghost_positions) > 0

    # ── Xử lý Sự kiện Tương tác (Input Events) ──

    def handle_events(self):
        """Lắng nghe các sự kiện đầu vào chuột, bàn phím và dispatch hành động phù hợp."""
        action = None
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1: action = self._handle_click(ev.pos) or action
                elif ev.button in (4, 5):
                    direction = 1 if ev.button == 4 else -1
                    for dd in self._dropdowns:
                        if dd.is_open: dd.handle_scroll(direction)
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self.slider_dragging = False
            elif ev.type == pygame.MOUSEMOTION and self.slider_dragging:
                self._update_slider(ev.pos[0])
                action = {"action": "SPEED_CHANGED", "speed": self.speed}
            elif ev.type == pygame.KEYDOWN:
                action = self._handle_key(ev.key) or action
        return action

    def _handle_click(self, pos):
        """Xử lý sự kiện click chuột: Dropdown mở -> Header -> Các nút điều khiển."""
        mx, my = pos

        # 1. Ưu tiên xử lý dropdown đang mở
        for dd in self._dropdowns:
            if dd.is_open and dd.contains_point(mx, my):
                if dd.handle_click(mx, my):
                    if dd is self._dd_map: return self._on_map_changed()
                    self.reset_search_state()
                    if dd is self._dd_algo:
                        self._update_heuristic_state()
                        return {"action": "ALGO_CHANGED", "algo": self.get_selected_algorithm()}
                    return {"action": "HEURISTIC_CHANGED"}
                return None

        # 2. Đóng tất cả dropdown nếu click ra ngoài
        any_was_open = any(dd.is_open for dd in self._dropdowns)
        for dd in self._dropdowns: dd.is_open = False

        # 3. Header clicks để mở dropdown
        for dd in self._dropdowns:
            if dd.rect.collidepoint(mx, my) and dd.enabled:
                for other in self._dropdowns:
                    if other is not dd: other.is_open = False
                dd.is_open = True
                return None

        if any_was_open: return None

        # 4. Nút điều khiển
        if self.btn_start.collidepoint(mx, my):
            if self.phase == "GAME_OVER": self.reset_search_state()
            self.is_running, self.is_paused = True, False
            return {"action": "START", "algo": self.get_selected_algorithm()}
        if self.btn_pause.collidepoint(mx, my) and self.is_running:
            self.is_paused = not self.is_paused
            self.metrics["status"] = "Tạm dừng" if self.is_paused else "Đang chạy..."
            return {"action": "PAUSE", "paused": self.is_paused}
        if self.btn_step.collidepoint(mx, my):
            self.is_paused = True
            return {"action": "STEP"}
        if self.btn_reset.collidepoint(mx, my):
            self.reset_search_state()
            return {"action": "RESET"}

        # 5. Slider & Presets
        if self.slider_track.collidepoint(mx, my):
            self.slider_dragging = True
            self._update_slider(mx)
            return {"action": "SPEED_CHANGED", "speed": self.speed}

        for r, val, _ in self.speed_presets:
            if r.collidepoint(mx, my):
                self.speed = val
                return {"action": "SPEED_CHANGED", "speed": self.speed}

        return None

    def _on_map_changed(self):
        """Xử lý tải lại map và cập nhật trạng thái khi người dùng đổi map."""
        idx = self._dd_map.selected_idx
        if 0 <= idx < len(self.map_files):
            self.load_map_file(self.map_files[idx])
            self.update_available_algorithms()
            self.metrics["status"] = (
                "Map có Ma: Chỉ hỗ trợ Minimax / Alpha-Beta" if self.has_ghosts()
                else "Map tìm kiếm: Chọn A*, BFS, DFS, UCS"
            )
        return {"action": "MAP_CHANGED", "map": self.get_selected_map()}

    def _handle_key(self, key):
        """Xử lý các phím tắt bàn phím tiện ích: Space, R, S, Esc."""
        if key == pygame.K_SPACE:
            if self.is_running:
                self.is_paused = not self.is_paused
                return {"action": "PAUSE" if self.is_paused else "START"}
            self.is_running, self.is_paused = True, False
            return {"action": "START", "algo": self.get_selected_algorithm()}
        if key == pygame.K_r:
            self.reset_search_state()
            return {"action": "RESET"}
        if key == pygame.K_s:
            self.is_paused = True
            return {"action": "STEP"}
        if key == pygame.K_ESCAPE:
            for dd in self._dropdowns: dd.is_open = False
        return None

    def _update_slider(self, mx):
        """Tính toán lại giá trị tốc độ (1..60) dựa trên tọa độ X của chuột trên slider."""
        track = self.slider_track
        clamped_x = max(track.left, min(mx, track.right))
        self.speed = max(1, min(60, int(1 + ((clamped_x - track.left) / track.width) * 59)))

    # ── Vẽ khu vực Board Game (Trái) ──

    def draw_board(self):
        """Vẽ toàn bộ lưới bản đồ, các lớp thuật toán, thức ăn và các thực thể."""
        self._frame_counter += 1
        pygame.draw.rect(self.screen, COLOR_BG, self.board_rect)
        cs = self.cell_size

        for r, row in enumerate(self.raw_map):
            for c, cell in enumerate(row):
                rect = pygame.Rect(self.board_offset_x + c * cs, self.board_offset_y + r * cs, cs, cs)
                if cell == '#':
                    pygame.draw.rect(self.screen, COLOR_WALL, rect)
                    pygame.draw.rect(self.screen, COLOR_WALL_GRID, rect, 1)
                    continue

                pygame.draw.rect(self.screen, COLOR_FLOOR, rect)
                if (r, c) in self.visited_nodes:
                    pygame.draw.rect(self.screen, COLOR_VISITED, rect)
                    pygame.draw.rect(self.screen, COLOR_VISITED_BORDER, rect, 1)
                elif (r, c) in self.frontier_nodes:
                    pygame.draw.rect(self.screen, COLOR_FRONTIER, rect)
                    pygame.draw.rect(self.screen, COLOR_FRONTIER_BORDER, rect, 1)

                if (r, c) in self.food_set and (r, c) not in self.eaten_food:
                    pygame.draw.circle(self.screen, COLOR_FOOD, rect.center, max(2, cs // 8))

        if self.phase == "SEARCHING" and self.current_node:
            cr, cc = self.current_node
            cx, cy = self.board_offset_x + cc * cs + cs // 2, self.board_offset_y + cr * cs + cs // 2
            ms = int(cs * 0.35 * (0.7 + 0.3 * math.sin(self._frame_counter * 0.15)))
            diamond = [(cx, cy - ms), (cx + ms, cy), (cx, cy + ms), (cx - ms, cy)]
            pygame.draw.polygon(self.screen, COLOR_ACCENT, diamond)
            pygame.draw.polygon(self.screen, COLOR_TEXT_WHITE, diamond, 2)

        self._draw_path()
        self._draw_ghosts()
        self._draw_pacman()

        if self.phase == "GAME_OVER":
            self._draw_game_over_overlay()

    def _draw_path(self):
        """Vẽ lộ trình đường đi: phân biệt phần đã đi qua và phần còn lại khi di chuyển."""
        if len(self.final_path) < 2: return
        cs, lw = self.cell_size, max(3, self.cell_size // 6)
        to_px = lambda p: (self.board_offset_x + p[1] * cs + cs // 2, self.board_offset_y + p[0] * cs + cs // 2)

        if self.phase == "MOVING" and self.move_step_idx > 0:
            if self.move_step_idx > 1:
                pygame.draw.lines(self.screen, (30, 140, 75), False, [to_px(p) for p in self.final_path[:self.move_step_idx]], lw)
            remaining = self.final_path[max(0, self.move_step_idx - 1):]
            if len(remaining) > 1:
                pygame.draw.lines(self.screen, COLOR_PATH, False, [to_px(p) for p in remaining], lw)
        else:
            pts = [to_px(p) for p in self.final_path]
            pygame.draw.lines(self.screen, COLOR_PATH, False, pts, lw)
            for pt in pts: pygame.draw.circle(self.screen, COLOR_PATH, pt, max(2, lw // 2))

    def _draw_pacman(self):
        """Vẽ Pacman bằng sprite hình ảnh; fallback sang hình học cơ bản nếu thiếu asset."""
        if not self.pacman_pos: return
        pr, pc = self.pacman_pos
        cs = self.cell_size
        cx, cy = self.board_offset_x + pc * cs, self.board_offset_y + pr * cs

        if self._pacman_sprite:
            spr = self._pacman_sprite
            self.screen.blit(spr, (cx + (cs - spr.get_width()) // 2, cy + (cs - spr.get_height()) // 2))
        else:
            center = (cx + cs // 2, cy + cs // 2)
            rad = max(6, int(cs * 0.42))
            pygame.draw.circle(self.screen, (255, 221, 0), center, rad)
            pygame.draw.polygon(self.screen, COLOR_BG, [
                center, (center[0] + rad, center[1] - rad // 2), (center[0] + rad, center[1] + rad // 2)
            ])
            pygame.draw.circle(self.screen, (20, 20, 20), (center[0], center[1] - rad // 2), max(2, rad // 5))

    def _draw_ghosts(self):
        """Vẽ các con Ma bằng sprite tương ứng tên hoặc fallback sang khối tròn màu."""
        cs = self.cell_size
        fallback_colors = [(255, 0, 0), (0, 255, 255), (255, 165, 0)]
        for i, (gr, gc) in enumerate(self.ghost_positions):
            gx, gy = self.board_offset_x + gc * cs, self.board_offset_y + gr * cs
            name = _GHOST_NAMES[i % len(_GHOST_NAMES)]
            spr = self._ghost_sprites.get(name)

            if spr:
                self.screen.blit(spr, (gx + (cs - spr.get_width()) // 2, gy + (cs - spr.get_height()) // 2))
            else:
                pygame.draw.circle(self.screen, fallback_colors[i % len(fallback_colors)], (gx + cs // 2, gy + cs // 2), max(6, int(cs * 0.40)))

    def _draw_game_over_overlay(self):
        """Vẽ lớp phủ mờ thông báo kết quả khi kết thúc màn chơi."""
        overlay = pygame.Surface((self.board_rect.width, self.board_rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        messages = {
            "WIN": ("🏆 CHIẾN THẮNG!", COLOR_WIN),
            "LOSE": ("💀 GAME OVER!", COLOR_GAME_OVER),
            "NO_PATH": ("❌ KHÔNG TÌM THẤY ĐƯỜNG!", COLOR_GAME_OVER),
        }
        text, color = messages.get(self.game_result, ("KẾT THÚC", COLOR_TEXT_MAIN))
        t_surf = self.font_title.render(text, True, color)
        ty = self.board_rect.height // 2 - 20
        self.screen.blit(t_surf, ((self.board_rect.width - t_surf.get_width()) // 2, ty))
        hint = self.font_main.render("Nhấn [Reset] hoặc [R] để chơi lại", True, COLOR_TEXT_MUTED)
        self.screen.blit(hint, ((self.board_rect.width - hint.get_width()) // 2, ty + 40))

    # ── Vẽ Bảng Điều Khiển Sidebar (Phải) ──

    def draw_panel(self):
        """Vẽ thanh bên: thông tin dự án, dropdowns, nút bấm, slider, metrics và chú thích."""
        panel = pygame.Rect(self.panel_x, 0, self.panel_width, self.screen_height)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel)
        pygame.draw.line(self.screen, COLOR_BORDER, (self.panel_x, 0), (self.panel_x, self.screen_height), 2)
        px, mpos = self.panel_x + 16, pygame.mouse.get_pos()

        # Header dự án
        self.screen.blit(self.font_title.render("PACMAN AI – NHÓM 13", True, COLOR_ACCENT), (px, 12))
        self.screen.blit(self.font_small.render("Bài tập lớn – Trí tuệ nhân tạo", True, COLOR_TEXT_MUTED), (px, 38))

        # Tiêu đề & Dropdowns
        sections = [
            (62, f"1. Chọn bản đồ: [{'Có Ma' if self.has_ghosts() else 'Không Ma'}]", (255, 140, 100) if self.has_ghosts() else COLOR_TEXT_MAIN, self._dd_map),
            (127, f"2. Thuật toán: ({'Chế độ Có Ma' if self.has_ghosts() else 'Chế độ Tìm kiếm'})", (255, 160, 120) if self.has_ghosts() else COLOR_TEXT_MAIN, self._dd_algo),
            (192, "3. Heuristic:" if self._dd_heuristic.enabled else "3. Heuristic: (Không khả dụng)", COLOR_TEXT_MAIN if self._dd_heuristic.enabled else (100, 110, 130), self._dd_heuristic),
        ]
        for y, title, col, dd in sections:
            self.screen.blit(self.font_bold.render(title, True, col), (px, y))
            dd.draw_header(self.screen, mpos)

        # 4. Nút bấm điều khiển
        self.screen.blit(self.font_bold.render("4. Điều khiển:", True, COLOR_TEXT_MAIN), (px, 257))
        btn_labels = [
            (self.btn_start, "Tiếp tục" if self.is_paused else "Bắt đầu", COLOR_BTN_START),
            (self.btn_pause, "Tạm dừng", COLOR_BTN_PAUSE),
            (self.btn_step, "Từng bước", COLOR_BTN_STEP),
            (self.btn_reset, "Đặt lại", COLOR_BTN_RESET),
        ]
        for rect, text, col in btn_labels:
            self._draw_btn(rect, text, col, mpos)

        # 5. Thanh trượt tốc độ
        self.screen.blit(self.font_bold.render(f"5. Tốc độ: {self.speed} bước/s", True, COLOR_TEXT_MAIN), (px, 330))
        self._draw_slider(mpos)

        # 6. Thống kê & chú thích
        self._draw_metrics(px)
        self._draw_legend(px)

        shortcut = "Phím tắt: [Space] Chạy | [S] Bước | [R] Reset | [Esc] Đóng menu"
        self.screen.blit(self.font_small.render(shortcut, True, (100, 110, 130)), (px, self.screen_height - 22))

    def _draw_slider(self, mpos):
        """Vẽ thanh trượt chỉnh tốc độ mô phỏng và các nút chọn tốc độ nhanh."""
        pygame.draw.rect(self.screen, COLOR_BTN_DEFAULT, self.slider_track, border_radius=4)
        fill_w = int(((self.speed - 1) / 59) * self.slider_track.width)
        if fill_w > 0:
            pygame.draw.rect(self.screen, COLOR_ACCENT, pygame.Rect(self.slider_track.x, self.slider_track.y, fill_w, 8), border_radius=4)

        knob_x = self.slider_track.x + fill_w
        pygame.draw.circle(self.screen, COLOR_TEXT_WHITE, (knob_x, self.slider_track.centery), 8)
        pygame.draw.circle(self.screen, COLOR_ACCENT, (knob_x, self.slider_track.centery), 5)

        for r, val, lbl in self.speed_presets:
            is_active = (self.speed == val)
            pygame.draw.rect(self.screen, COLOR_BTN_ACTIVE if is_active else COLOR_BTN_DEFAULT, r, border_radius=3)
            if is_active: pygame.draw.rect(self.screen, COLOR_ACCENT, r, 1, border_radius=3)
            t = self.font_small.render(lbl, True, COLOR_TEXT_WHITE if is_active else COLOR_TEXT_MUTED)
            self.screen.blit(t, t.get_rect(center=r.center))

    def _draw_metrics(self, px):
        """Vẽ thẻ hiển thị thông số thuật toán (Nodes mở rộng, Chi phí, Thời gian, Vòng lặp)."""
        card = pygame.Rect(px, 430, self.panel_width - 32, 175)
        self.screen.blit(self.font_bold.render("6. Thống kê (Metrics):", True, COLOR_TEXT_MAIN), (px, 410))
        pygame.draw.rect(self.screen, COLOR_CARD_BG, card, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_BORDER, card, 1, border_radius=6)

        st = str(self.metrics.get("status", ""))
        status_color = (COLOR_WIN if any(w in st for w in ("Hoàn thành", "Thắng"))
                        else COLOR_GAME_OVER if any(w in st for w in ("Thua", "OVER", "Không tìm thấy", "Thất bại", "❌"))
                        else (243, 156, 18) if "Đang" in st
                        else COLOR_BTN_PAUSE if "Tạm dừng" in st else COLOR_TEXT_MAIN)

        items = [
            ("Trạng thái:", st, status_color),
            ("Thuật toán:", self.metrics.get("algorithm", "") or self.get_selected_algorithm(), COLOR_ACCENT),
            ("Nodes mở rộng:", str(self.metrics.get("expanded", 0)), (255, 221, 0)),
            ("Chi phí:", str(self.metrics.get("cost", 0)), COLOR_FOOD),
            ("Độ dài đường:", str(self.metrics.get("path_length", 0)), COLOR_PATH),
            ("Thời gian:", f"{self.metrics.get('time_ms', 0)} ms", COLOR_TEXT_MUTED),
            ("Lượt (Turn):", str(self.metrics.get("turn", 0)), COLOR_ACCENT),
        ]
        for i, (lbl, val, c) in enumerate(items):
            ry = card.y + 10 + i * 22
            lbl_s, val_s = self.font_main.render(lbl, True, COLOR_TEXT_MUTED), self.font_bold.render(val, True, c)
            self.screen.blit(lbl_s, (card.x + 10, ry))
            self.screen.blit(val_s, (card.right - val_s.get_width() - 10, ry))

    def _draw_legend(self, px):
        """Vẽ chú thích màu sắc của các trạng thái ô trên bàn cờ."""
        self.screen.blit(self.font_bold.render("Chú thích:", True, COLOR_TEXT_MAIN), (px, 615))
        legends = [(COLOR_VISITED, "Explored"), (COLOR_FRONTIER, "Frontier"), (COLOR_PATH, "Path"), (COLOR_FOOD, "Food")]
        for i, (col, desc) in enumerate(legends):
            lx = px + i * 78
            pygame.draw.rect(self.screen, col, (lx, 637, 10, 10), border_radius=2)
            pygame.draw.rect(self.screen, (255, 255, 255), (lx, 637, 10, 10), 1, border_radius=2)
            self.screen.blit(self.font_small.render(desc, True, COLOR_TEXT_MUTED), (lx + 14, 635))

    def _draw_btn(self, rect, text, color, mpos):
        """Vẽ một nút bấm tương tác với hiệu ứng đổi sắc độ khi hover."""
        c = tuple(min(255, v + 25) for v in color) if rect.collidepoint(mpos) else color
        pygame.draw.rect(self.screen, c, rect, border_radius=5)
        t = self.font_bold.render(text, True, COLOR_TEXT_WHITE)
        self.screen.blit(t, t.get_rect(center=rect.center))

    # ── Tổng hợp Render & BaseUI Interface ──

    def render(self, game_state=None):
        """Vẽ toàn bộ khung hình theo đúng thứ tự Z-index và cập nhật màn hình."""
        self.draw_board()
        self.draw_panel()
        mpos = pygame.mouse.get_pos()
        for dd in self._dropdowns:
            dd.draw_dropdown_list(self.screen, mpos)
        pygame.display.flip()

    def tick(self, fps=None):
        """Điều phối tốc độ khung hình theo speed hiện thời hoặc tham số fps."""
        self.clock.tick(fps if fps is not None else self.speed)

    def show_metrics(self, metrics):
        """Hiển thị metrics cập nhật từ engine hoặc agent (BaseUI interface)."""
        if isinstance(metrics, dict):
            for k, v in metrics.items():
                if k in self.metrics:
                    self.metrics[k] = v


# ── WRAPPER COMPATIBILITY CLASS – GUI_UI ───────────────────────────────────────

class GUI_UI(BaseUI):
    """Lớp adapter chuẩn hóa tương thích giữa PacmanUI và GameLoop (engine.py)."""

    def __init__(self):
        self.ui = PacmanUI()
        self.quit_requested = False

    def initialize(self):
        self.ui.initialize()

    def render(self, game_state):
        if game_state: self.ui.sync_from_engine(game_state)
        self.ui.render()
        self.ui.tick(30)

    def show_metrics(self, metrics):
        self.ui.show_metrics(metrics)


# ── STANDALONE APPLICATION RUNNER (Chạy trực tiếp python ui/g_ui.py) ──────────

def _algo_name_to_search_key(name):
    """Chuyển đổi tên hiển thị sang mã key của src/search (VD: 'A*' -> 'astar')."""
    return _ALGO_KEY_MAP.get(name, "astar")


def _heuristic_name_to_key(name):
    """Chuyển đổi tên hiển thị sang mã key của heuristics (VD: 'MST' -> 'mst')."""
    return _HEURISTIC_KEY_MAP.get(name, "mst")


def run_gui_app():
    """Điểm khởi chạy ứng dụng đồ họa độc lập: Quản lý vòng lặp tìm kiếm và đối kháng."""
    print("=" * 50)
    print("  PACMAN AI – NHÓM 13 – GIAO DIỆN ĐỒ HỌA")
    print("=" * 50)

    ui = PacmanUI(width=1100, height=740)
    search_steps, demo_path, search_step_idx, search_time_ms = [], [], 0, 0.0
    adversarial_agent, ghost_agents, turn_game_state, turn_count = None, [], None, 0

    def _build_game_state_from_ui():
        """Chuyển đổi dữ liệu bản đồ từ UI sang GameState của engine (col, row)."""
        from src.engine import GameState
        gs = GameState()
        gs.height, gs.width = ui.map_rows, ui.map_cols
        for r, row in enumerate(ui.raw_map):
            for c, ch in enumerate(row):
                if ch == '#': gs.walls.add((c, r))
        if ui.start_pos: gs.pacman_pos = (ui.start_pos[1], ui.start_pos[0])
        gs.ghosts_pos = [(gc, gr) for gr, gc in ui.initial_ghost_positions]
        gs.food = {(fc, fr) for fr, fc in ui.food_set}
        return gs

    def solve_offline(algo_name, heuristic_name):
        """Khởi chạy thuật toán tìm kiếm (BFS/DFS/UCS/A*) và chuyển đổi đường đi sang pixel tọa độ."""
        from src.agents import SearchAgent
        if not ui.start_pos or not ui.food_set: return [], [], 0.0, {}

        gs = _build_game_state_from_ui()
        try:
            agent = SearchAgent(algorithm_name=algo_name, heuristic=heuristic_name)
        except ValueError as e:
            print(f"[LỖI] Thuật toán không hợp lệ: {e}")
            return [], [], 0.0, {}

        t0 = time.perf_counter()
        agent._plan_path(gs)
        elapsed = (time.perf_counter() - t0) * 1000
        metrics = agent.get_metrics()

        dir_map = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
        path_rc = []
        if metrics.get("found", False) and agent.plan:
            curr_r, curr_c = ui.start_pos
            path_rc.append((curr_r, curr_c))
            for action in agent.plan:
                dx, dy = dir_map.get(action, (0, 0))
                curr_c += dx
                curr_r += dy
                path_rc.append((curr_r, curr_c))

        vis_steps, visited = [], set()
        for pos in path_rc:
            visited.add(pos)
            vis_steps.append({"visited": set(visited), "frontier": set(), "current": pos})

        return vis_steps, path_rc, elapsed, metrics

    def start_turn_based():
        """Khởi tạo vòng lặp đối kháng: Pacman (Alpha-Beta / Minimax) vs Ghosts (Chaser)."""
        nonlocal adversarial_agent, ghost_agents, turn_game_state, turn_count
        algo, turn_count = ui.get_selected_algorithm(), 0
        turn_game_state = _build_game_state_from_ui()

        from src.agents import MinimaxAgent, AlphaBetaAgent, ChaserGhostAgent
        if algo == "Alpha-Beta":
            adversarial_agent = AlphaBetaAgent(depth=3)
        else:
            adversarial_agent = MinimaxAgent(depth=3)
            if algo != "Minimax": ui._dd_algo.select_by_value("Minimax")

        ghost_agents = [ChaserGhostAgent(index=i + 1, random_prob=0.3) for i in range(len(turn_game_state.ghosts_pos))]
        ui.phase, ui.is_running, ui.is_paused = "TURN_BASED", True, False
        ui.metrics["status"] = f"Đối kháng ({ui.get_selected_algorithm()}): Đang chơi..."

    def _check_game_over_turn():
        """Kiểm tra điều kiện thắng/thua sau mỗi hành động trong game đối kháng."""
        if not turn_game_state.is_game_over: return False
        ui.sync_from_engine(turn_game_state)
        ui.phase, ui.is_running = "GAME_OVER", False
        if turn_game_state.is_win():
            ui.game_result, ui.metrics["status"] = "WIN", "🏆 Thắng! Ăn hết thức ăn!"
        elif turn_game_state.is_lose():
            ui.game_result, ui.metrics["status"] = "LOSE", "💀 Thua! Bị Ma bắt!"
        return True

    def execute_one_turn():
        """Thực hiện một lượt chơi đối kháng hoàn chỉnh: Pacman đi -> Ma đi -> Kiểm tra va chạm."""
        nonlocal turn_game_state, turn_count
        if turn_game_state is None or turn_game_state.is_game_over: return False

        turn_count += 1
        try:
            pacman_action = adversarial_agent.get_action(turn_game_state)
        except Exception as e:
            ui.phase, ui.is_running = "GAME_OVER", False
            ui.metrics["status"] = f"Lỗi tác tử Pacman: {e}"
            return False

        turn_game_state = turn_game_state.generate_successor(0, pacman_action)
        if _check_game_over_turn(): return False

        for i, g_agent in enumerate(ghost_agents):
            if i + 1 > len(turn_game_state.ghosts_pos): break
            turn_game_state = turn_game_state.generate_successor(i + 1, g_agent.get_action(turn_game_state))
            if _check_game_over_turn(): return False

        ui.sync_from_engine(turn_game_state)
        ui.metrics.update({"turn": turn_count, "cost": turn_game_state.score, "status": f"Turn {turn_count} | Thức ăn còn: {len(turn_game_state.food)}"})
        return True

    def _sync_ui_from_engine():
        """Đồng bộ trạng thái từ engine sang UI (tương thích backward)."""
        ui.sync_from_engine(turn_game_state)

    def reset_session():
        """Dọn sạch dữ liệu phiên chạy cũ khi Reset hoặc đổi Map."""
        nonlocal search_steps, demo_path, search_step_idx, adversarial_agent, ghost_agents, turn_game_state, turn_count
        search_steps, demo_path = [], []
        search_step_idx, turn_count = 0, 0
        adversarial_agent, ghost_agents, turn_game_state = None, [], None

    def start_offline_search():
        """Bắt đầu tính toán đường đi offline cho map không Ma."""
        nonlocal search_steps, demo_path, search_step_idx, search_time_ms
        algo_display = ui.get_selected_algorithm()
        if algo_display in PacmanUI.ALGO_ADVERSARIAL:
            ui.metrics["status"], ui.is_running = "⚠ Thuật toán đối kháng cần map có Ma!", False
            return False

        algo_key = _algo_name_to_search_key(algo_display)
        heuristic_key = _heuristic_name_to_key(ui.get_selected_heuristic())
        try:
            search_steps, demo_path, search_time_ms, m = solve_offline(algo_key, heuristic_key)
        except Exception as e:
            ui.metrics["status"], ui.is_running = f"Lỗi: {e}", False
            return False

        if not m.get("found", False) or not demo_path:
            ui.phase, ui.game_result, ui.is_running = "GAME_OVER", "NO_PATH", False
            ui.metrics["status"] = "❌ Không tìm thấy đường đi!"
            return False

        search_step_idx = 0
        ui.is_running, ui.phase = True, "SEARCHING"
        ui.metrics.update({
            "time_ms": round(search_time_ms, 2),
            "expanded": m.get("expanded_nodes", 0),
            "path_length": m.get("plan_length", 0)
        })
        return True

    def advance_search_step():
        """Tiến 1 bước animation trong giai đoạn SEARCHING."""
        nonlocal search_step_idx
        if search_step_idx < len(search_steps):
            s = search_steps[search_step_idx]
            ui.update_search_step(s["visited"], s["frontier"], s["current"])
            ui.set_metrics(expanded=len(s["visited"]), status=f"Đang duyệt ({search_step_idx + 1}/{len(search_steps)})")
            search_step_idx += 1
            return True
        return False

    def advance_moving_step():
        """Tiến 1 bước di chuyển của Pacman trên đường đi tối ưu."""
        if ui.advance_move_step():
            ui.set_metrics(status=f"Di chuyển ({ui.move_step_idx}/{len(ui.final_path)})")
            return True
        # Chỉ hiển thị chiến thắng khi toàn bộ thức ăn trên bản đồ đã thực sự được ăn
        if ui.food_set and ui.eaten_food >= ui.food_set:
            ui.phase, ui.game_result, ui.is_running = "GAME_OVER", "WIN", False
            ui.set_metrics(status="Hoàn thành! Pacman ăn hết đồ ăn!")
        else:
            ui.phase, ui.game_result, ui.is_running = "GAME_OVER", "NO_PATH", False
            ui.set_metrics(status="❌ Không tìm thấy đường đi!")
        return False

    # ── Vòng lặp chính của ứng dụng (Main Loop) ──
    while True:
        ev = ui.handle_events()
        if ev:
            act = ev.get("action")

            if act == "START":
                if ui.phase in ("IDLE", "GAME_OVER"):
                    ui.reset_search_state()
                    ui.metrics["algorithm"] = ui.get_selected_algorithm()
                    if ui.has_ghosts():
                        if ui.get_selected_algorithm() not in PacmanUI.ALGO_ADVERSARIAL:
                            ui.metrics["status"], ui.is_running = "⚠ Map có Ma chỉ hỗ trợ Minimax hoặc Alpha-Beta!", False
                        else:
                            start_turn_based()
                    elif start_offline_search():
                        ui.is_paused = False
                elif ui.phase in ("SEARCHING", "MOVING", "TURN_BASED"):
                    ui.is_paused = False

            elif act in ("RESET", "MAP_CHANGED"):
                reset_session()

            elif act == "STEP":
                if ui.phase == "IDLE":
                    ui.metrics["algorithm"] = ui.get_selected_algorithm()
                    if ui.has_ghosts():
                        if ui.get_selected_algorithm() not in PacmanUI.ALGO_ADVERSARIAL:
                            ui.metrics["status"] = "⚠ Map có Ma chỉ hỗ trợ Minimax hoặc Alpha-Beta!"
                        else:
                            start_turn_based()
                            ui.is_paused = True
                            execute_one_turn()
                    elif ui.get_selected_algorithm() in PacmanUI.ALGO_ADVERSARIAL:
                        ui.metrics["status"] = "⚠ Thuật toán đối kháng cần map có Ma!"
                    elif start_offline_search():
                        ui.is_paused = True
                elif ui.phase == "TURN_BASED": execute_one_turn()
                elif ui.phase == "SEARCHING": advance_search_step()
                elif ui.phase == "MOVING": advance_moving_step()

        if ui.is_running and not ui.is_paused:
            if ui.phase == "SEARCHING":
                if not advance_search_step():
                    if demo_path and len(demo_path) >= 2:
                        ui.set_path(demo_path)
                        ui.current_node = None
                        ui.start_moving_phase()
                        ui.set_metrics(cost=len(demo_path) - 1, status="Tìm thấy đường! Đang di chuyển...")
                    else:
                        ui.phase, ui.game_result, ui.is_running = "GAME_OVER", "NO_PATH", False
                        ui.set_metrics(status="❌ Không tìm thấy đường đi!")
            elif ui.phase == "MOVING":
                advance_moving_step()
            elif ui.phase == "TURN_BASED":
                execute_one_turn()

        ui.render()
        ui.tick()


if __name__ == "__main__":
    run_gui_app()