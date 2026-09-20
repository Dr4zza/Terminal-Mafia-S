import socket
import threading
from main import player, SinglePlayer
from phase_manager import Phase_manager
import phase_manager
import time
from villager_questions import start_question_round
from game_logic import resolve_night_phase, resolve_day_vote, is_valid_vote_target

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
game_start = False

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

lan_ip = get_local_ip()
print("=== Game Server Started ===")
print(f"Players on the LAN/Hotspot connect to: {lan_ip}")
print(f"Waiting for players to join on port {PORT}...\n")

clients = []
client_names = {}
day_votes = {}    
mafia_votes = {}
doctor_votes = {}
detective_votes = {}

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

def broadcast_villager(message):
    if 'game_manager' in globals():
        for p in game_manager.player_list:
            if p.role == 'Villager' and p.alive:
                try:
                    p.conn.send(message.encode('utf-8'))
                except Exception:
                    pass

def handle_client(conn, addr):
    initial_data = conn.recv(1024).decode('utf-8')
    playername = initial_data.split(":", 1)[0] if ":" in initial_data else str(addr[1])
    client_names[conn] = playername
    print(f"[JOIN] Player connected from {addr}")
    broadcast(f"A new player joined from {playername}!", conn)
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
            
            playername = data.split(":", 1)[0]

            player = get_player_by_connection(conn)
            if player is not None and not player.alive:
                player.conn.send("GHOSTS CANNOT INTERACT.".encode('utf-8'))
                continue

            if "VOTE:" in data:
                target_input = data.split("VOTE:")[1].strip()
                
                # Look through the players to find a case-insensitive match
                actual_target = target_input 
                if 'game_manager' in globals():
                    for p in game_manager.player_list:
                        if p.name.lower() == target_input.lower():
                            actual_target = p.name
                            break
                
                # --- NEW: Check for self-voting explicitly ---
                if actual_target == playername:
                    conn.send("SERVER: You cannot vote for yourself!\n".encode('utf-8'))
                    
                # Check phase and validate target
                elif is_valid_vote_target(game_manager.player_list, playername, actual_target):
                    if pm.phase == "DAY":
                        day_votes[playername] = actual_target
                        broadcast(f'{playername} voted to lynch {actual_target}')
                        
                    elif pm.phase == "NIGHT":
                        if player.role == "Mafia":
                            mafia_votes[playername] = actual_target
                            broadcast_maf(f'{playername} voted to kill {actual_target}')
                        elif player.role == "Doctor":
                            doctor_votes[playername] = actual_target
                            conn.send(f"SERVER: You voted to heal {actual_target}\n".encode('utf-8'))
                        elif player.role == "Detective":
                            detective_votes[playername] = actual_target
                            conn.send(f"SERVER: You chose to investigate {actual_target}. Results will arrive in the morning.\n".encode('utf-8'))
                else:
                    conn.send(f"SERVER: Invalid target '{target_input}'. They might already be dead.\n".encode('utf-8'))
            else:
                if pm.phase == "NIGHT" and player.role == "Mafia":
                     broadcast_maf(data, conn)
                elif pm.phase == "DAY":
                     broadcast(data, conn)
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
    if 'game_manager' in globals():
        for p in game_manager.player_list:
            if p.conn == conn:
                return p
    return None

def notify_eliminated_player(victim_name):
    """Finds the eliminated player and sends them a direct 'You Died' message."""
    for p in game_manager.player_list:
        if p.name == victim_name:
            death_msg = "\n*** YOU DIED! You are now a ghost. Ghosts cannot chat or vote. ***"
            try:
                p.conn.send(death_msg.encode('utf-8'))
            except Exception:
                pass
            break

game_start = False

def accept_connections():
    while not game_start:
        try:
            conn, addr = server.accept()
            clients.append(conn)
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
        except Exception:
            break

accept_thread = threading.Thread(target=accept_connections, daemon=True)
accept_thread.start()

print("Server is open! Players can now join.")
print("Press [ENTER] on this server console at any time to start the game (requires 4+ players)...")

