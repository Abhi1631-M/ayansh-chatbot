/* ═══════════════════════════════════════════════════════════
   Ayansh Infotech Chatbot — Client-Side Logic
   ═══════════════════════════════════════════════════════════ */

const chatArea    = document.getElementById('chatArea');
const messageInput = document.getElementById('messageInput');
const sendBtn     = document.getElementById('sendBtn');
const welcomeCard = document.getElementById('welcomeCard');

let isWaiting = false;

/* ── Auto-resize textarea ──────────────────────────────── */
messageInput.addEventListener('input', () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
});

/* ── Send on Enter (Shift+Enter = new line) ────────────── */
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

/* ── Quick chip click ──────────────────────────────────── */
function sendQuickMessage(text) {
    messageInput.value = text;
    sendMessage();
}

/* ── Format time ───────────────────────────────────────── */
function getTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/* ── Simple markdown-to-HTML ───────────────────────────── */
function formatMarkdown(text) {
    let html = text
        // Bold: **text** or __text__
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.*?)__/g, '<strong>$1</strong>')
        // Italic: *text* or _text_
        .replace(/(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')
        // Inline code: `code`
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Line breaks
        .replace(/\n/g, '<br>');

    // Unordered lists: lines starting with * or -
    html = html.replace(/((?:(?:\*|-)\s.+?<br>?)+)/g, (match) => {
        const items = match
            .split('<br>')
            .filter(line => line.trim())
            .map(line => `<li>${line.replace(/^[\*\-]\s*/, '')}</li>`)
            .join('');
        return `<ul>${items}</ul>`;
    });

    return html;
}

/* ── Route label mapping ───────────────────────────────── */
function getRouteLabel(route) {
    const labels = {
        'inventory_api': 'Live Inventory',
        'knowledge_base_rag': 'Knowledge Base',
        'conversational': 'Conversational',
    };
    return labels[route] || route;
}

/* ── Add message to chat ───────────────────────────────── */
function addMessage(text, sender, route) {
    // Hide welcome card on first message
    if (welcomeCard) {
        welcomeCard.style.display = 'none';
    }

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;

    const avatarLabel = sender === 'bot' ? 'AI' : 'You';
    const formattedText = sender === 'bot' ? formatMarkdown(text) : text.replace(/\n/g, '<br>');

    let routeBadge = '';
    if (route && sender === 'bot') {
        routeBadge = `<span class="route-badge ${route}">${getRouteLabel(route)}</span>`;
    }

    msgDiv.innerHTML = `
        <div class="msg-avatar">${avatarLabel}</div>
        <div class="msg-content">
            <div class="msg-bubble">${formattedText}</div>
            <div class="msg-meta">
                ${routeBadge}
                <span>${getTime()}</span>
            </div>
        </div>
    `;

    chatArea.appendChild(msgDiv);
    scrollToBottom();
}

/* ── Typing indicator ──────────────────────────────────── */
function showTyping() {
    const div = document.createElement('div');
    div.className = 'typing-indicator';
    div.id = 'typingIndicator';
    div.innerHTML = `
        <div class="msg-avatar" style="background: var(--accent-gradient); color: white; font-size: 14px; font-weight: 700;">AI</div>
        <div class="typing-dots">
            <span></span><span></span><span></span>
        </div>
    `;
    chatArea.appendChild(div);
    scrollToBottom();
}

function hideTyping() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
}

/* ── Scroll to bottom ──────────────────────────────────── */
function scrollToBottom() {
    requestAnimationFrame(() => {
        chatArea.scrollTop = chatArea.scrollHeight;
    });
}

/* ── Send message ──────────────────────────────────────── */
async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || isWaiting) return;

    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Add user message
    addMessage(text, 'user');

    // Disable input
    isWaiting = true;
    sendBtn.disabled = true;
    messageInput.disabled = true;
    messageInput.placeholder = 'Waiting for response...';

    // Show typing
    showTyping();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text }),
        });

        const data = await response.json();

        hideTyping();

        if (data.error) {
            addMessage(`Sorry, something went wrong: ${data.error}`, 'bot');
        } else {
            addMessage(data.response, 'bot', data.route);
        }

    } catch (err) {
        hideTyping();
        addMessage('Sorry, I could not connect to the server. Please try again.', 'bot');
    } finally {
        isWaiting = false;
        sendBtn.disabled = false;
        messageInput.disabled = false;
        messageInput.placeholder = 'Ask about products, pricing, stock, specs...';
        messageInput.focus();
    }
}

/* ── Focus input on load ───────────────────────────────── */
messageInput.focus();
