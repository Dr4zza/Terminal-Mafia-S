import socket
import threading
from main import player, SinglePlayer
from phase_manager import Phase_manager
import phase_manager
import time
from villager_questions import start_question_round
from game_logic import resolve_night_phase, resolve_day_vote, is_valid_vote_target
from ascii_art import GRAVESTONE_ART, MAFIA_KILL_ART, DETECTIVE_ART, TITLE_ART, VILLAGER_WIN_ART, MAFIA_WIN_ART, ROLE_DETECTIVE_ART, ROLE_DOCTOR_ART, ROLE_MAFIA_ART, ROLE_VILLAGER_ART

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
global voting_status
voting_status = False


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
            elif p.alive == False:
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
    broadcast(f"A new player joined! Welcome {playername}!", conn)

    lobby_players = list(client_names.values())
    lobby_str = ", ".join(lobby_players)
    broadcast(f"Current Lobby ({len(lobby_players)}/4+): {lobby_str}\n")
    broadcast("Waiting for a host to start the game...")
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
            
            playername = data.split(":", 1)[0]

            player = get_player_by_connection(conn)

            if data.split(':',1)[-1].strip().lower() == "quit":
                break

            if player is not None and not player.alive:
                player.conn.send("GHOSTS CANNOT INTERACT.".encode('utf-8'))
                continue

            if not game_start or voting_status==False:
                if "VOTE:" in data:
                    conn.send("SERVER: You cannot vote until the game starts.\n".encode('utf-8'))
                else:
                    broadcast(data, conn)  # Broadcast to everyone in the lobby
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
                
                if actual_target == playername:
                    conn.send("SERVER: You cannot vote for yourself!\n".encode('utf-8'))
                    
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
                        elif player.role == "Villager":
                            conn.send("\nYou aren't allowed to vote.\n".encode('utf-8'))
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
        if conn in client_names:
            del client_names[conn]
            
        broadcast(f"\n{playername} has left the game.", conn)
        
        if not game_start:
            lobby_players = list(client_names.values())
            if lobby_players:
                broadcast(f"Current Lobby ({len(lobby_players)}/4+): {', '.join(lobby_players)}\n")
                
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
            if p.role == "Mafia":
                death_msg = "\n You were lynched and failed as the mafia, better luck next time."
            else:
                death_msg = "\n*** YOU DIED! You are now a ghost. Ghosts cannot chat or vote. ***"
            try:
                p.conn.send(death_msg.encode('utf-8'))
                time.sleep(0.1)
                p.conn.send(GRAVESTONE_ART.encode('utf-8'))
                p.conn.send("\nYou are now spectating the game. To leave, type 'quit'.\n".encode('utf-8'))
            except Exception:
                pass
            break

game_start = False

def accept_connections():
    while True:
        try:
            conn, addr = server.accept()
            if game_start:
                try:
                    conn.send("\n[SERVER] Sorry, a game is already in progress! Cannot join.\n".encode('utf-8'))
                except:
                    pass
                conn.close()
            else:
                clients.append(conn)
                thread = threading.Thread(target=handle_client, args=(conn, addr))
                thread.start()
        except Exception:
            break

accept_thread = threading.Thread(target=accept_connections, daemon=True)
accept_thread.start()


