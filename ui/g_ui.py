"""
gui_ui.py - Giao diện Đồ họa bằng Pygame.

Điều khiển:
    Space / Enter : đi 1 bước (chế độ từng bước)
    a             : chuyển sang chạy tự động
    s             : quay lại chế độ từng bước
    + / -         : tăng / giảm tốc độ chạy tự động
    q / Esc       : thoát game
"""
import sys
import time
import pygame
from ui.base_ui import BaseUI

# Bảng màu
BLACK = (18, 18, 18)
WHITE = (240, 240, 240)
BLUE = (33, 150, 243)
YELLOW = (255, 235, 59)
RED = (244, 67, 54)
GREEN = (76, 175, 80)
GRAY = (158, 158, 158)

class GUI_UI(BaseUI):
    def __init__(self, delay=0.15, step_mode=False, cell_size=50):
        self.delay = delay
        self.step_mode = step_mode
        self.cell_size = cell_size
        self.header_height = 60
        self.screen = None
        self.font = None
        self.large_font = None
        self.turn = 0
        
        # Khởi tạo Pygame ẩn trước, window sẽ hiện khi render frame đầu tiên
        pygame.init()
        pygame.display.set_caption("Pacman AI - Graphic UI")
        # Sử dụng font hệ thống có sẵn
        self.font = pygame.font.SysFont("consolas", 16, bold=True)
        self.large_font = pygame.font.SysFont("consolas", 24, bold=True)

    def initialize(self):
        print("Đang khởi tạo giao diện Pygame (GUI)...")

    def _init_screen(self, state):
        """Khởi tạo kích thước màn hình động dựa trên bản đồ."""
        width = state.width * self.cell_size
        height = state.height * self.cell_size + self.header_height
        self.screen = pygame.display.set_mode((width, height))

    def render(self, game_state):
        if self.screen is None:
            self._init_screen(game_state)

        self.turn += 1
        self._draw_frame(game_state)
        self._handle_interaction(game_state)

    def _draw_frame(self, state):
        self.screen.fill(BLACK)
        
        # 1. Vẽ Header (Thông tin)
        mode_text = "TỪNG BƯỚC" if self.step_mode else f"TỰ ĐỘNG ({self.delay:.2f}s)"
        info_str = f"Bước: {self.turn} | Điểm: {state.score} | Thức ăn: {len(state.food)} | {mode_text}"
        
        text_surf = self.font.render(info_str, True, WHITE)
        self.screen.blit(text_surf, (15, 20))
        pygame.draw.line(self.screen, GRAY, (0, self.header_height - 2), (self.screen.get_width(), self.header_height - 2), 2)

        # 2. Vẽ Map
        for y in range(state.height):
            for x in range(state.width):
                pos = (x, y)
                rect_x = x * self.cell_size
                rect_y = y * self.cell_size + self.header_height
                
                # Vẽ Tường
                if pos in state.walls:
                    rect = (rect_x, rect_y, self.cell_size, self.cell_size)
                    pygame.draw.rect(self.screen, BLUE, rect)
                    pygame.draw.rect(self.screen, BLACK, rect, 1) # Viền ô vuông
                else:
                    # Vẽ Thức ăn
                    if pos in state.food:
                        center = (rect_x + self.cell_size // 2, rect_y + self.cell_size // 2)
                        pygame.draw.circle(self.screen, WHITE, center, max(2, self.cell_size // 8))
                        
                    # Vẽ Ghost
                    if pos in state.ghosts_pos:
                        center = (rect_x + self.cell_size // 2, rect_y + self.cell_size // 2)
                        pygame.draw.circle(self.screen, RED, center, self.cell_size // 2 - 4)
                        
                    # Vẽ Pacman (Vẽ đè lên trên cùng)
                    if pos == state.pacman_pos:
                        center = (rect_x + self.cell_size // 2, rect_y + self.cell_size // 2)
                        pygame.draw.circle(self.screen, YELLOW, center, self.cell_size // 2 - 2)
                        
        pygame.display.flip()

    def _handle_interaction(self, state):
        if state.is_game_over:
            return

        if self.step_mode:
            # Chờ người dùng nhấn phím để đi tiếp
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_n):
                            waiting = False
                        elif event.key == pygame.K_a:
                            self.step_mode = False
                            waiting = False
                        elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                            pygame.quit()
                            sys.exit()
        else:
            # Chế độ tự động, có delay, bắt sự kiện chuyển đổi
            start_time = time.time()
            while time.time() - start_time < self.delay:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_s:
                            self.step_mode = True
                            return
                        elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                            pygame.quit()
                            sys.exit()
                        elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                            self.delay = max(0.01, self.delay / 1.5)
                            self._draw_frame(state) # Cập nhật text ngay lập tức
                        elif event.key == pygame.K_MINUS:
                            self.delay = min(2.0, self.delay * 1.5)
                            self._draw_frame(state)
                time.sleep(0.01)

    def show_metrics(self, metrics):
        """Hiển thị số liệu thống kê lên màn hình game."""
        if self.screen is None:
            return
            
        # Tạo hiệu ứng Overlay (Màn đen làm mờ)
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(220) # Độ mờ
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Vẽ Text
        title_surf = self.large_font.render("=== KẾT QUẢ TÌM KIẾM ===", True, GREEN)
        self.screen.blit(title_surf, (20, 60))
        
        y_offset = 110
        for key, value in metrics.items():
            if isinstance(value, float):
                value = f"{value:.6f}" if abs(value) < 1 else f"{value:.3f}"
            text_surf = self.font.render(f"{key}: {value}", True, WHITE)
            self.screen.blit(text_surf, (30, y_offset))
            y_offset += 35
            
        hint_surf = self.font.render("Nhấn phím bất kỳ để thoát...", True, GRAY)
        self.screen.blit(hint_surf, (30, y_offset + 30))
        pygame.display.flip()
        
        # Chờ người dùng đóng
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    waiting = False
        pygame.quit()