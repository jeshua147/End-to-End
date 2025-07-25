const socket = io();
let clientId = '';
let rsa = new JSEncrypt({ default_key_size: 2048 });
rsa.getKey();

socket.on('connect', () => {
    console.log('Connected to server ✅');
});

socket.on('server_message', (data) => {
    appendMessage(`🖥️ ${data.data}`);
});

socket.on('update_clients', (clients) => {
    const clientsSelect = document.getElementById('clients');
    clientsSelect.innerHTML = '';
    clients.forEach(client => {
        if (client.client_id !== clientId) {
            const option = document.createElement('option');
            option.value = client.client_id;
            option.text = client.username;
            clientsSelect.appendChild(option);
        }
    });
});

socket.on('receive_message', (data) => {
    try {
        const decrypted = rsa.decrypt(atob(data.encrypted_message));
        if (decrypted) {
            appendMessage(`${data.sender_name}: ${decrypted}`);
        } else {
            appendMessage(`${data.sender_name}: [Cannot decrypt message]`);
        }
    } catch (error) {
        appendMessage(`${data.sender_name}: [Decryption error]`);
    }
});

function register() {
    const username = document.getElementById('username').value;
    const publicKey = rsa.getPublicKey();
    socket.emit('register', { username, public_key: publicKey });
}

function sendMessage() {
    const recipientId = document.getElementById('clients').value;
    const message = document.getElementById('message').value;
    socket.emit('send_message', { recipient_id: recipientId, message });
    appendMessage(`You: ${message}`);
    document.getElementById('message').value = '';
}

function appendMessage(message) {
    const chat = document.getElementById('chat');
    chat.innerHTML += `<div>${message}</div>`;
    chat.scrollTop = chat.scrollHeight;
}

function exportKeys() {
    const publicKey = rsa.getPublicKey();
    const privateKey = rsa.getPrivateKey();
    const blob = new Blob([`Public Key:\n${publicKey}\n\nPrivate Key:\n${privateKey}`], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'keys.txt';
    link.click();
}
