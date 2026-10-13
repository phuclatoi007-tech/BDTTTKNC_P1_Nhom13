"""
adversarial.py - Thuật toán tìm kiếm đối kháng (Adversarial Search).

Cung cấp:
- MazeDistance: BFS tính khoảng cách mê cung (phục vụ hàm đánh giá)
- default_evaluation_fn: Hàm đánh giá trạng thái trò chơi cho Pacman (MAX)
- minimax_search: Thuật toán Minimax đối kháng thuần tuý (Game Tree Search)
- alphabeta_search: Thuật toán Minimax kết hợp cắt tỉa Alpha-Beta Pruning
"""
import time
from collections import deque
from dataclasses import dataclass
from src.search.problems import DIRECTIONS


@dataclass
class AdversarialSearchResult:
    """Kết quả trả về từ thuật toán tìm kiếm đối kháng."""
    action: str = "STOP"
    value: float = 0.0
    expanded_nodes: int = 0
    search_time: float = 0.0


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


def default_evaluation_fn(state, maze_distance=None):
    """
    Hàm đánh giá heuristic cho trạng thái bàn cờ:
    Pacman là MAX:
    + Thắng: +500 điểm thưởng
    - Thua: -500 điểm phạt
    - Bình thường:
      + Điểm số game hiện tại
      - 5 * số lượng thức ăn còn lại (khuyến khích ăn thức ăn)
      - Khoảng cách mê cung tới viên thức ăn gần nhất (khuyến khích tiến gần thức ăn)
      - Phạt nặng nếu Ghost ở quá gần (khoảng cách <= 2 ô)
    """
    if state.is_win():
        return state.score + 500
    if state.is_lose():
        return state.score - 500

    pos = state.pacman_pos
    value = state.score - 5 * len(state.food)

    if maze_distance is not None:
        reachable = [d for d in (maze_distance.distance(f, pos) for f in state.food)
                     if d != float("inf")]
        if reachable:
            value -= min(reachable)

        if state.ghosts_pos:
            g = min(maze_distance.distance(pos, gp) for gp in state.ghosts_pos)
            if g <= 2:
                value -= (3 - g) * 40
    else:
        # Fallback tính khoảng cách Manhattan nếu chưa khởi tạo maze_distance
        if state.food:
            value -= min(abs(pos[0] - f[0]) + abs(pos[1] - f[1]) for f in state.food)
        if state.ghosts_pos:
            g = min(abs(pos[0] - gp[0]) + abs(pos[1] - gp[1]) for gp in state.ghosts_pos)
            if g <= 2:
                value -= (3 - g) * 40

    return value


def get_legal_actions_filtered(state, agent_index):
    """
    Lấy danh sách các nước đi hợp lệ của agent_index,
    loại bỏ 'STOP' trừ khi không còn nước đi nào khác.
    """
    actions = state.get_legal_actions(agent_index)
    moves = [a for a in actions if a != "STOP"]
    return moves if moves else actions


def minimax_search(state, depth=3, evaluation_fn=None, maze_distance=None):
    """
    Thuật toán Minimax thuần cho đối kháng nhiều tác tử (Multi-agent Minimax):
    - Pacman (agent 0) là MAX.
    - Ghost (agent 1..N) là MIN.
    - 1 ply độ sâu (depth) = 1 lượt đầy đủ: Pacman đi rồi lần lượt từng Ghost đi.
    """
    t0 = time.perf_counter()
    eval_fn = evaluation_fn or (lambda s: default_evaluation_fn(s, maze_distance))
    expanded = 0

    def min_value(s, ghost_idx, d):
        nonlocal expanded
        if s.is_win() or s.is_lose() or d == 0:
            return eval_fn(s)

        actions = get_legal_actions_filtered(s, ghost_idx)
        if not actions:
            return eval_fn(s)

        num_agents = 1 + len(s.ghosts_pos)
        is_last_ghost = (ghost_idx == num_agents - 1)
        next_ghost = ghost_idx + 1

        v = float("inf")
        for action in actions:
            expanded += 1
            successor = s.generate_successor(ghost_idx, action)
            if is_last_ghost:
                v = min(v, max_value(successor, d - 1))
            else:
                v = min(v, min_value(successor, next_ghost, d))
        return v

    def max_value(s, d):
        nonlocal expanded
        if s.is_win() or s.is_lose() or d == 0:
            return eval_fn(s)

        actions = get_legal_actions_filtered(s, 0)
        if not actions:
            return eval_fn(s)

        num_agents = 1 + len(s.ghosts_pos)
        has_ghosts = (num_agents > 1)

        v = float("-inf")
        for action in actions:
            expanded += 1
            successor = s.generate_successor(0, action)
            if has_ghosts:
                v = max(v, min_value(successor, 1, d))
            else:
                v = max(v, max_value(successor, d - 1))
        return v

    actions = get_legal_actions_filtered(state, 0)
    if not actions:
        return AdversarialSearchResult(
            action="STOP", value=eval_fn(state), expanded_nodes=0, search_time=time.perf_counter() - t0
        )

    num_agents = 1 + len(state.ghosts_pos)
    has_ghosts = (num_agents > 1)

    best_action = actions[0]
    best_value = float("-inf")
    best_key = None

    for action in actions:
        expanded += 1
        child = state.generate_successor(0, action)
        if has_ghosts:
            v = min_value(child, 1, depth)
        else:
            v = max_value(child, depth - 1)

        # Phá hoà (tie-breaking): nếu điểm minimax ngang nhau,
        # ưu tiên nước đi có điểm đánh giá tức thời tốt hơn để tránh đi loanh quanh.
        key = (v, eval_fn(child))
        if best_key is None or key > best_key:
            best_key = key
            best_value = v
            best_action = action

    total_time = time.perf_counter() - t0
    return AdversarialSearchResult(
        action=best_action, value=best_value, expanded_nodes=expanded, search_time=total_time
    )


