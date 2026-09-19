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

def handle_client(conn, addr):
    print(f"[JOIN] Player connected from {addr}")
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
            print(data)
            playername = data.split(":", 1)[0]

            
    except ConnectionResetError:
        print(f"[LEAVE] {playername} disconnected.")
    finally:
        conn.close()

while True:
    conn, addr = server.accept()
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()