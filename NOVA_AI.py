
import os
import uuid
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

from flask import Flask, request, jsonify, session, render_template_string
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError

# ==========================================
# CONFIGURATION
# ==========================================

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "nova-development-key-change-me")

client = genai.Client()

PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"

PERSONALITY = """
You are NOVA, an AI assistant created by NV STUDIOS.

CORE RULES:
- Prioritize human life and safety.
- Never facilitate harm or illegal activity.
- Be helpful, accurate and friendly.
- Never invent information.

DEFAULT MODE:
- Professional and friendly.
- Use proper grammar.
- Explain clearly.

GET MODE:
- Talk like Gen Z / Gen Alpha.
- Keep answers short, usually 1-2 lines.
- Occasionally say bro, twin and homie.
- Be funny and slightly corny.
- Use emojis sparingly: 😭 ✌️ 🫩 🥀 💔
- Never use 😎.
- You can disagree with the user.

Safety and accuracy always come first.
"""

# In-memory chat storage.
# Conversations reset when the server restarts.

chats = {}


def create_chat(model=PRIMARY_MODEL):
    return client.chats.create(
        model=model,
        config={"system_instruction": PERSONALITY}
    )


# ==========================================
# PYTHON-GENERATED WEB INTERFACE
# ==========================================

HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVA AI | NV STUDIOS</title>

<style>
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    background: #080c15;
    color: #edf4ff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    height: 100vh;
    overflow: hidden;
}

#loader {
    position: fixed;
    inset: 0;
    background: #080c15;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    transition: opacity .6s;
}

.loader-logo {
    font-size: 48px;
    font-weight: 800;
    color: #51dfc0;
    letter-spacing: 8px;
    animation: pulse 1.5s infinite;
}

.loader-text {
    color: #8393aa;
    margin-top: 20px;
    font-size: 12px;
    letter-spacing: 4px;
}

.loader-bar {
    margin-top: 30px;
    width: 160px;
    height: 3px;
    background: #202b3d;
    border-radius: 10px;
    overflow: hidden;
}

.loader-progress {
    width: 40%;
    height: 100%;
    background: #51dfc0;
    animation: loading 1.2s infinite ease-in-out;
}

@keyframes pulse {
    50% { opacity: .45; }
}

@keyframes loading {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(300%); }
}

.app {
    display: flex;
    height: 100vh;
}

.sidebar {
    width: 245px;
    background: #101520;
    border-right: 1px solid #242e40;
    padding: 25px 18px;
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
}

.logo {
    color: #51dfc0;
    font-size: 27px;
    font-weight: 850;
    letter-spacing: 3px;
}

.brand {
    color: #728198;
    font-size: 9px;
    letter-spacing: 3px;
    margin-top: 8px;
}

.new-chat {
    background: #202b3c;
    color: white;
    border: 1px solid #35465c;
    padding: 13px;
    border-radius: 10px;
    margin-top: 35px;
    cursor: pointer;
    font-size: 13px;
    text-align: left;
    transition: .2s;
}

.new-chat:hover {
    background: #2c3c52;
    border-color: #51dfc0;
}

.sidebar-footer {
    margin-top: auto;
    color: #66748a;
    font-size: 11px;
    line-height: 1.8;
}

.main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    position: relative;
}

.topbar {
    height: 72px;
    padding: 0 30px;
    border-bottom: 1px solid #202b3b;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.top-title {
    font-size: 18px;
    font-weight: 750;
    letter-spacing: 1px;
}

.online {
    color: #51dfc0;
    font-size: 11px;
    font-weight: 700;
}

.mode-area {
    padding: 17px 30px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #202b3b;
}

.mode-name {
    font-size: 12px;
    font-weight: 700;
}

.mode-description {
    color: #7b8ba2;
    font-size: 11px;
    margin-top: 5px;
}

.toggle {
    width: 44px;
    height: 24px;
    position: relative;
}

.toggle input {
    display: none;
}

.switch {
    position: absolute;
    inset: 0;
    background: #303a4c;
    border-radius: 30px;
    cursor: pointer;
    transition: .3s;
}

.switch:before {
    content: "";
    position: absolute;
    height: 18px;
    width: 18px;
    left: 3px;
    top: 3px;
    border-radius: 50%;
    background: white;
    transition: .3s;
}

.toggle input:checked + .switch {
    background: #42c9aa;
}

.toggle input:checked + .switch:before {
    transform: translateX(20px);
}

.chat {
    flex: 1;
    overflow-y: auto;
    padding: 30px max(25px, 8%);
    scroll-behavior: smooth;
}

.welcome {
    text-align: center;
    margin: 75px auto 45px;
    animation: fadeIn .7s ease;
}

.welcome h1 {
    font-size: clamp(30px, 5vw, 48px);
    letter-spacing: 3px;
    color: #51dfc0;
}