def alphabeta_search(state, depth=3, evaluation_fn=None, maze_distance=None):
    """
    Thuật toán tìm kiếm đối kháng Minimax kết hợp cắt tỉa Alpha-Beta (Alpha-Beta Pruning):
    Cắt tỉa khi beta <= alpha, cho ra quyết định tương đương Minimax nhưng duyệt ít node hơn.
    """
    t0 = time.perf_counter()
    eval_fn = evaluation_fn or (lambda s: default_evaluation_fn(s, maze_distance))
    expanded = 0

    def min_value(s, ghost_idx, d, alpha, beta):
        nonlocal expanded
        if s.is_win() or s.is_lose() or d == 0:
            return eval_fn(s)

        actions = get_legal_actions_filtered(s, ghost_idx)
        if not actions:
            return eval_fn(s)

        num_agents = 1 + len(s.ghosts_pos)
        is_last_ghost = (ghost_idx == num_agents - 1)
        next_ghost = ghost_idx + 1

        v = float("inf")
        for action in actions:
            expanded += 1
            successor = s.generate_successor(ghost_idx, action)
            if is_last_ghost:
                v = min(v, max_value(successor, d - 1, alpha, beta))
            else:
                v = min(v, min_value(successor, next_ghost, d, alpha, beta))
            beta = min(beta, v)
            if beta <= alpha:
                break
        return v

    def max_value(s, d, alpha, beta):
        nonlocal expanded
        if s.is_win() or s.is_lose() or d == 0:
            return eval_fn(s)

        actions = get_legal_actions_filtered(s, 0)
        if not actions:
            return eval_fn(s)

        num_agents = 1 + len(s.ghosts_pos)
        has_ghosts = (num_agents > 1)

        v = float("-inf")
        for action in actions:
            expanded += 1
            successor = s.generate_successor(0, action)
            if has_ghosts:
                v = max(v, min_value(successor, 1, d, alpha, beta))
            else:
                v = max(v, max_value(successor, d - 1, alpha, beta))
            alpha = max(alpha, v)
            if beta <= alpha:
                break
        return v

    actions = get_legal_actions_filtered(state, 0)
    if not actions:
        return AdversarialSearchResult(
            action="STOP", value=eval_fn(state), expanded_nodes=0, search_time=time.perf_counter() - t0
        )

    num_agents = 1 + len(state.ghosts_pos)
    has_ghosts = (num_agents > 1)

    best_action = actions[0]
    best_value = float("-inf")
    best_key = None
    alpha = float("-inf")
    beta = float("inf")

    for action in actions:
        expanded += 1
        child = state.generate_successor(0, action)
        if has_ghosts:
            v = min_value(child, 1, depth, alpha, beta)
        else:
            v = max_value(child, depth - 1, alpha, beta)

        key = (v, eval_fn(child))
        if best_key is None or key > best_key:
            best_key = key
            best_value = v
            best_action = action
        alpha = max(alpha, best_value)

    total_time = time.perf_counter() - t0
    return AdversarialSearchResult(
        action=best_action, value=best_value, expanded_nodes=expanded, search_time=total_time
    )
