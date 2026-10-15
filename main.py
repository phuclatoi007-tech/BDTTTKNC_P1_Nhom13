import argparse
import sys
import time
import os

if sys.platform == "win32":
    # Đảm bảo in tiếng Việt trên Windows console không bị lỗi charmap codec
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.engine import GameLoop
from src.agents import (
    SearchAgent,
    DummyGhostAgent,
    MinimaxAgent,
    AlphaBetaAgent,
    ChaserGhostAgent,
)
from ui.cli_ui import CLI_UI


def main():
    # Xác định UI mặc định: nếu chạy không có tham số nào -> mở GUI đồ họa của Phúc
    default_ui = "gui" if len(sys.argv) == 1 else "cli"

    # 1. Đọc tham số dòng lệnh
    parser = argparse.ArgumentParser(description="Pacman Game - AI Search & Adversarial (Nhóm 13)")
    parser.add_argument(
        "-mode",
        type=str,
        default="search",
        choices=["search", "adversarial"],
        help="Chế độ chơi: search hoặc adversarial (mặc định: search)",
    )
    parser.add_argument(
        "-map",
        type=str,
        default="maps/map_co_ban.txt",
        help="Đường dẫn đến file map (mặc định: maps/map_co_ban.txt)",
    )
    parser.add_argument(
        "-algo",
        type=str,
        default=None,
        help="Thuật toán (bfs, dfs, ucs, greedy, astar, minimax, alphabeta)",
    )
    parser.add_argument(
        "-heuristic",
        type=str,
        default="mst",
        help="Heuristic sử dụng cho A* và Greedy (mst, theory_mst, maze, null)",
    )
    parser.add_argument(
        "-depth",
        type=int,
        default=3,
        help="Độ sâu của minimax / alphabeta (mặc định: 3)",
    )
    parser.add_argument(
        "-ui",
        type=str,
        default=default_ui,
        choices=["cli", "gui"],
        help=f"Giao diện hiển thị: cli (Terminal) hoặc gui (Đồ họa Pygame, mặc định: {default_ui})",
    )
    parser.add_argument(
        "-delay",
        type=float,
        default=0.15,
        help="Giây nghỉ giữa các bước ở chế độ tự động (mặc định: 0.15)",
    )
    parser.add_argument(
        "-step",
        action="store_true",
        help="Bắt đầu ở chế độ từng bước (nhấn Enter để đi tiếp)",
    )
    parser.add_argument(
        "-nocolor",
        action="store_true",
        help="Tắt màu ANSI trên terminal",
    )
    parser.add_argument(
        "-seed",
        type=int,
        default=None,
        help="Seed ngẫu nhiên của Ghost (để tái lập kết quả)",
    )
    parser.add_argument(
        "-max_turns",
        type=int,
        default=None,
        help="Số vòng tối đa (mặc định 200 cho adversarial, không giới hạn cho search)",
    )

    args = parser.parse_args()

    # 2. Khởi động GUI Desktop đồ họa tương tác (Pygame) nếu chọn gui
    if args.ui == "gui":
        try:
            from ui.g_ui import run_gui_app
            run_gui_app(
                initial_map=args.map if args.map else None,
                initial_algo=args.algo if args.algo else None,
                initial_heuristic=args.heuristic if args.heuristic else None,
            )
            return
        except ImportError as e:
            print(f"\n[LỖI] Không thể tải thư viện đồ họa Pygame: {e}")
            print("Vui lòng cài đặt: pip install pygame-ce (hoặc pip install pygame)")
            print("Chuyển tự động sang giao diện dòng lệnh (CLI)...\n")
            args.ui = "cli"
        except Exception as e:
            print(f"\n[CẢNH BÁO] Không thể khởi động GUI ({e}). Chuyển sang CLI...\n")
            args.ui = "cli"

    # 3. Chế độ CLI (Terminal): Sử dụng GameLoop và CLI_UI
    if args.algo is None:
        args.algo = "astar" if args.mode.lower() == "search" else "alphabeta"

    if args.max_turns is None:
        args.max_turns = 200 if args.mode.lower() == "adversarial" else None

    print("Bắt đầu game với các tham số:")
    print(f"- Chế độ (Mode): {args.mode}")
    print(f"- Bản đồ (Map): {args.map}")
    print(f"- Thuật toán (Algo): {args.algo}")
    print(f"- Giao diện (UI): {args.ui.upper()}")
    if args.algo.lower() in ("minimax", "alphabeta"):
        print(f"- Độ sâu (Depth): {args.depth}")
    elif args.mode.lower() == "search" and args.algo.lower() in ("astar", "greedy", "gbfs"):
        print(f"- Heuristic: {args.heuristic}")
    if args.max_turns:
        print(f"- Số vòng tối đa (Max turns): {args.max_turns}")

    ui = CLI_UI(delay=args.delay, step_mode=args.step, color=not args.nocolor)

    # 4. Khởi tạo Agent cho Pacman và Factory cho Ghost
    agents = []
    algo_lower = args.algo.lower().replace("-", "").replace("_", "")

    if args.mode.lower() == "search":
        if algo_lower in ("minimax", "alphabeta"):
            pacman_agent = SearchAgent(algorithm_name=algo_lower, depth=args.depth)
        elif algo_lower in ("bfs", "dfs", "astar", "ucs", "greedy", "gbfs"):
            pacman_agent = SearchAgent(algorithm_name=algo_lower, heuristic=args.heuristic)
        else:
            print(f"Cảnh báo: Thuật toán '{args.algo}' không được hỗ trợ. Mặc định chuyển về A*.")
            pacman_agent = SearchAgent(algorithm_name="astar", heuristic=args.heuristic)

        agents.append(pacman_agent)
        ghost_factory = lambda i: DummyGhostAgent(index=i, random_move=False)

    elif args.mode.lower() == "adversarial":
        if algo_lower == "minimax":
            pacman_agent = MinimaxAgent(depth=args.depth)
        elif algo_lower == "alphabeta":
            pacman_agent = AlphaBetaAgent(depth=args.depth)
        else:
            print(f"Cảnh báo: Thuật toán '{args.algo}' không hỗ trợ cho adversarial. Mặc định dùng AlphaBeta.")
            pacman_agent = AlphaBetaAgent(depth=args.depth)

        agents.append(pacman_agent)
        ghost_factory = lambda i: ChaserGhostAgent(
            index=i,
            random_prob=0.2,
            seed=(args.seed + i) if args.seed is not None else None,
        )

    # 5. Khởi tạo GameLoop với ghost_factory và max_turns
    game = GameLoop(
        map_file=args.map,
        agents=agents,
        ui=ui,
        max_turns=args.max_turns,
        ghost_factory=ghost_factory,
    )

    # 6. Chạy game
    game.run()

    # 7. In kết quả (Metrics)
    if hasattr(pacman_agent, "get_metrics"):
        ui.show_metrics(pacman_agent.get_metrics())


if __name__ == "__main__":
    main()