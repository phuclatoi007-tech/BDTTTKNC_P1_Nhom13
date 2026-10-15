"""
agents.py - Bộ não ra quyết định: kết nối Game Engine và các thuật toán AI.
"""
import random
import time
from collections import deque

from src.search.problems import DIRECTIONS, MultiFoodSearchProblem
from src.search.algorithms import run_search, normalize_algo_name
from src.search.adversarial import (
    MazeDistance,
    default_evaluation_fn,
    minimax_search,
    alphabeta_search,
    ghost_minimax_search,
    ghost_alphabeta_search,
    get_maze_distance,
)


class Agent:
    """Base Class cho mọi nhân vật trong game."""

    def get_action(self, game_state):
        raise NotImplementedError


class SearchAgent(Agent):
    """
    Agent dành cho Pacman (index 0).

    Lần gọi get_action đầu tiên: dịch GameState -> MultiFoodSearchProblem, chạy
    thuật toán tìm kiếm để có cả chuỗi hành động. Các lượt sau chỉ pop() từng
    hành động ra trả cho Game Engine.
    """

    def __init__(self, algorithm_name="astar", heuristic=None, depth=5):
        self.algorithm_name = normalize_algo_name(algorithm_name)
        self.depth = max(depth, 5) if self.algorithm_name in ("minimax", "alphabeta") else depth
        # A* và Greedy dùng heuristic (mặc định MST); các thuật toán mù không dùng
        if self.algorithm_name in ("astar", "greedy"):
            self.heuristic = heuristic if heuristic is not None else "mst"
        else:
            self.heuristic = None
        self.plan = None                 # deque các hành động còn lại
        self.metrics = {}
        self.stuck_reason = None

        self.adversarial_agent = None
        if self.algorithm_name == "minimax":
            self.adversarial_agent = MinimaxAgent(depth=self.depth)
        elif self.algorithm_name == "alphabeta":
            self.adversarial_agent = AlphaBetaAgent(depth=self.depth)

    # --- thông dịch GameState -> SearchProblem ------------------------------
    @staticmethod
    def build_problem(game_state):
        food_data = getattr(game_state, "food_values", None) or game_state.food
        return MultiFoodSearchProblem(
            walls=game_state.walls,
            width=game_state.width,
            height=game_state.height,
            start_pos=game_state.pacman_pos,
            food=food_data,
        )

    def _plan_path(self, game_state):
        t0 = time.perf_counter()
        problem = self.build_problem(game_state)
        result = run_search(self.algorithm_name, problem, self.heuristic, depth=self.depth)
        total = time.perf_counter() - t0

        self.plan = deque(result.actions)
        self.metrics = {
            "algorithm": self.algorithm_name,
            "heuristic": self.heuristic if isinstance(self.heuristic, str)
                         else getattr(self.heuristic, "__name__", None),
            "found": result.found,
            "path_cost": result.cost,
            "plan_length": len(result.actions),
            "expanded_nodes": result.expanded,
            "generated_nodes": result.generated,
            "max_frontier": result.max_frontier,
            "search_time": result.time,
            "preprocess_time": problem.preprocess_time,
            "total_time": total,
        }

    def get_action(self, game_state):
        if self.adversarial_agent is not None:
            action = self.adversarial_agent.get_action(game_state)
            if getattr(self.adversarial_agent, "stuck_reason", None):
                self.stuck_reason = self.adversarial_agent.stuck_reason
            return action

        if self.plan is None:
            self._plan_path(game_state)
        if not self.plan:                # hết kế hoạch hoặc vô nghiệm
            self.stuck_reason = ("plan_exhausted" if self.metrics.get("found")
                                 else "no_solution")
            return "STOP"
        return self.plan.popleft()

    def get_metrics(self):
        if self.adversarial_agent is not None:
            return self.adversarial_agent.get_metrics()
        return dict(self.metrics)

    def reset(self):
        self.plan = None
        self.metrics = {}
        self.stuck_reason = None
        if self.adversarial_agent is not None:
            self.adversarial_agent.reset()


class DummyGhostAgent(Agent):
    """
    Agent dành cho Ghost, chỉ để kiểm thử.
    random_move=False: đứng im (mặc định, kết quả tái lập được).
    random_move=True : đi ngẫu nhiên trong các hướng hợp lệ.
    """

    def __init__(self, index=1, random_move=False):
        self.index = index
        self.random_move = random_move

    def get_action(self, game_state):
        if not self.random_move:
            return "STOP"
        actions = [a for a in game_state.get_legal_actions(self.index)
                   if a != "STOP"]
        return random.choice(actions) if actions else "STOP"


