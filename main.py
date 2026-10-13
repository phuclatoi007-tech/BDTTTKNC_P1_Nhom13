import argparse
import time
from src.engine import GameLoop
from src.agents import SearchAgent, DummyGhostAgent
from ui.g_ui import GUI_UI
from ui.cli_ui import CLI_UI

def main():
    # 1. Đọc tham số dòng lệnh
    parser = argparse.ArgumentParser(description="Pacman Game")
    # Thay đổi thành -mode và bắt buộc nhập
    parser.add_argument("-mode", type=str, required=True, choices=["search", "adversarial"], 
                        help="Chế độ chơi: search hoặc adversarial")
    # Thay đổi thành -map và bắt buộc nhập
    parser.add_argument("-map", type=str, required=True, 
                        help="Đường dẫn đến file map (vd: maps/map1.txt)")
    # Thêm -algo để chọn thuật toán
    parser.add_argument("-algo", type=str, default="astar", 
                        help="Thuật toán (bfs, dfs, astar, ucs cho search; minimax, alphabeta cho adversarial)")
    # Giữ lại heuristic cho A*
    parser.add_argument("-heuristic", type=str, default="mst", 
                        help="Heuristic sử dụng cho A* (vd: mst)")
    # Lựa chọn loại UI
    parser.add_argument("-ui", type=str, default="cli", choices=["cli", "gui"],
                        help="Giao diện hiển thị: cli (Terminal) hoặc gui (Đồ họa Pygame)")
    
    args = parser.parse_args()
    
    print("Bắt đầu game với các tham số:")
    print(f"- Chế độ (Mode): {args.mode}")
    print(f"- Bản đồ (Map): {args.map}")
    print(f"- Thuật toán (Algo): {args.algo}")
    print(f"- Giao diện (UI): {args.ui.upper()}")
    if args.mode == "search" and args.algo == "astar":
        print(f"- Heuristic: {args.heuristic}")

    # 2. Khởi tạo UI
    if args.ui == "gui":
        try:
            from ui.g_ui import GUI_UI
            ui = GUI_UI()
        except ImportError:
            print("\n[LỖI] Không thể tải thư viện đồ họa.")
            print("Vui lòng cài đặt Pygame bằng lệnh: pip install pygame")
            print("Chuyển về giao diện CLI tự động...\n")
            from ui.cli_ui import CLI_UI
            ui = CLI_UI()
    else:
        from ui.cli_ui import CLI_UI
        ui = CLI_UI()
    
    # 3. Khởi tạo Agent cho Pacman[cite: 10]
    agents = []
    if args.mode.lower() == "search":
        if args.algo not in ["bfs", "dfs", "astar", "ucs"]:
            print(f"Cảnh báo: Thuật toán '{args.algo}' có thể không được hỗ trợ trong chế độ 'search'.")
            
        pacman_agent = SearchAgent(algorithm_name=args.algo, heuristic=args.heuristic)
        agents.append(pacman_agent)
        
        # Trong chế độ search, ghost thường đứng yên
        ghost_agent = DummyGhostAgent(index=1, random_move=False)
        agents.append(ghost_agent)

    elif args.mode.lower() == "adversarial":
        if args.algo not in ["minimax", "alphabeta"]:
            print(f"Cảnh báo: Thuật toán '{args.algo}' có thể không được hỗ trợ trong chế độ 'adversarial'.")
            
        # TODO: Cần import và khởi tạo AdversarialAgent ở đây
        # Ví dụ: 
        # pacman_agent = MinimaxAgent(depth=3)
        # agents.append(pacman_agent)
        # ghost_agent = DummyGhostAgent(index=1, random_move=True) # Hoặc một Ghost có AI
        # agents.append(ghost_agent)
        
        print(f"\n[LỖI] Cần cài đặt lớp cho thuật toán '{args.algo}' trong file agents.py!")
        print("Tạm thời thoát game vì chế độ adversarial chưa được implement agent thực tế.")
        return
    
    # 4. Khởi tạo GameLoop[cite: 10]
    game = GameLoop(map_file=args.map, agents=agents, ui=ui)
    
    # 5. Chạy game[cite: 10]
    game.run()

    # 6. In kết quả (Metrics)[cite: 10]
    if args.mode.lower() == "search" and hasattr(pacman_agent, 'get_metrics'):
        ui.show_metrics(pacman_agent.get_metrics())

if __name__ == "__main__":
    main()