document.getElementById('chat-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    const chatMessages = document.getElementById('chat-messages');
    const userMessageDiv = document.createElement('div');
    userMessageDiv.textContent = 'You: ' + message;
    chatMessages.appendChild(userMessageDiv);

    const response = await fetch('/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `message=${encodeURIComponent(message)}`
    });
    const data = await response.json();

    const botMessageDiv = document.createElement('div');
    botMessageDiv.innerHTML = 'Bot: ' + data.response;
    chatMessages.appendChild(botMessageDiv);

    input.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;
});