"""
agents.py - Bộ não ra quyết định: kết nối Game Engine và các thuật toán AI.
"""
import random
import time
from collections import deque

from src.search.problems import DIRECTIONS

from src.search.algorithms import run_search, normalize_algo_name
from src.search.problems import MultiFoodSearchProblem


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

    def __init__(self, algorithm_name="astar", heuristic=None):
        self.algorithm_name = normalize_algo_name(algorithm_name)
        # A* mặc định dùng MST; các thuật toán mù không dùng heuristic
        if self.algorithm_name == "astar":
            self.heuristic = heuristic if heuristic is not None else "mst"
        else:
            self.heuristic = None
        self.plan = None                 # deque các hành động còn lại
        self.metrics = {}
        # Khác None khi agent không còn gì để làm; GameLoop dựa vào đây để kết thúc
        # ván thay vì lặp STOP vô hạn: "no_solution" | "plan_exhausted"
        self.stuck_reason = None

    # --- thông dịch GameState -> SearchProblem ------------------------------
    @staticmethod
    def build_problem(game_state):
        return MultiFoodSearchProblem(
            walls=game_state.walls,
            width=game_state.width,
            height=game_state.height,
            start_pos=game_state.pacman_pos,
            food=game_state.food,
        )

    def _plan_path(self, game_state):
        t0 = time.perf_counter()
        problem = self.build_problem(game_state)
        result = run_search(self.algorithm_name, problem, self.heuristic)
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
        if self.plan is None:
            self._plan_path(game_state)
        if not self.plan:                # hết kế hoạch hoặc vô nghiệm
            self.stuck_reason = ("plan_exhausted" if self.metrics.get("found")
                                 else "no_solution")
            return "STOP"
        return self.plan.popleft()

    def get_metrics(self):
        return dict(self.metrics)


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
# Adversarial: Minimax / Alpha-Beta cho Pacman, Ghost đuổi theo Pacman
# ---------------------------------------------------------------------------
class MazeDistance:
    """Khoảng cách mê cung (BFS) tính lười và nhớ lại - dùng cho hàm đánh giá."""

    def __init__(self, state):
        self.walls = state.walls
        self.width = state.width
        self.height = state.height
        self._maps = {}

    def _bfs(self, source):
        dist = {source: 0}
        queue = deque([source])
        while queue:
            x, y = queue.popleft()
            d = dist[(x, y)] + 1
            for dx, dy in DIRECTIONS.values():
                nxt = (x + dx, y + dy)
                if (nxt not in dist and nxt not in self.walls
                        and 0 <= nxt[0] < self.width and 0 <= nxt[1] < self.height):
                    dist[nxt] = d
                    queue.append(nxt)
        return dist

    def distance(self, a, b):
        if b in self._maps:
            return self._maps[b].get(a, float("inf"))
        if a not in self._maps:
            self._maps[a] = self._bfs(a)
        return self._maps[a].get(b, float("inf"))