# 2. Main thread waits for the host to manually trigger the start
while True:
    input() # Pauses the terminal here until the host hits Enter
    
    # Ensure at least 4 players are fully registered before allowing the start
    if len(clients) >= 4 and len(client_names) == len(clients):
        game_start = True
        break
    elif len(clients) < 4:
        print(f"Cannot start yet. Only {len(clients)} players have joined. Need at least 4.")
    elif len(client_names) < len(clients):
        print("A player is still registering their name. Please wait a second and press [ENTER] again.")

print(f"\nStarting game with {len(clients)} players! Assigning roles...")
broadcast("\n--- HOST HAS STARTED THE GAME ---")

# 3. Create the game manager with everyone who joined before the host pressed Enter
game_manager = player(clients, client_names)

for p in game_manager.player_list:
    role_message = f"\nSERVER: Your secret role is {p.role}! Game starting in 10 seconds."
    p.conn.send(role_message.encode('utf-8'))

time.sleep(10)

pm = Phase_manager(broadcast)


def game_loop():
    while True:
        # --- DAY PHASE ---
        pm.set_day() 
        day_votes.clear()

        living_players = [p.name for p in game_manager.player_list if p.alive]
        living_str = ", ".join(living_players)

        broadcast("\nDiscuss who the Mafia is. Type 'VOTE: [name]' to lynch. You have 60 seconds")
        broadcast(f"\nAlive players {living_str}")
        time.sleep(60)
        
        # Day Resolution
        broadcast("\n--- LYNCHING RESOLUTION ---")
        day_result = resolve_day_vote(game_manager.player_list, day_votes)
        if day_result["eliminated"]:
            broadcast(f"{day_result['eliminated']} was lynched by the town.")
            notify_eliminated_player(day_result["eliminated"])
        else:
            broadcast("No majority reached. Nobody was lynched.")
        
        if day_result["win_status"]:
            broadcast(f"\nGAME OVER: {day_result['win_status']}")
            break

        time.sleep(0.5)
        # --- NIGHT PHASE ---
        pm.set_night()
        mafia_votes.clear()
        doctor_votes.clear()
        living_players = [p.name for p in game_manager.player_list if p.alive]
        living_str = ", ".join(living_players)

        broadcast_maf(f"\nMafia, you have 30 seconds to discuss. Type 'VOTE: [name]' to kill.\nTarget options: {living_str}")

        for p in game_manager.player_list:
            if p.role == 'Doctor' and p.alive:
                try:
                    p.conn.send(f"\nDoctor, you have 30 seconds. Type 'VOTE: [name]' to heal someone.\nTarget options: {living_str}\n".encode('utf-8'))
                except Exception:
                    pass
            elif p.role == 'Detective' and p.alive:
                try:
                    p.conn.send(f"\nDetective, you have 30 seconds. Type 'VOTE: [name]' to investigate someone.\nTarget options: {living_str}\n".encode('utf-8'))
                except Exception:
                    pass
        
        start_question_round(broadcast_villager)
        
        time.sleep(30)

        heal_target = list(doctor_votes.values())[0] if doctor_votes else None
        detective_target = list(detective_votes.values())[0] if detective_votes else None
        
        heal_target = None
        if doctor_votes:
            heal_target = list(doctor_votes.values())[0]

        night_result = resolve_night_phase(game_manager.player_list, mafia_votes, heal_target, detective_target)

        if night_result.get("detective_result") is not None:
            for p in game_manager.player_list:
                if p.role == 'Detective' and p.alive: # Only tell them if they survived the night!
                    suspect = detective_target
                    if night_result["detective_result"] is True:
                        p.conn.send(f"\n*** [INVESTIGATION RESULT] Your suspect {suspect} IS Mafia! ***\n".encode('utf-8'))
                    else:
                        p.conn.send(f"\n*** [INVESTIGATION RESULT] Your suspect {suspect} is NOT Mafia. ***\n".encode('utf-8'))
        
        pm.set_day()
        broadcast("\n--- MORNING NEWS ---")
        if night_result["eliminated"]:
             broadcast(f"\nTragedy! {night_result['eliminated']} was murdered in the night.")
             notify_eliminated_player(night_result["eliminated"])
        else:
             broadcast("\nThe town slept peacefully. No one was killed.")
             
        if night_result["win_status"]:
            broadcast(f"\nGAME OVER: {night_result['win_status']}")
            break

game_thread = threading.Thread(target=game_loop, daemon=True)
game_thread.start()

# Keep main thread alive
while True:
    time.sleep(1)