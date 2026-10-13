import sys
import argparse
import time

# Đảm bảo mã hóa UTF-8 an toàn trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from src.engine import GameLoop
from src.agents import SearchAgent, DummyGhostAgent
from ui.g_ui import GUI_UI
from ui.cli_ui import CLI_UI

def main():
    # 1. Đọc tham số dòng lệnh (TẤT CẢ đều là tùy chọn với giá trị mặc định hợp lý)
    parser = argparse.ArgumentParser(description="Pacman AI - Search & Adversarial Visualization")
    parser.add_argument("-ui", type=str, default="gui", choices=["gui", "cli"],
                        help="Giao diện hiển thị: gui (Đồ họa Pygame trực quan, mặc định) hoặc cli (Terminal)")
    parser.add_argument("-mode", type=str, default="search", choices=["search", "adversarial"], 
                        help="Chế độ chơi: search hoặc adversarial (mặc định: search)")
    parser.add_argument("-map", type=str, default="maps/map_co_ban.txt", 
                        help="Đường dẫn đến file map (mặc định: maps/map_co_ban.txt)")
    parser.add_argument("-algo", type=str, default="astar", 
                        help="Thuật toán: bfs, dfs, astar, ucs, greedy cho search; minimax, alphabeta cho adversarial")
    parser.add_argument("-heuristic", type=str, default="mst", 
                        help="Heuristic cho A* / Greedy (mst, manhattan, euclidean, maze, null)")
    parser.add_argument("-depth", type=int, default=3,
                        help="Độ sâu của minimax / alphabeta (mặc định: 3)")
    parser.add_argument("-seed", type=int, default=None,
                        help="Seed ngẫu nhiên của Ghost (để tái lập kết quả)")
    parser.add_argument("-max_turns", type=int, default=200,
                        help="Số vòng tối đa của chế độ adversarial (mặc định: 200)")
    parser.add_argument("-ghost_move", action="store_true",
                        help="Bật di chuyển ngẫu nhiên cho Ghost trong chế độ search (mặc định đứng yên)")
    
    args = parser.parse_args()

    # 2. Khi chạy GUI (Mặc định khi chạy 'python main.py' hoặc 'python main.py -ui gui'):
    # Toàn quyền điều khiển cấu hình được chuyển giao cho hệ thống Dropdown Menu trên giao diện Pygame
    if args.ui == "gui":
        try:
            from ui.g_ui import run_gui_app
            run_gui_app(
                initial_map=args.map,
                initial_algo=args.algo,
                initial_heuristic=args.heuristic
            )
            return
        except ImportError as e:
            print(f"\n[LỖI] Không thể tải thư viện đồ họa GUI: {e}")
            print("Vui lòng cài đặt Pygame bằng lệnh: pip install pygame")
            print("Chuyển về giao diện CLI tự động...\n")
            args.ui = "cli"

    # 3. Khi chạy CLI (-ui cli): Chạy vòng lặp game trên Terminal
    print("Bắt đầu game với các tham số:")
    print(f"- Chế độ (Mode): {args.mode}")
    print(f"- Bản đồ (Map): {args.map}")
    print(f"- Thuật toán (Algo): {args.algo}")
    print(f"- Giao diện (UI): CLI")
    if args.mode == "search" and args.algo in ("astar", "greedy"):
        print(f"- Heuristic: {args.heuristic}")
    if args.ghost_move:
        print("- Ghost Move: Bật (Ghost di chuyển ngẫu nhiên)")

    from ui.cli_ui import CLI_UI
    ui = CLI_UI()
    
    agents = []
    ghost_factory = None
    if args.mode.lower() == "search":
        if args.algo not in ["bfs", "dfs", "astar", "ucs"]:
            print(f"Cảnh báo: Thuật toán '{args.algo}' có thể không được hỗ trợ trong chế độ 'search'.")
            
        pacman_agent = SearchAgent(algorithm_name=args.algo, heuristic=args.heuristic)
        agents.append(pacman_agent)
        ghost_factory = lambda i: DummyGhostAgent(index=i, random_move=args.ghost_move)

    elif args.mode.lower() == "adversarial":
        if args.algo not in ["minimax", "alphabeta"]:
            print(f"Cảnh báo: Thuật toán '{args.algo}' có thể không được hỗ trợ trong chế độ 'adversarial'.")
            
        from src.agents import MinimaxAgent, AlphaBetaAgent, ChaserGhostAgent
        if args.algo.lower() == "minimax":
            pacman_agent = MinimaxAgent(depth=args.depth)
        else: # alphabeta
            pacman_agent = AlphaBetaAgent(depth=args.depth)
        agents.append(pacman_agent)
        ghost_factory = lambda i: ChaserGhostAgent(index=i, seed=args.seed)
    
    max_turns = args.max_turns if args.mode.lower() == "adversarial" else None
    game = GameLoop(map_file=args.map, agents=agents, ui=ui, max_turns=max_turns, ghost_factory=ghost_factory)
    game.run()

    if hasattr(pacman_agent, 'get_metrics'):
        ui.show_metrics(pacman_agent.get_metrics())

if __name__ == "__main__":
    main()