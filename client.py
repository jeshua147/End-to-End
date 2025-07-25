import socket
import threading
import pickle
import tkinter as tk
from cryptography.fernet import Fernet
from crypto_utils import encrypt_message, decrypt_message
from rsa_utils import encrypt_key
from rsa_utils import load_public_key

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 5555))

# Ask username at startup
username = input("Enter your username: ")

client.send(pickle.dumps(username))

server_public_key_bytes = client.recv(4096)
server_public_key = load_public_key(server_public_key_bytes)
symmetric_key = Fernet.generate_key()
encrypted_symmetric_key = encrypt_key(server_public_key, symmetric_key)
client.send(encrypted_symmetric_key)

def receive_messages():
    while True:
        try:
            sender, message = pickle.loads(client.recv(4096))
            decrypted_message = decrypt_message(symmetric_key, message)
            chat_box.config(state=tk.NORMAL)
            chat_box.insert(tk.END, f"{sender}: {decrypted_message}\n")
            chat_box.config(state=tk.DISABLED)
            chat_box.see(tk.END)
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def send_message():
    message = message_entry.get()
    encrypted_message = encrypt_message(symmetric_key, message)
    client.send(pickle.dumps(encrypted_message))
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, f"You ({username}): {message}\n")
    chat_box.config(state=tk.DISABLED)
    chat_box.see(tk.END)
    message_entry.delete(0, tk.END)

# Tkinter GUI
window = tk.Tk()
window.title("Secure Chat App")

chat_box = tk.Text(window, state=tk.DISABLED)
chat_box.pack(padx=10, pady=10)

message_entry = tk.Entry(window)
message_entry.pack(side=tk.LEFT, padx=(10, 0), pady=(0, 10), expand=True, fill=tk.X)

send_button = tk.Button(window, text="Send", command=send_message)
send_button.pack(side=tk.RIGHT, padx=(0, 10), pady=(0, 10))

receive_thread = threading.Thread(target=receive_messages)
receive_thread.start()

window.mainloop()
