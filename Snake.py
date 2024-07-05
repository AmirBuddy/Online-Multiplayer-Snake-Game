class Snake:
    def __init__(self, player_id, initial_position):
        self.player_id = player_id
        self.body = [initial_position]
        self.direction = (0, 1)
        self.grow_length = 0
        self.is_alive = True

    def set_direction(self, direction):
        if (self.direction[0] + direction[0], self.direction[1] + direction[1]) != (0, 0):
            self.direction = direction

    def move(self):
        if not self.is_alive:
            return
        new_head = (self.body[0][0] + self.direction[0], self.body[0][1] + self.direction[1])
        self.body.insert(0, new_head)

    def grow(self, length=1):
        self.grow_length += length

    def check_collision(self):
        head = self.body[0]
        if head in self.body[1:]:
            self.is_alive = False
        return not self.is_alive

    def get_positions(self):
        return self.body
