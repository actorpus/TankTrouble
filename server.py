import pygame
import math
import random
import socket
import hashlib
import threading
import pickle

print(socket.gethostbyname(socket.gethostname()))

CLIENT_VERSION = 'V0.0.6'


class BulletHandler:
    def __init__(self):
        self.bullets = []

    def reset(self):
        self.bullets = []

    def dump_all(self):
        return [
            (b.x, b.y) for b in self.bullets
        ]

    class _bullet:
        def __init__(self, x, y, r, parent_obj):
            self.x, self.y, r = x, y, r
            self.parent_obj = parent_obj

            self.dx = math.sin(r)
            self.dy = math.cos(r)

            self.ttl = 15

        def draw(self, d):
            pygame.draw.circle(d, (0, 0, 0), (self.x, self.y), 2)

        def update(self):
            tpf = 1 / clock.get_fps()

            # update position
            self.x += self.dx * tpf * 200
            self.y += self.dy * tpf * 200

            # map bounds
            if self.x < 16 or self.x > background.get_width() - 16 or self.y < 16 or self.y > background.get_height() - 16:
                return True

            # wall collision
            if background.get_at((int(self.x), int(self.y) - 4)) == (0, 0, 0):
                self.dy = - self.dy
            elif background.get_at((int(self.x), int(self.y) + 4)) == (0, 0, 0):
                self.dy = - self.dy
            if background.get_at((int(self.x) - 4, int(self.y))) == (0, 0, 0):
                self.dx = - self.dx
            elif background.get_at((int(self.x) + 4, int(self.y))) == (0, 0, 0):
                self.dx = - self.dx

            if background.get_at((int(self.x), int(self.y))) == SAFE:
                self.ttl = 0
                return True

            self.ttl -= tpf
            if self.ttl < 0:
                return True

    def create_bullet(self, tank_obj, limit=6):
        if not any((
            background.get_at((int(tank_obj.x + 12), int(tank_obj.y))) == SAFE,
            background.get_at((int(tank_obj.x - 12), int(tank_obj.y))) == SAFE,
            background.get_at((int(tank_obj.x), int(tank_obj.y + 12))) == SAFE,
            background.get_at((int(tank_obj.x), int(tank_obj.y - 12))) == SAFE
        )):

            if sum([b.parent_obj == tank_obj for b in self.bullets]) < limit:
                self.bullets.append(
                    self._bullet(
                        tank_obj.x + (math.sin(tank_obj.r) * 15),
                        tank_obj.y + (math.cos(tank_obj.r) * 15),
                        tank_obj.r,
                        tank_obj
                    )
                )

    def update_bullets(self):
        remove = []

        for b in self.bullets:
            if b.update():
                remove.append(b)

        for _ in remove:
            self.bullets.remove(_)

    def check_collision(self, tank_obj, dist=10):
        # return any(
        #     [(((b.x - tank_obj.x) ** 2 + (b.y - tank_obj.y) ** 2) ** 0.5) < dist for b in self.bullets]
        # )
        for bullet in self.bullets:
            if (((bullet.x - tank_obj.x) ** 2 + (bullet.y - tank_obj.y) ** 2) ** 0.5) < dist:  # collision
                self.bullets.remove(bullet)
                return True


class PowerUpHandler:
    def __init__(self):
        self.powerups = []

    def reset(self):
        self.powerups = []

    def dump_all(self):
        return [
            (b.x, b.y, b.type) for b in self.powerups
        ]

    def spawn_random(self, x, y):
        return self.spawn(x, y, random.randint(0, 2))

    def spawn(self, x, y, tpe):
        self.powerups.append(
            self.powerup(x * 16, y * 16, tpe)
        )

    def update_powerups(self, tanks):
        remove = []

        for b in self.powerups:
            if b.update():
                remove.append(b)

        for _ in remove:
            self.powerups.remove(_)

        for tank_obj in tanks:
            for powerup in self.powerups:
                if (((powerup.x - tank_obj.x) ** 2 + (powerup.y - tank_obj.y) ** 2) ** 0.5) < 10:  # collision
                    self.powerups.remove(powerup)

                    tank_obj.active_powerup = powerup.type

    class powerup:
        def __init__(self, x, y, tpe):
            self.x = x
            self.y = y
            self.type = tpe
            self.ttl = 30

        def update(self):
            tpf = 1 / clock.get_fps()

            self.ttl -= tpf
            if self.ttl < 0:
                return True