.welcome p {
    color: #8594a9;
    margin-top: 12px;
    font-size: 14px;
}

.message {
    margin-bottom: 28px;
    animation: fadeIn .3s ease;
}

.message.user {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
}

.message.ai {
    display: block;
}

.sender {
    font-size: 11px;
    font-weight: 750;
    color: #51dfc0;
    margin-bottom: 9px;
    letter-spacing: 1px;
}

.user .sender {
    color: #8cebd8;
}

.user .content {
    background: #203b48;
    border: 1px solid #345c68;
    border-radius: 15px 15px 3px 15px;
    padding: 13px 17px;
    max-width: min(75%, 650px);
}

.ai .content {
    padding: 0;
    color: #e1e9f4;
    line-height: 1.8;
    font-size: 14px;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.timestamp {
    color: #69778c;
    font-size: 9px;
    margin-top: 8px;
}

.user .timestamp {
    text-align: right;
}

.input-area {
    padding: 15px 30px 20px;
    border-top: 1px solid #202b3b;
}

.input-box {
    max-width: 900px;
    margin: auto;
    display: flex;
    align-items: center;
    gap: 10px;
    background: #151d2b;
    border: 1px solid #2b394e;
    border-radius: 15px;
    padding: 9px 10px 9px 17px;
    transition: .2s;
}

.input-box:focus-within {
    border-color: #51dfc0;
    box-shadow: 0 0 20px #51dfc015;
}

#messageInput {
    flex: 1;
    resize: none;
    background: transparent;
    border: none;
    outline: none;
    color: white;
    font: inherit;
    font-size: 14px;
    min-height: 40px;
    max-height: 120px;
    padding: 10px 0;
}

#messageInput::placeholder {
    color: #718198;
}

.send {
    height: 43px;
    width: 45px;
    border: none;
    border-radius: 10px;
    background: #51dfc0;
    color: #071711;
    font-size: 20px;
    font-weight: bold;
    cursor: pointer;
    transition: .2s;
}

.send:hover {
    background: #79f2d7;
    transform: scale(1.04);
}

.send:disabled {
    opacity: .4;
    cursor: not-allowed;
}

.typing {
    color: #51dfc0;
    font-size: 12px;
    margin: 0 auto 10px;
    max-width: 900px;
    display: none;
}

