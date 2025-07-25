from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime
from cryptography.fernet import Fernet
import os
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app)

# MySQL Configuration (Use environment variables in production)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'chat_user',
    'password': 'secure_password',
    'database': 'secure_chat_db'
}

KEY_FILE = 'encryption_key.key'
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as key_file:
        key = key_file.read()
else:
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as key_file:
        key_file.write(key)
cipher_suite = Fernet(key)

user_sessions = {}  # Maps username to session ID
users = set()       # Set of usernames
announced_users = set()

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def save_user_to_db(username, sid):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO users (username, session_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE session_id = %s", (username, sid, sid))
            connection.commit()
        except Error as e:
            print(f"Error saving user: {e}")
        finally:
            cursor.close()
            connection.close()

def save_message_to_db(sender, recipient, message, timestamp):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        encrypted_message = cipher_suite.encrypt(message.encode()).decode()
        try:
            cursor.execute("INSERT INTO messages (sender, recipient, message, timestamp) VALUES (%s, %s, %s, %s)",
                           (sender, recipient, encrypted_message, timestamp))
            connection.commit()
        except Error as e:
            print(f"Error saving message: {e}")
        finally:
            cursor.close()
            connection.close()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('register')
def handle_register(data):
    username = data['username']
    sid = request.sid
    if username not in users:
        users.add(username)
        user_sessions[username] = sid
        save_user_to_db(username, sid)
        # Send "You have joined" to the registering user
        emit('global_message', {'msg': f"{username} has joined"}, room=sid)
        # Send join message to all existing users
        for existing_user, existing_sid in user_sessions.items():
            if existing_user != username:
                emit('global_message', {'msg': f"{username} has joined"}, room=existing_sid)
        announced_users.add(username)
    
    emit('user_list', {'users': list(users - {username})}, broadcast=True)

@socketio.on('send_message')
def handle_message(data):
    username = data['username']
    message = data['message']
    
    if message.strip() == '' or username not in user_sessions:
        return

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted_message = f"[{timestamp}] {username}: {message}"

    emit('global_message', {'msg': formatted_message}, broadcast=True)
    save_message_to_db(username, "All", message, timestamp)

@socketio.on('leave')
def handle_leave(data):
    username = data['username']
    if username in users:
        users.remove(username)
        del user_sessions[username]
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("DELETE FROM users WHERE username = %s", (username,))
                connection.commit()
            except Error as e:
                print(f"Error deleting user: {e}")
            finally:
                cursor.close()
                connection.close()
        emit('global_message', {'msg': f"{username} has left the chat!"}, broadcast=True)
        if username in announced_users:
            announced_users.remove(username)
        emit('user_list', {'users': list(users)}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    for username, sid in list(user_sessions.items()):
        if sid == request.sid:
            users.remove(username)
            del user_sessions[username]
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                try:
                    cursor.execute("DELETE FROM users WHERE username = %s", (username,))
                    connection.commit()
                except Error as e:
                    print(f"Error deleting user: {e}")
                finally:
                    cursor.close()
                    connection.close()
            emit('global_message', {'msg': f"{username} has left the chat!"}, broadcast=True)
            if username in announced_users:
                announced_users.remove(username)
            emit('user_list', {'users': list(users)}, broadcast=True)
            break

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)  # Production settings