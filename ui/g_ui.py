"""
gui_ui.py - Giao diện Đồ họa bằng Pygame.

Điều khiển:
    Space / Enter / n : đi 1 bước (chế độ từng bước)
    a                 : chuyển sang chạy tự động
    s                 : quay lại chế độ từng bước
    + / -             : tăng / giảm tốc độ chạy tự động
    q / Esc           : thoát game
"""
import sys
import time
import os
import pygame
from ui.base_ui import BaseUI

# Bảng màu
BLACK = (18, 18, 18)
WHITE = (240, 240, 240)
BLUE = (33, 150, 243)
DARK_BLUE = (13, 71, 161)
YELLOW = (255, 235, 59)
RED = (244, 67, 54)
GREEN = (76, 175, 80)
GRAY = (158, 158, 158)
ORANGE = (255, 152, 0)
CYAN = (0, 188, 212)
PINK = (233, 30, 99)


class GUI_UI(BaseUI):
    def __init__(self, delay=0.15, step_mode=False, cell_size=40):
        self.delay = delay
        self.step_mode = step_mode
        self.cell_size = cell_size
        self.header_height = 60
        self.screen = None
        self.font = None
        self.large_font = None
        self.turn = 0
        self.quit_requested = False
        self.restart_requested = False

        # Khởi tạo Pygame
        pygame.init()
        pygame.display.set_caption("Pacman AI - Đồ hoạ Desktop (Pygame)")

        # Thử nạp font từ asset
        font_path = os.path.join("asset", "fonts", "font.ttf")
        if os.path.exists(font_path):
            try:
                self.font = pygame.font.Font(font_path, 15)
                self.large_font = pygame.font.Font(font_path, 22)
            except Exception:
                self.font = pygame.font.SysFont("consolas", 15, bold=True)
                self.large_font = pygame.font.SysFont("consolas", 22, bold=True)
        else:
            self.font = pygame.font.SysFont("consolas", 15, bold=True)
            self.large_font = pygame.font.SysFont("consolas", 22, bold=True)

        # Nạp sprites từ asset
        self.pacman_img = None
        self.ghost_imgs = []
        self._load_sprites()

    def _load_sprites(self):
        sprite_size = (self.cell_size - 4, self.cell_size - 4)
        pacman_path = os.path.join("asset", "images", "pacman", "pacman.png")
        if os.path.exists(pacman_path):
            try:
                img = pygame.image.load(pacman_path).convert_alpha()
                self.pacman_img = pygame.transform.scale(img, sprite_size)
            except Exception:
                pass

        ghost_files = ["Blinky.png", "Inky.png", "Clyde.png"]
        for gf in ghost_files:
            g_path = os.path.join("asset", "images", "ghosts", gf)
            if os.path.exists(g_path):
                try:
                    img = pygame.image.load(g_path).convert_alpha()
                    self.ghost_imgs.append(pygame.transform.scale(img, sprite_size))
                except Exception:
                    pass

    def initialize(self):
        print("Đang khởi tạo giao diện Pygame Desktop (GUI)...")

    def _init_screen(self, state):
        """Khởi tạo kích thước màn hình động dựa trên bản đồ (tối thiểu 480x480)."""
        map_w = state.width * self.cell_size
        map_h = state.height * self.cell_size
        width = max(map_w + 40, 480)
        height = max(map_h + self.header_height + 40, 480)
        self.screen = pygame.display.set_mode((width, height))

    def render(self, game_state, is_pacman_move=False):
        if self.screen is None:
            self._init_screen(game_state)

        if is_pacman_move:
            self.turn += 1
        self._draw_frame(game_state)
        self._handle_interaction(game_state)

    def _draw_frame(self, state):
        self.screen.fill(BLACK)

        # 1. Vẽ Header (Thông tin)
        mode_text = "TỪNG BƯỚC" if self.step_mode else f"TỰ ĐỘNG ({self.delay:.2f}s)"
        info_str = f"Bước: {self.turn} | Điểm: {state.score} | Thức ăn: {len(state.food)} | {mode_text} | r: Chơi lại"

        text_surf = self.font.render(info_str, True, WHITE)
        self.screen.blit(text_surf, (15, 20))
        pygame.draw.line(
            self.screen,
            GRAY,
            (0, self.header_height - 2),
            (self.screen.get_width(), self.header_height - 2),
            2,
        )

        # 2. Căn giữa bản đồ trên màn hình
        map_w = state.width * self.cell_size
        offset_x = (self.screen.get_width() - map_w) // 2
        offset_y = self.header_height + 15

        for y in range(state.height):
            for x in range(state.width):
                pos = (x, y)
                rect_x = offset_x + x * self.cell_size
                rect_y = offset_y + y * self.cell_size

                # Vẽ Tường
                if pos in state.walls:
                    rect = (rect_x, rect_y, self.cell_size, self.cell_size)
                    pygame.draw.rect(self.screen, DARK_BLUE, rect)
                    pygame.draw.rect(self.screen, BLUE, rect, 1)
                else:
                    # Vẽ Thức ăn
                    if pos in state.food:
                        center = (
                            rect_x + self.cell_size // 2,
                            rect_y + self.cell_size // 2,
                        )
                        pygame.draw.circle(
                            self.screen, WHITE, center, max(3, self.cell_size // 7)
                        )

                    # Vẽ Ghost
                    if pos in state.ghosts_pos:
                        g_idx = state.ghosts_pos.index(pos)
                        if self.ghost_imgs:
                            g_img = self.ghost_imgs[g_idx % len(self.ghost_imgs)]
                            self.screen.blit(g_img, (rect_x + 2, rect_y + 2))
                        else:
                            center = (
                                rect_x + self.cell_size // 2,
                                rect_y + self.cell_size // 2,
                            )
                            colors = [RED, CYAN, ORANGE, PINK]
                            color = colors[g_idx % len(colors)]
                            pygame.draw.circle(
                                self.screen, color, center, self.cell_size // 2 - 3
                            )

                    # Vẽ Pacman (Vẽ đè lên trên cùng)
                    if pos == state.pacman_pos:
                        if self.pacman_img:
                            self.screen.blit(self.pacman_img, (rect_x + 2, rect_y + 2))
                        else:
                            center = (
                                rect_x + self.cell_size // 2,
                                rect_y + self.cell_size // 2,
                            )
                            pygame.draw.circle(
                                self.screen, YELLOW, center, self.cell_size // 2 - 2
                            )

        # 3. Hiển thị thông báo trạng thái kết thúc nếu có
        if state.is_game_over:
            status_text = ""
            status_color = WHITE
            if state.is_win():
                status_text = "CHIẾN THẮNG!"
                status_color = GREEN
            elif state.is_lose():
                status_text = "GAME OVER! PACMAN BỊ BẮT!"
                status_color = RED
            elif state.end_reason == "no_solution":
                status_text = "BẢN ĐỒ KHÔNG CÓ LỜI GIẢI!"
                status_color = ORANGE

            if status_text:
                status_text += " (Nhấn R để chơi lại, phím khác để thoát)"
                banner_surf = self.large_font.render(status_text, True, status_color)
                banner_rect = banner_surf.get_rect(
                    center=(self.screen.get_width() // 2, self.screen.get_height() - 25)
                )
                self.screen.blit(banner_surf, banner_rect)

        pygame.display.flip()

    def _handle_interaction(self, state):
        if state.is_game_over:
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit_requested = True
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self.restart_requested = True
                            waiting = False
                        elif event.key in (pygame.K_q, pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                            waiting = False
                time.sleep(0.01)
            return

        if self.step_mode:
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit_requested = True
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_n):
                            waiting = False
                        elif event.key == pygame.K_a:
                            self.step_mode = False
                            waiting = False
                        elif event.key == pygame.K_r:
                            self.restart_requested = True
                            waiting = False
                        elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                            self.quit_requested = True
                            pygame.quit()
                            sys.exit()
                time.sleep(0.01)
        else:
            start_time = time.time()
            while time.time() - start_time < self.delay:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit_requested = True
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_s:
                            self.step_mode = True
                            return
                        elif event.key == pygame.K_r:
                            self.restart_requested = True
                            return
                        elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                            self.quit_requested = True
                            pygame.quit()
                            sys.exit()
                        elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                            self.delay = max(0.01, self.delay / 1.5)
                            self._draw_frame(state)
                        elif event.key == pygame.K_MINUS:
                            self.delay = min(2.0, self.delay * 1.5)
                            self._draw_frame(state)
                time.sleep(0.01)

    def show_metrics(self, metrics):
        """Hiển thị số liệu thống kê lên màn hình game."""
        if self.screen is None:
            return

        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(225)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        title_surf = self.large_font.render("=== KẾT QUẢ THỐNG KÊ (METRICS) ===", True, GREEN)
        self.screen.blit(title_surf, (20, 40))

        y_offset = 85
        for key, value in metrics.items():
            if isinstance(value, float):
                val_str = f"{value:.6f}" if abs(value) < 1 else f"{value:.3f}"
            else:
                val_str = str(value)
            text_surf = self.font.render(f"{key}: {val_str}", True, WHITE)
            self.screen.blit(text_surf, (30, y_offset))
            y_offset += 28

        hint_surf = self.font.render("Nhấn phím bất kỳ hoặc Esc/Q để thoát...", True, YELLOW)
        self.screen.blit(hint_surf, (30, y_offset + 20))
        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN):
                    waiting = False
        pygame.quit()