"""
test_pacman.py - Bộ kiểm thử tự động (Unit Tests) cho Dự án Pacman AI.

Bao gồm 12 bài kiểm thử (vượt yêu cầu tối thiểu 10 bài của đề bài):
1. BFS tìm đường đi ngắn nhất
2. DFS tìm thấy lời giải hợp lệ
3. UCS tìm đường đi có chi phí tối thiểu
4. Greedy Best-First Search tìm được lời giải
5. A* với MST Heuristic tìm được chuỗi hành động tối ưu
6. Tính Admissible của MST Heuristic (h <= h*)
7. Giá trị Heuristic tại trạng thái đích bằng 0
8. Phát hiện bản đồ không có lời giải
9. Minimax và Alpha-Beta đưa ra hành động tương đương
10. Alpha-Beta Pruning mở rộng ít node hơn Minimax
11. Luật va chạm với Ghost dẫn đến Game Over (Thua)
12. Ăn hết thức ăn dẫn đến Chiến thắng
"""
import unittest

from src.engine import GameState, GameLoop
from src.search.problems import MultiFoodSearchProblem
from src.search.algorithms import dfs, bfs, ucs, greedy, astar
from src.search.heuristics import mst_heuristic, null_heuristic
from src.search.adversarial import minimax_search, alphabeta_search
from src.agents import MinimaxAgent, AlphaBetaAgent


