import socket
import threading

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

def handle_client(conn, addr):
    print(f"[JOIN] Player connected from {addr}")
    clients.append(conn)
    broadcast(f"A new player joined from {addr[0]}!", conn)
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            
            if not data:
                break
            print(data)
            broadcast(data, conn)
            playername = data.split(":", 1)[0]

            
    except ConnectionResetError:
        pass
    finally:
        print(f"[LEAVE] Player {playername} disconnected.")
        if conn in clients:
            clients.remove(conn)
            broadcast(f"Player {playername} has left the game.", conn)
        conn.close()

while True:
    conn, addr = server.accept()
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()