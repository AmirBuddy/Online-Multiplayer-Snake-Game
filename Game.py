from threading import RLock
import random
import time

class Snake:
    DIRECTIONS = {
        'w': (-1, 0), 
        's': (1, 0), 
        'a': (0, -1), 
        'd': (0, 1) 
    }

    def __init__(self, cid, position):
        self.cid = cid
        self.body = [position]
        self.direction = random.choice(['w', 'a', 's', 'd'])
        self.alive = True

    def grow(self):
        if not self.alive:
            return None

        head = self.body[0]
        new_head = (head[0] + self.DIRECTIONS[self.direction][0], head[1] + self.DIRECTIONS[self.direction][1])
        self.body = [new_head] + self.body
        return new_head

    def change_direction(self, new_direction):
        if new_direction in self.DIRECTIONS and \
           (self.DIRECTIONS[new_direction][0] != -self.DIRECTIONS[self.direction][0] or
            self.DIRECTIONS[new_direction][1] != -self.DIRECTIONS[self.direction][1]):
            self.direction = new_direction

    def is_alive(self):
        return self.alive

    def set_alive(self, alive):
        self.alive = alive

class Game:
    def __init__(self, height, width, winner_length, game_event):
        self.EMPTY_PLACE = ' '
        self.BORDER = '#'
        self.FRUIT = '*'
        self.HEIGHT = height
        self.WIDTH = width
        self.WINNER_LENGTH = winner_length
        self.game_event = game_event
        self.state_lock = RLock()
        self.snakes = {}
        self.game_map = [[self.EMPTY_PLACE for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]
        for i in range(self.HEIGHT):
            self.game_map[i][0] = self.game_map[i][self.WIDTH - 1] = self.BORDER
        for i in range(self.WIDTH):
            self.game_map[0][i] = self.game_map[self.HEIGHT - 1][i] = self.BORDER
        for _ in range(3):
            self.add_fruit()

    def rand_empty_place(self):
        while True:
            y = random.randint(1, self.HEIGHT - 2)
            x = random.randint(1, self.WIDTH - 2)
            with self.state_lock:
                if self.game_map[y][x] == self.EMPTY_PLACE:
                    return y, x

    def add_fruit(self):
        with self.state_lock:
            position = self.rand_empty_place()
            self.game_map[position[0]][position[1]] = self.FRUIT

    def add_snake(self, cid):
        with self.state_lock:
            if cid in self.snakes:
                return False
            self.snakes[cid] = {}
            self.snakes[cid]['input'] = None
            with self.state_lock:
                position = self.rand_empty_place()
                self.game_map[position[0]][position[1]] = cid
                snake = Snake(cid, position)
            self.snakes[cid]['snake'] = snake
            return True

    def set_input(self, cid, char):
        if cid in self.snakes:
            self.snakes[cid]['input'] = char

    def is_alive(self, cid):
        return self.snakes[cid]['snake'].is_alive()

    def get_state(self):
        with self.state_lock:
            res = []
            for row in self.game_map:
                res.append(''.join(row))
            return res

    def remove(self, cid):
        if cid in self.snakes:
            with self.state_lock:
                snake = self.snakes[cid]['snake']
                for part in snake.body:
                    if self.game_map[part[0]][part[1]] == cid:
                        self.game_map[part[0]][part[1]] = self.EMPTY_PLACE
                snake.set_alive(False)
                del self.snakes[cid]

    def update(self):
        while not self.game_event.is_set():
            with self.state_lock:
                for cid, info in self.snakes.items():
                    snake = info['snake']
                    if info['input']:
                        snake.change_direction(info['input'])
                        info['input'] = None
                    new_head = snake.grow()
                    if not new_head or self.game_map[new_head[0]][new_head[1]] in [self.BORDER] + list(self.snakes.keys()):
                        snake.set_alive(False)
                    else:
                        if self.game_map[new_head[0]][new_head[1]] == self.FRUIT:
                            self.add_fruit()
                        else:
                            tail = snake.body[-1]
                            snake.body.remove(tail)
                            self.game_map[tail[0]][tail[1]] = self.EMPTY_PLACE
                        self.game_map[new_head[0]][new_head[1]] = snake.cid

                self.remove_dead_snakes()
            time.sleep(0.8)

    def remove_dead_snakes(self):
        to_remove = [cid for cid, info in self.snakes.items() if not info['snake'].is_alive()]
        for cid in to_remove:
            self.remove(cid)
