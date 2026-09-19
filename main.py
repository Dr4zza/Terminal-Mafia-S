import random

class SinglePlayer:
    def __init__(self, conn, addr, role):
        self.conn = conn
        self.addr = addr
        self.role = role

class player():
    def __init__(self, players):
        self.player_list = []
        
        role_pool = ['Mafia'] + ['Doctor'] + ['Villager'] * (len(players) - 2)
        
        random.shuffle(role_pool)
        
        for i, conn in enumerate(players):
            addr = conn.getpeername() 
            assigned_role = role_pool[i]
            
            new_player = SinglePlayer(conn, addr, assigned_role)
            self.player_list.append(new_player)

    def daycycle(self):
        pass