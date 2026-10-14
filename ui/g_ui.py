"""
ui/g_ui.py
Giao diện đồ họa Pygame cho đồ án Pacman AI – Nhóm 13.

Tính năng chính:
  1. Dropdown Menu tương tác: Map / Algorithm (A*, Greedy, BFS, DFS, UCS, Minimax, Alpha-Beta) / Heuristic.
  2. Hai chế độ vận hành:
     • Map KHÔNG có Ma -> Offline Search (Duyệt tìm kiếm -> Di chuyển ăn đồ ăn).
     • Map CÓ Ma        -> Turn-by-Turn Game Loop (Pacman và Ghost luân phiên).
  3. Quản lý tài nguyên: Tự động nạp sprite và font tùy chỉnh (fallback an toàn).
  4. Kiến trúc tinh gọn (DRY): Tách các hàm bước duyệt/di chuyển dùng chung cho cả Chạy tự động và Nút Step.
  5. Hỗ trợ truyền tham số khởi tạo từ CLI (initial_map, initial_algo, initial_heuristic).
  6. Tương thích 100% với BaseUI, SearchAgent, AdversarialAgent và GameLoop.
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


# ── HÀM TIỆN ÍCH NẠP TÀI NGUYÊN ───────────────────────────────────────────────

def _load_font(size, bold=False):
    """Nạp font tùy chỉnh từ asset, tự động fallback về SysFont nếu lỗi."""
    try:
        f = pygame.font.Font(_FONT_PATH, size)
        if bold:
            f.set_bold(True)
        return f
    except (FileNotFoundError, OSError):
        return pygame.font.SysFont("Arial", size, bold=bold)


def _load_sprite(path, size):
    """Nạp ảnh sprite và scale chuẩn (size, size); trả về None nếu file thiếu."""
    if not os.path.exists(path):
        return None
    try:
        surf = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(surf, (size, size))
    except (pygame.error, OSError):
        return None


# ── DROPDOWN MENU TƯƠNG TÁC ───────────────────────────────────────────────────

class DropdownMenu:
    """Widget danh sách chọn thả xuống tùy biến giao diện phẳng."""

    def __init__(self, x, y, w, h, items, label="", font=None, font_small=None, max_visible=8):
        self.rect = pygame.Rect(x, y, w, h)
        self.items = list(items)
        self.label = label
        self.font = font or _load_font(13)
        self.font_small = font_small or _load_font(12)
        self.selected_idx = 0 if self.items else -1
        self.is_open = False
        self.scroll_offset = 0
        self.max_visible = max_visible
        self.enabled = True

    @property
    def value(self):
        return self.items[self.selected_idx] if 0 <= self.selected_idx < len(self.items) else None

    def set_items(self, new_items, keep_selection=False):
        old_val = self.value
        self.items = list(new_items)
        self.scroll_offset = 0
        if keep_selection and old_val in self.items:
            self.selected_idx = self.items.index(old_val)
        else:
            self.selected_idx = 0 if self.items else -1

    def select_by_value(self, value):
        if value in self.items:
            self.selected_idx = self.items.index(value)
            return True
        return False

    def _dropdown_rect(self):
        visible = min(len(self.items), self.max_visible)
        return pygame.Rect(self.rect.x, self.rect.bottom + 2, self.rect.width, visible * self.rect.height + 4)

    def handle_click(self, mx, my):
        """Xử lý nhấp chuột mở/đóng hoặc chọn item; trả về True nếu giá trị thay đổi."""
        if not self.enabled:
            return False
        if self.rect.collidepoint(mx, my):
            self.is_open = not self.is_open
            return False
        if self.is_open and self._dropdown_rect().collidepoint(mx, my):
            dd_rect = self._dropdown_rect()
            item_h = self.rect.height
            rel_y = my - (dd_rect.y + 2)
            clicked_idx = self.scroll_offset + int(rel_y // item_h)
            if 0 <= clicked_idx < len(self.items):
                changed = (self.selected_idx != clicked_idx)
                self.selected_idx = clicked_idx
                self.is_open = False
                return changed
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
    """Lớp giao diện đồ họa chính quản lý bàn cờ, bảng điều khiển và tương tác người dùng."""

    ALGO_SEARCH = ["A*", "Greedy", "BFS", "DFS", "UCS"]
    ALGO_ADVERSARIAL = ["Minimax", "Alpha-Beta"]
    HEURISTICS = ["MST", "Maze (Farthest)", "Null"]
    ALGO_NEEDS_HEURISTIC = {"A*", "Greedy"}

    def __init__(self, width=1100, height=740):
        pygame.init()
        self.width, self.height = width, height
        self.panel_width = 320
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Pacman AI – Nhóm 13 (A*, Greedy, BFS, DFS, Minimax, Alpha-Beta)")
        self.clock = pygame.time.Clock()

        self.font_title = _load_font(18, bold=True)
        self.font_main = _load_font(14)
        self.font_bold = _load_font(14, bold=True)
        self.font_small = _load_font(12)
        self.font_stat = _load_font(13)

        self.board_rect = pygame.Rect(0, 0, width - self.panel_width, height)
        self.panel_rect = pygame.Rect(width - self.panel_width, 0, self.panel_width, height)

        self.raw_map, self.map_rows, self.map_cols = [], 0, 0
        self.cell_size, self.board_offset_x, self.board_offset_y = 30, 0, 0
        self.start_pos, self.pacman_pos, self.food_set, self.ghosts = None, None, set(), []
        self.initial_ghost_positions, self.eaten_food = [], set()

        self.phase = "IDLE"  # IDLE | SEARCHING | MOVING | TURN_BASED | GAME_OVER
        self.is_running = False
        self.is_paused = False
        self.speed = 20
        self.game_result = None

        self.visited_nodes = set()
        self.frontier_nodes = set()
        self.current_node = None
        self.final_path = []
        self.move_step_idx = 0
        self._frame_counter = 0

        self.metrics = {
            "algorithm": "A*", "heuristic": "MST", "status": "Sẵn sàng",
            "time_ms": 0.0, "cost": 0, "expanded": 0, "path_length": 0, "turn": 0,
        }

        self.maps_dir = os.path.join(_PROJECT_ROOT, "maps")
        self._init_dropdowns()
        self._init_ui_buttons()
        self._load_sprites()

        available_maps = self._scan_maps()
        if available_maps:
            self.load_map_file(os.path.join(self.maps_dir, available_maps[0] + ".txt"))

    def _scan_maps(self):
        """Quét toàn bộ file .txt trong thư mục maps/."""
        if not os.path.exists(self.maps_dir):
            return ["map_co_ban"]
        maps = [f[:-4] for f in sorted(os.listdir(self.maps_dir)) if f.endswith(".txt")]
        return maps if maps else ["map_co_ban"]

    def _init_dropdowns(self):
        """Khởi tạo các dropdown chọn Map, Thuật toán, Heuristic."""
        px = self.panel_rect.x + 16
        w = self.panel_width - 32
        h = 32
        self.dd_map = DropdownMenu(px, 55, w, h, self._scan_maps(), label="Bản đồ", font=self.font_main, font_small=self.font_small)
        self.dd_algo = DropdownMenu(px, 95, w, h, self.ALGO_SEARCH, label="Thuật toán", font=self.font_main, font_small=self.font_small)
        self.dd_heuristic = DropdownMenu(px, 135, w, h, self.HEURISTICS, label="Heuristic", font=self.font_main, font_small=self.font_small)
        self.dropdowns = [self.dd_map, self.dd_algo, self.dd_heuristic]

    def _init_ui_buttons(self):
        """Thiết lập tọa độ các nút bấm điều khiển và thanh trượt tốc độ."""
        px = self.panel_rect.x + 16
        w = self.panel_width - 32
        bw2 = (w - 8) // 2
        bw3 = (w - 16) // 3

        self.btn_start = pygame.Rect(px, 185, bw2, 34)
        self.btn_pause = pygame.Rect(px + bw2 + 8, 185, bw2, 34)
        self.btn_step = pygame.Rect(px, 227, bw3, 30)
        self.btn_reset = pygame.Rect(px + bw3 + 8, 227, bw3, 30)
        self.btn_quit = pygame.Rect(px + 2 * (bw3 + 8), 227, bw3, 30)
        self.slider_track = pygame.Rect(px + 10, 290, w - 20, 6)

    def _update_heuristic_state(self):
        """Bật/tắt dropdown heuristic tùy thuộc thuật toán có sử dụng heuristic hay không."""
        self.dd_heuristic.enabled = (self.get_selected_algorithm() in self.ALGO_NEEDS_HEURISTIC)

    def get_valid_algorithms_for_current_map(self):
        """Trả về danh sách thuật toán hợp lệ theo đặc tính bản đồ (có/không có Ma)."""
        return list(self.ALGO_ADVERSARIAL) if self.has_ghosts() else list(self.ALGO_SEARCH)

    def update_available_algorithms(self):
        """Cập nhật dropdown thuật toán cho phù hợp với bản đồ đang chọn."""
        valid = self.get_valid_algorithms_for_current_map()
        self.dd_algo.set_items(valid, keep_selection=True)
        self._update_heuristic_state()

    def _load_sprites(self):
        """Nạp sprite Pacman và Ma với kích thước phù hợp kích thước ô lưới."""
        sz = max(16, min(48, int(self.cell_size * 0.9)))
        self.spr_pacman = _load_sprite(_PACMAN_IMG, sz)
        self.spr_ghosts = {}
        for name, path in _GHOST_IMGS.items():
            s = _load_sprite(path, sz)
            if s:
                self.spr_ghosts[name] = s

    def initialize(self):
        pass

    def load_map_file(self, file_path):
        """Đọc và nạp dữ liệu bản đồ từ file .txt."""
        if not os.path.exists(file_path):
            return False
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [l.rstrip("\r\n") for l in f if l.strip()]
        if not lines:
            return False
        self.set_map(lines)
        return True

    def set_map(self, map_data):
        """Khởi tạo cấu trúc dữ liệu bản đồ, tính toán kích thước ô lưới phù hợp khung hình."""
        self.raw_map = [list(r) for r in map_data]
        self.map_rows = len(self.raw_map)
        self.map_cols = max(len(r) for r in self.raw_map) if self.raw_map else 0

        pad = 20
        max_w, max_h = self.board_rect.width - 2 * pad, self.board_rect.height - 2 * pad
        cs_w = max_w // max(1, self.map_cols)
        cs_h = max_h // max(1, self.map_rows)
        self.cell_size = max(12, min(50, min(cs_w, cs_h)))

        bw = self.map_cols * self.cell_size
        bh = self.map_rows * self.cell_size
        self.board_offset_x = (self.board_rect.width - bw) // 2
        self.board_offset_y = (self.board_rect.height - bh) // 2

        self.start_pos = None
        self.food_set = set()
        self.initial_ghost_positions = []

        for r in range(self.map_rows):
            for c in range(len(self.raw_map[r])):
                ch = self.raw_map[r][c]
                if ch == "P":
                    self.start_pos = (r, c)
                elif ch == ".":
                    self.food_set.add((r, c))
                elif ch == "G":
                    self.initial_ghost_positions.append((r, c))

        self._load_sprites()
        self.reset_search_state()
        self.update_available_algorithms()

    def reset_search_state(self):
        """Đưa trạng thái game và các tập nút duyệt về trạng thái ban đầu."""
        self.phase = "IDLE"
        self.is_running = False
        self.is_paused = False
        self.game_result = None
        self.visited_nodes.clear()
        self.frontier_nodes.clear()
        self.current_node = None
        self.final_path = []
        self.move_step_idx = 0
        self.pacman_pos = self.start_pos
        self.ghosts = list(self.initial_ghost_positions)
        self.eaten_food.clear()
        self.metrics.update({
            "status": "Sẵn sàng", "time_ms": 0.0, "cost": 0,
            "expanded": 0, "path_length": 0, "turn": 0,
        })

    def sync_from_engine(self, gs):
        """Đồng bộ vị trí Pacman, Ghost, Food từ GameState vào UI."""
        if gs.pacman_pos:
            self.pacman_pos = (gs.pacman_pos[1], gs.pacman_pos[0])
        self.ghosts = [(gp[1], gp[0]) for gp in gs.ghosts_pos]
        self.eaten_food = self.food_set - {(fp[1], fp[0]) for fp in gs.food}

    def update_search_step(self, visited=None, frontier=None, current=None):
        """Cập nhật các tập nút đã duyệt (visited), biên (frontier) và nút hiện tại."""
        if visited:
            self.visited_nodes = set(visited)
        if frontier is not None:
            self.frontier_nodes = set(frontier)
        self.current_node = current

    def set_path(self, path):
        """Thiết lập lộ trình đường đi tối ưu."""
        self.final_path = list(path) if path else []
        self.move_step_idx = 0

    def start_moving_phase(self):
        """Chuyển sang giai đoạn Pacman di chuyển thực tế trên lộ trình."""
        self.phase = "MOVING"
        self.move_step_idx = 0
        if self.final_path:
            self.pacman_pos = self.final_path[0]

    def advance_move_step(self):
        """Tiến 1 bước di chuyển của Pacman; trả về True nếu vẫn đang di chuyển."""
        if self.move_step_idx < len(self.final_path):
            self.pacman_pos = self.final_path[self.move_step_idx]
            if self.pacman_pos in self.food_set:
                self.eaten_food.add(self.pacman_pos)
            self.move_step_idx += 1
            return True
        return False

    def is_moving_done(self):
        return self.move_step_idx >= len(self.final_path)

    def update_pacman(self, pos):
        self.pacman_pos = pos
        if pos in self.food_set:
            self.eaten_food.add(pos)

    def set_metrics(self, **kwargs):
        """Cập nhật các chỉ số hiển thị ở bảng điều khiển một cách linh hoạt."""
        for k, v in kwargs.items():
            if v is not None:
                if k == "time_taken":
                    self.metrics["time_ms"] = round(v * 1000, 2)
                elif k in ("cost", "expanded", "status", "path_length", "time_ms", "turn"):
                    self.metrics[k] = v
                elif k in self.metrics:
                    self.metrics[k] = v

    def get_selected_algorithm(self):
        return self.dd_algo.value or "A*"

    def get_selected_map(self):
        return self.dd_map.value or ""

    def get_selected_heuristic(self):
        return self.dd_heuristic.value or "MST"

    def has_ghosts(self):
        return bool(self.initial_ghost_positions)

    def handle_events(self):
        """Xử lý sự kiện Pygame (chuột, phím, cửa sổ); trả về dict mô tả hành động."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    action = self._handle_click(event.pos)
                    if action:
                        return {"action": action}
                elif event.button in (4, 5):
                    d = 1 if event.button == 4 else -1
                    for dd in self.dropdowns:
                        if dd.is_open:
                            dd.handle_scroll(d)
                            break
            elif event.type == pygame.KEYDOWN:
                return self._handle_key(event.key)
            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0] and self.slider_track.collidepoint(event.pos):
                    self._update_slider(event.pos[0])
        return None

    def _handle_click(self, pos):
        """Điều phối nhấp chuột vào dropdown, nút bấm hoặc thanh trượt."""
        mx, my = pos
        open_dd = next((dd for dd in self.dropdowns if dd.is_open), None)
        if open_dd:
            changed = open_dd.handle_click(mx, my)
            if changed:
                if open_dd == self.dd_map:
                    self._on_map_changed()
                    return "MAP_CHANGED"
                elif open_dd == self.dd_algo:
                    self._update_heuristic_state()
            return None

        for dd in self.dropdowns:
            if dd.rect.collidepoint(mx, my):
                dd.handle_click(mx, my)
                return None

        if self.btn_start.collidepoint(mx, my):
            self.is_running = True
            self.is_paused = False
            return "START"
        elif self.btn_pause.collidepoint(mx, my):
            if self.is_running:
                self.is_paused = not self.is_paused
            return "PAUSE"
        elif self.btn_step.collidepoint(mx, my):
            return "STEP"
        elif self.btn_reset.collidepoint(mx, my):
            self.reset_search_state()
            return "RESET"
        elif self.btn_quit.collidepoint(mx, my):
            pygame.quit()
            sys.exit(0)
        elif self.slider_track.collidepoint(mx, my):
            self._update_slider(mx)
            return None
        return None

    def _on_map_changed(self):
        """Xử lý nạp bản đồ mới khi người dùng đổi lựa chọn trên dropdown."""
        map_name = self.dd_map.value
        if map_name:
            self.load_map_file(os.path.join(self.maps_dir, map_name + ".txt"))

    def _handle_key(self, key):
        """Phím tắt bàn phím: Space (Pause), S (Step), R (Reset), Esc/Q (Thoát)."""
        if key == pygame.K_SPACE:
            if self.is_running:
                self.is_paused = not self.is_paused
            return {"action": "PAUSE"}
        elif key == pygame.K_s:
            return {"action": "STEP"}
        elif key == pygame.K_r:
            self.reset_search_state()
            return {"action": "RESET"}
        elif key in (pygame.K_ESCAPE, pygame.K_q):
            pygame.quit()
            sys.exit(0)
        return None

    def _update_slider(self, mx):
        """Cập nhật giá trị tốc độ dựa trên vị trí kéo chuột trên thanh trượt."""
        r = (max(self.slider_track.left, min(mx, self.slider_track.right)) - self.slider_track.left) / self.slider_track.width
        self.speed = max(1, min(60, int(1 + r * 59)))

    # ── PHẦN VẼ BÀN CỜ (Bên trái) ─────────────────────────────────────────────

    def draw_board(self):
        """Vẽ toàn bộ bàn cờ: ô tường, sàn, thức ăn, tập visited/frontier, đường đi, tác tử."""
        self._frame_counter += 1
        pygame.draw.rect(self.screen, COLOR_BG, self.board_rect)
        cs = self.cell_size

        for r in range(self.map_rows):
            for c in range(len(self.raw_map[r])):
                cell = self.raw_map[r][c]
                x = self.board_offset_x + c * cs
                y = self.board_offset_y + r * cs
                rect = pygame.Rect(x, y, cs, cs)

                if cell == '#':
                    pygame.draw.rect(self.screen, COLOR_WALL, rect)
                    pygame.draw.rect(self.screen, COLOR_WALL_GRID, rect, 1)
                else:
                    pygame.draw.rect(self.screen, COLOR_FLOOR, rect)
                    if (r, c) == self.current_node:
                        pygame.draw.rect(self.screen, COLOR_ACCENT, rect)
                        pygame.draw.rect(self.screen, COLOR_TEXT_WHITE, rect, 2)
                    elif (r, c) in self.visited_nodes:
                        pygame.draw.rect(self.screen, COLOR_VISITED, rect)
                        pygame.draw.rect(self.screen, COLOR_VISITED_BORDER, rect, 1)
                    elif (r, c) in self.frontier_nodes:
                        pygame.draw.rect(self.screen, COLOR_FRONTIER, rect)
                        pygame.draw.rect(self.screen, COLOR_FRONTIER_BORDER, rect, 1)

                    if (r, c) in self.food_set and (r, c) not in self.eaten_food:
                        fr = max(2, cs // 6)
                        pygame.draw.circle(self.screen, COLOR_FOOD, rect.center, fr)

        if not self.has_ghosts() and self.food_set:
            cx, cy = self.board_offset_x + self.start_pos[1] * cs + cs // 2, self.board_offset_y + self.start_pos[0] * cs + cs // 2
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
        if len(self.final_path) < 2:
            return
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
            for pt in pts:
                pygame.draw.circle(self.screen, COLOR_PATH, pt, max(2, lw // 2))

    def _draw_pacman(self):
        """Vẽ Pacman bằng sprite hình ảnh; fallback sang hình học cơ bản nếu thiếu asset."""
        if not self.pacman_pos:
            return
        pr, pc = self.pacman_pos
        cs = self.cell_size
        cx, cy = self.board_offset_x + pc * cs, self.board_offset_y + pr * cs

        if self.spr_pacman:
            sw, sh = self.spr_pacman.get_size()
            self.screen.blit(self.spr_pacman, (cx + (cs - sw) // 2, cy + (cs - sh) // 2))
        else:
            center = (cx + cs // 2, cy + cs // 2)
            rad = max(4, int(cs * 0.42))
            pygame.draw.circle(self.screen, (255, 230, 0), center, rad)
            mouth_angle = 0.25 * math.pi * abs(math.sin(self._frame_counter * 0.2))
            pts = [center,
                   (center[0] + int(rad * math.cos(-mouth_angle)), center[1] + int(rad * math.sin(-mouth_angle))),
                   (center[0] + int(rad * math.cos(mouth_angle)), center[1] + int(rad * math.sin(mouth_angle)))]
            pygame.draw.polygon(self.screen, COLOR_FLOOR, pts)

    def _draw_ghosts(self):
        """Vẽ danh sách các con Ma trên bản đồ."""
        cs = self.cell_size
        fallback_colors = [(230, 50, 50), (50, 200, 230), (230, 150, 50)]

        for i, (gr, gc) in enumerate(self.ghosts):
            x = self.board_offset_x + gc * cs
            y = self.board_offset_y + gr * cs
            gname = _GHOST_NAMES[i % len(_GHOST_NAMES)]
            spr = self.spr_ghosts.get(gname)

            if spr:
                sw, sh = spr.get_size()
                self.screen.blit(spr, (x + (cs - sw) // 2, y + (cs - sh) // 2))
            else:
                color = fallback_colors[i % len(fallback_colors)]
                r = pygame.Rect(x + 2, y + 2, cs - 4, cs - 4)
                pygame.draw.ellipse(self.screen, color, r)

    def _draw_game_over_overlay(self):
        """Vẽ khung mờ thông báo kết quả ván chơi (Chiến thắng / Bị bắt / Vô nghiệm)."""
        overlay = pygame.Surface((self.board_rect.width, self.board_rect.height), pygame.SRCALPHA)
        overlay.fill(COLOR_OVERLAY)
        self.screen.blit(overlay, (0, 0))

        is_win = (self.game_result == "WIN")
        title_text = "CHIẾN THẮNG!" if is_win else "THUA CUỘC!" if self.game_result == "LOSE" else "KHÔNG CÓ LỜI GIẢI!"
        title_color = COLOR_WIN if is_win else COLOR_GAME_OVER

        box = pygame.Rect(self.board_rect.width // 2 - 160, self.board_rect.height // 2 - 60, 320, 120)
        pygame.draw.rect(self.screen, COLOR_CARD_BG, box, border_radius=10)
        pygame.draw.rect(self.screen, title_color, box, 2, border_radius=10)

        t_surf = self.font_title.render(title_text, True, title_color)
        self.screen.blit(t_surf, (box.centerx - t_surf.get_width() // 2, box.y + 20))

        sub = self.font_small.render("Nhấn RESET hoặc phím R để chơi lại", True, COLOR_TEXT_MUTED)
        self.screen.blit(sub, (box.centerx - sub.get_width() // 2, box.y + 65))

    # ── PHẦN VẼ BẢNG ĐIỀU KHIỂN (Bên phải) ────────────────────────────────────

    def draw_panel(self):
        """Vẽ toàn bộ bảng điều khiển bên phải: Dropdowns, Nút bấm, Slider, Metrics, Legend."""
        mpos = pygame.mouse.get_pos()
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, self.panel_rect)
        pygame.draw.line(self.screen, COLOR_DIVIDER, (self.panel_rect.x, 0), (self.panel_rect.x, self.height), 1)

        px = self.panel_rect.x + 16
        title = self.font_title.render("PACMAN AI", True, COLOR_ACCENT)
        self.screen.blit(title, (px, 16))
        sub = self.font_small.render("Nhóm 13 – Trí Tuệ Nhân Tạo", True, COLOR_TEXT_MUTED)
        self.screen.blit(sub, (px + title.get_width() + 10, 20))

        for dd in self.dropdowns:
            dd.draw_header(self.screen, mpos)

        # Nút bấm điều khiển
        start_txt = "▶ Tiếp tục" if (self.is_running and self.is_paused) else "▶ Bắt đầu"
        self._draw_btn(self.btn_start, start_txt, COLOR_BTN_START, mpos)

        pause_txt = "▶ Tiếp tục" if self.is_paused else "⏸ Tạm dừng"
        pause_col = COLOR_BTN_PAUSE if self.is_paused else COLOR_BTN_DEFAULT
        self._draw_btn(self.btn_pause, pause_txt, pause_col, mpos)

        self._draw_btn(self.btn_step, "⏭ Bước", COLOR_BTN_STEP, mpos)
        self._draw_btn(self.btn_reset, "↺ Reset", COLOR_BTN_RESET, mpos)
        self._draw_btn(self.btn_quit, "✕ Thoát", COLOR_BTN_DEFAULT, mpos)

        self._draw_slider(mpos)
        self._draw_metrics(px)
        self._draw_legend(px)

        # Vẽ danh sách dropdown mở sau cùng để đảm bảo Z-Index cao nhất
        for dd in reversed(self.dropdowns):
            if dd.is_open:
                dd.draw_dropdown_list(self.screen, mpos)
                break

    def _draw_slider(self, mpos):
        """Vẽ thanh trượt điều chỉnh tốc độ duyệt / di chuyển."""
        px = self.panel_rect.x + 16
        lbl = self.font_small.render(f"Tốc độ: {self.speed} bước/giây", True, COLOR_TEXT_MUTED)
        self.screen.blit(lbl, (px, 272))

        pygame.draw.rect(self.screen, COLOR_BORDER, self.slider_track, border_radius=3)
        r = (self.speed - 1) / 59
        fw = int(self.slider_track.width * r)
        fill_rect = pygame.Rect(self.slider_track.x, self.slider_track.y, fw, self.slider_track.height)
        pygame.draw.rect(self.screen, COLOR_ACCENT, fill_rect, border_radius=3)

        hx = self.slider_track.x + fw
        hy = self.slider_track.centery
        hcol = COLOR_TEXT_WHITE if self.slider_track.collidepoint(mpos) else COLOR_ACCENT
        pygame.draw.circle(self.screen, hcol, (hx, hy), 7)

    def _draw_metrics(self, px):
        """Vẽ thẻ hiển thị chỉ số thời gian, số nút mở rộng, chi phí và trạng thái."""
        card_w = self.panel_width - 32
        card_rect = pygame.Rect(px, 320, card_w, 205)
        pygame.draw.rect(self.screen, COLOR_CARD_BG, card_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BORDER, card_rect, 1, border_radius=8)

        ct = self.font_bold.render("THÔNG SỐ & KẾT QUẢ", True, COLOR_ACCENT)
        self.screen.blit(ct, (px + 12, 330))

        y = 358
        rows = [
            ("Thuật toán:", str(self.metrics.get("algorithm", "—"))),
            ("Thời gian tính:", f"{self.metrics.get('time_ms', 0):.2f} ms"),
            ("Nút đã mở rộng:", str(self.metrics.get("expanded", 0))),
            ("Độ dài đường đi:", str(self.metrics.get("path_length", len(self.final_path)))),
            ("Chi phí (Cost):", str(self.metrics.get("cost", 0))),
        ]
        for label, val in rows:
            self.screen.blit(self.font_stat.render(label, True, COLOR_TEXT_MUTED), (px + 12, y))
            v_surf = self.font_bold.render(val, True, COLOR_TEXT_WHITE)
            self.screen.blit(v_surf, (px + card_w - 12 - v_surf.get_width(), y))
            y += 24

        st = self.metrics.get("status", "Sẵn sàng")
        st_col = (COLOR_WIN if "Hoàn thành" in st or "chiến thắng" in st
                  else COLOR_GAME_OVER if ("❌" in st or "Lỗi" in st or "bị ma bắt" in st)
                  else COLOR_ACCENT)
        st_surf = self.font_bold.render(st, True, st_col)
        self.screen.blit(st_surf, (px + 12, card_rect.bottom - 26))

    def _draw_legend(self, px):
        """Vẽ bảng chú giải các màu sắc trên bản đồ."""
        y = 540
        self.screen.blit(self.font_small.render("CHÚ GIẢI", True, COLOR_TEXT_MUTED), (px, y))
        y += 18
        items = [
            (COLOR_ACCENT, "Điểm xuất phát"), (COLOR_FOOD, "Thức ăn / Mục tiêu"),
            (COLOR_VISITED, "Đã duyệt (Visited)"), (COLOR_FRONTIER, "Biên (Frontier)"),
            (COLOR_PATH, "Lộ trình tối ưu"),
        ]
        for col, text in items:
            pygame.draw.rect(self.screen, col, (px, y + 2, 12, 12), border_radius=2)
            self.screen.blit(self.font_small.render(text, True, COLOR_TEXT_MUTED), (px + 20, y))
            y += 18

    def _draw_btn(self, rect, text, color, mpos):
        """Hàm phụ trợ vẽ nút bấm với hiệu ứng hover."""
        bg = COLOR_BTN_HOVER if rect.collidepoint(mpos) else color
        pygame.draw.rect(self.screen, bg, rect, border_radius=5)
        pygame.draw.rect(self.screen, COLOR_BORDER, rect, 1, border_radius=5)
        t = self.font_main.render(text, True, COLOR_TEXT_WHITE)
        self.screen.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

    def render(self, game_state=None):
        """Render 1 khung hình hoàn chỉnh lên màn hình."""
        self.draw_board()
        self.draw_panel()
        pygame.display.flip()

    def tick(self, fps=None):
        """Điều tiết tốc độ khung hình."""
        self.clock.tick(fps or self.speed)

    def show_metrics(self, metrics):
        """Cập nhật và in kết quả metrics ra console."""
        print("\n--- KẾT QUẢ THUẬT TOÁN (GUI) ---")
        for k, v in metrics.items():
            print(f"  {k}: {v}")


# ── LỚP TƯƠNG THÍCH BaseUI CHO GameLoop ────────────────────────────────────────

class GUI_UI(BaseUI):
    """Lớp giao diện tương thích hoàn toàn với BaseUI để chạy cùng GameLoop của Engine."""

    def __init__(self, delay=0.15, step_mode=False, cell_size=40):
        self.delay = delay
        self.step_mode = step_mode
        self.cell_size = cell_size
        self.ui = None

    def initialize(self):
        if self.ui is None:
            self.ui = PacmanUI()
            self.ui.initialize()

    def render(self, game_state, is_pacman_move=False):
        if self.ui is None:
            self.initialize()
        self.ui.sync_from_engine(game_state)
        self.ui.metrics["cost"] = game_state.score
        self.ui.render(game_state)
        self.ui.tick()

    def show_metrics(self, metrics):
        if self.ui:
            self.ui.show_metrics(metrics)


# ── HÀM CHUYỂN ĐỔI TÊN THUẬT TOÁN & HEURISTIC ────────────────────────────────

_ALGO_KEY_MAP = {
    "BFS": "bfs",
    "DFS": "dfs",
    "UCS": "ucs",
    "A*": "astar",
    "Greedy": "greedy",
}

_HEURISTIC_KEY_MAP = {
    "MST": "mst",
    "Maze (Farthest)": "maze",
    "Null": "null",
}


def _algo_name_to_search_key(name):
    return _ALGO_KEY_MAP.get(name, str(name).lower())


def _heuristic_name_to_key(name):
    return _HEURISTIC_KEY_MAP.get(name, "mst")


# ── ĐIỂM KHỞI CHẠY ỨNG DỤNG ĐỒ HỌA (run_gui_app) ──────────────────────────────

def run_gui_app(initial_map=None, initial_algo=None, initial_heuristic=None):
    """Khởi chạy ứng dụng đồ họa GUI độc lập với vòng lặp sự kiện tinh gọn."""
    print("=" * 50)
    print("  PACMAN AI – NHÓM 13 – GIAO DIỆN ĐỒ HỌA")
    print("=" * 50)

    ui = PacmanUI(width=1100, height=740)

    # Nạp thiết lập ban đầu nếu có từ tham số dòng lệnh CLI
    if initial_map:
        clean_map = os.path.basename(initial_map).replace(".txt", "")
        if clean_map in ui.dd_map.items:
            ui.dd_map.select_by_value(clean_map)
            ui._on_map_changed()
        elif os.path.exists(initial_map):
            ui.load_map_file(initial_map)
    if initial_algo:
        algo_up = initial_algo.upper()
        matched = next((it for it in ui.dd_algo.items
                        if it.upper() == algo_up or it.upper().replace("-", "") == algo_up.replace("-", "")), None)
        if matched:
            ui.dd_algo.select_by_value(matched)
            ui._update_heuristic_state()
    if initial_heuristic:
        h_low = initial_heuristic.lower()
        matched_h = next((it for it in ui.dd_heuristic.items if h_low in it.lower()), None)
        if matched_h:
            ui.dd_heuristic.select_by_value(matched_h)

    # Biến trạng thái tìm kiếm offline & turn-based
    search_steps, demo_path, search_step_idx, search_time_ms = [], [], 0, 0.0
    adversarial_agent, ghost_agents, turn_game_state, turn_count = None, [], None, 0

    def _build_game_state_from_ui():
        """Chuyển đổi dữ liệu bản đồ từ UI sang GameState của engine."""
        from src.engine import GameState
        gs = GameState()
        gs.height, gs.width = ui.map_rows, ui.map_cols
        for r, row in enumerate(ui.raw_map):
            for c, ch in enumerate(row):
                if ch == '#':
                    gs.walls.add((c, r))
        if ui.start_pos:
            gs.pacman_pos = (ui.start_pos[1], ui.start_pos[0])
        gs.ghosts_pos = [(gc, gr) for gr, gc in ui.initial_ghost_positions]
        gs.food = {(fc, fr) for fr, fc in ui.food_set}
        return gs

    def solve_offline(algo_name, heuristic_name):
        """Khởi chạy thuật toán tìm kiếm (BFS/DFS/UCS/Greedy/A*) và tạo danh sách bước."""
        from src.agents import SearchAgent
        if not ui.start_pos or not ui.food_set:
            return [], [], 0.0, {}

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
        """Khởi tạo vòng lặp đối kháng lượt đi (Pacman ↔ Ghost)."""
        nonlocal adversarial_agent, ghost_agents, turn_game_state, turn_count
        algo = ui.get_selected_algorithm()
        turn_count = 0
        turn_game_state = _build_game_state_from_ui()

        from src.agents import MinimaxAgent, AlphaBetaAgent, ChaserGhostAgent
        adversarial_agent = MinimaxAgent(depth=3) if algo == "Minimax" else AlphaBetaAgent(depth=3)
        ghost_agents = [ChaserGhostAgent(index=i, random_prob=0.2, seed=100 + i)
                        for i in range(1, len(turn_game_state.ghosts_pos) + 1)]

        ui.sync_from_engine(turn_game_state)
        ui.phase, ui.is_running, ui.is_paused = "TURN_BASED", True, False
        ui.metrics.update({"turn": 0, "cost": turn_game_state.score, "status": "Bắt đầu đối kháng!"})

    def _check_game_over_turn():
        """Kiểm tra điều kiện kết thúc ván sau mỗi lượt."""
        nonlocal turn_game_state
        if turn_game_state.is_game_over:
            ui.sync_from_engine(turn_game_state)
            ui.phase, ui.is_running = "GAME_OVER", False
            ui.game_result = "WIN" if turn_game_state.end_reason == "win" else "LOSE"
            msg = ("🏆 Pacman chiến thắng!" if ui.game_result == "WIN"
                   else "💀 Pacman bị ma bắt!" if turn_game_state.end_reason == "ghost"
                   else "Hết lượt đi tối đa!")
            ui.metrics["status"] = msg
            return True
        return False

    def execute_one_turn():
        """Thực hiện một lượt luân phiên: Pacman đi 1 bước -> Mỗi Ma đi 1 bước."""
        nonlocal turn_game_state, turn_count
        if turn_game_state is None or turn_game_state.is_game_over:
            return False

        turn_count += 1
        try:
            pacman_action = adversarial_agent.get_action(turn_game_state)
        except Exception as e:
            ui.phase, ui.is_running = "GAME_OVER", False
            ui.metrics["status"] = f"Lỗi tác tử Pacman: {e}"
            return False

        turn_game_state = turn_game_state.generate_successor(0, pacman_action)
        if _check_game_over_turn():
            return False

        for i, g_agent in enumerate(ghost_agents):
            if i + 1 > len(turn_game_state.ghosts_pos):
                break
            turn_game_state = turn_game_state.generate_successor(i + 1, g_agent.get_action(turn_game_state))
            if _check_game_over_turn():
                return False

        ui.sync_from_engine(turn_game_state)
        ui.metrics.update({"turn": turn_count, "cost": turn_game_state.score,
                           "status": f"Turn {turn_count} | Thức ăn còn: {len(turn_game_state.food)}"})
        return True

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
        if ui.food_set and ui.eaten_food >= ui.food_set:
            ui.phase, ui.game_result, ui.is_running = "GAME_OVER", "WIN", False
            ui.set_metrics(status="🏆 Hoàn thành! Pacman ăn hết thức ăn!")
        else:
            ui.phase, ui.game_result, ui.is_running = "GAME_OVER", "NO_PATH", False
            ui.set_metrics(status="❌ Không tìm thấy đường đi!")
        return False

    # ── VÒNG LẶP CHÍNH CỦA ỨNG DỤNG (Main Loop) ──────────────────────────────
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
                elif ui.phase == "TURN_BASED":
                    execute_one_turn()
                elif ui.phase == "SEARCHING":
                    advance_search_step()
                elif ui.phase == "MOVING":
                    advance_moving_step()

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