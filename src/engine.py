class GameState:
    """Biểu diễn trạng thái vật lý của bàn chơi tại một thời điểm."""

    def __init__(self):
        # Khởi tạo kích thước và các tập hợp thực thể trên bản đồ
        self.width = 0
        self.height = 0
        self.walls = set()        # Tập hợp tọa độ (x, y) của tường
        self.pacman_pos = None    # Tọa độ (x, y) của Pacman
        self.ghosts_pos = []      # Danh sách tọa độ (x, y) của các Ghost
        self.food = set()         # Tập hợp tọa độ (x, y) của thức ăn (hoặc dict {(x, y): value})
        self.food_values = {}     # Dict {(x, y): điểm_thức_ăn > 0} (mặc định 10 cho mỗi viên '.')
        self.default_food_value = 10
        self.score = 0

        # Cờ trạng thái kết thúc
        self.is_game_over = False
        self.win = False
        self.lose = False
        # Lý do kết thúc: "win" | "lose" | "no_solution" | "plan_exhausted"
        #                 | "max_turns" | "quit" | None (đang chơi)
        self.end_reason = None

    def get_food_value(self, pos):
        """Trả về giá trị điểm dương của viên thức ăn tại toạ độ pos."""
        if isinstance(self.food, dict) and pos in self.food:
            return self.food[pos]
        if self.food_values and pos in self.food_values:
            return self.food_values[pos]
        return self.default_food_value

    def copy(self):
        """
        Bản sao nhanh (thay cho copy.deepcopy, chậm ~10 lần khi Minimax sinh hàng
        trăm nghìn trạng thái). Chỉ sao chép các trường thay đổi theo thời gian
        (food, ghosts_pos); walls không bao giờ bị sửa nên được dùng chung.
        """
        new = GameState.__new__(GameState)
        new.__dict__.update(self.__dict__)
        new.food = dict(self.food) if isinstance(self.food, dict) else set(self.food)
        if self.food_values:
            new.food_values = dict(self.food_values)
        new.ghosts_pos = list(self.ghosts_pos)
        return new

    def get_legal_actions(self, agent_index):
        """Trả về các bước đi hợp lệ (không đâm tường) cho Pacman hoặc Ghost."""
        if self.is_win() or self.is_lose():
            return []

        # Xác định vị trí hiện tại của tác tử (agent) đang xét
        if agent_index == 0:  # Pacman luôn có index = 0
            x, y = self.pacman_pos
        else:                 # Ghost có index > 0
            ghost_idx = agent_index - 1
            if ghost_idx >= len(self.ghosts_pos):
                return []
            x, y = self.ghosts_pos[ghost_idx]

        legal_actions = []
        # Các hướng di chuyển có thể (dx, dy)
        directions = {
            'UP': (0, -1),
            'DOWN': (0, 1),
            'LEFT': (-1, 0),
            'RIGHT': (1, 0),
            'STOP': (0, 0)
        }

        for action, (dx, dy) in directions.items():
            next_x, next_y = x + dx, y + dy
            # Nếu vị trí tiếp theo nằm trong bản đồ và không phải là tường
            if (0 <= next_x < self.width and 0 <= next_y < self.height
                    and (next_x, next_y) not in self.walls):
                legal_actions.append(action)

        return legal_actions

    def generate_successor(self, agent_index, action):
        """Trả về một GameState mới sau khi thực hiện hành động."""
        # TẠO BẢN SAO ĐỘC LẬP: cực kỳ quan trọng cho Minimax Tree Search, tránh làm
        # hỏng trạng thái ván thật khi AI đang "tưởng tượng" tương lai.
        successor = self.copy()

        if action == 'STOP' or action not in successor.get_legal_actions(agent_index):
            return successor

        directions = {
            'UP': (0, -1),
            'DOWN': (0, 1),
            'LEFT': (-1, 0),
            'RIGHT': (1, 0)
        }
        dx, dy = directions.get(action, (0, 0))

        if agent_index == 0:  # Lượt di chuyển của Pacman
            curr_x, curr_y = successor.pacman_pos
            next_pos = (curr_x + dx, curr_y + dy)
            successor.pacman_pos = next_pos

            # Cập nhật điểm và thức ăn (mọi thức ăn ăn được trước khi bị bắt đều tính điểm)
            if next_pos in successor.food:
                food_val = successor.get_food_value(next_pos)
                if isinstance(successor.food, dict):
                    del successor.food[next_pos]
                else:
                    successor.food.remove(next_pos)
                if successor.food_values and next_pos in successor.food_values:
                    del successor.food_values[next_pos]
                successor.score += food_val

        else:  # Lượt di chuyển của Ghost
            ghost_idx = agent_index - 1
            curr_x, curr_y = successor.ghosts_pos[ghost_idx]
            successor.ghosts_pos[ghost_idx] = (curr_x + dx, curr_y + dy)

        # Kiểm tra trạng thái game (thắng/thua) sau mỗi lần cập nhật
        successor._update_game_status()

        return successor

    def _update_game_status(self):
        """Kiểm tra và cập nhật trạng thái thắng/thua."""
        # Thua: Pacman chạm vào bất kỳ Ghost nào
        if self.pacman_pos in self.ghosts_pos:
            self.lose = True
            self.is_game_over = True
            self.end_reason = "lose"
        # Thắng: Đã ăn toàn bộ thức ăn
        elif len(self.food) == 0:
            self.win = True
            self.is_game_over = True
            self.end_reason = "win"

    def is_win(self):
        """Kiểm tra trạng thái kết thúc (thắng)."""
        return self.win

    def is_lose(self):
        """Kiểm tra trạng thái kết thúc (thua)."""
        return self.lose

    def end_game(self, reason):
        """Kết thúc ván chơi không do thắng/thua (vô nghiệm, hết lượt, thoát...)."""
        self.is_game_over = True
        self.end_reason = reason


