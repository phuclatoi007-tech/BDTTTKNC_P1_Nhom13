"""
algorithms.py - Động cơ tìm kiếm (Search Engine).

Chỉ có MỘT thuật toán lõi: general_graph_search. Các thuật toán cụ thể
(DFS, BFS, UCS, A*) chỉ khác nhau ở cấu trúc dữ liệu Frontier được truyền vào:
    DFS -> Stack (LIFO)            BFS -> Queue (FIFO)
    UCS -> PriorityQueue theo g    A*  -> PriorityQueue theo f = g + h
"""
import heapq
import itertools
import time
from collections import deque
from dataclasses import dataclass, field

from src.search.heuristics import get_heuristic
from src.search.adversarial import (
    minimax_search,
    alphabeta_search,
    get_maze_distance,
    AdversarialSearchResult,
)


# ---------------------------------------------------------------------------
# 1. Cấu trúc dữ liệu
# ---------------------------------------------------------------------------
class Node:
    """Đỉnh trên cây tìm kiếm: <state, parent, action, g>."""
    __slots__ = ("state", "parent", "action", "g")

    def __init__(self, state, parent=None, action=None, g=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.g = g

    def path_actions(self):
        """Truy xuất ngược về gốc để lấy chuỗi hành động."""
        actions, node = [], self
        while node.parent is not None:
            actions.append(node.action)
            node = node.parent
        actions.reverse()
        return actions


class Frontier:
    """Giao diện chung của tập biên. Mỗi state xuất hiện tối đa 1 lần."""
    # True nếu được phép thay node cũ bằng node cùng state nhưng g rẻ hơn
    REPLACE_ON_BETTER = False

    def __init__(self):
        self._nodes = {}          # state -> node đang nằm trong frontier

    def get(self, state):
        return self._nodes.get(state)

    def __len__(self):
        return len(self._nodes)

    def is_empty(self):
        return not self._nodes

    def push(self, node):
        raise NotImplementedError

    def pop(self):
        raise NotImplementedError


class StackFrontier(Frontier):
    """LIFO - dùng cho DFS."""

    def __init__(self):
        super().__init__()
        self._items = []

    def push(self, node):
        self._nodes[node.state] = node
        self._items.append(node)

    def pop(self):
        node = self._items.pop()
        del self._nodes[node.state]
        return node


class QueueFrontier(Frontier):
    """FIFO - dùng cho BFS."""

    def __init__(self):
        super().__init__()
        self._items = deque()

    def push(self, node):
        self._nodes[node.state] = node
        self._items.append(node)

    def pop(self):
        node = self._items.popleft()
        del self._nodes[node.state]
        return node


class PriorityQueueFrontier(Frontier):
    """
    Hàng đợi ưu tiên - dùng cho UCS và A*.
    priority_fn(node) -> khoá so sánh (số hoặc tuple). Khi gặp lại state với
    g rẻ hơn, node mới thay thế node cũ (xoá lười: entry cũ bị bỏ qua khi pop).
    """
    REPLACE_ON_BETTER = True

    def __init__(self, priority_fn):
        super().__init__()
        self._priority_fn = priority_fn
        self._heap = []
        self._counter = itertools.count()   # phá hoà: vào trước ra trước

    def push(self, node):
        self._nodes[node.state] = node
        heapq.heappush(self._heap,
                       (self._priority_fn(node), next(self._counter), node))

    def pop(self):
        while True:
            _, _, node = heapq.heappop(self._heap)
            if self._nodes.get(node.state) is node:   # bỏ entry đã bị thay thế
                del self._nodes[node.state]
                return node


# ---------------------------------------------------------------------------
# 2. Kết quả + thuật toán đồ thị tổng quát
# ---------------------------------------------------------------------------
@dataclass
class SearchResult:
    actions: list = field(default_factory=list)
    found: bool = False
    cost: float = 0
    expanded: int = 0         # số node đã mở rộng
    generated: int = 0        # số node đã sinh ra
    max_frontier: int = 0     # kích thước frontier lớn nhất
    time: float = 0.0         # thời gian tìm kiếm (giây)


def general_graph_search(problem, frontier):
    """
    Vòng lặp lõi: Rút Node -> Kiểm tra đích -> Thêm vào Explored ->
    Sinh node kề -> Đẩy vào Frontier (bỏ qua state đã xét / cập nhật nếu rẻ hơn).
    """
    t0 = time.perf_counter()
    result = SearchResult()

    if not problem.is_solvable():          # chặn sớm, tránh vét cạn vô ích
        result.time = time.perf_counter() - t0
        return result

    frontier.push(Node(problem.get_start_state()))
    explored = set()
    result.generated = 1
    result.max_frontier = 1

    while not frontier.is_empty():
        node = frontier.pop()                                   # (*) bước quyết định

        if problem.is_goal(node.state):
            result.found = True
            result.actions = node.path_actions()
            result.cost = node.g
            break

        explored.add(node.state)
        result.expanded += 1

        for next_state, action, step_cost in problem.get_successors(node.state):
            if next_state in explored:
                continue
            child = Node(next_state, node, action, node.g + step_cost)
            old = frontier.get(next_state)
            if old is None:
                frontier.push(child)
                result.generated += 1
            elif frontier.REPLACE_ON_BETTER and child.g < old.g:
                frontier.push(child)                            # (**) cập nhật g rẻ hơn
                result.generated += 1
        result.max_frontier = max(result.max_frontier, len(frontier))

    result.time = time.perf_counter() - t0
    return result


# ---------------------------------------------------------------------------
# 3. Các thuật toán cụ thể (wrappers)
# ---------------------------------------------------------------------------
def dfs(problem):
    return general_graph_search(problem, StackFrontier())


def bfs(problem):
    return general_graph_search(problem, QueueFrontier())


def ucs(problem):
    return general_graph_search(problem, PriorityQueueFrontier(lambda n: n.g))


def greedy(problem, heuristic="mst"):
    h = get_heuristic(heuristic)
    def priority(node):
        return h(node.state, problem)
    return general_graph_search(problem, PriorityQueueFrontier(priority))


def astar(problem, heuristic="mst"):
    h = get_heuristic(heuristic)
    # f = g + h; hoà thì ưu tiên h nhỏ hơn (node gần đích hơn)
    def priority(node):
        hv = h(node.state, problem)
        return (node.g + hv, hv)
    return general_graph_search(problem, PriorityQueueFrontier(priority))


def problem_adversarial_search(problem, depth=4, heuristic="mst", use_pruning=True):
    """
    Áp dụng tìm kiếm cây đánh giá độ sâu (depth-limited evaluation search)
    lên bài toán SearchProblem (khi không có GameState).
    """
    t0 = time.perf_counter()
    result = SearchResult()
    if not problem.is_solvable():
        result.time = time.perf_counter() - t0
        return result

    h = get_heuristic(heuristic)

    def eval_state(s):
        return -h(s, problem)

    def max_value(state, d, alpha, beta):
        nonlocal expanded
        if problem.is_goal(state) or d == 0:
            return eval_state(state)
        best = float("-inf")
        for next_state, _, step_cost in problem.get_successors(state):
            expanded += 1
            child_alpha = alpha + step_cost if use_pruning and alpha != float("-inf") else float("-inf")
            v = max_value(next_state, d - 1, child_alpha, beta) - step_cost
            best = max(best, v)
            if use_pruning:
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
        return best

    current = problem.get_start_state()
    actions = []
    expanded = 0
    total_cost = 0
    max_steps = 1000
    visited = {current}

    while not problem.is_goal(current) and len(actions) < max_steps:
        successors = problem.get_successors(current)
        if not successors:
            break
        best_val = float("-inf")
        best_act = None
        best_nxt = None
        best_cost = 1
        alpha = float("-inf")
        for nxt, act, cost in successors:
            expanded += 1
            child_alpha = alpha + cost if use_pruning and alpha != float("-inf") else float("-inf")
            v = max_value(nxt, depth - 1, child_alpha, float("inf")) - cost
            if nxt in visited:
                v -= 10  # Phạt tránh chu trình
            if v > best_val:
                best_val = v
                best_act = act
                best_nxt = nxt
                best_cost = cost
            if use_pruning:
                alpha = max(alpha, best_val)
        if best_act is None:
            break
        actions.append(best_act)
        total_cost += best_cost
        current = best_nxt
        visited.add(current)

    result.found = problem.is_goal(current)
    result.actions = actions
    result.cost = total_cost
    result.expanded = expanded
    result.time = time.perf_counter() - t0
    return result


def minimax(target, depth=4, evaluation_fn=None, heuristic="mst", maze_distance=None, agent_index=0):
    """
    Thuật toán Minimax cho đối kháng (GameState) hoặc bài toán tìm kiếm (SearchProblem).
    """
    if hasattr(target, "generate_successor"):
        md = get_maze_distance(target, maze_distance)
        return minimax_search(
            target, depth=depth, evaluation_fn=evaluation_fn, maze_distance=md, agent_index=agent_index
        )
    return problem_adversarial_search(target, depth=depth, heuristic=heuristic, use_pruning=False)


def alphabeta(target, depth=4, evaluation_fn=None, heuristic="mst", maze_distance=None, agent_index=0):
    """
    Thuật toán Alpha-Beta Pruning cho đối kháng (GameState) hoặc bài toán tìm kiếm (SearchProblem).
    """
    if hasattr(target, "generate_successor"):
        md = get_maze_distance(target, maze_distance)
        return alphabeta_search(
            target, depth=depth, evaluation_fn=evaluation_fn, maze_distance=md, agent_index=agent_index
        )
    return problem_adversarial_search(target, depth=depth, heuristic=heuristic, use_pruning=True)


ALGORITHMS = {
    "dfs": dfs,
    "bfs": bfs,
    "ucs": ucs,
    "greedy": greedy,
    "astar": astar,
    "minimax": minimax,
    "alphabeta": alphabeta,
}


def normalize_algo_name(name):
    key = str(name).lower().replace("*", "star").replace("-", "").replace("_", "")
    if key in ("gbfs", "greedy", "greedybestfirst"):
        return "greedy"
    if key in ("mini_max", "minimax"):
        return "minimax"
    if key in ("alpha_beta", "alphabeta"):
        return "alphabeta"
    if key not in ALGORITHMS:
        raise ValueError(f"Thuật toán không hợp lệ: {name!r}. Chọn: {list(ALGORITHMS)}")
    return key


def run_search(algo_name, problem, heuristic=None, depth=4):
    """Điểm vào thống nhất: chạy thuật toán theo tên."""
    key = normalize_algo_name(algo_name)
    if key in ("astar", "greedy"):
        return ALGORITHMS[key](problem, heuristic if heuristic is not None else "mst")
    if key in ("minimax", "alphabeta"):
        return ALGORITHMS[key](problem, depth=depth, heuristic=heuristic if heuristic is not None else "mst")
    return ALGORITHMS[key](problem)