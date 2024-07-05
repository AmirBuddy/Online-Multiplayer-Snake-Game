import random
import Snake

class Game:
    def __init__(self, height=24, width=40, winner_length=15):
        self.EMPTY_PLACE = ' '
        self.BORDER = '#'
        self.FRUIT = '*'
        self.HEIGHT = height
        self.WIDTH = width
        self.WINNER_LENGTH = winner_length
        self.snakes = {}
        self.game_map = [[self.EMPTY_PLACE for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]
        for i in range(self.HEIGHT):
            self.game_map[i][0] = self.game_map[i][self.WIDTH - 1] = self.BORDER
        for i in range(self.WIDTH):
            self.game_map[0][i] = self.game_map[self.HEIGHT - 1][i] = self.BORDER
        for _ in range(3):
            position = self.rand_empty_place()
            self.game_map[position[0]][position[1]] = self.FRUIT

    def rand_empty_place(self):
        while True:
            y = random.randint(1, self.HEIGHT - 2)
            x = random.randint(1, self.WIDTH - 2)
            if self.game_map[y][x] == self.EMPTY_PLACE:
                return y, x

    def add_snake(self, player_id):
        position = self.rand_empty_place()
        snake = Snake(player_id, position)
        self.snakes[player_id] = snake
        self.game_map[position[0]][position[1]] = player_id

    def move_snakes(self):
        for snake in self.snakes.values():
            if snake.is_alive:
                snake.move()
                self.update_snake_on_map(snake)

    def update_snake_on_map(self, snake):
        for y, x in snake.get_positions():
            self.game_map[y][x] = snake.player_id

    def check_collisions(self):
        for snake in self.snakes.values():
            if snake.check_collision():
                # Handle snake death or game over
                pass

    def get_game_state(self):
        return {
            'snakes': {player_id: snake.get_positions() for player_id, snake in self.snakes.items()},
            'map': self.game_map
        }
