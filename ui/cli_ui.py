"""
cli_ui.py - Giao diện dòng lệnh TƯƠNG TÁC.

Điều khiển (khi chạy trong terminal thật):
    Enter / n  : đi 1 bước (chế độ từng bước)
    a          : chạy tự động
    s          : quay lại chế độ từng bước
    + / -      : tăng / giảm tốc độ chạy tự động
    q          : thoát game
    Ctrl+C     : tạm dừng khi đang chạy tự động (chuyển sang từng bước)

Khi stdin/stdout không phải terminal (pipe, file...), giao diện tự động chạy
không cần nhập và không xóa màn hình.
"""
import sys
import time

from ui.base_ui import BaseUI

RESET = "\033[0m"
COLORS = {
    "#": "\033[34;1m",   # tường: xanh dương
    "P": "\033[33;1m",   # Pacman: vàng
    "G": "\033[31;1m",   # Ghost: đỏ
    ".": "\033[37;1m",   # thức ăn: trắng
}
CLEAR = "\033[H\033[J"
MIN_DELAY, MAX_DELAY = 0.01, 2.0


class CLI_UI(BaseUI):
    def __init__(self, delay=0.15, step_mode=False, color=True, clear=True):
        self.delay = delay
        self.interactive = sys.stdin.isatty() and sys.stdout.isatty()
        self.step_mode = step_mode and self.interactive
        self.color = color and sys.stdout.isatty()
        self.clear = clear and sys.stdout.isatty()
        self.quit_requested = False
        self.turn = 0

    # --- vòng đời ------------------------------------------------------------
    def initialize(self):
        print("=== PACMAN - GIAO DIỆN DÒNG LỆNH ===")
        if self.interactive:
            print("Điều khiển: [Enter] bước tiếp | a: tự động | s: từng bước | "
                  "+/-: tốc độ | q: thoát")
            if self.step_mode:
                input("Nhấn Enter để bắt đầu...")
            else:
                time.sleep(1.0)

    def render(self, game_state):
        if self.clear:
            sys.stdout.write(CLEAR)
        print(self._header(game_state))
        for line in self._draw_map(game_state):
            print(line)
        print(self._legend())
        sys.stdout.flush()
        self.turn += 1
        self._wait_for_user(game_state)

    def show_metrics(self, metrics):
        """Hiển thị số liệu thống kê sau khi game kết thúc."""
        print("\n--- THỐNG KÊ (METRICS) ---")
        width = max((len(str(k)) for k in metrics), default=0)
        for key, value in metrics.items():
            if isinstance(value, float):
                value = f"{value:.6f}" if abs(value) < 1 else f"{value:.3f}"
            print(f"{str(key):<{width}} : {value}")

    # --- vẽ -------------------------------------------------------------------
    def _header(self, state):
        mode = "TỪNG BƯỚC" if self.step_mode else f"TỰ ĐỘNG ({self.delay:.2f}s/bước)"
        return (f"Bước: {max(self.turn, 0):<4} Điểm: {state.score:<6} "
                f"Thức ăn còn: {len(state.food):<3} Chế độ: "
                f"{mode if self.interactive else 'KHÔNG TƯƠNG TÁC'}")

    def _paint(self, ch):
        if self.color and ch in COLORS:
            return f"{COLORS[ch]}{ch}{RESET}"
        return ch

    def _draw_map(self, state):
        lines = []
        for y in range(state.height):
            row = []
            for x in range(state.width):
                pos = (x, y)
                if pos in state.walls:
                    ch = "#"
                elif pos == state.pacman_pos:
                    ch = "P"
                elif pos in state.ghosts_pos:
                    ch = "G"
                elif pos in state.food:
                    ch = "."
                else:
                    ch = " "
                row.append(self._paint(ch))
            lines.append("".join(row))
        return lines

    def _legend(self):
        return (f"{self._paint('P')} Pacman   {self._paint('G')} Ghost   "
                f"{self._paint('.')} Thức ăn   {self._paint('#')} Tường")

    # --- tương tác --------------------------------------------------------------
    def _wait_for_user(self, state):
        if state.is_game_over:             # ván đã xong: không chờ nữa
            return
        if not self.interactive:
            time.sleep(self.delay)
            return

        if not self.step_mode:
            try:
                time.sleep(self.delay)
            except KeyboardInterrupt:      # Ctrl+C = tạm dừng
                self.step_mode = True
            else:
                return

        while True:                        # chế độ từng bước: chờ lệnh
            try:
                cmd = input("[Enter] bước tiếp | a: tự động | +/-: tốc độ | "
                            "q: thoát > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                cmd = "a"                  # hết input -> chạy tự động
            if cmd in ("", "n"):
                return
            if cmd == "a":
                self.step_mode = False
                return
            if cmd == "s":
                self.step_mode = True
                return
            if cmd == "+":
                self.delay = max(MIN_DELAY, self.delay / 1.5)
                print(f"Tốc độ: {self.delay:.2f}s/bước")
            elif cmd == "-":
                self.delay = min(MAX_DELAY, self.delay * 1.5)
                print(f"Tốc độ: {self.delay:.2f}s/bước")
            elif cmd == "q":
                self.quit_requested = True
                return
            else:
                print("Lệnh không hợp lệ.")
