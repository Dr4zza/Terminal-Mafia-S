import random
from game_logic import build_role_pool

class SinglePlayer:
    def __init__(self, conn, addr, role, name):
        self.conn = conn
        self.addr = addr
        self.role = role
        self.name = name
        self.alive = True


class player():
    def __init__(self, players, name_map):
        self.player_list = []

        role_pool = build_role_pool(len(players))

        for i, conn in enumerate(players):
            addr = conn.getpeername()
            assigned_role = role_pool[i]
            player_name = name_map.get(conn, str(addr[1]))
            new_player = SinglePlayer(conn, addr, assigned_role, player_name)
            self.player_list.append(new_player)

