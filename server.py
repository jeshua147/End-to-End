import socket
import threading
import pickle
import os
from rsa_utils import generate_keys, decrypt_key
from crypto_utils import decrypt_message
from rsa_utils import serialize_public_key

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 5555))
server.listen()

clients = {}
usernames = {}
keys = {}

server_private_key, server_public_key = generate_keys()

if not os.path.exists("chat_history"):
    os.makedirs("chat_history")

def broadcast(message, sender_client):
    for client in clients:
        if client != sender_client:
            try:
                client.send(pickle.dumps(message))
            except Exception as e:
                print(f"Error sending message: {e}")

def handle_client(client):
    try:
        username = pickle.loads(client.recv(4096))
        usernames[client] = username
        print(f"[+] {username} connected.")

        serialized_pubkey = serialize_public_key(server_public_key)
        client.send(serialized_pubkey)
        encrypted_symmetric_key = client.recv(4096)
        symmetric_key = decrypt_key(encrypted_symmetric_key, server_private_key)
        keys[client] = symmetric_key

        while True:
            message = pickle.loads(client.recv(4096))
            decrypted_message = decrypt_message(symmetric_key, message)
            print(f"[{username}]: {decrypted_message}")

            # Save chat history
            with open(f"chat_history/{username}.txt", "a") as f:
                f.write(f"{username}: {decrypted_message}\n")

            broadcast((username, message), client)

    except Exception as e:
        print(f"[-] {usernames.get(client, client)} disconnected: {e}")
    finally:
        if client in clients:
            clients.pop(client)
        if client in usernames:
            print(f"[-] {usernames[client]} left the chat.")
            usernames.pop(client)
        client.close()

def receive():
    while True:
        client, address = server.accept()
        print(f"[NEW CONNECTION] {address}")

        clients[client] = address
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

print("[STARTING] Server is running...")
receive()
