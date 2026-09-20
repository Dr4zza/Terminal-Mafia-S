import socket
import threading
import sys
import random
from ascii_art import show_phase
import os

PLAYER_NAME = input("Enter the name you want to use: ")
PORT = 5555

while True:
    SERVER_IP = input("Enter Host IP (e.g., 192.168.1.5 or 127.0.0.1): ")
    print(f"Connecting to {SERVER_IP}")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect((SERVER_IP, PORT))
        print("Connected to the game! (Type 'quit' to exit)")

        client.send(f"{PLAYER_NAME}: has connected".encode('utf-8'))
        
        break 
        
    except Exception as e:
        print(f"\n[ERROR] Could not connect to {SERVER_IP}.")
        print("Check if the host started the server and if the IP is correct.\n")

def receive_messages():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if not message:
                print("\n[Disconnected from server]")
                client.close()
                sys.exit()
                
            # 1. Use 'in' instead of '==' to catch merged packets
            if "phase is day" in message.lower():
                show_phase("DAY")
            if "phase is night" in message.lower():
                show_phase("NIGHT")
                
            # 2. Always print the message so you don't lose the game text
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

        send = f"{PLAYER_NAME}: {action}"
        client.send(send.encode('utf-8'))

    except KeyboardInterrupt:
        print("\nExiting game...")
        client.close()
        break
