"""
ui/g_ui.py
══════════════════════════════════════════════════════════════════════════════
Giao diện đồ họa Pygame cho đồ án Pacman AI – Nhóm 13.

Tính năng chính:
  1. Dropdown Menu tương tác:  Map / Algorithm / Heuristic
  2. Hai chế độ chạy:
     • Map KHÔNG có Ma → Offline Search (SEARCHING → MOVING)
     • Map CÓ Ma        → Turn-by-Turn Game Loop (Pacman ↔ Ghost luân phiên)
  3. Nạp sprite Pacman & Ghost từ thư mục asset/images/.
  4. Font tùy chỉnh từ asset/fonts/font.ttf.
  5. Kết nối trực tiếp với module tìm kiếm (src/search/) và agents (src/agents).

LƯU Ý: File này KHÔNG sửa đổi bất kỳ code nào trong thư mục search/.
══════════════════════════════════════════════════════════════════════════════
"""
import os
import sys
import time
import math
import pygame

# ── Thêm thư mục gốc dự án vào PYTHONPATH để import được src.* ──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ui.base_ui import BaseUI

# ══════════════════════════════════════════════════════════════════════════════
# ĐƯỜNG DẪN TÀI NGUYÊN (Asset Paths)
# ══════════════════════════════════════════════════════════════════════════════
_ASSET_DIR   = os.path.join(_PROJECT_ROOT, "asset")
_FONT_PATH   = os.path.join(_ASSET_DIR, "fonts", "font.ttf")
_IMG_DIR     = os.path.join(_ASSET_DIR, "images")
_PACMAN_IMG  = os.path.join(_IMG_DIR, "pacman", "pacman.png")
_GHOST_IMGS  = {
    "Blinky": os.path.join(_IMG_DIR, "ghosts", "Blinky.png"),
    "Inky":   os.path.join(_IMG_DIR, "ghosts", "Inky.png"),
    "Clyde":  os.path.join(_IMG_DIR, "ghosts", "Clyde.png"),
}
# Thứ tự gán tên ghost theo index xuất hiện trên map
_GHOST_NAMES = ["Blinky", "Inky", "Clyde"]

# ══════════════════════════════════════════════════════════════════════════════
# BẢNG MÀU RGB – Thiết kế Dark Navy / Cyan Accent
# ══════════════════════════════════════════════════════════════════════════════

# --- Nền & Khung ---
COLOR_BG             = (15,  18,  30)
COLOR_PANEL_BG       = (20,  24,  40)
COLOR_CARD_BG        = (30,  36,  58)
COLOR_BORDER         = (45,  55,  85)
COLOR_DIVIDER        = (38,  46,  72)

# --- Chữ ---
COLOR_TEXT_MAIN      = (235, 240, 245)
COLOR_TEXT_MUTED     = (140, 150, 170)
COLOR_TEXT_WHITE     = (255, 255, 255)

# --- Màu nhấn ---
COLOR_ACCENT         = (0,  180, 216)

# --- Bản đồ ---
COLOR_WALL           = (33,  70, 139)
COLOR_WALL_GRID      = (25,  55, 110)
COLOR_FLOOR          = (15,  18,  30)
COLOR_FOOD           = (255, 183,   3)
COLOR_GOAL           = (230,  57,  70)

# --- Lớp màu thuật toán ---
COLOR_VISITED        = (35,  60,  95)
COLOR_VISITED_BORDER = (50,  80, 120)
COLOR_FRONTIER       = (180, 110,  20)
COLOR_FRONTIER_BORDER= (220, 145,  40)
COLOR_PATH           = (46, 204, 113)

# --- Nút bấm ---
COLOR_BTN_DEFAULT    = (38,  48,  78)
COLOR_BTN_HOVER      = (55,  70, 110)
COLOR_BTN_ACTIVE     = (0,  160, 200)
COLOR_BTN_START      = (40, 167,  69)
COLOR_BTN_PAUSE      = (240, 150,   0)
COLOR_BTN_STEP       = (70,  85, 120)
COLOR_BTN_RESET      = (220,  53,  69)

# --- Dropdown ---
COLOR_DD_BG          = (28,  34,  56)
COLOR_DD_HOVER       = (45,  58,  95)
COLOR_DD_BORDER      = (60,  75, 115)
COLOR_DD_SELECTED    = (0,  140, 180)

# --- Game Over / Win ---
COLOR_GAME_OVER      = (220,  53,  69)
COLOR_WIN            = (46, 204, 113)
COLOR_OVERLAY        = (0,    0,   0, 150)


# ══════════════════════════════════════════════════════════════════════════════
# HÀM TIỆN ÍCH
# ══════════════════════════════════════════════════════════════════════════════

def _load_font(size, bold=False):
    """Nạp font từ asset/fonts/font.ttf, fallback sang SysFont nếu lỗi."""
    try:
        f = pygame.font.Font(_FONT_PATH, size)
        if bold:
            f.set_bold(True)
        return f
    except (FileNotFoundError, OSError):
        return pygame.font.SysFont("Arial", size, bold=bold)


def _load_sprite(path, size):
    """Nạp ảnh sprite từ đường dẫn, scale về (size, size).
    Trả về None nếu file không tồn tại."""
    if not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, (size, size))
    except pygame.error:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# DROPDOWN MENU – Hộp chọn thả xuống tương tác
# ══════════════════════════════════════════════════════════════════════════════