class Tank:
    def __init__(self, inputs=(pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE), default=(100, 100, 0)):
        self.x, self.y, self.r = default
        self.default = default
        self.color = 0, 0, 0
        self.alive = True
        self.data = {"w": False, "a": False, "s": False, "d": False, "SPACE": False}
        self.letters = inputs
        self.name = ""
        self.shoot_countdown = 0
        self.active_powerup = 2
        # 0: NONE
        # 1: SNIPER
        # 2: SHIELD

    def kill(self):
        if self.active_powerup == 2:
            self.active_powerup = 0
        else:
            self.alive = False

    def get_pos(self):
        return self.x, self.y

    def reset(self):
        self.x, self.y, self.r = self.default
        self.alive = True

    def parse(self):
        if self.alive:
            fps = 1 / clock.get_fps()

            # update tank
            if self.data["a"]:
                self.r += fps * 3  # 2

            if self.data["d"]:
                self.r -= fps * 3  # 2

            if self.data["w"]:
                nx = self.x + math.sin(self.r) * fps * 100  # 50
                ny = self.y + math.cos(self.r) * fps * 100  # 50

                if background.get_at((int(nx), int(ny))) == (0, 0, 0):
                    return

                self.x = nx
                self.y = ny

            if self.data["s"]:
                nx = self.x - math.sin(self.r) * fps * 100  # 50
                ny = self.y - math.cos(self.r) * fps * 100  # 50

                if background.get_at((int(nx), int(ny))) == (0, 0, 0):
                    return

                self.x = nx
                self.y = ny

            if bullets.check_collision(self):
                self.kill()

            self.shoot_countdown -= fps

    def save(self, data):
        self.data = data

        if data["SPACE"]:
            if self.shoot_countdown < 0:
                bullets.create_bullet(self)
                self.shoot_countdown = 0.2


class connections_handler:
    START_POSS = [
        (48, 48,   0.75 * math.pi),
        (976, 48,  1.25 * math.pi),
        (976, 976, 1.75 * math.pi),
        (48, 976,  0.25 * math.pi)
    ]

    def __init__(self, connection_limit=1, port=3956):
        self.connection_limit = connection_limit

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("", port))
        self.server.listen(1)

        self.connections = []

    def len_alive(self):
        return sum([_.alive for _ in self.connections])

    def dump_all(self):
        o = []
        for t in self.connections:
            if t.alive:
                o.append((t.x, t.y, t.r, t.color, t.active_powerup))

        return o

    def start(self):
        while len(self.connections) < self.connection_limit:
            client, connection = self.server.accept()

            pos = self.START_POSS[len(self.connections)]

            tank = Tank(default=pos)

            self.connections.append(tank)
            self.connection_handler(tank, client)

    def update_all(self):
        for tank in self.connections:
            tank.parse()

    def reset_all(self):
        for tank in self.connections:
            tank.reset()

    class connection_handler(threading.Thread):
        @staticmethod
        def dump(data: dict):
            _data = b''

            _data += len(data["bullets"]).to_bytes(1, "big")

            for bullet in data["bullets"]:
                # x, y
                _data += int(bullet[0]).to_bytes(2, "big")
                _data += int(bullet[1]).to_bytes(2, "big")

            _data += len(data["tanks"]).to_bytes(1, "big")

            for tank in data["tanks"]:
                # x, y
                _data += int(tank[0]).to_bytes(2, "big")
                _data += int(tank[1]).to_bytes(2, "big")

                # r
                _data += (int(tank[2] * 40.584) % 255).to_bytes(1, "big")

                # r, g, b
                _data += int(tank[3][0] * 255).to_bytes(1, "big")
                _data += int(tank[3][1] * 255).to_bytes(1, "big")
                _data += int(tank[3][2] * 255).to_bytes(1, "big")
                _data += tank[4].to_bytes(1, "big")

            _data += len(data["powerups"]).to_bytes(1, "big")

            print(data)

            print(_data)
            for powerup in data["powerups"]:
                # x, y
                _data += int(powerup[0]).to_bytes(2, "big")
                _data += int(powerup[1]).to_bytes(2, "big")

                # type
                _data += int(powerup[2]).to_bytes(1, "big")

            print(_data)

            return _data

        @staticmethod
        def load(data):
            data = int.from_bytes(data, "big")

            return {
                "w": (data >> 0) % 2,
                "a": (data >> 1) % 2,
                "s": (data >> 2) % 2,
                "d": (data >> 3) % 2,
                "SPACE": (data >> 4) % 2
            }

        def __init__(self, parser, client):
            super().__init__()

            self.parser = parser
            self.client = client

            extra = random.randbytes(8)

            with open("client.py", "rb") as file:
                hsh = hashlib.sha1(file.read() + extra, usedforsecurity=True).digest()

            client.send(extra)

            client_hsh, parser.color, parser.name = pickle.loads(
                client.recv(1024)
            )

            if client_hsh == hsh:
                print("good hash")
                client.send(pickle.dumps([
                    '0CLIENT (%s) VALID' % CLIENT_VERSION,
                    map
                ]))

                self.daemon = True
                self.start()
            else:
                print("bad hash")
                client.send(b'1CLIENT INTEGRITY COMPROMISED\nPLEASE REACQUIRE %s' % CLIENT_VERSION)
                client.close()

        def run(self):
            local_clock = pygame.time.Clock()
            while True:
                data = self.client.recv(1024)

                try:
                    data2 = self.load(data)
                    self.parser.save(data2)

                except pickle.UnpicklingError:
                    # print("FUKIN BROKE INIT", e, data)
                    ...

                self.client.send(self.dump(
                    {
                        "bullets": bullets.dump_all(),
                        "tanks": connections.dump_all(),
                        "powerups": powerups.dump_all()
                    }
                ))

                local_clock.tick(60)


