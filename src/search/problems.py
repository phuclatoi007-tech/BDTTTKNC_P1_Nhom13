"""
problems.py - Module định nghĩa bài toán tìm kiếm (Unified Problem Formulation).

Chỉ có MỘT mô hình duy nhất cho mọi trường hợp (1 hay N thức ăn):
    State       = (vị_trí_pacman, frozenset(thức_ăn_còn_lại))
    Start state = (vị_trí_ban_đầu, toàn_bộ_thức_ăn)
    Goal test   = tập thức ăn còn lại rỗng
    Transition  = di chuyển 1 ô; nếu ô mới có thức ăn thì loại khỏi tập

Module này KHÔNG phụ thuộc vào GameState của engine: chỉ làm việc với các
tuple toạ độ đơn giản. SearchAgent đóng vai trò "thông dịch viên".

Kèm theo là bộ tiền xử lý APSP (Maze Distance Cache): chạy BFS lặp lại một lần
duy nhất lúc khởi tạo để tra cứu khoảng cách mê cung O(1) cho Heuristic.
"""
import time
from collections import deque

INF = float("inf")

# Tên hành động trùng khớp với src/engine.py
DIRECTIONS = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0),
}


class SearchProblem:
    """Giao diện chung của một bài toán tìm kiếm P = <S, s0, A, T, G, C>."""

    def get_start_state(self):
        raise NotImplementedError

    def is_goal(self, state):
        raise NotImplementedError

    def get_successors(self, state):
        """Trả về danh sách (state_mới, action, step_cost)."""
        raise NotImplementedError

    def is_solvable(self):
        """Kiểm tra nhanh điều kiện cần để tồn tại lời giải."""
        return True


class MazeDistanceCache:
    """
    Giải bài toán APSP trên các "điểm quan tâm" (vị trí đầu + mọi thức ăn)
    bằng Repeated BFS. Với mỗi điểm quan tâm p ta lưu BFS-map p -> mọi ô,
    nên khoảng cách giữa một điểm quan tâm và BẤT KỲ ô nào đều tra O(1).
    (Lưới vô hướng, chi phí đơn vị => khoảng cách đối xứng.)
    """

    def __init__(self, is_free, sources):
        self._is_free = is_free
        self._maps = {}
        for src in sources:
            if src not in self._maps:
                self._maps[src] = self._bfs(src)

    def _bfs(self, source):
        dist = {source: 0}
        queue = deque([source])
        while queue:
            x, y = queue.popleft()
            d = dist[(x, y)] + 1
            for dx, dy in DIRECTIONS.values():
                nxt = (x + dx, y + dy)
                if nxt not in dist and self._is_free(nxt):
                    dist[nxt] = d
                    queue.append(nxt)
        return dist

    def distance(self, a, b):
        """Khoảng cách (số bước) ngắn nhất a -> b; INF nếu không tới được.
        Ít nhất một trong hai điểm phải là điểm quan tâm."""
        if a in self._maps:
            return self._maps[a].get(b, INF)
        if b in self._maps:
            return self._maps[b].get(a, INF)
        raise KeyError(f"Không có BFS-map cho {a} và {b}")


class MultiFoodSearchProblem(SearchProblem):
    """
    Bài toán ăn toàn bộ thức ăn (multi-goal / TSP trên mê cung).

    Tham số:
        walls, width, height : bản đồ (ô ngoài biên coi như tường)
        start_pos            : vị trí ban đầu của Pacman
        food                 : iterable các toạ độ thức ăn
        cost_fn              : (pos, action, new_pos) -> chi phí >= 0 (mặc định 1)
        min_step_cost        : cận dưới của chi phí 1 bước, dùng để giữ heuristic
                               admissible khi cost_fn khác 1 (mặc định 1)
    """

    def __init__(self, walls, width, height, start_pos, food,
                 cost_fn=None, min_step_cost=1):
        self.walls = frozenset(walls)
        self.width = width
        self.height = height
        self.start_pos = start_pos
        self.initial_food = frozenset(food)
        self.cost_fn = cost_fn
        self.min_step_cost = min_step_cost if cost_fn else 1

        # Bộ nhớ đệm riêng cho heuristic (vd: MST theo từng tập thức ăn)
        self.heuristic_memo = {}

        t0 = time.perf_counter()
        self.distance_cache = MazeDistanceCache(
            self._is_free, [start_pos, *self.initial_food])
        self.preprocess_time = time.perf_counter() - t0

        self._solvable = all(
            self.distance_cache.distance(start_pos, f) != INF
            for f in self.initial_food)

    # ---- tiện ích lưới ----------------------------------------------------
    def _is_free(self, pos):
        x, y = pos
        return (0 <= x < self.width and 0 <= y < self.height
                and pos not in self.walls)

    # ---- mô hình bài toán -------------------------------------------------
    def get_start_state(self):
        return (self.start_pos, self.initial_food)

    def is_goal(self, state):
        return len(state[1]) == 0

    def is_solvable(self):
        return self._solvable

    def get_successors(self, state):
        (x, y), foods = state
        successors = []
        for action, (dx, dy) in DIRECTIONS.items():
            nxt = (x + dx, y + dy)
            if not self._is_free(nxt):
                continue
            new_foods = foods - {nxt} if nxt in foods else foods
            cost = self.cost_fn((x, y), action, nxt) if self.cost_fn else 1
            successors.append(((nxt, new_foods), action, cost))
        return successors
