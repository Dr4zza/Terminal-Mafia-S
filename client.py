import socket
import threading
import sys
import random
from ascii_art import show_phase

SERVER_IP = input("Enter Host IP (e.g., 192.168.1.5 or 127.0.0.1): ")
PORT = 5555

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect((SERVER_IP, PORT))
    print("Connected to the game! (Type 'quit' to exit)")
    playername = f"Player {random.choice([i for i in range(0,30)])}"
except Exception as e:
    print(f"Could not connect: {e}")
    sys.exit()


def receive_messages():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if not message:
                print("\n[Disconnected from server]")
                client.close()
                sys.exit()
            if message == "phase is day":
                show_phase("DAY")
            elif message == "phase is night":
                show_phase("NIGHT")
            else:
                print(f"\n{message}")
        except Exception:
            print("\n[Connection lost]")
            client.close()
            sys.exit()


receive_thread = threading.Thread(target=receive_messages)
receive_thread.daemon = True
receive_thread.start()

while True:
    try:
        action = input()

        if action.lower() == 'quit':
            client.close()
            break

        send = f"{playername}: {action}"
        client.send(send.encode('utf-8'))

    except KeyboardInterrupt:
        print("\nExiting game...")
        client.close()
        break
