const socket = io();
let username = '';
let keys = {};

// Generate RSA key pair
const crypt = new JSEncrypt({ default_key_size: 1024 });
crypt.getKey();
const publicKey = crypt.getPublicKey();

function joinChat() {
    username = document.getElementById('username').value.trim();
    if (!username) return alert('Please enter a username');

    socket.emit('join', { username });
}

document.getElementById('username').addEventListener('change', joinChat);

socket.on('update_users', users => {
    const recipientSelect = document.getElementById('recipient');
    recipientSelect.innerHTML = '';
    users.filter(u => u !== username).forEach(user => {
        const option = document.createElement('option');
        option.value = user;
        option.textContent = user;
        recipientSelect.appendChild(option);
    });
});

function sendMessage() {
    const recipient = document.getElementById('recipient').value;
    const message = document.getElementById('message').value.trim();

    if (!recipient || !message) return alert('Recipient and message are required');

    const encrypted = crypt.encrypt(message);
    socket.emit('send_message', {
        sender: username,
        recipient: recipient,
        message: encrypted
    });

    document.getElementById('message').value = '';
}

socket.on('receive_message', data => {
    const messagesDiv = document.getElementById('messages');
    let decrypted = '';
    try {
        decrypted = crypt.decrypt(data.message);
    } catch (e) {
        decrypted = '[Encrypted message]';
    }
    messagesDiv.innerHTML += `<div><b>${data.sender}</b>: ${decrypted}</div>`;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
});