class DropdownMenu:
    """Dropdown Menu gọn gàng, hỗ trợ:
       - Đóng/mở bằng click vào header
       - Chọn item từ danh sách thả xuống
       - Vẽ sau cùng (top Z-index) để không bị đè
       - Mutual exclusive: chỉ 1 dropdown mở tại 1 thời điểm

    Tham số:
        x, y        : Tọa độ góc trên bên trái của header
        w, h        : Chiều rộng / cao của header
        items       : Danh sách chuỗi hiển thị
        label       : Nhãn tiêu đề hiển thị trước giá trị đang chọn
        font        : pygame.font.Font dùng vẽ chữ
        font_small  : Font nhỏ hơn cho danh sách items
        max_visible : Số item tối đa hiển thị khi mở (có thanh cuộn nếu vượt)
    """

    def __init__(self, x, y, w, h, items, label="", font=None, font_small=None,
                 max_visible=8):
        self.rect = pygame.Rect(x, y, w, h)
        self.items = list(items)
        self.label = label
        self.font = font
        self.font_small = font_small or font
        self.max_visible = max_visible
        self.selected_idx = 0
        self.is_open = False
        self.hovered_idx = -1          # Item đang hover (trong danh sách)
        self.scroll_offset = 0         # Offset cuộn (cho danh sách dài)
        self.enabled = True            # Có cho phép tương tác không

    @property
    def value(self):
        """Trả về item đang được chọn."""
        if 0 <= self.selected_idx < len(self.items):
            return self.items[self.selected_idx]
        return None

    def set_items(self, new_items, keep_selection=False):
        """Cập nhật danh sách items, reset selection nếu cần."""
        old_val = self.value
        self.items = list(new_items)
        if keep_selection and old_val in self.items:
            self.selected_idx = self.items.index(old_val)
        else:
            self.selected_idx = 0
        self.scroll_offset = 0
        self.is_open = False
        self.hovered_idx = -1

    def select_by_value(self, value):
        """Chọn item theo giá trị (chuỗi)."""
        if value in self.items:
            self.selected_idx = self.items.index(value)

    # ── Tính toán rect danh sách mở ──
    def _dropdown_rect(self):
        """Trả về Rect bao quanh toàn bộ danh sách thả xuống."""
        visible = min(len(self.items), self.max_visible)
        item_h = self.rect.height
        return pygame.Rect(self.rect.x, self.rect.bottom + 2,
                           self.rect.width, visible * item_h + 4)

    # ── Xử lý click chuột ──
    def handle_click(self, mx, my):
        """Xử lý click chuột. Trả về True nếu có thay đổi selection."""
        if not self.enabled:
            return False

        # Click vào header → toggle mở/đóng
        if self.rect.collidepoint(mx, my):
            self.is_open = not self.is_open
            self.scroll_offset = 0
            return False

        # Click vào item trong danh sách (khi đang mở)
        if self.is_open:
            dd_rect = self._dropdown_rect()
            if dd_rect.collidepoint(mx, my):
                item_h = self.rect.height
                rel_y = my - dd_rect.y - 2
                idx = self.scroll_offset + int(rel_y / item_h)
                if 0 <= idx < len(self.items):
                    self.selected_idx = idx
                    self.is_open = False
                    return True
            # Click ra ngoài → đóng
            self.is_open = False
        return False

    def handle_scroll(self, direction):
        """Xử lý cuộn chuột khi dropdown đang mở."""
        if not self.is_open:
            return
        max_offset = max(0, len(self.items) - self.max_visible)
        self.scroll_offset = max(0, min(max_offset,
                                        self.scroll_offset - direction))

    # ── Vẽ dropdown ──
    def draw_header(self, surface, mpos):
        """Vẽ phần header (hộp chọn hiện tại)."""
        # Xác định màu nền
        if not self.enabled:
            bg = COLOR_BTN_DEFAULT
            border = COLOR_BORDER
            text_color = (80, 90, 110)
        elif self.is_open:
            bg = COLOR_DD_SELECTED
            border = COLOR_ACCENT
            text_color = COLOR_TEXT_WHITE
        elif self.rect.collidepoint(mpos):
            bg = COLOR_BTN_HOVER
            border = COLOR_ACCENT
            text_color = COLOR_TEXT_MAIN
        else:
            bg = COLOR_DD_BG
            border = COLOR_DD_BORDER
            text_color = COLOR_TEXT_MAIN

        pygame.draw.rect(surface, bg, self.rect, border_radius=5)
        pygame.draw.rect(surface, border, self.rect, 1, border_radius=5)

        # Chữ hiển thị: "label: value" hoặc chỉ "value"
        display_text = self.value or "—"
        if self.label:
            display_text = f"{self.label}: {display_text}"
        # Cắt text nếu quá dài
        max_text_w = self.rect.width - 28
        t = self.font.render(display_text, True, text_color)
        if t.get_width() > max_text_w:
            # Cắt dần cho vừa
            while len(display_text) > 3 and t.get_width() > max_text_w:
                display_text = display_text[:-2] + "…"
                t = self.font.render(display_text, True, text_color)
        surface.blit(t, (self.rect.x + 10, self.rect.centery - t.get_height() // 2))

        # Mũi tên ▼ / ▲
        arrow = "▲" if self.is_open else "▼"
        a_surf = self.font.render(arrow, True, text_color)
        surface.blit(a_surf, (self.rect.right - a_surf.get_width() - 8,
                              self.rect.centery - a_surf.get_height() // 2))

    def draw_dropdown_list(self, surface, mpos):
        """Vẽ danh sách thả xuống (chỉ khi đang mở).
        Phải gọi SAU TẤT CẢ các element khác (top Z-index)."""
        if not self.is_open or not self.items:
            return

        dd_rect = self._dropdown_rect()
        item_h = self.rect.height

        # Nền dropdown + viền
        pygame.draw.rect(surface, COLOR_DD_BG, dd_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_DD_BORDER, dd_rect, 1, border_radius=4)

        visible = min(len(self.items), self.max_visible)
        for i in range(visible):
            idx = self.scroll_offset + i
            if idx >= len(self.items):
                break

            item_rect = pygame.Rect(dd_rect.x + 2, dd_rect.y + 2 + i * item_h,
                                    dd_rect.width - 4, item_h)

            # Xác định màu nền item
            if idx == self.selected_idx:
                ibg = COLOR_DD_SELECTED
                itc = COLOR_TEXT_WHITE
            elif item_rect.collidepoint(mpos):
                ibg = COLOR_DD_HOVER
                itc = COLOR_TEXT_MAIN
            else:
                ibg = COLOR_DD_BG
                itc = COLOR_TEXT_MUTED

            pygame.draw.rect(surface, ibg, item_rect, border_radius=3)
            t = self.font_small.render(self.items[idx], True, itc)
            surface.blit(t, (item_rect.x + 10,
                             item_rect.centery - t.get_height() // 2))

        # Thanh cuộn nhỏ (nếu danh sách dài hơn max_visible)
        if len(self.items) > self.max_visible:
            scroll_h = max(10, int(dd_rect.height * self.max_visible / len(self.items)))
            max_offset = len(self.items) - self.max_visible
            scroll_y = dd_rect.y + int((dd_rect.height - scroll_h) * self.scroll_offset / max_offset)
            scroll_rect = pygame.Rect(dd_rect.right - 6, scroll_y, 4, scroll_h)
            pygame.draw.rect(surface, COLOR_ACCENT, scroll_rect, border_radius=2)

    def contains_point(self, mx, my):
        """Kiểm tra xem điểm (mx, my) có nằm trong vùng header hoặc danh sách không."""
        if self.rect.collidepoint(mx, my):
            return True
        if self.is_open and self._dropdown_rect().collidepoint(mx, my):
            return True
        return False


# ══════════════════════════════════════════════════════════════════════════════
# LỚP GIAO DIỆN CHÍNH – PacmanUI
# ══════════════════════════════════════════════════════════════════════════════

class PacmanUI(BaseUI):
    """Giao diện Pygame chính cho Pacman AI.

    Kế thừa BaseUI, cung cấp đầy đủ các method interface:
    initialize(), render(), show_metrics(), load_map_file(), set_map(),
    reset_search_state(), update_search_step(), set_path(), set_metrics(),
    handle_events(), tick().
    """

    # ── Danh sách thuật toán & heuristic ──
    # Thuật toán tìm kiếm đường đi (dành cho map KHÔNG có Ma)
    ALGO_SEARCH = ["A*", "Greedy", "BFS", "DFS", "UCS"]
    # Thuật toán đối kháng (dành cho map CÓ Ma)
    ALGO_ADVERSARIAL = ["Minimax", "Alpha-Beta"]
    # Toàn bộ thuật toán hệ thống hỗ trợ
    ALGORITHMS = ALGO_SEARCH + ALGO_ADVERSARIAL
    # Thuật toán cần heuristic (A* và Greedy)
    ALGO_NEEDS_HEURISTIC = {"A*", "Greedy"}
    # Danh sách heuristic
    HEURISTICS = ["MST", "Maze (Farthest)", "Null"]

    def __init__(self, width=1100, height=740):
        """Khởi tạo toàn bộ giao diện Pygame.

        Tham số:
            width  : Chiều rộng cửa sổ (px)
            height : Chiều cao cửa sổ (px)
        """
        pygame.init()
        pygame.display.set_caption("Pacman AI Search – Nhóm 13")
        self.screen_width, self.screen_height = width, height
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()

        # ── Font chữ tùy chỉnh ──
        self.font_title = _load_font(20, bold=True)
        self.font_bold  = _load_font(13, bold=True)
        self.font_main  = _load_font(12)
        self.font_small = _load_font(11)

        # ── Layout: Board (trái) | Panel Sidebar (phải) ──
        self.panel_width = 360
        self.panel_x = width - self.panel_width
        self.board_rect = pygame.Rect(0, 0, self.panel_x, height)

        # ── Quét danh sách file map trong thư mục maps/ ──
        self.map_files = self._scan_maps()

        # ── Trạng thái tương tác ──
        self.is_running = False
        self.is_paused = False
        self.speed = 10                 # Tốc độ (bước/giây)
        self.slider_dragging = False

        # ── Dữ liệu bản đồ ──
        self.raw_map = []               # Ma trận ký tự bản đồ
        self.map_rows = 0
        self.map_cols = 0
        self.cell_size = 30
        self.board_offset_x = 20
        self.board_offset_y = 20

        # ── Vị trí thực thể ──
        self.pacman_pos = None          # (row, col) – tọa độ hiện tại của Pacman
        self.start_pos = None           # (row, col) – vị trí ban đầu Pacman
        self.ghost_positions = []       # [(row, col), ...] – vị trí hiện tại các Ghost
        self.initial_ghost_positions = []  # Vị trí ban đầu Ghost (để reset)
        self.food_set = set()           # Tập tọa độ thức ăn ban đầu
        self.eaten_food = set()         # Tập tọa độ thức ăn đã bị ăn

        # ── Dữ liệu thuật toán (Offline Search) ──
        self.visited_nodes = set()
        self.frontier_nodes = set()
        self.final_path = []
        self.current_node = None        # Node đang xét (highlight SEARCHING)

        # ── State Machine ──
        # "IDLE"       → Chờ bấm Start
        # "SEARCHING"  → Thuật toán đang duyệt (Pacman đứng im)
        # "MOVING"     → Pacman di chuyển theo đường (map không Ma)
        # "TURN_BASED" → Vòng lặp luân phiên Pacman ↔ Ghost
        # "GAME_OVER"  → Kết thúc (thắng/thua)
        self.phase = "IDLE"
        self.move_step_idx = 0
        self._frame_counter = 0
        self.game_result = ""           # "WIN" / "LOSE" / "NO_PATH" / ""

        # ── Metrics thống kê ──
        self.metrics = {
            "status": "Sẵn sàng",
            "algorithm": "",
            "expanded": 0,
            "cost": 0,
            "time_ms": 0.0,
            "path_length": 0,
            "turn": 0,
        }

        # ── Sprite cache (được nạp/scale lại khi đổi map) ──
        self._pacman_sprite = None
        self._ghost_sprites = {}        # {tên_ghost: Surface}

        # ── Khởi tạo Dropdown Menu & các nút bấm ──
        self._init_dropdowns()
        self._init_ui_buttons()

        # ── Nạp map mặc định ──
        if self.map_files:
            self._dd_map.selected_idx = 0
            self.load_map_file(self.map_files[0])
            self.update_available_algorithms()

    # ══════════════════════════════════════════════════════════════════════
    # KHỞI TẠO UI (Dropdown, Nút bấm)
    # ══════════════════════════════════════════════════════════════════════

    def _scan_maps(self):
        """Quét thư mục maps/ lấy danh sách file .txt, sắp xếp theo tên."""
        maps_dir = os.path.join(_PROJECT_ROOT, "maps")
        if os.path.isdir(maps_dir):
            found = sorted(f for f in os.listdir(maps_dir) if f.endswith(".txt"))
            if found:
                return [os.path.join("maps", f).replace("\\", "/") for f in found]
        return []

    def _init_dropdowns(self):
        """Khởi tạo 3 Dropdown Menu: Map, Algorithm, Heuristic."""
        px = self.panel_x + 16
        pw = self.panel_width - 32
        dd_w = pw
        dd_h = 30

        # Dropdown 1: Chọn bản đồ
        map_display = [os.path.basename(m).replace(".txt", "") for m in self.map_files]
        self._dd_map = DropdownMenu(
            px, 80, dd_w, dd_h, map_display or ["(Không có map)"],
            font=self.font_bold, font_small=self.font_main, max_visible=8
        )

        # Dropdown 2: Chọn thuật toán
        self._dd_algo = DropdownMenu(
            px, 145, dd_w, dd_h, self.ALGORITHMS,
            font=self.font_bold, font_small=self.font_main, max_visible=8
        )

        # Dropdown 3: Chọn heuristic (chỉ bật khi thuật toán cần)
        self._dd_heuristic = DropdownMenu(
            px, 210, dd_w, dd_h, self.HEURISTICS,
            font=self.font_bold, font_small=self.font_main, max_visible=6
        )
        self._update_heuristic_state()

        # Danh sách tất cả dropdown (dùng cho mutual exclusive)
        self._dropdowns = [self._dd_map, self._dd_algo, self._dd_heuristic]

    def _init_ui_buttons(self):
        """Tính tọa độ các nút điều khiển: Start, Pause, Step, Reset, Slider."""
        px = self.panel_x + 16
        pw = self.panel_width - 32
        bw = (pw - 24) // 4  # Chiều rộng mỗi nút (4 nút + 3 gap)
        y_btn = 280

        self.btn_start = pygame.Rect(px, y_btn, bw, 34)
        self.btn_pause = pygame.Rect(px + (bw + 8), y_btn, bw, 34)
        self.btn_step  = pygame.Rect(px + (bw + 8) * 2, y_btn, bw, 34)
        self.btn_reset = pygame.Rect(px + (bw + 8) * 3, y_btn, bw, 34)

        # Thanh slider tốc độ
        self.slider_track = pygame.Rect(px, 355, pw, 8)
        # Nút preset tốc độ
        sw = (pw - 24) // 4
        self.speed_presets = [
            (pygame.Rect(px + i * (sw + 8), 375, sw, 22), v, l)
            for i, (v, l) in enumerate([(3, "0.5x"), (10, "1x"), (25, "3x"), (60, "Max")])
        ]

    def _update_heuristic_state(self):
        """Bật/tắt Dropdown Heuristic tùy theo thuật toán đang chọn và loại map."""
        if self.has_ghosts():
            self._dd_heuristic.enabled = False
        else:
            algo = self._dd_algo.value
            self._dd_heuristic.enabled = (algo in self.ALGO_NEEDS_HEURISTIC)

    def get_valid_algorithms_for_current_map(self):
        """Trả về danh sách thuật toán hợp lệ cho bản đồ hiện tại.
        - Map có Ma   → chỉ cho phép Minimax, Alpha-Beta (đối kháng)
        - Map không Ma → chỉ cho phép A*, BFS, DFS, UCS (tìm kiếm đường đi)
        """
        if self.has_ghosts():
            return list(self.ALGO_ADVERSARIAL)
        else:
            return list(self.ALGO_SEARCH)

    def update_available_algorithms(self):
        """Cập nhật Dropdown Algorithm và Heuristic theo bản đồ hiện tại."""
        valid_algos = self.get_valid_algorithms_for_current_map()
        self._dd_algo.set_items(valid_algos, keep_selection=True)
        if self._dd_algo.value not in valid_algos:
            self._dd_algo.selected_idx = 0
        self._update_heuristic_state()

    # ══════════════════════════════════════════════════════════════════════
    # NẠP VÀ SCALE SPRITE
    # ══════════════════════════════════════════════════════════════════════

    def _load_sprites(self):
        """Nạp và scale sprite Pacman + Ghost theo cell_size hiện tại.
        Gọi lại mỗi khi đổi map (vì cell_size có thể thay đổi)."""
        cs = self.cell_size
        sprite_size = max(12, int(cs * 0.85))  # Sprite nhỏ hơn cell một chút

        # Pacman sprite
        self._pacman_sprite = _load_sprite(_PACMAN_IMG, sprite_size)

        # Ghost sprites
        self._ghost_sprites = {}
        for name, path in _GHOST_IMGS.items():
            spr = _load_sprite(path, sprite_size)
            if spr:
                self._ghost_sprites[name] = spr

    # ══════════════════════════════════════════════════════════════════════
    # API INTERFACE (kế thừa từ BaseUI)
    # ══════════════════════════════════════════════════════════════════════

    def initialize(self):
        """Khởi tạo giao diện (BaseUI interface)."""
        pass  # Đã khởi tạo trong __init__

    def load_map_file(self, file_path):
        """Đọc file bản đồ .txt và nạp vào giao diện.

        Tham số:
            file_path : Đường dẫn tương đối/tuyệt đối tới file map

        Trả về:
            True nếu nạp thành công, False nếu file không tồn tại.
        """
        # Thử cả đường dẫn tương đối từ gốc dự án
        full_path = file_path
        if not os.path.isabs(file_path):
            full_path = os.path.join(_PROJECT_ROOT, file_path)

        if not os.path.exists(full_path):
            return False
        with open(full_path, "r", encoding="utf-8") as f:
            lines = [ln.rstrip("\r\n") for ln in f if ln.strip()]
        self.set_map(lines)
        return True

    def set_map(self, map_data):
        """Nạp ma trận bản đồ, phân tích vị trí thực thể, tính cell_size.

        Ký tự bản đồ:
            '#' → Tường          'P' → Pacman
            'G' → Ghost          '.' → Thức ăn
            ' ' → Đường đi trống

        Tham số:
            map_data : Danh sách chuỗi (mỗi chuỗi = 1 hàng bản đồ)
        """
        self.raw_map = [list(row) for row in map_data]
        self.map_rows = len(self.raw_map)
        self.map_cols = max((len(r) for r in self.raw_map), default=0)

        # Phân tích vị trí thực thể
        self.start_pos = None
        self.ghost_positions = []
        self.initial_ghost_positions = []
        self.food_set = set()

        for r in range(self.map_rows):
            for c in range(len(self.raw_map[r])):
                ch = self.raw_map[r][c]
                if ch == 'P':
                    self.start_pos = (r, c)
                    self.pacman_pos = (r, c)
                elif ch == 'G':
                    self.ghost_positions.append((r, c))
                    self.initial_ghost_positions.append((r, c))
                elif ch == '.':
                    self.food_set.add((r, c))

        # Tính cell_size để bản đồ vừa khung vẽ
        if self.map_cols > 0 and self.map_rows > 0:
            aw = self.board_rect.width - 40
            ah = self.board_rect.height - 40
            self.cell_size = max(12, min(48, aw // self.map_cols, ah // self.map_rows))
            self.board_offset_x = (self.board_rect.width - self.map_cols * self.cell_size) // 2
            self.board_offset_y = (self.board_rect.height - self.map_rows * self.cell_size) // 2

        # Nạp lại sprite theo cell_size mới
        self._load_sprites()

        # Cập nhật thuật toán hợp lệ theo map mới
        if hasattr(self, "_dd_algo"):
            self.update_available_algorithms()

        # Reset trạng thái tìm kiếm
        self.reset_search_state()

    def reset_search_state(self):
        """Đặt lại toàn bộ tiến trình tìm kiếm và di chuyển.
        Khôi phục Pacman, Ghost về vị trí ban đầu; xóa visited/frontier/path."""
        self.visited_nodes.clear()
        self.frontier_nodes.clear()
        self.final_path = []
        self.eaten_food.clear()
        self.pacman_pos = self.start_pos
        self.ghost_positions = list(self.initial_ghost_positions)
        self.phase = "IDLE"
        self.current_node = None
        self.move_step_idx = 0
        self._frame_counter = 0
        self.is_running = False
        self.is_paused = False
        self.game_result = ""
        self.metrics = {
            "status": "Sẵn sàng",
            "algorithm": "",
            "expanded": 0,
            "cost": 0,
            "time_ms": 0.0,
            "path_length": 0,
            "turn": 0,
        }

    def update_search_step(self, visited=None, frontier=None, current=None):
        """GIAI ĐOẠN SEARCHING: Cập nhật tập explored/frontier và node đang xét.
        Pacman KHÔNG di chuyển. Đồ ăn KHÔNG bị ăn.

        Tham số:
            visited  : set/list tọa độ đã duyệt
            frontier : set/list tọa độ trong hàng đợi
            current  : tuple (r, c) node đang xét
        """
        self.phase = "SEARCHING"
        if visited is not None:
            self.visited_nodes.update(
                visited if isinstance(visited, (set, list)) else [visited])
        if frontier is not None:
            self.frontier_nodes = set(
                frontier if isinstance(frontier, (set, list)) else [frontier])
        if current is not None:
            self.current_node = current

    def set_path(self, path):
        """Thiết lập đường đi tối ưu và chuẩn bị giai đoạn MOVING.

        Tham số:
            path : Danh sách tọa độ (r, c) đường đi
        """
        self.final_path = list(path) if path else []
        self.metrics["path_length"] = len(self.final_path)
        self.move_step_idx = 0

    def start_moving_phase(self):
        """Chuyển sang GIAI ĐOẠN MOVING: Pacman bắt đầu đi theo final_path."""
        self.phase = "MOVING"
        self.move_step_idx = 0
        self.current_node = None
        if self.final_path:
            self.pacman_pos = self.final_path[0]

    def advance_move_step(self):
        """Di chuyển Pacman 1 bước trên final_path, ăn thức ăn nếu có.

        Trả về:
            True nếu còn bước tiếp theo, False nếu đã hết đường.
        """
        if self.phase != "MOVING" or not self.final_path:
            return False
        if self.move_step_idx >= len(self.final_path):
            return False

        pos = self.final_path[self.move_step_idx]
        self.pacman_pos = pos
        # Ăn thức ăn tại ô này
        if pos in self.food_set:
            self.eaten_food.add(pos)
        self.move_step_idx += 1
        return self.move_step_idx < len(self.final_path)

    def is_moving_done(self):
        """Kiểm tra Pacman đã đi hết final_path chưa."""
        return self.move_step_idx >= len(self.final_path)

    def update_pacman(self, pos):
        """Cập nhật vị trí Pacman trực tiếp."""
        self.pacman_pos = pos
        if self.phase == "MOVING" and pos is not None:
            if pos in self.food_set:
                self.eaten_food.add(pos)

    def set_metrics(self, expanded=None, cost=None, time_taken=None, status=None,
                    path_length=None, algorithm=None, turn=None):
        """Cập nhật thống kê hiệu năng (Metrics).

        Tham số:
            expanded   : Số node đã mở rộng
            cost       : Chi phí đường đi
            time_taken : Thời gian chạy (ms)
            status     : Chuỗi trạng thái hiển thị
            path_length: Độ dài đường đi
            algorithm  : Tên thuật toán
            turn       : Số lượt hiện tại
        """
        if expanded is not None:    self.metrics["expanded"] = expanded
        if cost is not None:        self.metrics["cost"] = cost
        if time_taken is not None:  self.metrics["time_ms"] = round(time_taken, 2)
        if status is not None:      self.metrics["status"] = status
        if path_length is not None: self.metrics["path_length"] = path_length
        if algorithm is not None:   self.metrics["algorithm"] = algorithm
        if turn is not None:        self.metrics["turn"] = turn

    def get_selected_algorithm(self):
        """Trả về tên thuật toán đang chọn trên Dropdown."""
        return self._dd_algo.value or "BFS"

    def get_selected_map(self):
        """Trả về đường dẫn file map đang chọn."""
        idx = self._dd_map.selected_idx
        if 0 <= idx < len(self.map_files):
            return self.map_files[idx]
        return None

    def get_selected_heuristic(self):
        """Trả về tên heuristic đang chọn trên Dropdown."""
        return self._dd_heuristic.value or "MST"

    def has_ghosts(self):
        """Kiểm tra bản đồ hiện tại có Ghost hay không."""
        return len(self.initial_ghost_positions) > 0

    # ══════════════════════════════════════════════════════════════════════
    # XỬ LÝ SỰ KIỆN (Events)
    # ══════════════════════════════════════════════════════════════════════

    def handle_events(self):
        """Lắng nghe và xử lý sự kiện Pygame.

        Trả về:
            dict mô tả hành động người dùng, hoặc None nếu không có.
        """
        action = None
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:  # Click trái
                    action = self._handle_click(ev.pos) or action
                elif ev.button in (4, 5):  # Cuộn chuột
                    direction = 1 if ev.button == 4 else -1
                    for dd in self._dropdowns:
                        if dd.is_open:
                            dd.handle_scroll(direction)
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self.slider_dragging = False
            elif ev.type == pygame.MOUSEMOTION and self.slider_dragging:
                self._update_slider(ev.pos[0])
                action = {"action": "SPEED_CHANGED", "speed": self.speed}
            elif ev.type == pygame.KEYDOWN:
                action = self._handle_key(ev.key) or action
        return action

    def _handle_click(self, pos):
        """Xử lý click chuột tại vị trí pos = (mx, my).

        Logic ưu tiên:
        1. Kiểm tra Dropdown đang mở (top Z-index) trước
        2. Kiểm tra Header Dropdown
        3. Kiểm tra các nút điều khiển & slider
        """
        mx, my = pos

        # ── Bước 1: Kiểm tra click vào Dropdown đang mở ──
        # (Mutual exclusive: đóng các dropdown khác trước)
        clicked_in_dropdown = False
        for dd in self._dropdowns:
            if dd.is_open and dd.contains_point(mx, my):
                changed = dd.handle_click(mx, my)
                clicked_in_dropdown = True
                if changed:
                    # Xử lý khi thay đổi selection
                    if dd is self._dd_map:
                        return self._on_map_changed()
                    elif dd is self._dd_algo:
                        self._update_heuristic_state()
                        self.reset_search_state()
                        return {"action": "ALGO_CHANGED", "algo": self.get_selected_algorithm()}
                    elif dd is self._dd_heuristic:
                        self.reset_search_state()
                        return {"action": "HEURISTIC_CHANGED"}
                break

        # Nếu click vào dropdown đang mở → không xử lý gì thêm
        if clicked_in_dropdown:
            return None

        # ── Bước 2: Đóng tất cả dropdown đang mở (click ra ngoài) ──
        any_was_open = any(dd.is_open for dd in self._dropdowns)
        for dd in self._dropdowns:
            dd.is_open = False

        # ── Bước 3: Kiểm tra click vào header Dropdown ──
        for dd in self._dropdowns:
            if dd.rect.collidepoint(mx, my) and dd.enabled:
                # Mở dropdown này, đóng tất cả dropdown khác
                for other in self._dropdowns:
                    if other is not dd:
                        other.is_open = False
                dd.is_open = True
                return None

        # Nếu vừa đóng dropdown bằng click ra ngoài → bỏ qua click
        if any_was_open:
            return None

        # ── Bước 4: Nút Start ──
        if self.btn_start.collidepoint(mx, my):
            if self.phase == "GAME_OVER":
                self.reset_search_state()
            self.is_running = True
            self.is_paused = False
            return {"action": "START", "algo": self.get_selected_algorithm()}

        # ── Bước 5: Nút Pause/Resume ──
        if self.btn_pause.collidepoint(mx, my) and self.is_running:
            self.is_paused = not self.is_paused
            self.metrics["status"] = "Tạm dừng" if self.is_paused else "Đang chạy..."
            return {"action": "PAUSE", "paused": self.is_paused}

        # ── Bước 6: Nút Step ──
        if self.btn_step.collidepoint(mx, my):
            self.is_paused = True
            return {"action": "STEP"}

        # ── Bước 7: Nút Reset ──
        if self.btn_reset.collidepoint(mx, my):
            self.reset_search_state()
            return {"action": "RESET"}

        # ── Bước 8: Thanh slider tốc độ ──
        if self.slider_track.collidepoint(mx, my):
            self.slider_dragging = True
            self._update_slider(mx)
            return {"action": "SPEED_CHANGED", "speed": self.speed}

        # ── Bước 9: Nút preset tốc độ ──
        for r, val, _ in self.speed_presets:
            if r.collidepoint(mx, my):
                self.speed = val
                return {"action": "SPEED_CHANGED", "speed": self.speed}

        return None

    def _on_map_changed(self):
        """Xử lý khi người dùng đổi map từ Dropdown."""
        idx = self._dd_map.selected_idx
        if 0 <= idx < len(self.map_files):
            self.load_map_file(self.map_files[idx])
            self.update_available_algorithms()
            if self.has_ghosts():
                self.metrics["status"] = "Map có Ma: Chỉ hỗ trợ Minimax / Alpha-Beta"
            else:
                self.metrics["status"] = "Map tìm kiếm: Chọn A*, BFS, DFS, UCS"
        return {"action": "MAP_CHANGED", "map": self.get_selected_map()}

    def _handle_key(self, key):
        """Xử lý phím tắt bàn phím."""
        if key == pygame.K_SPACE:
            if self.is_running:
                self.is_paused = not self.is_paused
                return {"action": "PAUSE" if self.is_paused else "START"}
            else:
                self.is_running = True
                self.is_paused = False
                return {"action": "START", "algo": self.get_selected_algorithm()}
        if key == pygame.K_r:
            self.reset_search_state()
            return {"action": "RESET"}
        if key == pygame.K_s:
            self.is_paused = True
            return {"action": "STEP"}
        if key == pygame.K_ESCAPE:
            # Đóng dropdown đang mở
            for dd in self._dropdowns:
                dd.is_open = False
        return None

    def _update_slider(self, mx):
        """Cập nhật tốc độ dựa theo vị trí chuột trên thanh slider."""
        ratio = (max(self.slider_track.left, min(mx, self.slider_track.right))
                 - self.slider_track.left) / self.slider_track.width
        self.speed = max(1, min(60, int(1 + ratio * 59)))

    # ══════════════════════════════════════════════════════════════════════
    # RENDERING – VẼ BOARD (bàn cờ bên trái)
    # ══════════════════════════════════════════════════════════════════════

    def draw_board(self):
        """Vẽ toàn bộ khu vực trò chơi: tường, thức ăn, explored/frontier,
        đường đi, Pacman sprite, Ghost sprite."""
        self._frame_counter += 1
        pygame.draw.rect(self.screen, COLOR_BG, self.board_rect)
        cs = self.cell_size

        # ── Vẽ từng ô bản đồ ──
        for r in range(self.map_rows):
            for c in range(len(self.raw_map[r])):
                cell = self.raw_map[r][c]
                x = self.board_offset_x + c * cs
                y = self.board_offset_y + r * cs
                rect = pygame.Rect(x, y, cs, cs)

                # --- Tường ---
                if cell == '#':
                    pygame.draw.rect(self.screen, COLOR_WALL, rect)
                    pygame.draw.rect(self.screen, COLOR_WALL_GRID, rect, 1)
                    continue

                # --- Nền đường đi ---
                pygame.draw.rect(self.screen, COLOR_FLOOR, rect)

                # --- Lớp màu thuật toán (Explored / Frontier) ---
                if (r, c) in self.visited_nodes:
                    pygame.draw.rect(self.screen, COLOR_VISITED, rect)
                    pygame.draw.rect(self.screen, COLOR_VISITED_BORDER, rect, 1)
                elif (r, c) in self.frontier_nodes:
                    pygame.draw.rect(self.screen, COLOR_FRONTIER, rect)
                    pygame.draw.rect(self.screen, COLOR_FRONTIER_BORDER, rect, 1)

                # --- Thức ăn: chỉ vẽ nếu CHƯA bị ăn ---
                if (r, c) in self.food_set and (r, c) not in self.eaten_food:
                    dot_radius = max(2, cs // 8)
                    pygame.draw.circle(self.screen, COLOR_FOOD, rect.center, dot_radius)

        # ── Highlight node đang xét (SEARCHING) ──
        if self.phase == "SEARCHING" and self.current_node is not None:
            cr, cc = self.current_node
            cx = self.board_offset_x + cc * cs + cs // 2
            cy = self.board_offset_y + cr * cs + cs // 2
            pulse = 0.7 + 0.3 * math.sin(self._frame_counter * 0.15)
            marker_size = int(cs * 0.35 * pulse)
            diamond = [
                (cx, cy - marker_size), (cx + marker_size, cy),
                (cx, cy + marker_size), (cx - marker_size, cy),
            ]
            pygame.draw.polygon(self.screen, COLOR_ACCENT, diamond)
            pygame.draw.polygon(self.screen, (255, 255, 255), diamond, 2)

        # ── Đường đi tối ưu ──
        self._draw_path()

        # ── Vẽ Ghost (sprite hoặc fallback) ──
        self._draw_ghosts()

        # ── Vẽ Pacman (sprite hoặc fallback) ──
        self._draw_pacman()

        # ── Overlay Game Over / Win ──
        if self.phase == "GAME_OVER":
            self._draw_game_over_overlay()

    def _draw_path(self):
        """Vẽ đường đi tối ưu (final_path) lên bản đồ."""
        if len(self.final_path) < 2:
            return
        cs = self.cell_size
        lw = max(3, cs // 6)

        if self.phase == "MOVING" and self.move_step_idx > 0:
            # Phần đã đi (mờ)
            if self.move_step_idx > 1:
                done_pts = [
                    (self.board_offset_x + c * cs + cs // 2,
                     self.board_offset_y + r * cs + cs // 2)
                    for r, c in self.final_path[:self.move_step_idx]
                ]
                pygame.draw.lines(self.screen, (30, 140, 75), False, done_pts, lw)
            # Phần chưa đi (sáng)
            remaining = self.final_path[max(0, self.move_step_idx - 1):]
            if len(remaining) > 1:
                rem_pts = [
                    (self.board_offset_x + c * cs + cs // 2,
                     self.board_offset_y + r * cs + cs // 2)
                    for r, c in remaining
                ]
                pygame.draw.lines(self.screen, COLOR_PATH, False, rem_pts, lw)
        else:
            # Vẽ toàn bộ đường đi
            pts = [
                (self.board_offset_x + c * cs + cs // 2,
                 self.board_offset_y + r * cs + cs // 2)
                for r, c in self.final_path
            ]
            pygame.draw.lines(self.screen, COLOR_PATH, False, pts, lw)
            for pt in pts:
                pygame.draw.circle(self.screen, COLOR_PATH, pt, max(2, lw // 2))

    def _draw_pacman(self):
        """Vẽ Pacman tại vị trí hiện tại bằng sprite.
        Nếu sprite không nạp được → fallback vẽ hình tròn vàng + miệng."""
        if not self.pacman_pos:
            return
        pr, pc = self.pacman_pos
        cs = self.cell_size
        cx = self.board_offset_x + pc * cs
        cy = self.board_offset_y + pr * cs

        if self._pacman_sprite:
            # Căn sprite vào giữa ô
            spr = self._pacman_sprite
            sx = cx + (cs - spr.get_width()) // 2
            sy = cy + (cs - spr.get_height()) // 2
            self.screen.blit(spr, (sx, sy))
        else:
            # Fallback: vẽ hình tròn vàng + miệng + mắt
            center_x = cx + cs // 2
            center_y = cy + cs // 2
            rad = max(6, int(cs * 0.42))
            pygame.draw.circle(self.screen, (255, 221, 0), (center_x, center_y), rad)
            pygame.draw.polygon(self.screen, COLOR_BG,
                                [(center_x, center_y),
                                 (center_x + rad, center_y - rad // 2),
                                 (center_x + rad, center_y + rad // 2)])
            eye_r = max(2, rad // 5)
            pygame.draw.circle(self.screen, (20, 20, 20),
                               (center_x, center_y - rad // 2), eye_r)

    def _draw_ghosts(self):
        """Vẽ tất cả Ghost tại vị trí hiện tại bằng sprite.
        Mỗi ghost được gán tên theo thứ tự (_GHOST_NAMES).
        Nếu sprite không có → fallback vẽ hình tròn đỏ."""
        cs = self.cell_size
        for i, (gr, gc) in enumerate(self.ghost_positions):
            gx = self.board_offset_x + gc * cs
            gy = self.board_offset_y + gr * cs
            name = _GHOST_NAMES[i % len(_GHOST_NAMES)]
            spr = self._ghost_sprites.get(name)

            if spr:
                sx = gx + (cs - spr.get_width()) // 2
                sy = gy + (cs - spr.get_height()) // 2
                self.screen.blit(spr, (sx, sy))
            else:
                # Fallback: vẽ hình tròn + chữ G
                center_x = gx + cs // 2
                center_y = gy + cs // 2
                rad = max(6, int(cs * 0.40))
                ghost_colors = [(255, 0, 0), (0, 255, 255), (255, 165, 0)]
                color = ghost_colors[i % len(ghost_colors)]
                pygame.draw.circle(self.screen, color, (center_x, center_y), rad)

    def _draw_game_over_overlay(self):
        """Vẽ overlay bán trong suốt khi game kết thúc (thắng/thua)."""
        # Tạo surface bán trong suốt
        overlay = pygame.Surface((self.board_rect.width, self.board_rect.height),
                                 pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        # Chọn màu và text theo kết quả
        if self.game_result == "WIN":
            text = "🏆 CHIẾN THẮNG!"
            color = COLOR_WIN
        elif self.game_result == "LOSE":
            text = "💀 GAME OVER!"
            color = COLOR_GAME_OVER
        elif self.game_result == "NO_PATH":
            text = "❌ KHÔNG CÓ LỜI GIẢI!"
            color = COLOR_GAME_OVER
        else:
            text = "KẾT THÚC"
            color = COLOR_TEXT_MAIN

        t_surf = self.font_title.render(text, True, color)
        tx = (self.board_rect.width - t_surf.get_width()) // 2
        ty = self.board_rect.height // 2 - 20
        self.screen.blit(t_surf, (tx, ty))

        # Hướng dẫn
        hint = self.font_main.render("Nhấn [Reset] hoặc [R] để chơi lại", True, COLOR_TEXT_MUTED)
        self.screen.blit(hint, ((self.board_rect.width - hint.get_width()) // 2, ty + 40))

    # ══════════════════════════════════════════════════════════════════════
    # RENDERING – VẼ SIDEBAR (Panel bên phải)
    # ══════════════════════════════════════════════════════════════════════

    def draw_panel(self):
        """Vẽ bảng điều khiển Sidebar: Dropdown, nút điều khiển, metrics, legend."""
        panel = pygame.Rect(self.panel_x, 0, self.panel_width, self.screen_height)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel)
        pygame.draw.line(self.screen, COLOR_BORDER,
                         (self.panel_x, 0), (self.panel_x, self.screen_height), 2)

        px = self.panel_x + 16
        mpos = pygame.mouse.get_pos()

        # ── Tiêu đề ──
        title = self.font_title.render("PACMAN AI – NHÓM 13", True, COLOR_ACCENT)
        self.screen.blit(title, (px, 12))
        sub = self.font_small.render("Bài tập lớn – Trí tuệ nhân tạo", True, COLOR_TEXT_MUTED)
        self.screen.blit(sub, (px, 38))

        # ── 1. Dropdown Bản đồ ──
        map_title = "1. Chọn bản đồ:" + (" [Có Ma]" if self.has_ghosts() else " [Không Ma]")
        map_title_color = (255, 140, 100) if self.has_ghosts() else COLOR_TEXT_MAIN
        self.screen.blit(
            self.font_bold.render(map_title, True, map_title_color), (px, 62))
        self._dd_map.draw_header(self.screen, mpos)

        # ── 2. Dropdown Thuật toán ──
        if self.has_ghosts():
            algo_title = "2. Thuật toán: (Chế độ Có Ma)"
            algo_color = (255, 160, 120)
        else:
            algo_title = "2. Thuật toán: (Chế độ Tìm kiếm)"
            algo_color = COLOR_TEXT_MAIN
        self.screen.blit(
            self.font_bold.render(algo_title, True, algo_color), (px, 127))
        self._dd_algo.draw_header(self.screen, mpos)

        # ── 3. Dropdown Heuristic (ẩn/vô hiệu hóa nếu không cần) ──
        heuristic_title = "3. Heuristic:" if self._dd_heuristic.enabled else "3. Heuristic: (Không khả dụng)"
        self.screen.blit(
            self.font_bold.render(heuristic_title, True,
                                  COLOR_TEXT_MAIN if self._dd_heuristic.enabled
                                  else (100, 110, 130)),
            (px, 192))
        self._dd_heuristic.draw_header(self.screen, mpos)

        # ── 4. Nút điều khiển mô phỏng ──
        self.screen.blit(
            self.font_bold.render("4. Điều khiển:", True, COLOR_TEXT_MAIN), (px, 257))
        label_start = "Tiếp tục" if self.is_paused else "Bắt đầu"
        self._draw_btn(self.btn_start, label_start, COLOR_BTN_START, mpos)
        self._draw_btn(self.btn_pause, "Tạm dừng", COLOR_BTN_PAUSE, mpos)
        self._draw_btn(self.btn_step,  "Từng bước", COLOR_BTN_STEP, mpos)
        self._draw_btn(self.btn_reset, "Đặt lại",   COLOR_BTN_RESET, mpos)

        # ── 5. Tốc độ + Slider ──
        self.screen.blit(
            self.font_bold.render(f"5. Tốc độ: {self.speed} bước/s", True, COLOR_TEXT_MAIN),
            (px, 330))
        self._draw_slider(mpos)

        # ── 6. Metrics ──
        self._draw_metrics(px)

        # ── 7. Legend ──
        self._draw_legend(px)

        # ── 8. Phím tắt ──
        shortcut = "Phím tắt: [Space] Chạy | [S] Bước | [R] Reset | [Esc] Đóng menu"
        self.screen.blit(
            self.font_small.render(shortcut, True, (100, 110, 130)),
            (px, self.screen_height - 22))

    def _draw_slider(self, mpos):
        """Vẽ thanh slider tốc độ + nút preset."""
        pw = self.panel_width - 32
        # Thanh nền
        pygame.draw.rect(self.screen, COLOR_BTN_DEFAULT, self.slider_track, border_radius=4)
        # Phần đã fill
        fill_w = int(((self.speed - 1) / 59) * self.slider_track.width)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.slider_track.x, self.slider_track.y, fill_w, 8)
            pygame.draw.rect(self.screen, COLOR_ACCENT, fill_rect, border_radius=4)
        # Nút kéo (knob)
        knob_x = self.slider_track.x + fill_w
        pygame.draw.circle(self.screen, COLOR_TEXT_WHITE,
                           (knob_x, self.slider_track.centery), 8)
        pygame.draw.circle(self.screen, COLOR_ACCENT,
                           (knob_x, self.slider_track.centery), 5)
        # Preset buttons
        for r, val, lbl in self.speed_presets:
            is_active = (self.speed == val)
            bg = COLOR_BTN_ACTIVE if is_active else COLOR_BTN_DEFAULT
            pygame.draw.rect(self.screen, bg, r, border_radius=3)
            if is_active:
                pygame.draw.rect(self.screen, COLOR_ACCENT, r, 1, border_radius=3)
            tc = COLOR_TEXT_WHITE if is_active else COLOR_TEXT_MUTED
            t = self.font_small.render(lbl, True, tc)
            self.screen.blit(t, t.get_rect(center=r.center))

    def _draw_metrics(self, px):
        """Vẽ thẻ thống kê hiệu năng (Metrics card)."""
        pw = self.panel_width - 32
        y = 410
        self.screen.blit(
            self.font_bold.render("6. Thống kê (Metrics):", True, COLOR_TEXT_MAIN),
            (px, y))
        card = pygame.Rect(px, y + 20, pw, 175)
        pygame.draw.rect(self.screen, COLOR_CARD_BG, card, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_BORDER, card, 1, border_radius=6)

        # Xác định màu trạng thái
        st = str(self.metrics.get("status", ""))
        if "Hoàn thành" in st or "Thắng" in st:
            status_color = COLOR_WIN
        elif any(k in st for k in ["Thua", "OVER", "Không", "không", "Lỗi", "❌"]):
            status_color = COLOR_GAME_OVER
        elif "Đang" in st:
            status_color = (243, 156, 18)
        elif "Tạm dừng" in st:
            status_color = COLOR_BTN_PAUSE
        else:
            status_color = COLOR_TEXT_MAIN

        algo_display = self.metrics.get("algorithm", "") or self.get_selected_algorithm()

        items = [
            ("Trạng thái:",     str(self.metrics.get("status", "")),     status_color),
            ("Thuật toán:",     algo_display,                            COLOR_ACCENT),
            ("Nodes mở rộng:",  str(self.metrics.get("expanded", 0)),    (255, 221, 0)),
            ("Chi phí:",        str(self.metrics.get("cost", 0)),        COLOR_FOOD),
            ("Độ dài đường:",   str(self.metrics.get("path_length", 0)), COLOR_PATH),
            ("Thời gian:",      f"{self.metrics.get('time_ms', 0)} ms",  COLOR_TEXT_MUTED),
            ("Lượt (Turn):",    str(self.metrics.get("turn", 0)),        COLOR_ACCENT),
        ]
        ry = card.y + 10
        for lbl, val, c in items:
            lbl_s = self.font_main.render(lbl, True, COLOR_TEXT_MUTED)
            self.screen.blit(lbl_s, (card.x + 10, ry))
            val_s = self.font_bold.render(val, True, c)
            self.screen.blit(val_s, (card.right - val_s.get_width() - 10, ry))
            ry += 22

    def _draw_legend(self, px):
        """Vẽ chú thích màu sắc (Legend) ở cuối sidebar."""
        y = 615
        self.screen.blit(
            self.font_bold.render("Chú thích:", True, COLOR_TEXT_MAIN), (px, y))
        legends = [
            (COLOR_VISITED,  "Explored"),
            (COLOR_FRONTIER, "Frontier"),
            (COLOR_PATH,     "Path"),
            (COLOR_FOOD,     "Food"),
        ]
        lx = px
        for col, desc in legends:
            pygame.draw.rect(self.screen, col, (lx, y + 22, 10, 10), border_radius=2)
            pygame.draw.rect(self.screen, (255, 255, 255), (lx, y + 22, 10, 10), 1, border_radius=2)
            self.screen.blit(self.font_small.render(desc, True, COLOR_TEXT_MUTED), (lx + 14, y + 20))
            lx += 78

    def _draw_btn(self, rect, text, color, mpos):
        """Vẽ một nút bấm với hiệu ứng hover."""
        c = tuple(min(255, v + 25) for v in color) if rect.collidepoint(mpos) else color
        pygame.draw.rect(self.screen, c, rect, border_radius=5)
        t = self.font_bold.render(text, True, COLOR_TEXT_WHITE)
        self.screen.blit(t, t.get_rect(center=rect.center))

    # ══════════════════════════════════════════════════════════════════════
    # RENDER TỔNG HỢP
    # ══════════════════════════════════════════════════════════════════════

    def render(self, game_state=None):
        """Vẽ lại toàn bộ khung hình.
        Tham số game_state được chấp nhận (BaseUI interface) nhưng không bắt buộc.
        """
        self.draw_board()
        self.draw_panel()

        # ── Vẽ Dropdown lists SAU CÙNG (top Z-index) ──
        mpos = pygame.mouse.get_pos()
        for dd in self._dropdowns:
            dd.draw_dropdown_list(self.screen, mpos)

        pygame.display.flip()

    def tick(self, fps=None):
        """Giới hạn FPS."""
        self.clock.tick(fps if fps is not None else self.speed)

    def show_metrics(self, metrics):
        """Hiển thị metrics (BaseUI interface)."""
        if isinstance(metrics, dict):
            for k, v in metrics.items():
                if k in self.metrics:
                    self.metrics[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# WRAPPER CLASS – GUI_UI (dùng cho main.py import)
# ══════════════════════════════════════════════════════════════════════════════

class GUI_UI(BaseUI):
    """Wrapper cho PacmanUI, triển khai đầy đủ interface BaseUI
    để tương thích với GameLoop trong engine.py."""

    def __init__(self, delay=0.15, step_mode=False, cell_size=40):
        self.ui = PacmanUI()
        self.quit_requested = False
        self.restart_requested = False
        self.delay = delay
        self.step_mode = step_mode
        self.turn = 0

    def initialize(self):
        self.ui.initialize()

    def render(self, game_state, is_pacman_move=False):
        """Đồng bộ GameState → PacmanUI rồi vẽ."""
        if game_state:
            # Đồng bộ vị trí từ engine GameState (tọa độ engine: (x,y) = (col,row))
            if game_state.pacman_pos:
                x, y = game_state.pacman_pos
                self.ui.pacman_pos = (y, x)
            # Ghost
            self.ui.ghost_positions = [(gy, gx) for gx, gy in game_state.ghosts_pos]
            # Food đã ăn
            all_initial = self.ui.food_set
            current_food = {(fy, fx) for fx, fy in game_state.food}
            self.ui.eaten_food = all_initial - current_food

            if game_state.is_game_over:
                self.ui.phase = "GAME_OVER"
                if game_state.is_win():
                    self.ui.game_result = "WIN"
                    self.ui.metrics["status"] = "🏆 Thắng! Ăn hết thức ăn!"
                elif game_state.is_lose():
                    self.ui.game_result = "LOSE"
                    self.ui.metrics["status"] = "💀 Thua! Bị Ma bắt!"
                elif game_state.end_reason in ("no_solution", "plan_exhausted"):
                    self.ui.game_result = "NO_PATH"
                    self.ui.metrics["status"] = "❌ Bản đồ không có lời giải!"
                else:
                    self.ui.game_result = "LOSE"
                    self.ui.metrics["status"] = f"Kết thúc: {game_state.end_reason}"
        self.ui.render()
        self.ui.tick(30)

    def show_metrics(self, metrics):
        self.ui.show_metrics(metrics)


# ══════════════════════════════════════════════════════════════════════════════
# STANDALONE GAME LOOP – Chạy trực tiếp: python ui/g_ui.py
# ══════════════════════════════════════════════════════════════════════════════

def _algo_name_to_search_key(name):
    """Chuyển tên thuật toán hiển thị → key dùng trong src/search.

    Ví dụ: 'A*' → 'astar', 'BFS' → 'bfs'
    """
    mapping = {
        "BFS": "bfs",
        "DFS": "dfs",
        "UCS": "ucs",
        "A*": "astar",
        "Greedy": "greedy",
        "Greedy Best-First": "greedy",
    }
    return mapping.get(name, "astar")


def _heuristic_name_to_key(name):
    """Chuyển tên heuristic hiển thị → key dùng trong src/search/heuristics.

    Ví dụ: 'MST' → 'mst', 'Maze (Farthest)' → 'maze'
    """
    mapping = {
        "MST": "mst",
        "Maze (Farthest)": "maze",
        "Null": "null",
    }
    return mapping.get(name, "mst")


def run_gui_app(initial_map=None, initial_algo=None, initial_heuristic=None):
    """Vòng lặp chính khi chạy GUI độc lập.

    Luồng xử lý:
    ──────────────────────────────────────────────────────────
    MAP KHÔNG CÓ MA:
      1. IDLE → User bấm Start
      2. SEARCHING → Thuật toán duyệt, Pacman đứng im, tô màu explored/frontier
      3. MOVING → Pacman di chuyển theo đường, ăn thức ăn
      4. GAME_OVER / IDLE

    MAP CÓ MA:
      1. IDLE → User bấm Start
      2. TURN_BASED → Vòng lặp luân phiên:
         a. Pacman ra quyết định 1 bước (Minimax/AlphaBeta/Search+tránh Ma)
         b. Ma di chuyển 1 bước
         c. Kiểm tra va chạm
      3. GAME_OVER / IDLE
    ──────────────────────────────────────────────────────────
    """
    print("=" * 50)
    print("  PACMAN AI – NHÓM 13 – GIAO DIỆN ĐỒ HỌA")
    print("=" * 50)

    ui = PacmanUI(width=1100, height=740)

    # Nạp thiết lập ban đầu nếu có từ tham số dòng lệnh
    if initial_map:
        clean_map = os.path.basename(initial_map).replace(".txt", "")
        if clean_map in ui._dd_map.items:
            ui._dd_map.select_by_value(clean_map)
            ui._on_map_changed()
        elif os.path.exists(initial_map):
            ui.load_map_file(initial_map)
            ui.update_available_algorithms()

    if initial_algo:
        algo_name_map = {
            "bfs": "BFS", "dfs": "DFS", "ucs": "UCS", "astar": "A*",
            "greedy": "Greedy", "gbfs": "Greedy",
            "minimax": "Minimax", "alphabeta": "Alpha-Beta"
        }
        val = algo_name_map.get(initial_algo.lower().replace("-", "").replace("_", ""), initial_algo)
        if val in ui._dd_algo.items:
            ui._dd_algo.select_by_value(val)
            ui._update_heuristic_state()

    if initial_heuristic:
        heur_map = {"mst": "MST", "maze": "Maze (Farthest)", "null": "Null"}
        val = heur_map.get(initial_heuristic.lower(), initial_heuristic)
        if val in ui._dd_heuristic.items:
            ui._dd_heuristic.select_by_value(val)

    # ── Biến trạng thái cho Offline Search (map không Ma) ──
    search_steps = []           # Danh sách bước duyệt
    demo_path = []              # Đường đi tìm được
    search_step_idx = 0         # Bước duyệt hiện tại
    search_time_ms = 0.0        # Thời gian thuật toán

    # ── Biến trạng thái cho Turn-Based (map có Ma) ──
    adversarial_agent = None    # Agent đối kháng cho Pacman
    ghost_agents = []           # Danh sách agent cho Ghost
    turn_game_state = None      # GameState engine dùng cho turn-based
    turn_count = 0

    def _build_game_state_from_ui():
        """Xây dựng GameState engine từ dữ liệu UI hiện tại.
        Chuyển đổi tọa độ (row, col) của UI → (x, y) = (col, row) của engine."""
        from src.engine import GameState
        gs = GameState()
        gs.height = ui.map_rows
        gs.width = ui.map_cols
        # Xây tập tường
        for r in range(ui.map_rows):
            for c in range(len(ui.raw_map[r])):
                if ui.raw_map[r][c] == '#':
                    gs.walls.add((c, r))   # engine dùng (x=col, y=row)
        # Pacman
        if ui.start_pos:
            pr, pc = ui.start_pos
            gs.pacman_pos = (pc, pr)
        # Ghosts
        gs.ghosts_pos = [(gc, gr) for gr, gc in ui.initial_ghost_positions]
        # Food (chưa ăn)
        gs.food = {(fc, fr) for fr, fc in ui.food_set}
        return gs

    def solve_offline(algo_name, heuristic_name):
        """Chạy thuật toán tìm kiếm Offline (BFS/DFS/UCS/A*/Greedy).
        Trả về (search_steps_for_vis, path_rc, elapsed_ms, metrics).

        Tham số:
            algo_name     : Tên thuật toán ('bfs', 'dfs', 'ucs', 'astar')
            heuristic_name: Tên heuristic ('mst', 'maze', 'null')
        """
        from src.agents import SearchAgent
        from src.engine import GameState

        if not ui.start_pos or not ui.food_set:
            return [], [], 0.0, {}

        # Xây dựng GameState engine
        gs = _build_game_state_from_ui()

        # Tạo SearchAgent
        try:
            agent = SearchAgent(algorithm_name=algo_name, heuristic=heuristic_name)
        except ValueError as e:
            print(f"[LỖI] Thuật toán không hợp lệ: {e}")
            return [], [], 0.0, {}

        # Gọi _plan_path để chạy thuật toán
        t0 = time.perf_counter()
        agent._plan_path(gs)
        elapsed = (time.perf_counter() - t0) * 1000

        metrics = agent.get_metrics()

        # Chuyển chuỗi action → danh sách tọa độ (row, col)
        direction_map = {
            "UP": (0, -1), "DOWN": (0, 1),
            "LEFT": (-1, 0), "RIGHT": (1, 0),
        }
        path_rc = []
        if agent.plan and metrics.get("found", False):
            # Bắt đầu từ start_pos
            curr_r, curr_c = ui.start_pos
            path_rc.append((curr_r, curr_c))
            actions = list(agent.plan)
            for action in actions:
                dx, dy = direction_map.get(action, (0, 0))
                curr_c += dx
                curr_r += dy
                path_rc.append((curr_r, curr_c))

        # Tạo visualization steps (simplified: chỉ dùng visited_nodes từ metrics)
        # Vì thuật toán thật chạy xong ngay, ta tạo animation steps từ path
        vis_steps = []
        visited = set()
        if path_rc:
            for i, pos in enumerate(path_rc):
                visited.add(pos)
                vis_steps.append({
                    "visited": set(visited),
                    "frontier": set(),
                    "current": pos,
                })

        return vis_steps, path_rc, elapsed, metrics

    def start_turn_based():
        """Khởi tạo chế độ Turn-Based cho map có Ma."""
        nonlocal adversarial_agent, ghost_agents, turn_game_state, turn_count

        algo = ui.get_selected_algorithm()
        turn_count = 0

        # Xây dựng GameState engine
        turn_game_state = _build_game_state_from_ui()

        # Tạo Pacman Agent (Minimax hoặc AlphaBeta)
        from src.agents import MinimaxAgent, AlphaBetaAgent, ChaserGhostAgent

        if algo == "Alpha-Beta":
            adversarial_agent = AlphaBetaAgent(depth=3)
        elif algo == "Minimax":
            adversarial_agent = MinimaxAgent(depth=3)
        else:
            # Thuật toán không hợp lệ cho map có Ma → fallback an toàn sang Minimax
            adversarial_agent = MinimaxAgent(depth=3)
            ui._dd_algo.select_by_value("Minimax")

        # Tạo Ghost Agents (ChaserGhostAgent đuổi Pacman)
        ghost_agents = []
        for i in range(len(turn_game_state.ghosts_pos)):
            ghost_agents.append(ChaserGhostAgent(index=i + 1, random_prob=0.3))

        ui.phase = "TURN_BASED"
        ui.is_running = True
        ui.is_paused = False
        ui.metrics["status"] = f"Đối kháng ({ui.get_selected_algorithm()}): Đang chơi..."

    def execute_one_turn():
        """Thực hiện 1 lượt chơi Turn-Based:
        1. Pacman đi 1 bước (Minimax / Alpha-Beta)
        2. Mỗi Ghost đi 1 bước (ChaserGhostAgent)
        3. Kiểm tra va chạm + thắng/thua

        Trả về:
            True nếu game tiếp tục, False nếu kết thúc.
        """
        nonlocal turn_game_state, turn_count, adversarial_agent

        if turn_game_state is None or turn_game_state.is_game_over:
            return False

        turn_count += 1

        # ── Lượt Pacman: ra quyết định 1 hành động ──
        try:
            pacman_action = adversarial_agent.get_action(turn_game_state)
        except Exception as e:
            ui.phase = "GAME_OVER"
            ui.is_running = False
            ui.metrics["status"] = f"Lỗi tác tử Pacman: {e}"
            return False

        # Áp dụng action Pacman
        turn_game_state = turn_game_state.generate_successor(0, pacman_action)

        # Kiểm tra kết thúc sau lượt Pacman
        if turn_game_state.is_game_over:
            _sync_ui_from_engine()
            if turn_game_state.is_win():
                ui.phase = "GAME_OVER"
                ui.game_result = "WIN"
                ui.metrics["status"] = "🏆 Thắng! Ăn hết thức ăn!"
            elif turn_game_state.is_lose():
                ui.phase = "GAME_OVER"
                ui.game_result = "LOSE"
                ui.metrics["status"] = "💀 Thua! Bị Ma bắt!"
            ui.is_running = False
            return False

        # ── Lượt Ghost: mỗi Ghost đi 1 bước ──
        for i, g_agent in enumerate(ghost_agents):
            agent_idx = i + 1
            if agent_idx > len(turn_game_state.ghosts_pos):
                break
            g_action = g_agent.get_action(turn_game_state)
            turn_game_state = turn_game_state.generate_successor(agent_idx, g_action)

            # Kiểm tra va chạm sau mỗi Ghost di chuyển
            if turn_game_state.is_game_over:
                _sync_ui_from_engine()
                if turn_game_state.is_lose():
                    ui.phase = "GAME_OVER"
                    ui.game_result = "LOSE"
                    ui.metrics["status"] = "💀 Thua! Bị Ma bắt!"
                ui.is_running = False
                return False

        # ── Đồng bộ UI ──
        _sync_ui_from_engine()

        # Cập nhật metrics
        food_left = len(turn_game_state.food)
        ui.metrics["turn"] = turn_count
        ui.metrics["cost"] = turn_game_state.score
        ui.metrics["status"] = f"Turn {turn_count} | Thức ăn còn: {food_left}"

        return True

    def _sync_ui_from_engine():
        """Đồng bộ vị trí từ engine GameState → UI PacmanUI.
        Engine dùng (x=col, y=row), UI dùng (row, col)."""
        if turn_game_state is None:
            return
        # Pacman
        px, py = turn_game_state.pacman_pos
        ui.pacman_pos = (py, px)
        # Ghosts
        ui.ghost_positions = [(gy, gx) for gx, gy in turn_game_state.ghosts_pos]
        # Food đã ăn
        current_food_rc = {(fy, fx) for fx, fy in turn_game_state.food}
        ui.eaten_food = ui.food_set - current_food_rc

    # ══════════════════════════════════════════════════════════════════════
    # VÒNG LẶP CHÍNH (Main Loop)
    # ══════════════════════════════════════════════════════════════════════
    while True:
        ev = ui.handle_events()

        if ev:
            act = ev.get("action")

            # ── START: Bấm nút Bắt đầu ──
            if act == "START":
                if ui.phase in ("IDLE", "GAME_OVER"):
                    ui.reset_search_state()
                    algo_display = ui.get_selected_algorithm()
                    ui.metrics["algorithm"] = algo_display

                    if ui.has_ghosts():
                        # Map có Ma → Bắt buộc thuật toán đối kháng
                        if algo_display not in PacmanUI.ALGO_ADVERSARIAL:
                            ui.metrics["status"] = "⚠ Map có Ma chỉ hỗ trợ Minimax hoặc Alpha-Beta!"
                            ui.is_running = False
                            continue
                        start_turn_based()
                    else:
                        # Map không Ma → Offline Search
                        if algo_display in PacmanUI.ALGO_ADVERSARIAL:
                            ui.metrics["status"] = "⚠ Thuật toán đối kháng cần map có Ma!"
                            ui.is_running = False
                            continue

                        algo_key = _algo_name_to_search_key(algo_display)
                        heuristic_key = _heuristic_name_to_key(ui.get_selected_heuristic())

                        try:
                            search_steps, demo_path, search_time_ms, m = solve_offline(
                                algo_key, heuristic_key)
                        except Exception as e:
                            ui.metrics["status"] = f"Lỗi: {e}"
                            ui.is_running = False
                            continue

                        if not m.get("found", False) or not demo_path:
                            ui.phase = "GAME_OVER"
                            ui.game_result = "NO_PATH"
                            ui.is_running = False
                            ui.metrics["status"] = "❌ Bản đồ không có lời giải!"
                            continue

                        search_step_idx = 0
                        ui.is_running = True
                        ui.is_paused = False
                        ui.phase = "SEARCHING"
                        ui.metrics["time_ms"] = round(search_time_ms, 2)
                        ui.metrics["expanded"] = m.get("expanded_nodes", 0)
                        ui.metrics["path_length"] = m.get("plan_length", 0)

                elif ui.phase in ("SEARCHING", "MOVING", "TURN_BASED"):
                    # Resume
                    ui.is_paused = False

            # ── RESET ──
            elif act == "RESET":
                search_steps, demo_path = [], []
                search_step_idx = 0
                adversarial_agent = None
                ghost_agents = []
                turn_game_state = None
                turn_count = 0

            # ── MAP_CHANGED ──
            elif act == "MAP_CHANGED":
                search_steps, demo_path = [], []
                search_step_idx = 0
                adversarial_agent = None
                ghost_agents = []
                turn_game_state = None
                turn_count = 0

            # ── STEP (Từng bước) ──
            elif act == "STEP":
                if ui.phase == "IDLE":
                    # Chưa start → tự động start rồi pause
                    algo_display = ui.get_selected_algorithm()
                    ui.metrics["algorithm"] = algo_display

                    if ui.has_ghosts():
                        if algo_display not in PacmanUI.ALGO_ADVERSARIAL:
                            ui.metrics["status"] = "⚠ Map có Ma chỉ hỗ trợ Minimax hoặc Alpha-Beta!"
                            continue
                        start_turn_based()
                        ui.is_paused = True
                        # Thực hiện 1 lượt
                        execute_one_turn()
                    else:
                        if algo_display in PacmanUI.ALGO_ADVERSARIAL:
                            ui.metrics["status"] = "⚠ Thuật toán đối kháng cần map có Ma!"
                            continue

                        algo_key = _algo_name_to_search_key(algo_display)
                        heuristic_key = _heuristic_name_to_key(ui.get_selected_heuristic())

                        try:
                            search_steps, demo_path, search_time_ms, m = solve_offline(
                                algo_key, heuristic_key)
                        except Exception as e:
                            ui.metrics["status"] = f"Lỗi: {e}"
                            continue

                        if not m.get("found", False) or not demo_path:
                            ui.phase = "GAME_OVER"
                            ui.game_result = "NO_PATH"
                            ui.metrics["status"] = "❌ Bản đồ không có lời giải!"
                            continue

                        search_step_idx = 0
                        ui.is_running = True
                        ui.phase = "SEARCHING"
                        ui.metrics["time_ms"] = round(search_time_ms, 2)
                        ui.metrics["expanded"] = m.get("expanded_nodes", 0)

                elif ui.phase == "TURN_BASED":
                    # Thực hiện 1 lượt turn-based
                    execute_one_turn()

                elif ui.phase == "SEARCHING":
                    # Tiến 1 bước searching
                    if search_step_idx < len(search_steps):
                        s = search_steps[search_step_idx]
                        ui.update_search_step(s["visited"], s["frontier"], s["current"])
                        ui.set_metrics(
                            expanded=len(s["visited"]),
                            status=f"Đang duyệt ({search_step_idx + 1}/{len(search_steps)})"
                        )
                        search_step_idx += 1

                elif ui.phase == "MOVING":
                    # Tiến 1 bước moving
                    still_moving = ui.advance_move_step()
                    if not still_moving:
                        ui.phase = "GAME_OVER"
                        remaining_food = len(ui.food_set) - len(ui.eaten_food)
                        if remaining_food == 0 and len(ui.food_set) > 0:
                            ui.game_result = "WIN"
                            ui.metrics["status"] = "🏆 Hoàn thành! Pacman ăn hết thức ăn!"
                        else:
                            ui.game_result = "NO_PATH"
                            ui.metrics["status"] = "❌ Bản đồ không có lời giải!"
                        ui.is_running = False

        # ══════════════════════════════════════════════════════════════════
        # GIAI ĐOẠN 1: SEARCHING (Offline) – Pacman đứng im
        # ══════════════════════════════════════════════════════════════════
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
                # Tìm kiếm hoàn tất → chuyển sang MOVING
                ui.set_path(demo_path)
                if demo_path and len(demo_path) > 1:
                    ui.current_node = None
                    ui.start_moving_phase()
                    ui.set_metrics(
                        cost=len(demo_path) - 1,
                        status="Tìm thấy đường! Đang di chuyển..."
                    )
                else:
                    ui.phase = "GAME_OVER"
                    ui.game_result = "NO_PATH"
                    ui.is_running = False
                    ui.set_metrics(status="❌ Bản đồ không có lời giải!")

        # ══════════════════════════════════════════════════════════════════
        # GIAI ĐOẠN 2: MOVING – Pacman đi theo đường, ăn đồ ăn
        # ══════════════════════════════════════════════════════════════════
        elif ui.phase == "MOVING" and ui.is_running and not ui.is_paused:
            still_moving = ui.advance_move_step()
            step = ui.move_step_idx
            total = len(ui.final_path)
            if still_moving:
                ui.set_metrics(status=f"Di chuyển ({step}/{total})")
            else:
                ui.phase = "GAME_OVER"
                remaining_food = len(ui.food_set) - len(ui.eaten_food)
                if remaining_food == 0 and len(ui.food_set) > 0:
                    ui.game_result = "WIN"
                    ui.metrics["status"] = "🏆 Hoàn thành! Pacman ăn hết thức ăn!"
                else:
                    ui.game_result = "NO_PATH"
                    ui.metrics["status"] = "❌ Bản đồ không có lời giải!"
                ui.is_running = False

        # ══════════════════════════════════════════════════════════════════
        # GIAI ĐOẠN 3: TURN-BASED – Pacman ↔ Ghost luân phiên
        # ══════════════════════════════════════════════════════════════════
        elif ui.phase == "TURN_BASED" and ui.is_running and not ui.is_paused:
            execute_one_turn()

        # ── Render và tick ──
        ui.render()
        ui.tick()


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    run_gui_app()