class GameLoop:
    """Quản lý luồng chạy của game."""

    # Thông điệp kết thúc theo lý do
    END_MESSAGES = {
        "win": "CHIẾN THẮNG! Pacman đã hoàn thành nhiệm vụ!",
        "lose": "GAME OVER! Pacman đã bị tiêu diệt!",
        "no_solution": "GAME OVER! Bản đồ KHÔNG CÓ LỜI GIẢI "
                       "(Pacman không thể ăn hết thức ăn).",
        "plan_exhausted": "GAME OVER! Agent đã hết kế hoạch nhưng chưa thắng.",
        "max_turns": "HẾT LƯỢT! Đã đạt số lượt tối đa mà chưa phân thắng bại.",
        "quit": "Đã dừng trò chơi theo yêu cầu của người chơi.",
    }

    def __init__(self, map_file, agents, ui, max_turns=None, ghost_factory=None):
        """
        Khởi tạo GameLoop.
        - map_file: Đường dẫn tới file map txt
        - agents: Danh sách tác tử (Index 0 luôn là Pacman, phần còn lại là Ghosts)
        - ui: Giao diện người dùng (CLI_UI hoặc GUI_UI)
        - max_turns: số vòng tối đa (None = không giới hạn). Cần cho chế độ
          adversarial để tránh Pacman và Ghost đuổi nhau vô tận.
        - ghost_factory: hàm index -> Agent; nếu có, tự tạo 1 agent cho MỖI Ghost
          trong map (index 1..N) và nối vào sau danh sách agents.
        """
        self.map_file = map_file
        self.initial_agents = list(agents)
        self.ui = ui
        self.max_turns = max_turns
        self.ghost_factory = ghost_factory
        self.reset()

    def reset(self):
        """Khởi động lại toàn bộ trạng thái game và các tác tử."""
        self.state = GameState()
        self._load_map(self.map_file)
        self.agents = []
        for a in self.initial_agents:
            if hasattr(a, "reset"):
                a.reset()
            self.agents.append(a)
        if self.ghost_factory is not None:
            self.agents.extend([self.ghost_factory(i) for i in
                                range(1, len(self.state.ghosts_pos) + 1)])
        if hasattr(self.ui, "turn"):
            self.ui.turn = 0
        if hasattr(self.ui, "restart_requested"):
            self.ui.restart_requested = False

    def _load_map(self, map_file):
        """Parse file text để khởi tạo tọa độ vật lý cho GameState."""
        try:
            with open(map_file, 'r') as f:
                lines = [line.rstrip("\r\n") for line in f.readlines()]

            self.state.height = len(lines)
            self.state.width = max((len(l) for l in lines), default=0)

            for y, line in enumerate(lines):
                for x, char in enumerate(line):
                    if char == '#':
                        self.state.walls.add((x, y))
                    elif char == 'P':
                        self.state.pacman_pos = (x, y)
                    elif char == 'G':
                        self.state.ghosts_pos.append((x, y))
                    elif char == '.':
                        self.state.food.add((x, y))
                        self.state.food_values[(x, y)] = 10
                    elif char in ('o', 'O'):
                        self.state.food.add((x, y))
                        self.state.food_values[(x, y)] = 50
                    elif char.isdigit() and int(char) > 0:
                        self.state.food.add((x, y))
                        self.state.food_values[(x, y)] = int(char) * 10
        except FileNotFoundError:
            print(f"[Error] Không tìm thấy file map: {map_file}")
            exit(1)

        if self.state.pacman_pos is None:
            print(f"[Error] Map '{map_file}' không có vị trí Pacman ('P').")
            exit(1)
        # Map không có thức ăn thì thắng ngay (tránh vòng lặp vô nghĩa)
        self.state._update_game_status()

    def _should_stop(self):
        return self.state.is_win() or self.state.is_lose() or self.state.is_game_over

    def run(self):
        """Vòng lặp chính của trò chơi."""
        self.ui.initialize()

        while True:
            # 1. Khởi tạo và vẽ frame đầu tiên
            self.ui.render(self.state, is_pacman_move=False)

            # 2. Vòng lặp game diễn ra cho đến khi kết thúc (thắng/thua/vô nghiệm/...)
            turn = 0
            while not self._should_stop():
                if getattr(self.ui, "restart_requested", False):
                    break
                if self.max_turns is not None and turn >= self.max_turns:
                    self.state.end_game("max_turns")
                    break
                turn += 1

                for agent_index, agent in enumerate(self.agents):
                    # Thoát vòng lặp tác tử nếu game đã kết thúc ở lượt đi trước đó hoặc restart
                    if self._should_stop() or getattr(self.ui, "restart_requested", False):
                        break

                    # a. Lấy action từ Agent tương ứng
                    action = agent.get_action(self.state)

                    # a'. Agent báo "bế tắc" (vô nghiệm / hết kế hoạch) -> dừng game,
                    #     KHÔNG tiếp tục vòng lặp với action STOP vô hạn.
                    reason = getattr(agent, "stuck_reason", None)
                    if agent_index == 0 and reason:
                        self.state.end_game(reason)
                        break

                    # b. Cập nhật GameState mới
                    self.state = self.state.generate_successor(agent_index, action)

                    # c. Vẽ UI
                    self.ui.render(self.state, is_pacman_move=(agent_index == 0))

                    # d. Người chơi yêu cầu thoát hoặc restart
                    if getattr(self.ui, "quit_requested", False) or getattr(self.ui, "restart_requested", False):
                        break

                if getattr(self.ui, "quit_requested", False):
                    self.state.end_game("quit")
                    break

            if getattr(self.ui, "restart_requested", False):
                self.reset()
                continue

            break

        # 3. Kết thúc trò chơi và in kết quả
        print("-" * 30)
        print(self.END_MESSAGES.get(self.state.end_reason, "Trò chơi kết thúc."))
        print(f"Điểm số cuối cùng: {self.state.score}")
        print("-" * 30)