.bottom-note {
    text-align: center;
    color: #58677d;
    font-size: 9px;
    letter-spacing: 2px;
    margin-top: 12px;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

@media(max-width: 650px) {
    .sidebar {
        width: 65px;
        padding: 20px 9px;
        align-items: center;
    }

    .logo {
        font-size: 19px;
        letter-spacing: 0;
    }

    .brand, .sidebar-footer {
        display: none;
    }

    .new-chat {
        font-size: 0;
        width: 45px;
        text-align: center;
        padding: 13px 0;
    }

    .new-chat:after {
        content: "+";
        font-size: 20px;
    }

    .topbar {
        padding: 0 15px;
    }

    .mode-area {
        padding: 14px 15px;
    }

    .chat {
        padding: 20px 15px;
    }

    .input-area {
        padding: 12px;
    }

    .user .content {
        max-width: 90%;
    }
}
</style>
</head>

<body>

<div id="loader">
    <div class="loader-logo">✦ NOVA</div>
    <div class="loader-text">INITIALIZING INTELLIGENCE</div>
    <div class="loader-bar">
        <div class="loader-progress"></div>
    </div>
</div>

<div class="app">

    <aside class="sidebar">

        <div class="logo">✦ NOVA</div>
        <div class="brand">NV STUDIOS</div>

        <button class="new-chat" onclick="newChat()">
            + &nbsp; New Chat
        </button>

        <div class="sidebar-footer">
            <b>NV STUDIOS</b><br>
            NOVA AI WEB<br>
            VERSION 1.0
        </div>

    </aside>

    <main class="main">

        <header class="topbar">
            <div class="top-title">NOVA AI</div>
            <div class="online" id="status">● ONLINE</div>
        </header>

        <section class="mode-area">

            <div>
                <div class="mode-name">GET MODE</div>
                <div class="mode-description" id="modeDescription">
                    Professional personality
                </div>
            </div>

            <label class="toggle">
                <input type="checkbox" id="modeToggle"
                       onchange="changeMode()">
                <span class="switch"></span>
            </label>

        </section>

        <section class="chat" id="chat">

            <div class="welcome" id="welcome">
                <h1>✦ NOVA</h1>
                <p>Your intelligence. Your universe.</p>
            </div>

        </section>

        <div class="typing" id="typing">
            ✦ NOVA is thinking...
        </div>

        <section class="input-area">

            <div class="input-box">

                <textarea
                    id="messageInput"
                    placeholder="Message NOVA..."
                    rows="1"
                    onkeydown="handleKey(event)"
                ></textarea>

                <button class="send" id="sendButton"
                        onclick="sendMessage()">➤</button>

            </div>

            <div class="bottom-note">
                NOVA AI · POWERED BY GEMINI · NV STUDIOS
            </div>

        </section>

    </main>

</div>

<script>
let conversationId = null;
let busy = false;

window.addEventListener("load", () => {
    setTimeout(() => {
        const loader = document.getElementById("loader");
        loader.style.opacity = "0";
        setTimeout(() => loader.remove(), 600);
    }, 1000);

    newChat();
});

function handleKey(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function changeMode() {
    const active = document.getElementById("modeToggle").checked;

    document.getElementById("modeDescription").textContent =
        active ? "Casual personality activated 🔥" :
                 "Professional personality";
}

function addMessage(sender, message, type) {

    document.getElementById("welcome").style.display = "none";

    const chat = document.getElementById("chat");

    const row = document.createElement("div");
    row.className = "message " + type;

    const name = document.createElement("div");
    name.className = "sender";
    name.textContent = sender;

    const content = document.createElement("div");
    content.className = "content";
    content.textContent = message;

    const timestamp = document.createElement("div");
    timestamp.className = "timestamp";
    timestamp.textContent = new Date().toLocaleTimeString(
        [], {hour: "2-digit", minute: "2-digit"}
    );

    row.appendChild(name);
    row.appendChild(content);
    row.appendChild(timestamp);

    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;
}

async function sendMessage() {

    if (busy) return;

    const input = document.getElementById("messageInput");
    const message = input.value.trim();

    if (!message) return;

    busy = true;

    document.getElementById("sendButton").disabled = true;
    document.getElementById("status").textContent = "● THINKING";
    document.getElementById("typing").style.display = "block";

    addMessage("YOU", message, "user");

    input.value = "";

    try {

        const response = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message: message,
                get_mode: document.getElementById("modeToggle").checked,
                conversation_id: conversationId
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Something went wrong.");
        }

        conversationId = data.conversation_id;

        addMessage("✦ NOVA", data.reply, "ai");

    } catch (error) {

        addMessage("NOVA ERROR", error.message, "ai");

    } finally {

        busy = false;
        document.getElementById("sendButton").disabled = false;
        document.getElementById("typing").style.display = "none";
        document.getElementById("status").textContent = "● ONLINE";

    }
}

async function newChat() {

    if (busy) return;

    try {

        const response = await fetch("/new-chat", {
            method: "POST"
        });

        const data = await response.json();

        conversationId = data.conversation_id;

        const chat = document.getElementById("chat");
        chat.innerHTML = "";

        const welcome = document.createElement("div");
        welcome.className = "welcome";
        welcome.id = "welcome";
        welcome.innerHTML =
            "<h1>✦ NOVA</h1><p>Your intelligence. Your universe.</p>";

        chat.appendChild(welcome);

    } catch (error) {
        console.error(error);
    }
}
</script>

</body>
</html>
"""


# ==========================================
# ROUTES
# ==========================================

@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/new-chat", methods=["POST"])
def new_chat_route():

    conversation_id = str(uuid.uuid4())

    chats[conversation_id] = {
        "chat": create_chat(),
        "model": PRIMARY_MODEL
    }

    return jsonify({
        "conversation_id": conversation_id
    })


@app.route("/chat", methods=["POST"])
def chat_route():

    data = request.get_json(silent=True) or {}

    message = data.get("message", "").strip()
    conversation_id = data.get("conversation_id")

    get_mode = bool(data.get("get_mode", False))

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    if len(message) > 10000:
        return jsonify({"error": "Message is too long."}), 400

    if not conversation_id or conversation_id not in chats:
        return jsonify({"error": "Chat session expired. Start a new chat."}), 400

    chat_data = chats[conversation_id]

    mode_instruction = (
        "GET MODE IS ACTIVE. Use the casual personality."
        if get_mode
        else "DEFAULT MODE IS ACTIVE. Use the professional personality."
    )

    prompt = f"""
{mode_instruction}

Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M")}

User message:
{message}
"""

    try:

        try:

            response = chat_data["chat"].send_message(prompt)

        except ServerError:

            chat_data["model"] = FALLBACK_MODEL

            chat_data["chat"] = create_chat(FALLBACK_MODEL)

            response = chat_data["chat"].send_message(prompt)

        return jsonify({
            "reply": response.text or "I couldn't generate a response.",
            "conversation_id": conversation_id,
            "model": chat_data["model"]
        })

    except Exception as error:

        app.logger.exception("NOVA request failed")

        return jsonify({
            "error": "NOVA encountered an error. Please try again."
        }), 500


# ==========================================
# START SERVER
# ==========================================

if __name__ == "__main__":

    print("=" * 45)
    print("✦ NOVA AI | NV STUDIOS")
    print("NOVA WEB SERVER IS STARTING")
    print("=" * 45)

    app.run(
    host="0.0.0.0",
    port=5001,
    debug=False
)