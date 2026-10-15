"""
heuristics.py - Bộ tính toán Heuristic h(state, problem).

Mọi heuristic có chữ ký  h(state, problem) -> số >= 0  để A* gọi thống nhất.
"""
from src.search.problems import INF


def null_heuristic(state, problem):
    """h = 0: ép A* hoạt động như UCS."""
    return 0


def _mst_cost(foods, problem):
    """
    Trọng số cây khung nhỏ nhất (Prim, O(k^2)) trên đồ thị đầy đủ các thức ăn,
    cạnh = khoảng cách mê cung lấy từ Cache. Kết quả được nhớ theo tập thức ăn.
    """
    memo = problem.heuristic_memo.setdefault("mst", {})
    if foods in memo:
        return memo[foods]

    dist = problem.distance_cache.distance
    nodes = list(foods)
    total = 0
    if len(nodes) > 1:
        best = {n: dist(nodes[0], n) for n in nodes[1:]}
        while best:
            nxt = min(best, key=best.get)
            cost = best.pop(nxt)
            if cost == INF:
                memo[foods] = INF
                return INF
            total += cost
            for n in best:
                d = dist(nxt, n)
                if d < best[n]:
                    best[n] = d
    memo[foods] = total
    return total


def mst_heuristic(state, problem):
    """
    h(n) = (khoảng cách tới thức ăn gần nhất) + MST(thức ăn còn lại).

    Admissible: mọi đường đi ăn hết thức ăn phải tới thức ăn đầu tiên (>= d_min),
    rồi nối tất cả thức ăn còn lại (>= MST). Consistent: ăn 1 thức ăn hay đi 1 ô
    đều làm h giảm không quá chi phí bước đi, nên A* + Explored Set vẫn tối ưu.
    """
    pos, foods = state
    if not foods:
        return 0
    dist = problem.distance_cache.distance
    d_min = min(dist(f, pos) for f in foods)
    if d_min == INF:
        return INF
    mst = _mst_cost(foods, problem)
    if mst == INF:
        return INF
    return (d_min + mst) * problem.min_step_cost


def theory_mst_heuristic(state, problem):
    """
    h(n) = MST({pos} U foods).
    Cài đặt chuẩn lý thuyết: Gộp chung vị trí Pacman và thức ăn thành 1 đồ thị.
    Không dùng cache vì 'pos' thay đổi liên tục ở mỗi bước đi.
    """
    pos, foods = state
    if not foods:
        return 0

    dist = problem.distance_cache.distance
    nodes = [pos] + list(foods)  # G_A = {p} U F

    total = 0
    # Khởi tạo khoảng cách từ 'pos' đến tất cả các đỉnh 'foods'
    best = {n: dist(pos, n) for n in nodes[1:]}

    # Thuật toán Prim tối ưu bằng Dictionary
    while best:
        nxt = min(best, key=best.get)
        cost = best.pop(nxt)

        if cost == INF:
            return INF  # Cắt tỉa ngay nếu có thức ăn không thể tới được

        total += cost
        # Cập nhật lại khoảng cách ngắn nhất cho các đỉnh chưa thăm
        for n in best:
            d = dist(nxt, n)
            if d < best[n]:
                best[n] = d

    return total * problem.min_step_cost


def farthest_food_heuristic(state, problem):
    """h = khoảng cách mê cung tới thức ăn xa nhất (admissible, yếu hơn MST)."""
    pos, foods = state
    if not foods:
        return 0
    dist = problem.distance_cache.distance
    return max(dist(f, pos) for f in foods) * problem.min_step_cost


HEURISTICS = {
    "null": null_heuristic,
    "mst": mst_heuristic,               # Code cũ có cache của đồng đội
    "theory_mst": theory_mst_heuristic, # Code mới chuẩn lý thuyết của bạn
    "maze": farthest_food_heuristic,
}


def get_heuristic(h):
    """Nhận tên (str), hàm (callable) hoặc None; trả về hàm heuristic."""
    if h is None:
        return null_heuristic
    if callable(h):
        return h
    key = str(h).lower()
    if key not in HEURISTICS:
        raise ValueError(f"Heuristic không hợp lệ: {h!r}. Chọn: {list(HEURISTICS)}")
    return HEURISTICS[key]