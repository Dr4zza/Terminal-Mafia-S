import socket
import threading
from main import player, SinglePlayer
from phase_manager import Phase_manager
import phase_manager
import time
from villager_questions import start_question_round


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


HOST = '0.0.0.0'
PORT = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

lan_ip = get_local_ip()
print("=== Game Server Started ===")
print(f"Players on the LAN/Hotspot connect to: {lan_ip}")
print(f"Waiting for players to join on port {PORT}...\n")

clients = []


def broadcast(message, sender_conn=None):
    for client in clients:
        if client != sender_conn:
            try:
                client.send(message.encode('utf-8'))
            except:
                clients.remove(client)

def broadcast_maf(message, sender_conn=None):
    if 'game_manager' in globals():
        for p in game_manager.player_list:
            if p.role == 'Mafia' and p.conn != sender_conn:
                try:
                    p.conn.send(message.encode('utf-8'))
                except Exception:
                    pass

def handle_client(conn, addr):
    playername = str(addr[1])
    print(f"[JOIN] Player connected from {addr}")
    broadcast(f"A new player joined from {addr[0]}!", conn)
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            playername = data.split(":", 1)[0]
            if not data:
                break

            player = get_player_by_connection(conn)
            if player is not None and not player.alive:
                print(f"[IGNORED] Eliminated player tried to send: {data}")
                continue

            if "VOTE:" in data:
                target = data.split("VOTE:")[1].strip()

                if playername == "VOTE":
                    playername = str(addr[1])

                broadcast(f'{playername} voted for {target}', conn)
            else:
                broadcast(data, conn)
                broadcast_maf(data, conn)
                
            print(data)

    except ConnectionResetError:
        pass
    finally:
        print(f"[LEAVE] {playername} disconnected.")

        if conn in clients:
            clients.remove(conn)
            broadcast(f"{playername} has left the game.", conn)

        conn.close()


def get_player_by_connection(conn):

    for p in game_manager.player_list:
        if p.conn == conn:
            return p

    return None


EXPECTED_PLAYERS = 4


print(f"Waiting for {EXPECTED_PLAYERS} players to join...")

while len(clients) < EXPECTED_PLAYERS:
    conn, addr = server.accept()
    clients.append(conn)
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()

print("Lobby full. Assigning roles...")
broadcast("\n--- LOBBY FULL. GAME STARTING ---")
game_manager = player(clients)

for p in game_manager.player_list:
    role_message = f"\nSERVER: Your secret role is {p.role}!"
    p.conn.send(role_message.encode('utf-8'))

pm = Phase_manager(broadcast)


def game_loop():
    pm.set_day()  # day no 1
    time.sleep(30)  # shuttin stuff off for 30s
    pm.set_night()  # night no 1
    # remaining stuff to be coded after keshav's logic


game_thread = threading.Thread(target=game_loop, daemon=True)
game_thread.start()


def night_time():
    phase_manager.set_night()
    broadcast("Mafia Discussion..")
    broadcast("\n 30s remaining")
    time.sleep(30)

    broadcast("\n======ACTION TIME======")
    start_question_round(broadcast)
    time.sleep(20)
