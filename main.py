"""
main.py – Điểm vào chính của đồ án Pacman AI.

Cách chạy:
    python main.py                → Mở thẳng giao diện đồ họa (GUI)
    python main.py -ui gui        → Mở giao diện đồ họa (GUI)
    python main.py -ui cli -mode search -map maps/map_co_ban.txt -algo astar
                                  → Chạy bằng giao diện dòng lệnh (CLI)

Khi chạy GUI:
    - KHÔNG cần truyền bất kỳ tham số dòng lệnh nào
    - Toàn bộ cấu hình (Map, Thuật toán, Heuristic) được chọn trực tiếp
      trên giao diện qua Dropdown Menu
"""
import argparse
import time

def main():
    """Hàm chính: phân tích tham số CLI và khởi động ứng dụng."""

    # ── 1. Đọc tham số dòng lệnh (tất cả đều OPTIONAL) ──
    parser = argparse.ArgumentParser(description="Pacman AI – Nhóm 13")
    parser.add_argument("-mode", type=str, default="search",
                        choices=["search", "adversarial"],
                        help="Chế độ chơi: search hoặc adversarial (mặc định: search)")
    parser.add_argument("-map", type=str, default="maps/map_co_ban.txt",
                        help="Đường dẫn tới file map (mặc định: maps/map_co_ban.txt)")
    parser.add_argument("-algo", type=str, default="astar",
                        help="Thuật toán (bfs, dfs, astar, ucs, minimax, alphabeta)")
    parser.add_argument("-heuristic", type=str, default="mst",
                        help="Heuristic cho A* (mst, maze, null)")
    parser.add_argument("-ui", type=str, default="gui",
                        choices=["cli", "gui"],
                        help="Giao diện: cli hoặc gui (mặc định: gui)")

    args = parser.parse_args()

    # ── 2. Khởi động theo loại giao diện ──
    if args.ui == "gui":
        # ─────────────────────────────────────────────────────
        # CHẾ ĐỘ GUI: Mở thẳng giao diện đồ họa Pygame
        # Người dùng chọn Map / Thuật toán / Heuristic qua Dropdown Menu
        # ─────────────────────────────────────────────────────
        try:
            from ui.g_ui import run_gui_app
            run_gui_app()
        except ImportError as e:
            print(f"\n[LỖI] Không thể tải thư viện đồ họa: {e}")
            print("Vui lòng cài đặt Pygame: pip install pygame")
            print("Chuyển về giao diện CLI tự động...\n")
            args.ui = "cli"  # Fallback sang CLI

    if args.ui == "cli":
        # ─────────────────────────────────────────────────────
        # CHẾ ĐỘ CLI: Chạy bằng giao diện dòng lệnh
        # Yêu cầu truyền đầy đủ tham số qua CLI
        # ─────────────────────────────────────────────────────
        from src.engine import GameLoop
        from src.agents import SearchAgent, DummyGhostAgent
        from ui.cli_ui import CLI_UI

        print("Bắt đầu game với các tham số:")
        print(f"- Chế độ (Mode): {args.mode}")
        print(f"- Bản đồ (Map): {args.map}")
        print(f"- Thuật toán (Algo): {args.algo}")
        print(f"- Giao diện (UI): CLI")
        if args.algo == "astar":
            print(f"- Heuristic: {args.heuristic}")

        ui = CLI_UI()
        agents = []

        if args.mode == "search":
            pacman_agent = SearchAgent(
                algorithm_name=args.algo, heuristic=args.heuristic)
            agents.append(pacman_agent)
            ghost_agent = DummyGhostAgent(index=1, random_move=False)
            agents.append(ghost_agent)

        elif args.mode == "adversarial":
            from src.agents import AlphaBetaAgent, ChaserGhostAgent
            pacman_agent = AlphaBetaAgent(depth=3)
            agents.append(pacman_agent)
            # Ghost agents sẽ được tạo bởi ghost_factory

        game = GameLoop(
            map_file=args.map,
            agents=agents,
            ui=ui,
            max_turns=500 if args.mode == "adversarial" else None,
            ghost_factory=(lambda i: ChaserGhostAgent(index=i, random_prob=0.3))
                if args.mode == "adversarial" else None,
        )
        game.run()

        # In metrics
        if hasattr(agents[0], 'get_metrics'):
            ui.show_metrics(agents[0].get_metrics())


if __name__ == "__main__":
    main()