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


def astar(problem, heuristic="mst"):
    h = get_heuristic(heuristic)
    # f = g + h; hoà thì ưu tiên h nhỏ hơn (node gần đích hơn)
    def priority(node):
        hv = h(node.state, problem)
        return (node.g + hv, hv)
    return general_graph_search(problem, PriorityQueueFrontier(priority))


ALGORITHMS = {"dfs": dfs, "bfs": bfs, "ucs": ucs, "astar": astar}


def normalize_algo_name(name):
    key = str(name).lower().replace("*", "star").replace("-", "").replace("_", "")
    if key not in ALGORITHMS:
        raise ValueError(f"Thuật toán không hợp lệ: {name!r}. Chọn: {list(ALGORITHMS)}")
    return key


def run_search(algo_name, problem, heuristic=None):
    """Điểm vào thống nhất: chạy thuật toán theo tên."""
    key = normalize_algo_name(algo_name)
    if key == "astar":
        return astar(problem, heuristic if heuristic is not None else "mst")
    return ALGORITHMS[key](problem)