# ---------------------------------------------------------------------------
# Adversarial: Minimax / Alpha-Beta cho Pacman & Smart Cut-Off Ghost
# ---------------------------------------------------------------------------
class AdversarialAgent(Agent):
    """
    Pacman (index 0) = MAX, các Ghost (index >= 1) = MIN.
    Một "độ sâu" = một vòng đủ lượt Pacman rồi lần lượt từng Ghost.
    """

    def __init__(self, depth=5, use_pruning=False, evaluation_fn=None):
        self.depth = max(depth, 5)
        self.use_pruning = use_pruning
        self._custom_eval_fn = evaluation_fn
        self.evaluation_fn = evaluation_fn or self.evaluate
        self._maze = None
        self._visit_counts = {}
        self._last_food_count = None
        self.expanded_nodes = 0
        self.moves = 0
        self.total_time = 0.0
        self.stuck_reason = None
        self.last_eval_value = 0.0

    def evaluate(self, state):
        if self._maze is None:
            self._maze = get_maze_distance(state)
        return default_evaluation_fn(state, self._maze)

    def get_action(self, game_state):
        if self._maze is None:
            self._maze = get_maze_distance(game_state)

        cur_food_count = len(game_state.food)
        if self._last_food_count != cur_food_count:
            self._visit_counts.clear()
            self._last_food_count = cur_food_count

        state_key = (game_state.pacman_pos, cur_food_count)
        self._visit_counts[state_key] = self._visit_counts.get(state_key, 0) + 1

        eval_fn = self._custom_eval_fn or (lambda s: default_evaluation_fn(s, self._maze))
        if self.use_pruning:
            res = alphabeta_search(
                game_state,
                depth=self.depth,
                evaluation_fn=eval_fn,
                maze_distance=self._maze,
                agent_index=0,
                visit_counts=self._visit_counts,
            )
        else:
            res = minimax_search(
                game_state,
                depth=self.depth,
                evaluation_fn=eval_fn,
                maze_distance=self._maze,
                agent_index=0,
                visit_counts=self._visit_counts,
            )

        self.expanded_nodes += res.expanded_nodes
        self.last_eval_value = res.value
        self.moves += 1
        self.total_time += res.search_time
        return res.action

    def get_metrics(self):
        return {
            "algorithm": "alphabeta" if self.use_pruning else "minimax",
            "depth": self.depth,
            "moves": self.moves,
            "last_eval_value": self.last_eval_value,
            "expanded_nodes": self.expanded_nodes,
            "total_time": self.total_time,
            "avg_time_per_move": self.total_time / self.moves if self.moves else 0.0,
        }

    def reset(self):
        self._maze = None
        self._visit_counts.clear()
        self._last_food_count = None
        self.expanded_nodes = 0
        self.moves = 0
        self.total_time = 0.0
        self.stuck_reason = None
        self.last_eval_value = 0.0


class MinimaxAgent(AdversarialAgent):
    def __init__(self, depth=5, evaluation_fn=None):
        super().__init__(max(depth, 5), use_pruning=False, evaluation_fn=evaluation_fn)


class AlphaBetaAgent(AdversarialAgent):
    def __init__(self, depth=5, evaluation_fn=None):
        super().__init__(max(depth, 5), use_pruning=True, evaluation_fn=evaluation_fn)


class ChaserGhostAgent(Agent):
    """
    Smart Intercepting & Cut-Off Ghost (MIN Agent):
    Sử dụng tìm kiếm đối kháng Alpha-Beta với hàm đánh giá Geodesic Choke-Point
    và bộ nhớ chống nhấp nhả (_visit_counts) để tận dụng tối đa từng nhịp (tempo)
    khoá chặt đường rút của Pacman và phong toả cụm thức ăn lớn nhất.
    """

    def __init__(self, index=1, random_prob=0.0, seed=None, depth=3, use_pruning=True):
        self.index = index
        self.random_prob = random_prob
        self.rng = random.Random(seed)
        self.depth = depth
        self.use_pruning = use_pruning
        self._maze = None
        self._visit_counts = {}
        self._last_food_count = None

    def get_action(self, game_state):
        actions = [a for a in game_state.get_legal_actions(self.index)
                   if a != "STOP"]
        if not actions:
            return "STOP"

        if self._maze is None:
            self._maze = get_maze_distance(game_state)

        gx, gy = game_state.ghosts_pos[self.index - 1]
        # Nếu nước đi kế tiếp bắt được Pacman ngay lập tức -> bắt ngay
        for action in actions:
            dx, dy = DIRECTIONS[action]
            if (gx + dx, gy + dy) == game_state.pacman_pos:
                return action

        cur_food_count = len(game_state.food)
        if self._last_food_count != cur_food_count:
            self._visit_counts.clear()
            self._last_food_count = cur_food_count

        g_key = ((gx, gy), cur_food_count)
        self._visit_counts[g_key] = self._visit_counts.get(g_key, 0) + 1

        if self.use_pruning:
            res = ghost_alphabeta_search(
                game_state,
                ghost_index=self.index,
                depth=self.depth,
                maze_distance=self._maze,
                visit_counts=self._visit_counts,
            )
        else:
            res = ghost_minimax_search(
                game_state,
                ghost_index=self.index,
                depth=self.depth,
                maze_distance=self._maze,
                visit_counts=self._visit_counts,
            )
        return res.action

    def reset(self):
        self._maze = None
        self._visit_counts.clear()
        self._last_food_count = None


class MinimaxGhostAgent(ChaserGhostAgent):
    def __init__(self, index=1, depth=3):
        super().__init__(index=index, random_prob=0.0, depth=depth, use_pruning=False)


class AlphaBetaGhostAgent(ChaserGhostAgent):
    def __init__(self, index=1, depth=3):
        super().__init__(index=index, random_prob=0.0, depth=depth, use_pruning=True)