# display = pygame.display.set_mode((1024, 1024))
clock = pygame.time.Clock()

while clock.get_fps() == 0:
    clock.tick(60)
# running = True

WALL = 0, 0, 0
SAFE = 0, 255, 200


def gen_map(m):
    m = m.split("\n")[1:]

    d = pygame.surface.Surface((1024, 1024))

    d.fill((255, 255, 255))

    for y in range(64):
        for x in range(64):
            if m[y][x] == "#":
                pygame.draw.rect(d, WALL, (x * 16, y * 16, 16, 16))

            elif m[y][x] == "s":
                pygame.draw.rect(d, SAFE, (x * 16, y * 16, 16, 16))

    return d


# local_tanks = [
#     Tank(default=(64, 64, 0)),
#     # Tank((pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT), (display.get_width()-100, display.get_height()-100, 3.1415269))
# ]


bullets = BulletHandler()
powerups = PowerUpHandler()

powerups.spawn(32, 16, 2)

map = """
################################################################
#                                                              #
#                                                              #
#                                                              #
#      #                                                #      #
#      #                                                #      #
#      #   #######                            #######   #      #
#   ####                ################                ####   #
#                                                              #
#                                                              #
#     #                                                  #     #
#     #                                                  #     #
#     #                                                  #     #
#     #                                                  #     #
#     #                                                  #     #
#     #                                                  #     #
#     #                                                  #     #
#     #                                                  #     #
#                                                              #
#                                                              #
#                                                              #
#                                                              #
#                                                              #
#                                                              #
#      #                ######ssss######                #      #
#      #                ######ssss######                #      #
#      #                ##ssssssssssss##                #      #
#      #                ##ssssssssssss##                #      #
#      #                ##ssssssssssss##                #      #
#      #                ##ssssssssssss##                #      #
#      #                ssssssssssssssss                #      #
#      #                ssssssssssssssss                #      #
#      #                ssssssssssssssss                #      #
#      #                ssssssssssssssss                #      #
#      #                ##ssssssssssss##                #      #
#      #                ##ssssssssssss##                #      #
#      #                ##ssssssssssss##                #      #
#      #                ##ssssssssssss##                #      #
#      #                ######ssss######                #      #
#      #                ######ssss######                #      #
#                                                              #
#                                                              #
#                                                              #
#                                                              #
#                                                              #
#                                                              #
#     #                                                  #     #
#     #                                                  #     #
#     #                                                  #     #
#     #                                                  #     #
#     #                                                  #     #
#     #                                                  #     #
#     #                                                  #     #
#     #                                                  #     #
#                                                              #
#                                                              #
#   ####                ################                ####   #
#      #   #######                            #######   #      #
#      #                                                #      #
#      #                                                #      #
#                                                              #
#                                                              #
#                                                              #
################################################################
"""

background = gen_map(map)

connections = connections_handler(connection_limit=1)
connections.start()

# while running:
#     for e in pygame.event.get():
#         if e.type == pygame.QUIT:
#             running = False
#
#         if e.type == pygame.KEYDOWN:
#             if e.key == pygame.K_SPACE:
#                 connections.reset_all()
#                 bullets.reset()

while True:
    bullets.update_bullets()
    powerups.update_powerups(connections.connections)

    # display.blit(background, (0, 0))

    # bullets.draw_bullets()
    #
    # for _ in local_tanks:
    #     _.draw(display)
    #     _.localUpdate()

    connections.update_all()

    if len(connections.connections) > 1:
        if connections.len_alive() == 1:
            winner = "no one"

            for _ in connections.connections:
                if _.alive:
                    winner = _.name
                    break

            print(winner, "won!")

            connections.reset_all()
            bullets.reset()

    # pygame.display.update()
    clock.tick(60)
