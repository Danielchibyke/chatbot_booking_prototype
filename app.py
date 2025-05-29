# app.py

from flask import Flask, render_template, request, jsonify, session
from chatbot_agent import get_chatbot_response
import os
from dotenv import load_dotenv
from datetime import timedelta
import random

load_dotenv() # Load environment variables

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
app.permanent_session_lifetime = timedelta(hours=2)

# Basic HTML template for the chat interface
# Create a 'templates' folder and put this HTML inside 'index.html'
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Appointment Bot</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .chat-container { background-color: white; width: 400px; height: 600px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); display: flex; flex-direction: column; overflow: hidden; }
        .chat-header { background-color: #007bff; color: white; padding: 15px; text-align: center; font-size: 1.2em; border-top-left-radius: 8px; border-top-right-radius: 8px; }
        .chat-messages { flex-grow: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; }
        .message { margin-bottom: 10px; padding: 8px 12px; border-radius: 15px; max-width: 80%; word-wrap: break-word; }
        .user-message { background-color: #dcf8c6; align-self: flex-end; }
        .bot-message { background-color: #e0e0e0; align-self: flex-start; }
        .chat-input-container { display: flex; padding: 15px; border-top: 1px solid #eee; }
        .chat-input { flex-grow: 1; padding: 10px; border: 1px solid #ddd; border-radius: 20px; outline: none; }
        .chat-send-btn { background-color: #007bff; color: white; border: none; padding: 10px 15px; border-radius: 20px; margin-left: 10px; cursor: pointer; }
        .chat-send-btn:hover { background-color: #0056b3; }
        .chat-clear-btn {
    background-color: #ff4444;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 20px;
    margin-left: 10px;
    cursor: pointer;
}
.chat-clear-btn:hover {
    background-color: #cc0000;
}
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">Appointment Booking Bot</div>
        <div class="chat-messages" id="chatMessages"></div>
        <div class="chat-input-container">
            <input type="text" id="userInput" class="chat-input" placeholder="Type your message..." autofocus>
            <button id="sendBtn" class="chat-send-btn">Send</button>
        </div>
    </div>

    <script>
        const chatMessages = document.getElementById('chatMessages');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');

        function appendMessage(sender, message) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', `${sender}-message`);
            messageDiv.textContent = message;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll to bottom
        }

        async function sendMessage() {
            const message = userInput.value.trim();
            if (message === '') return;

            appendMessage('user', message);
            userInput.value = '';

            // Simulate bot typing
            appendMessage('bot', 'Typing...');
            const botThinkingMessage = chatMessages.lastChild;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                const data = await response.json();
                botThinkingMessage.remove(); // Remove "Typing..."
                appendMessage('bot', data.response);
            } catch (error) {
                console.error('Error:', error);
                botThinkingMessage.remove(); // Remove "Typing..."
                appendMessage('bot', "Sorry, I'm having trouble connecting right now.");
            }
        }

        sendBtn.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });

        // Initial bot greeting
        appendMessage('bot', 'Hello! How can I help you book an appointment today?');

        // Add this to your existing JavaScript in templates/index.html

// Replace the existing DOMContentLoaded event listener with this:
document.addEventListener('DOMContentLoaded', function() {
    // Load chat history from server
    fetch('/load-history')
        .then(response => response.json())
        .then(data => {
            // Clear any existing messages (like the hardcoded greeting)
            chatMessages.innerHTML = '';
            
            // Add all messages from history
            data.history.forEach(msg => {
                appendMessage(msg.sender, msg.message);
            });
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });
});


// Add clear chat functionality
function clearChat() {
    fetch('/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    }).then(() => {
        chatMessages.innerHTML = '';
        fetch('/load-history')
            .then(response => response.json())
            .then(data => {
                appendMessage('bot', data.history[0].message);
            });
    });
}

// Add clear button to your HTML
const clearBtn = document.createElement('button');
clearBtn.id = 'clearBtn';
clearBtn.className = 'chat-clear-btn';
clearBtn.textContent = 'Clear';
document.querySelector('.chat-input-container').appendChild(clearBtn);
clearBtn.addEventListener('click', clearChat);
    </script>
</body>
</html>
"""

# Create a 'templates' directory if it doesn't exist
os.makedirs('templates', exist_ok=True)
with open('templates/index.html', 'w') as f:
    f.write(HTML_TEMPLATE)


@app.route('/')
def index():
    if 'chat_history' not in session:
        session['chat_history'] = [{
            "sender": "bot", 
            "message": random.choice([
                "Hello! I'm your booking assistant. How can I help today?",
                "Hi there! Ready to book an appointment?",
                "Welcome! What can I help you schedule today?"
            ])
        }]
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"response": "Please enter a message."})

    bot_response = get_chatbot_response(user_message, session['chat_history'])
    
    session['chat_history'].extend([
        {"sender": "user", "message": user_message},
        {"sender": "bot", "message": bot_response}
    ])
    session.modified = True
    
    return jsonify({"response": bot_response})

@app.route('/clear', methods=['POST'])
def clear_chat():
    session['chat_history'] = [{
        "sender": "bot", 
        "message": random.choice([
            "Hello again! What can I help you with now?",
            "Hi there! What would you like to book today?",
            "Let's start fresh. How can I assist you?"
        ])
    }]
    session.modified = True
    return jsonify({"status": "success"})
# Load chat history on page load
@app.route('/load-history')
def load_history():
    if 'chat_history' not in session:
        session['chat_history'] = [{
            "sender": "bot", 
            "message": random.choice([
                "Hello! I'm your booking assistant. How can I help today?",
                "Hi there! Ready to book an appointment?",
                "Welcome! What can I help you schedule today?"
            ])
        }]
    return jsonify({"history": session['chat_history']})

if __name__ == '__main__':
    app.run(debug=True,  host='0.0.0.0')