while True:
    game_start = False
    voting_status = False
    print("\n--- LOBBY OPEN ---")
    print("Players can now join. Press [ENTER] to start the game (requires 4+ players)...")

    # Wait for the host to manually trigger the start
    while True:
        input() 
        for c in list(clients):
            try:
                # Send an invisible space to test if the connection is still alive
                c.send(" ".encode('utf-8'))
            except Exception:
                if c in clients: clients.remove(c)
                if c in client_names: del client_names[c]
                
        if len(clients) >= 4 and len(client_names) == len(clients):
            game_start = True
            break
        elif len(clients) < 4:
            print(f"Cannot start yet. Only {len(clients)} active players connected. Need at least 4.")
        elif len(client_names) < len(clients):
            print("A player is still registering their name. Please wait a second and press [ENTER] again.")


    print(f"\nStarting game with {len(clients)} players! Assigning new roles...")

    game_manager = player(clients, client_names) 

    broadcast("\n--- HOST HAS STARTED THE GAME ---\n")
    broadcast(TITLE_ART)


    for p in game_manager.player_list:
        try:
            if p.role == "Villager":
                p.conn.send(ROLE_VILLAGER_ART.encode('utf-8'))
            elif p.role == "Mafia":
                p.conn.send(ROLE_MAFIA_ART.encode('utf-8'))
            elif p.role == "Doctor":
                p.conn.send(ROLE_DOCTOR_ART.encode('utf-8'))
            elif p.role == "Detective":
                p.conn.send(ROLE_DETECTIVE_ART.encode('utf-8'))
                
            # Send the text confirmation
            role_message = f"\nSERVER: Your secret role is {p.role}! Game starting in 10 seconds.\n"
            p.conn.send(role_message.encode('utf-8'))
        except Exception:
            pass

    time.sleep(10)
    pm = Phase_manager(broadcast)

    def game_loop():
        global voting_status
        while True:
            # --- DAY PHASE ---
            pm.set_day() 
            day_votes.clear()
            voting_status = True

            living_players = [p.name for p in game_manager.player_list if p.alive]
            living_str = ", ".join(living_players)

            broadcast("\nDiscuss who the Mafia is. Type 'VOTE: [name]' to lynch. You have 60 seconds")
            broadcast(f"\nAlive players {living_str}")
            time.sleep(60)
            
            # Day Resolution
            voting_status = False
            broadcast("\n--- LYNCHING RESOLUTION ---")
            day_result = resolve_day_vote(game_manager.player_list, day_votes)
            if day_result["eliminated"]:
                broadcast(f"{day_result['eliminated']} was lynched by the town.")
                notify_eliminated_player(day_result["eliminated"])
            else:
                broadcast("No majority reached. Nobody was lynched.")
            
            if day_result["win_status"]:
                if night_result["win_status"] == "VILLAGERS_WIN":
                    broadcast(VILLAGER_WIN_ART)
                elif night_result["win_status"] == "MAFIA_WIN":
                    broadcast(MAFIA_WIN_ART)
                broadcast(f"\nGAME OVER: {day_result['win_status']}")
                break

            time.sleep(10)
            broadcast("\nNight is falling in 10 seconds.\n")
            # --- NIGHT PHASE ---
            pm.set_night()
            mafia_votes.clear()
            doctor_votes.clear()
            detective_votes.clear()

            voting_status = True
            living_players = [p.name for p in game_manager.player_list if p.alive]
            living_str = ", ".join(living_players)
            broadcast_maf(f"\n--- MAFIA MEET ---")
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

            night_result = resolve_night_phase(game_manager.player_list, mafia_votes, heal_target, detective_target)

            if night_result.get("detective_result") is not None:
                for p in game_manager.player_list:
                    if p.role == 'Detective' and p.alive: 
                        suspect = detective_target
                        try:
                            if night_result["detective_result"] is True:
                                p.conn.send(DETECTIVE_ART.encode('utf-8'))
                                p.conn.send(f"\n*** [INVESTIGATION RESULT] Your suspect {suspect} IS Mafia! ***\n".encode('utf-8'))
                            else:
                                p.conn.send(DETECTIVE_ART.encode('utf-8'))
                                p.conn.send(f"\n*** [INVESTIGATION RESULT] Your suspect {suspect} is NOT Mafia. ***\n".encode('utf-8'))
                        except Exception:
                            pass
                    elif p.role != "Detective":
                        try:
                            p.conn.send("\nInforming Detective about investigation...".encode('utf-8'))
                        except Exception:
                            pass
            time.sleep(10)
            
            pm.set_day()
            broadcast("\n--- MORNING NEWS ---")
            if night_result["eliminated"]:
                 for p in game_manager.player_list:
                     if p.alive:
                        try:
                            p.conn.send(f"\nTragedy! {night_result['eliminated']} was murdered in the night.\n".encode('utf-8'))
                            p.conn.send(MAFIA_KILL_ART.encode('utf-8'))
                        except Exception:
                            pass
                 notify_eliminated_player(night_result["eliminated"])
            else:
                 broadcast("\nThe town slept peacefully. No one was killed.")

            time.sleep(5)

            if night_result["win_status"]:
                if night_result["win_status"] == "VILLAGERS_WIN":
                    broadcast(VILLAGER_WIN_ART)
                elif night_result["win_status"] == "MAFIA_WIN":
                    broadcast(MAFIA_WIN_ART)
                broadcast(f"\nGAME OVER: {night_result['win_status']}\n")
                broadcast("Waiting for Host to restart the game...")
                break

    game_thread = threading.Thread(target=game_loop, daemon=True)
    game_thread.start()

    game_thread.join() 

    print("\nGame Over! Press [ENTER] to return players to the lobby.")
    input()
    broadcast("\n--- RETURNED TO LOBBY. Waiting for host to start a new match ---")
    broadcast("\n--- LOBBY CHAT ---")