class AdversarialAgent(Agent):
    """
    Pacman (index 0) = MAX, các Ghost (index >= 1) = MIN.
    Một "độ sâu" = một vòng đủ lượt Pacman rồi lần lượt từng Ghost.

    use_pruning=False -> Minimax thuần;  True -> Alpha-Beta (cho kết quả giống
    hệt Minimax nhưng mở rộng ít node hơn).
    """

    WIN_BONUS = 500
    LOSE_PENALTY = 500

    def __init__(self, depth=3, use_pruning=False, evaluation_fn=None):
        self.depth = depth
        self.use_pruning = use_pruning
        self.evaluation_fn = evaluation_fn or self.evaluate
        self._maze = None
        self.expanded_nodes = 0
        self.moves = 0
        self.total_time = 0.0
        self.stuck_reason = None

    # --- hàm đánh giá --------------------------------------------------------
    def evaluate(self, state):
        if state.is_win():
            return state.score + self.WIN_BONUS
        if state.is_lose():
            return state.score - self.LOSE_PENALTY

        pos = state.pacman_pos
        value = state.score - 5 * len(state.food)          # ăn thêm = lợi
        # gần mồi hơn (bỏ qua mồi không thể tới - khoảng cách vô cực)
        reachable = [d for d in (self._maze.distance(f, pos) for f in state.food)
                     if d != float("inf")]
        if reachable:
            value -= min(reachable)

        if state.ghosts_pos:
            g = min(self._maze.distance(pos, gp) for gp in state.ghosts_pos)
            if g <= 2:                                      # phạt khi ghost quá gần
                value -= (3 - g) * 40
        return value

    # --- cây trò chơi ----------------------------------------------------------
    @staticmethod
    def _actions(state, agent_index):
        actions = state.get_legal_actions(agent_index)
        moves = [a for a in actions if a != "STOP"]
        return moves if moves else actions                  # bỏ STOP trừ khi bí

    def _value(self, state, agent_index, depth, alpha, beta):
        if state.is_win() or state.is_lose() or depth == 0:
            return self.evaluation_fn(state)

        actions = self._actions(state, agent_index)
        if not actions:
            return self.evaluation_fn(state)

        n_agents = 1 + len(state.ghosts_pos)
        next_index = (agent_index + 1) % n_agents
        next_depth = depth - 1 if next_index == 0 else depth
        is_max = agent_index == 0

        best = float("-inf") if is_max else float("inf")
        for action in actions:
            self.expanded_nodes += 1
            child = state.generate_successor(agent_index, action)
            v = self._value(child, next_index, next_depth, alpha, beta)
            if is_max:
                best = max(best, v)
                alpha = max(alpha, best)
            else:
                best = min(best, v)
                beta = min(beta, best)
            if self.use_pruning and beta < alpha:           # cắt tỉa (nghiêm ngặt)
                break
        return best

    # --- giao diện Agent ----------------------------------------------------------
    def get_action(self, game_state):
        t0 = time.perf_counter()
        if self._maze is None:
            self._maze = MazeDistance(game_state)

        actions = self._actions(game_state, 0)
        if not actions:
            return "STOP"

        best_action, best_value, best_key = actions[0], float("-inf"), None
        alpha, beta = float("-inf"), float("inf")
        n_agents = 1 + len(game_state.ghosts_pos)
        next_depth = self.depth - 1 if n_agents == 1 else self.depth
        for action in actions:
            self.expanded_nodes += 1
            child = game_state.generate_successor(0, action)
            v = self._value(child, 1 % n_agents, next_depth, alpha, beta)
            # Hoà giá trị minimax -> chọn nước có đánh giá tức thời tốt hơn, để
            # Pacman không "trì hoãn" (vd: đi vòng vòng thay vì ăn mồi ngay).
            key = (v, self.evaluation_fn(child))
            if best_key is None or key > best_key:
                best_key, best_value, best_action = key, v, action
            alpha = max(alpha, best_value)

        self.moves += 1
        self.total_time += time.perf_counter() - t0
        return best_action

    def get_metrics(self):
        return {
            "algorithm": "alphabeta" if self.use_pruning else "minimax",
            "depth": self.depth,
            "moves": self.moves,
            "expanded_nodes": self.expanded_nodes,
            "total_time": self.total_time,
            "avg_time_per_move": self.total_time / self.moves if self.moves else 0.0,
        }


class MinimaxAgent(AdversarialAgent):
    def __init__(self, depth=3, evaluation_fn=None):
        super().__init__(depth, use_pruning=False, evaluation_fn=evaluation_fn)


class AlphaBetaAgent(AdversarialAgent):
    def __init__(self, depth=3, evaluation_fn=None):
        super().__init__(depth, use_pruning=True, evaluation_fn=evaluation_fn)


class ChaserGhostAgent(Agent):
    """
    Ghost đuổi Pacman: đi nước làm giảm khoảng cách mê cung tới Pacman nhiều nhất;
    với xác suất random_prob thì đi ngẫu nhiên (để Pacman còn cơ hội thoát).
    """

    def __init__(self, index=1, random_prob=0.2, seed=None):
        self.index = index
        self.random_prob = random_prob
        self.rng = random.Random(seed)
        self._maze = None

    def get_action(self, game_state):
        actions = [a for a in game_state.get_legal_actions(self.index)
                   if a != "STOP"]
        if not actions:
            return "STOP"
        if self.rng.random() < self.random_prob:
            return self.rng.choice(actions)

        if self._maze is None:
            self._maze = MazeDistance(game_state)
        gx, gy = game_state.ghosts_pos[self.index - 1]

        def dist_after(action):
            dx, dy = DIRECTIONS[action]
            return self._maze.distance(game_state.pacman_pos, (gx + dx, gy + dy))

        best = min(dist_after(a) for a in actions)
        return self.rng.choice([a for a in actions if dist_after(a) == best])