class TestPacmanAlgorithms(unittest.TestCase):
    def setUp(self):
        """Khởi tạo một bản đồ nhỏ hình chữ U để kiểm thử tìm kiếm."""
        # #####
        # #P .#  (1,1) là P, (3,1) là .
        # # # #  (2,1) là tường ngăn cách trên hàng 1
        # #   #  (1,3), (2,3), (3,3) là đường vòng phía dưới
        # #####
        self.walls = {
            (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
            (0, 1),         (2, 1),         (4, 1),
            (0, 2),         (2, 2),         (4, 2),
            (0, 3),                         (4, 3),
            (0, 4), (1, 4), (2, 4), (3, 4), (4, 4),
        }
        self.start_pos = (1, 1)
        self.food = {(3, 1)}
        self.problem = MultiFoodSearchProblem(
            walls=self.walls,
            width=5,
            height=5,
            start_pos=self.start_pos,
            food=self.food,
        )

    def test_01_bfs_shortest_path(self):
        """1. Kiểm tra BFS tìm đường đi có số bước ngắn nhất."""
        result = bfs(self.problem)
        self.assertTrue(result.found)
        # Đường vòng qua (1,2) -> (1,3) -> (2,3) -> (3,3) -> (3,2) -> (3,1) = 6 bước
        self.assertEqual(len(result.actions), 6)
        self.assertEqual(result.cost, 6)

    def test_02_dfs_finds_solution(self):
        """2. Kiểm tra DFS tìm được đường đi tới đích trên bản đồ có nghiệm."""
        result = dfs(self.problem)
        self.assertTrue(result.found)
        self.assertGreater(len(result.actions), 0)

    def test_03_ucs_optimal_cost(self):
        """3. Kiểm tra Uniform-Cost Search (UCS) tìm đường có chi phí tối thiểu."""
        result = ucs(self.problem)
        self.assertTrue(result.found)
        self.assertEqual(result.cost, 6)

    def test_04_greedy_best_first_search(self):
        """4. Kiểm tra Greedy Best-First Search tìm được lời giải."""
        result = greedy(self.problem, heuristic="mst")
        self.assertTrue(result.found)
        self.assertGreater(len(result.actions), 0)

    def test_05_astar_mst_optimal(self):
        """5. Kiểm tra A* với MST Heuristic tìm được chuỗi hành động tối ưu."""
        result = astar(self.problem, heuristic="mst")
        self.assertTrue(result.found)
        self.assertEqual(result.cost, 6)

    def test_06_heuristic_admissible(self):
        """6. Kiểm tra tính Admissible của MST Heuristic: h(s) <= h*(s)."""
        start_state = self.problem.get_start_state()
        h_val = mst_heuristic(start_state, self.problem)
        # Khoảng cách tối ưu thực tế từ (1,1) đến (3,1) là 6
        true_optimal_cost = 6
        self.assertLessEqual(h_val, true_optimal_cost)
        self.assertGreaterEqual(h_val, 0)

    def test_07_heuristic_goal_state_is_zero(self):
        """7. Kiểm tra giá trị Heuristic tại trạng thái đích luôn bằng 0."""
        goal_state = ((3, 1), frozenset())
        h_val = mst_heuristic(goal_state, self.problem)
        self.assertEqual(h_val, 0)

    def test_08_unsolvable_map_detection(self):
        """8. Kiểm tra hệ thống phát hiện chính xác bản đồ không có lời giải."""
        # Bản đồ có thức ăn bị bao bọc hoàn toàn bởi tường
        unsolvable_problem = MultiFoodSearchProblem(
            walls=self.walls | {(3, 2)},  # Chặn nốt lối vào (3,1)
            width=5,
            height=5,
            start_pos=self.start_pos,
            food=self.food,
        )
        self.assertFalse(unsolvable_problem.is_solvable())
        result = astar(unsolvable_problem)
        self.assertFalse(result.found)
        self.assertEqual(len(result.actions), 0)

    def test_09_minimax_alphabeta_equivalence(self):
        """9. Kiểm tra Minimax và Alpha-Beta đưa ra hành động tương đương."""
        state = GameState()
        state.width = 5
        state.height = 3
        state.pacman_pos = (1, 1)
        state.ghosts_pos = [(3, 1)]
        state.food = {(1, 2)}
        state.walls = set()

        res_minimax = minimax_search(state, depth=2)
        res_alphabeta = alphabeta_search(state, depth=2)

        self.assertEqual(res_minimax.action, res_alphabeta.action)
        self.assertEqual(res_minimax.value, res_alphabeta.value)

    def test_10_alphabeta_pruning_efficiency(self):
        """10. Kiểm tra Alpha-Beta Pruning mở rộng ít hơn hoặc bằng số node so với Minimax."""
        state = GameState()
        state.width = 6
        state.height = 4
        state.pacman_pos = (1, 1)
        state.ghosts_pos = [(4, 2)]
        state.food = {(1, 2), (2, 2)}
        state.walls = set()

        res_minimax = minimax_search(state, depth=2)
        res_alphabeta = alphabeta_search(state, depth=2)

        self.assertLessEqual(res_alphabeta.expanded_nodes, res_minimax.expanded_nodes)

    def test_11_ghost_collision_loses_game(self):
        """11. Kiểm tra luật va chạm: Pacman chạm Ghost dẫn đến Game Over (Thua)."""
        state = GameState()
        state.pacman_pos = (1, 1)
        state.ghosts_pos = [(2, 1)]
        state.food = {(1, 2)}

        # Pacman đi RIGHT vào (2, 1), nơi Ghost đang đứng
        next_state = state.generate_successor(0, "RIGHT")
        self.assertTrue(next_state.is_lose())
        self.assertTrue(next_state.is_game_over)
        self.assertEqual(next_state.end_reason, "lose")

    def test_12_food_collection_wins_game(self):
        """12. Kiểm tra luật chiến thắng: Ăn hết thức ăn dẫn đến Chiến thắng."""
        state = GameState()
        state.pacman_pos = (1, 1)
        state.ghosts_pos = [(4, 4)]
        state.food = {(1, 2)}

        # Pacman đi DOWN vào (1, 2) ăn viên thức ăn duy nhất còn lại
        next_state = state.generate_successor(0, "DOWN")
        self.assertTrue(next_state.is_win())
        self.assertTrue(next_state.is_game_over)
    def test_13_greedy_vs_astar_suboptimality(self):
        """13. Kiểm tra Greedy tìm ra đường đi dưới tối ưu (dài hơn A*) trên map_greedy_vs_astar."""
        with open("maps/map_greedy_vs_astar.txt", "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        walls = set()
        food = set()
        start_pos = None
        for r, line in enumerate(lines):
            for c, ch in enumerate(line):
                if ch == "#":
                    walls.add((c, r))
                elif ch == "P":
                    start_pos = (c, r)
                elif ch == ".":
                    food.add((c, r))

        problem = MultiFoodSearchProblem(
            walls=walls, width=len(lines[0]), height=len(lines), start_pos=start_pos, food=food
        )
        res_astar = astar(problem, "mst")
        res_greedy = greedy(problem, "mst")

        self.assertTrue(res_astar.found)
        self.assertTrue(res_greedy.found)
        self.assertLess(res_astar.cost, res_greedy.cost)
        self.assertEqual(res_astar.cost, 34)
        self.assertEqual(res_greedy.cost, 44)

    def test_14_unsolvable_map_does_not_win(self):
        """14. Kiểm tra map không lời giải kết thúc với no_solution và không bao giờ báo win."""
        from src.agents import SearchAgent
        state = GameState()
        with open("maps/map_khong_loi_giai_pacman.txt", "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        for r, line in enumerate(lines):
            for c, ch in enumerate(line):
                if ch == "#":
                    state.walls.add((c, r))
                elif ch == "P":
                    state.pacman_pos = (c, r)
                elif ch == ".":
                    state.food.add((c, r))
        state.width = len(lines[0])
        state.height = len(lines)

        agent = SearchAgent(algorithm_name="astar", heuristic="mst")
        action = agent.get_action(state)
        self.assertEqual(action, "STOP")
        self.assertEqual(agent.stuck_reason, "no_solution")
        self.assertFalse(agent.metrics["found"])

        state.end_game(agent.stuck_reason)
        self.assertTrue(state.is_game_over)
        self.assertFalse(state.is_win())
        self.assertEqual(state.end_reason, "no_solution")


if __name__ == "__main__":
    unittest.main()
