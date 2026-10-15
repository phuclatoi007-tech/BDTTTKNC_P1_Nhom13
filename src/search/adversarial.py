"""
adversarial.py - Thuật toán tìm kiếm đối kháng (Adversarial Search).

Cung cấp:
- MazeDistance: BFS tính khoảng cách mê cung có cache tự động theo bản đồ
- default_evaluation_fn: Hàm đánh giá Safe-Pool & Geodesic Cut-Off:
    + Khi bị bắt (is_lose): Eval(s) = Score(s) (mọi thức ăn đã ăn đều giữ nguyên điểm).
    + Khi còn sống: Eval(s) = Score(s) + V_safe(P, G, F) + M_escape(P, G) + Phi_guide(P, G, F)
      * Pacman (MAX):
        1. Ưu tiên gom sạch toàn bộ thức ăn an toàn trong vòng lặp (loop) và ngoài không gian mở
           vì việc chui sớm vào ngõ cụt sẽ làm Ghost bịt cửa ngõ cụt, khiến V_safe của toàn bộ
           thức ăn bên ngoài sụp đổ về 0 ngay trong cây tìm kiếm 5 bước.
        2. Khi Ghost đã ép sát và không còn thức ăn an toàn bên ngoài (V_safe -> 0), Pacman
           lập tức lao thẳng vào bãi thức ăn lớn ở ngõ cụt (Kamikaze) để vét tối đa điểm thật
           vào Score(s) trước khi bị bắt.
      * Ghost (MIN):
        Cắt đường (cut-off) nhằm tối thiểu hoá V_safe(P, G, F) — tức là chiếm giữ các nút cổ chai
        (chokepoints) để biến nhiều thức ăn giá trị cao nhất từ trạng thái "an toàn cho Pacman"
        thành "bị Ghost phong toả", đồng thời ép góc khi Pacman vào ngõ cụt.
- minimax_search: Thuật toán Minimax đối kháng đa tác tử (Multi-agent Minimax)
- alphabeta_search: Thuật toán Minimax kết hợp cắt tỉa Alpha-Beta + Move Ordering
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
        self.walls = frozenset(state.walls)
        self.width = state.width
        self.height = state.height
        self._maps = {}
        self._pile_memo = {}

    def _bfs(self, source):
        dist = {source: 0}
        queue = deque([source])
        walls = self.walls
        w, h = self.width, self.height
        dirs = tuple(DIRECTIONS.values())
        while queue:
            x, y = queue.popleft()
            d = dist[(x, y)] + 1
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                nxt = (nx, ny)
                if 0 <= nx < w and 0 <= ny < h and nxt not in walls and nxt not in dist:
                    dist[nxt] = d
                    queue.append(nxt)
        return dist

    def distance(self, a, b):
        if a == b:
            return 0
        if b in self._maps:
            return self._maps[b].get(a, float("inf"))
        if a not in self._maps:
            self._maps[a] = self._bfs(a)
        return self._maps[a].get(b, float("inf"))


_MAZE_DISTANCE_CACHE = {}


def get_maze_distance(state, maze_distance=None):
    """Lấy hoặc khởi tạo MazeDistance có cache cho bản đồ hiện tại."""
    if maze_distance is not None:
        return maze_distance
    if not hasattr(state, "walls") or not hasattr(state, "width") or not hasattr(state, "height"):
        return None
    key = (state.width, state.height, frozenset(state.walls))
    md = _MAZE_DISTANCE_CACHE.get(key)
    if md is None:
        if len(_MAZE_DISTANCE_CACHE) > 16:
            _MAZE_DISTANCE_CACHE.clear()
        md = MazeDistance(state)
        _MAZE_DISTANCE_CACHE[key] = md
    return md


def extract_food_items(state):
    """
    Trích xuất danh sách [(toạ_độ, giá_trị_dương), ...] của toàn bộ thức ăn còn lại.
    """
    raw_food = getattr(state, "food", None)
    if not raw_food:
        return []

    if isinstance(raw_food, dict):
        return [(pos, float(val)) for pos, val in raw_food.items() if val > 0]

    value_map = getattr(state, "food_values", None)
    if not isinstance(value_map, dict):
        value_map = None
        for attr in ("food_scores", "food_weights", "food_points", "food_map", "values"):
            candidate = getattr(state, attr, None)
            if isinstance(candidate, dict):
                value_map = candidate
                break

    getter = getattr(state, "get_food_value", None)
    default_val = float(getattr(state, "default_food_value", getattr(state, "food_value", 10.0)))
    if default_val <= 0:
        default_val = 10.0

    items = []
    for f in raw_food:
        if isinstance(f, tuple) and len(f) == 3:
            pos = (f[0], f[1])
            val = float(f[2])
        else:
            pos = f
            if value_map is not None and pos in value_map:
                val = float(value_map[pos])
            elif callable(getter):
                val = float(getter(pos))
            else:
                val = default_val
        if val > 0:
            items.append((pos, val))

    return items


def _get_pile_stats(food_items, md):
    """
    Tính trọng số cụm thức ăn (Pile Weight) W(f) trong bán kính mê cung <= 4:
        W(f) = v(f) + sum_{f' != f, d(f, f') <= 4} v(f') / (1 + 0.35 * d(f, f'))
    """
    food_key = frozenset(food_items)
    if md is not None and food_key in md._pile_memo:
        return md._pile_memo[food_key]

    n = len(food_items)
    pile_weights = [val for _, val in food_items]
    if n > 1:
        for i in range(n):
            fi, vi = food_items[i]
            for j in range(i + 1, n):
                fj, vj = food_items[j]
                if abs(fi[0] - fj[0]) + abs(fi[1] - fj[1]) <= 4:
                    d_ff = md.distance(fi, fj) if md is not None else (abs(fi[0] - fj[0]) + abs(fi[1] - fj[1]))
                    if d_ff <= 4:
                        factor = 0.65 / (1.0 + 0.35 * d_ff)
                        pile_weights[i] += vj * factor
                        pile_weights[j] += vi * factor

    w_max = max(pile_weights) if pile_weights else 1.0
    v_min = min(val for _, val in food_items) if food_items else 10.0
    stats = (pile_weights, w_max, v_min)

    if md is not None:
        if len(md._pile_memo) > 256:
            md._pile_memo.clear()
        md._pile_memo[food_key] = stats
    return stats


def default_evaluation_fn(state, maze_distance=None):
    """
    Hàm đánh giá Safe-Pool & Escape-Mobility cho Pacman (MAX) và Ghost (MIN):

    1. Trạng thái kết thúc (Terminal):
       - is_lose(): trả về đúng float(state.score).
       - is_win() : trả về float(state.score) + 20.0.

    2. Trạng thái còn sống (Non-Terminal):
       Eval(s) = Score(s) + V_safe(P, G, F) + M_escape(P, G) + Phi_guide(P, G, F)

       - V_safe(P, G, F): Tổng giá trị chiết khấu của các viên thức ăn MÀ PACMAN ĐẾN KỊP
         TRƯỚC GHOST và KHÔNG BỊ GHOST CHẶN ĐƯỜNG:
         + Nếu Pacman chui vào ngõ cụt sớm, chỉ sau 2-3 bước trong cây Minimax, Ghost sẽ
           tiến ra đứng ở cửa ngõ cụt. Khi đó với mọi thức ăn bên ngoài vòng lặp (loop),
           d(P, f) = d(P, G) + d(G, f) (slack = 0 và d_G < d_P), làm V_safe của toàn bộ
           bàn cờ bên ngoài sụp về 0! Nhờ vậy Pacman NHÌN THẤY RÕ việc chui vào ngõ cụt sớm
           làm mất sạch mồi bên ngoài, nên Pacman sẽ ở lại vòng lặp (loop) gom sạch mồi
           an toàn trước!
         + Ngược lại, khi toàn bộ mồi an toàn trong loop đã ăn hết (hoặc đã bị Ghost phong toả
           hết khiến V_safe ~ 0), việc lao vào ngõ cụt ăn mồi điểm cao (+10, +20, +30 vào Score)
           trước khi bị bắt sẽ có tổng điểm cao hơn hẳn việc chạy lòng vòng chờ chết!

       - M_escape(P, G): Điểm linh hoạt đường thoát (số hướng đi kề cạnh Pacman có d(nxt, G) >= 2).
         Giúp Pacman ưu tiên đứng ở vòng lặp (2-3 lối thoát) hơn là tự chui vào đáy ngõ cụt (0 lối thoát)
         khi chưa cần thiết.

       - Phi_guide(P, G, F): Gradient dẫn đường mượt tới viên thức ăn gần nhất và giúp Ghost
         tận dụng từng nhịp (tempo) áp sát khoá cửa ngõ cụt.
    """
    score = float(state.score)

    if state.is_win():
        return score + 20.0
    if state.is_lose():
        return score

    food_items = extract_food_items(state)
    if not food_items:
        return score

    md = get_maze_distance(state, maze_distance)
    p_pos = state.pacman_pos
    ghosts = getattr(state, "ghosts_pos", None) or []

    def dist(a, b):
        if md is not None:
            return md.distance(a, b)
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    pile_weights, w_max, v_min = _get_pile_stats(food_items, md)
    ghost_to_pac = [dist(p_pos, gp) for gp in ghosts]

    # 1. Tính độ linh hoạt lối thoát tức thời của Pacman (M_escape)
    # Trong loop mở: Pacman có >= 2 hướng đi an toàn; trong đáy ngõ cụt bị chặn: 0-1 hướng.
    safe_exits = 0
    px, py = p_pos
    walls = state.walls
    w, h = state.width, state.height
    for dx, dy in DIRECTIONS.values():
        nx, ny = px + dx, py + dy
        nxt = (nx, ny)
        if 0 <= nx < w and 0 <= ny < h and nxt not in walls:
            if not ghosts or min(dist(nxt, gp) for gp in ghosts) >= 2:
                safe_exits += 1
    m_escape = 0.08 * v_min * min(safe_exits, 3)

    # 2. Tính V_safe (bể thức ăn an toàn không bị Ghost cắt đường) & Phi_guide
    v_safe_pool = 0.0
    min_dp = float("inf")
    min_safe_dp = float("inf")
    best_pile_pull = 0.0

    cutoff_numer = 0.0
    cutoff_denom = 0.0

    for idx, (f_pos, v_f) in enumerate(food_items):
        dp = dist(p_pos, f_pos)
        if dp == float("inf"):
            continue

        if dp < min_dp:
            min_dp = dp

        w_pile = pile_weights[idx]
        w_norm = w_pile / w_max

        if not ghosts:
            v_safe_pool += 0.30 * v_f * (0.90 ** dp)
            if dp < min_safe_dp:
                min_safe_dp = dp
            pile_pull = w_norm * (0.86 ** dp)
            if pile_pull > best_pile_pull:
                best_pile_pull = pile_pull
            continue

        # Đánh giá khả năng tiếp cận viên thức ăn f_pos trước tất cả các Ghost
        worst_safety = 1.0
        min_access = 1.0
        min_dg = float("inf")

        for g_idx, gp in enumerate(ghosts):
            dg = dist(gp, f_pos)
            if dg == float("inf"):
                continue
            if dg < min_dg:
                min_dg = dg
            dpg = ghost_to_pac[g_idx]

            # slack == 0 nghĩa là Ghost đứng ngay trên đường đi ngắn nhất từ Pacman tới f_pos
            slack = max(0.0, (dpg + dg) - dp)
            lead_pac = dg - dp  # > 0 nếu Pacman gần f_pos hơn Ghost

            # Mức độ an toàn thực sự của viên thức ăn f_pos đối với Pacman:
            # - Nếu Ghost đứng chặn trên đường đi (slack <= 1) và Ghost gần f_pos hơn hoặc bằng Pacman (lead_pac <= 0),
            #   viên thức ăn này ĐÃ BỊ PHONG TOẢ (safety ~ 0).
            # - Nếu Pacman gần hơn Ghost (lead_pac >= 1) và đường đi không bị Ghost đứng chặn đầu,
            #   viên thức ăn này AN TOÀN để Pacman gom (farm).
            if slack == 0 and lead_pac <= 0:
                safety_g = 0.0
            elif slack <= 1 and lead_pac <= -1:
                safety_g = 0.04
            elif lead_pac >= 2:
                safety_g = min(1.0, (0.65 + 0.12 * lead_pac) * (slack / (1.0 + slack)))
            elif lead_pac == 1:
                safety_g = 0.50 * (slack / (1.0 + slack))
            elif lead_pac == 0:
                safety_g = 0.20 * (slack / (1.5 + slack))
            else:
                # Ghost gần f_pos hơn Pacman nhưng chưa đứng thẳng trên đường nối (slack >= 2)
                safety_g = 0.10 / (1.0 - lead_pac)

            if safety_g < worst_safety:
                worst_safety = safety_g

            # Chi phí cắt đường cho Ghost (dùng để dẫn đường Ghost khi chọn nước đi)
            behind = max(0.0, dg - (dp - 1.0))
            c_cut = 2.4 * behind + 1.25 * slack + 0.38 * dpg + 0.14 * dg
            access_g = c_cut / (10.0 + c_cut)
            if access_g < min_access:
                min_access = access_g

        # Đóng góp vào bể thức ăn an toàn V_safe:
        # Hệ số 0.32 < 1.0 đảm bảo việc THỰC SỰ ĂN viên thức ăn (+1.0 * v_f vào Score)
        # luôn lời hơn gấp 3 lần việc chỉ đứng nhìn viên thức ăn đó.
        v_safe_pool += 0.32 * v_f * worst_safety * (0.90 ** dp)

        if worst_safety >= 0.25 and dp < min_safe_dp:
            min_safe_dp = dp

        pile_pull = w_norm * (0.35 + 0.65 * worst_safety) * (0.86 ** dp)
        if pile_pull > best_pile_pull:
            best_pile_pull = pile_pull

        # Trọng số mục tiêu cho Ghost: bỏ qua viên sát miệng Pacman không cứu kịp, tập trung chặn cụm lớn
        if dp + 2 <= min_dg and dp <= 2:
            intercept_weight = 0.02 * (w_norm ** 2)
        elif min_dg <= dp + 3:
            urgency = 1.0 / (1.0 + 0.12 * dp)
            intercept_weight = (w_norm ** 2) * (0.65 + 0.35 * urgency)
        else:
            intercept_weight = 0.25 * (w_norm ** 2)

        cutoff_numer += intercept_weight * min_access
        cutoff_denom += intercept_weight

    if min_dp == float("inf"):
        return score

    # 3. Gradient dẫn đường cho Pacman:
    # Ưu tiên kéo Pacman về viên thức ăn AN TOÀN gần nhất (trong loop);
    # nếu không còn viên nào an toàn (đã bị vây kín), kéo thẳng vào cụm thức ăn gần nhất để Kamikaze!
    if min_safe_dp < float("inf"):
        pac_guide = v_min * (0.22 * (0.86 ** min_safe_dp) + 0.12 * best_pile_pull)
    else:
        pac_guide = v_min * (0.22 * (0.86 ** min_dp) + 0.12 * best_pile_pull)

    # 4. Gradient dẫn đường cắt mặt & ép tempo cho Ghost
    ghost_guide = (v_min * 0.22 * (cutoff_numer / cutoff_denom)) if (ghosts and cutoff_denom > 0) else 0.0

    # Biên độ sống sót cơ bản 0.20 * v_min đảm bảo không bao giờ tự sát khi không ăn thêm được mồi
    survival_base = 0.20 * v_min

    return score + survival_base + v_safe_pool + m_escape + pac_guide + ghost_guide


def get_legal_actions_filtered(state, agent_index):
    """
    Lấy danh sách các nước đi hợp lệ của agent_index,
    loại bỏ 'STOP' trừ khi không còn nước đi nào khác.
    """
    actions = state.get_legal_actions(agent_index)
    moves = [a for a in actions if a != "STOP"]
    return moves if moves else actions


def _order_actions_fast(state, agent_index, actions, md):
    """
    Sắp xếp thứ tự nước đi nhanh O(|actions|) để tăng hiệu quả cắt tỉa Alpha-Beta.
    """
    if len(actions) <= 1 or md is None:
        return actions

    food_items = extract_food_items(state)
    if not food_items:
        return actions

    p_pos = state.pacman_pos
    pile_weights, w_max, _ = _get_pile_stats(food_items, md)

    if agent_index == 0:
        ghosts = getattr(state, "ghosts_pos", None) or []

        def food_attractiveness(i):
            f_pos, _ = food_items[i]
            dp = md.distance(p_pos, f_pos)
            w_norm = pile_weights[i] / w_max
            if ghosts:
                min_dg = min(md.distance(gp, f_pos) for gp in ghosts)
                safe_bonus = 1.5 if dp < min_dg else 0.6
            else:
                safe_bonus = 1.0
            return safe_bonus * w_norm * (0.86 ** dp)

        target_food = max(range(len(food_items)), key=food_attractiveness)
        t_pos = food_items[target_food][0]
        return sorted(
            actions,
            key=lambda a: md.distance(
                (p_pos[0] + DIRECTIONS.get(a, (0, 0))[0], p_pos[1] + DIRECTIONS.get(a, (0, 0))[1]),
                t_pos,
            ),
        )
    else:
        ghosts = getattr(state, "ghosts_pos", None) or []
        g_idx = agent_index - 1
        if g_idx >= len(ghosts):
            return actions
        cur_pos = ghosts[g_idx]

        best_idx = 0
        best_score = -1.0
        for i, (f_pos, _) in enumerate(food_items):
            dp = md.distance(p_pos, f_pos)
            dg = md.distance(cur_pos, f_pos)
            w_norm = pile_weights[i] / w_max
            saveable = 0.02 if (dp + 2 <= dg and dp <= 2) else 1.0
            sc = saveable * (w_norm ** 2) / (1.0 + 0.12 * dp)
            if sc > best_score:
                best_score = sc
                best_idx = i

        target_food = food_items[best_idx][0]
        dp_target = md.distance(p_pos, target_food)

        def ghost_move_priority(a):
            dx, dy = DIRECTIONS.get(a, (0, 0))
            nxt = (cur_pos[0] + dx, cur_pos[1] + dy)
            dg = md.distance(nxt, target_food)
            dpg = md.distance(p_pos, nxt)
            behind = max(0.0, dg - (dp_target - 1.0))
            slack = max(0.0, dpg + dg - dp_target)
            return 2.4 * behind + 1.25 * slack + 0.38 * dpg + 0.14 * dg

        return sorted(actions, key=ghost_move_priority)


def _eval_for_pacman_leaf(eval_fn, s, d, pac_path, visit_counts):
    """
    Đánh giá node lá cho Pacman:
    - Nếu bị bắt (is_lose): phạt nhẹ -0.02 * (d + 1) để khi tất cả phương án đều bị bắt
      với cùng số điểm, Pacman chọn phương án sống lâu nhất.
    - Giới hạn chặt phạt chống lặp <= 0.50 để không bao giờ cản Pacman đi ngược ra khỏi ngõ cụt.
    """
    val = eval_fn(s)
    if s.is_win():
        return val + 0.05 * (d + 1)
    if s.is_lose():
        return val - 0.02 * (d + 1)

    state_key = (s.pacman_pos, len(s.food))
    penalty = 0.0
    if pac_path and state_key in pac_path:
        penalty += 0.08
    if visit_counts:
        repeats = visit_counts.get(state_key, 0)
        if repeats > 0:
            penalty += min(0.42, 0.06 * repeats)
    return val - penalty


def _eval_for_ghost_leaf(eval_fn, s, d, ghost_idx, ghost_path, visit_counts):
    """
    Đánh giá node lá cho Ghost (MIN):
    - Thưởng âm khi bắt được Pacman sớm (-0.05 * (d + 1)).
    - Phạt dương nếu Ghost đi lặp lại ô vừa đứng để chống nhấp nhả mất tempo.
    """
    val = eval_fn(s)
    if s.is_win():
        return val + 0.05 * (d + 1)
    if s.is_lose():
        return val - 0.05 * (d + 1)

    ghosts = getattr(s, "ghosts_pos", None) or []
    g_i = ghost_idx - 1
    if 0 <= g_i < len(ghosts):
        g_key = (ghosts[g_i], len(s.food))
        penalty = 0.0
        if ghost_path and g_key in ghost_path:
            penalty += 0.12
        if visit_counts:
            repeats = visit_counts.get(g_key, 0)
            if repeats > 0:
                penalty += min(0.50, 0.08 * repeats)
        val += penalty
    return val


def minimax_search(
    state,
    depth=5,
    evaluation_fn=None,
    maze_distance=None,
    agent_index=0,
    visit_counts=None,
):
    """
    Thuật toán Minimax thuần cho đối kháng nhiều tác tử (Multi-agent Minimax):
    - Pacman (agent 0) là MAX.
    - Ghost (agent 1..N) là MIN.
    """
    if len(getattr(state, "ghosts_pos", ())) >= 2 and depth > 4:
        depth = 4

    t0 = time.perf_counter()
    md = get_maze_distance(state, maze_distance)
    eval_fn = evaluation_fn or (lambda s: default_evaluation_fn(s, md))
    expanded = 0
    is_pacman_root = (agent_index == 0)

    def leaf_val(s, d, trace_path):
        if is_pacman_root:
            return _eval_for_pacman_leaf(eval_fn, s, d, trace_path, visit_counts)
        return _eval_for_ghost_leaf(eval_fn, s, d, agent_index, trace_path, visit_counts)

    def min_value(s, ghost_idx, d, trace_path):
        nonlocal expanded
        if s.is_win() or s.is_lose() or d == 0:
            return leaf_val(s, d, trace_path)

        actions = get_legal_actions_filtered(s, ghost_idx)
        if not actions:
            return leaf_val(s, d, trace_path)

        num_agents = 1 + len(s.ghosts_pos)
        is_last_ghost = (ghost_idx == num_agents - 1)
        next_ghost = ghost_idx + 1
        if not is_pacman_root and ghost_idx == agent_index:
            new_trace = trace_path + ((s.ghosts_pos[ghost_idx - 1], len(s.food)),)
        else:
            new_trace = trace_path

        v = float("inf")
        for action in actions:
            expanded += 1
            successor = s.generate_successor(ghost_idx, action)
            if is_last_ghost:
                v = min(v, max_value(successor, d - 1, new_trace))
            else:
                v = min(v, min_value(successor, next_ghost, d, new_trace))
        return v

    def max_value(s, d, trace_path):
        nonlocal expanded
        if s.is_win() or s.is_lose() or d == 0:
            return leaf_val(s, d, trace_path)

        actions = get_legal_actions_filtered(s, 0)
        if not actions:
            return leaf_val(s, d, trace_path)

        num_agents = 1 + len(s.ghosts_pos)
        has_ghosts = (num_agents > 1)
        new_trace = trace_path + ((s.pacman_pos, len(s.food)),) if is_pacman_root else trace_path

        v = float("-inf")
        for action in actions:
            expanded += 1
            successor = s.generate_successor(0, action)
            if has_ghosts:
                v = max(v, min_value(successor, 1, d, new_trace))
            else:
                v = max(v, max_value(successor, d - 1, new_trace))
        return v

    actions = get_legal_actions_filtered(state, agent_index)
    if not actions:
        return AdversarialSearchResult(
            action="STOP", value=eval_fn(state), expanded_nodes=0, search_time=time.perf_counter() - t0
        )

    num_agents = 1 + len(state.ghosts_pos)
    has_ghosts = (num_agents > 1)
    if is_pacman_root:
        root_trace = ((state.pacman_pos, len(state.food)),)
    else:
        root_trace = ((state.ghosts_pos[agent_index - 1], len(state.food)),)

    if agent_index == 0:
        best_action = actions[0]
        best_value = float("-inf")
        best_key = None

        for action in actions:
            expanded += 1
            child = state.generate_successor(0, action)
            if has_ghosts:
                v = min_value(child, 1, depth, root_trace)
            else:
                v = max_value(child, depth - 1, root_trace)

            imm = _eval_for_pacman_leaf(eval_fn, child, depth, root_trace, visit_counts)
            key = (round(v, 7), imm)
            if best_key is None or key > best_key:
                best_key = key
                best_value = v
                best_action = action
    else:
        is_last_ghost = (agent_index == num_agents - 1)
        next_ghost = agent_index + 1
        best_action = actions[0]
        best_value = float("inf")
        best_key = None

        for action in actions:
            expanded += 1
            child = state.generate_successor(agent_index, action)
            if is_last_ghost:
                v = max_value(child, depth - 1, root_trace)
            else:
                v = min_value(child, next_ghost, depth, root_trace)

            imm = _eval_for_ghost_leaf(eval_fn, child, depth, agent_index, root_trace, visit_counts)
            key = (round(v, 7), imm)
            if best_key is None or key < best_key:
                best_key = key
                best_value = v
                best_action = action

    total_time = time.perf_counter() - t0
    return AdversarialSearchResult(
        action=best_action, value=best_value, expanded_nodes=expanded, search_time=total_time
    )


def alphabeta_search(
    state,
    depth=5,
    evaluation_fn=None,
    maze_distance=None,
    agent_index=0,
    visit_counts=None,
):
    """
    Thuật toán tìm kiếm đối kháng Minimax kết hợp cắt tỉa Alpha-Beta (Alpha-Beta Pruning)
    và sắp xếp thứ tự nước đi (Move Ordering).
    """
    if len(getattr(state, "ghosts_pos", ())) >= 2 and depth > 4:
        depth = 4

    t0 = time.perf_counter()
    md = get_maze_distance(state, maze_distance)
    eval_fn = evaluation_fn or (lambda s: default_evaluation_fn(s, md))
    expanded = 0
    is_pacman_root = (agent_index == 0)

    def leaf_val(s, d, trace_path):
        if is_pacman_root:
            return _eval_for_pacman_leaf(eval_fn, s, d, trace_path, visit_counts)
        return _eval_for_ghost_leaf(eval_fn, s, d, agent_index, trace_path, visit_counts)

    def min_value(s, ghost_idx, d, alpha, beta, trace_path):
        nonlocal expanded
        if s.is_win() or s.is_lose() or d == 0:
            return leaf_val(s, d, trace_path)

        actions = get_legal_actions_filtered(s, ghost_idx)
        if not actions:
            return leaf_val(s, d, trace_path)
        if d >= 2:
            actions = _order_actions_fast(s, ghost_idx, actions, md)

        num_agents = 1 + len(s.ghosts_pos)
        is_last_ghost = (ghost_idx == num_agents - 1)
        next_ghost = ghost_idx + 1
        if not is_pacman_root and ghost_idx == agent_index:
            new_trace = trace_path + ((s.ghosts_pos[ghost_idx - 1], len(s.food)),)
        else:
            new_trace = trace_path

        v = float("inf")
        for action in actions:
            expanded += 1
            successor = s.generate_successor(ghost_idx, action)
            if is_last_ghost:
                v = min(v, max_value(successor, d - 1, alpha, beta, new_trace))
            else:
                v = min(v, min_value(successor, next_ghost, d, alpha, beta, new_trace))
            beta = min(beta, v)
            if beta <= alpha:
                break
        return v

    def max_value(s, d, alpha, beta, trace_path):
        nonlocal expanded
        if s.is_win() or s.is_lose() or d == 0:
            return leaf_val(s, d, trace_path)

        actions = get_legal_actions_filtered(s, 0)
        if not actions:
            return leaf_val(s, d, trace_path)
        if d >= 2:
            actions = _order_actions_fast(s, 0, actions, md)

        num_agents = 1 + len(s.ghosts_pos)
        has_ghosts = (num_agents > 1)
        new_trace = trace_path + ((s.pacman_pos, len(s.food)),) if is_pacman_root else trace_path

        v = float("-inf")
        for action in actions:
            expanded += 1
            successor = s.generate_successor(0, action)
            if has_ghosts:
                v = max(v, min_value(successor, 1, d, alpha, beta, new_trace))
            else:
                v = max(v, max_value(successor, d - 1, alpha, beta, new_trace))
            alpha = max(alpha, v)
            if beta <= alpha:
                break
        return v

    actions = get_legal_actions_filtered(state, agent_index)
    if not actions:
        return AdversarialSearchResult(
            action="STOP", value=eval_fn(state), expanded_nodes=0, search_time=time.perf_counter() - t0
        )
    actions = _order_actions_fast(state, agent_index, actions, md)

    num_agents = 1 + len(state.ghosts_pos)
    has_ghosts = (num_agents > 1)
    if is_pacman_root:
        root_trace = ((state.pacman_pos, len(state.food)),)
    else:
        root_trace = ((state.ghosts_pos[agent_index - 1], len(state.food)),)

    alpha = float("-inf")
    beta = float("inf")

    if agent_index == 0:
        best_action = actions[0]
        best_value = float("-inf")
        best_key = None

        for action in actions:
            expanded += 1
            child = state.generate_successor(0, action)
            if has_ghosts:
                v = min_value(child, 1, depth, alpha, beta, root_trace)
            else:
                v = max_value(child, depth - 1, alpha, beta, root_trace)

            imm = _eval_for_pacman_leaf(eval_fn, child, depth, root_trace, visit_counts)
            key = (round(v, 7), imm)
            if best_key is None or key > best_key:
                best_key = key
                best_value = v
                best_action = action
            alpha = max(alpha, best_value)
    else:
        is_last_ghost = (agent_index == num_agents - 1)
        next_ghost = agent_index + 1
        best_action = actions[0]
        best_value = float("inf")
        best_key = None

        for action in actions:
            expanded += 1
            child = state.generate_successor(agent_index, action)
            if is_last_ghost:
                v = max_value(child, depth - 1, alpha, beta, root_trace)
            else:
                v = min_value(child, next_ghost, depth, alpha, beta, root_trace)

            imm = _eval_for_ghost_leaf(eval_fn, child, depth, agent_index, root_trace, visit_counts)
            key = (round(v, 7), imm)
            if best_key is None or key < best_key:
                best_key = key
                best_value = v
                best_action = action
            beta = min(beta, best_value)

    total_time = time.perf_counter() - t0
    return AdversarialSearchResult(
        action=best_action, value=best_value, expanded_nodes=expanded, search_time=total_time
    )


def ghost_minimax_search(
    state, ghost_index=1, depth=3, evaluation_fn=None, maze_distance=None, visit_counts=None
):
    """Hàm tiện ích chạy Minimax trực tiếp cho Ghost thứ `ghost_index` (MIN)."""
    return minimax_search(
        state,
        depth=depth,
        evaluation_fn=evaluation_fn,
        maze_distance=maze_distance,
        agent_index=ghost_index,
        visit_counts=visit_counts,
    )


def ghost_alphabeta_search(
    state, ghost_index=1, depth=3, evaluation_fn=None, maze_distance=None, visit_counts=None
):
    """Hàm tiện ích chạy Alpha-Beta trực tiếp cho Ghost thứ `ghost_index` (MIN)."""
    return alphabeta_search(
        state,
        depth=depth,
        evaluation_fn=evaluation_fn,
        maze_distance=maze_distance,
        agent_index=ghost_index,
        visit_counts=visit_counts,
    )