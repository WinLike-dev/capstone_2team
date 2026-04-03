from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["debug"])

html_content = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Hub v2 - Debug Chat</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --panel-bg: #1e293b;
            --text-color: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --user-msg-bg: #3b82f6;
            --bot-msg-bg: #334155;
            --danger: #ef4444;
            --success: #22c55e;
            --warning: #f59e0b;
        }

        body {
            margin: 0;
            padding: 0;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
            width: 300px;
            background-color: var(--panel-bg);
            border-right: 1px solid var(--border-color);
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .sidebar h1 {
            font-size: 1.2rem;
            margin: 0;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .input-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .input-group label {
            font-size: 0.85rem;
            color: var(--text-muted);
            font-weight: 600;
        }

        .input-group input {
            background-color: var(--bg-color);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 10px;
            border-radius: 6px;
            font-size: 0.9 remit;
            outline: none;
            transition: border-color 0.2s;
        }

        .input-group input:focus {
            border-color: var(--primary);
        }

        .btn-reset {
            background-color: var(--border-color);
            color: var(--text-color);
            border: none;
            padding: 10px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: background-color 0.2s;
        }
        
        .btn-reset:hover {
            background-color: #475569;
        }

        .debug-panel {
            margin-top: auto;
            background-color: var(--bg-color);
            border-radius: 8px;
            padding: 15px;
            font-family: monospace;
            font-size: 0.8rem;
            color: #10b981;
            white-space: pre-wrap;
            overflow-y: auto;
            max-height: 300px;
            border: 1px solid var(--border-color);
        }

        /* Main Chat Area */
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .chat-messages {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .message-wrapper {
            display: flex;
            flex-direction: column;
            max-width: 80%;
        }

        .message-wrapper.user {
            align-self: flex-end;
            align-items: flex-end;
        }

        .message-wrapper.bot {
            align-self: flex-start;
            align-items: flex-start;
        }

        .message {
            padding: 12px 18px;
            border-radius: 12px;
            line-height: 1.5;
            font-size: 0.95rem;
            position: relative;
        }

        .user .message {
            background-color: var(--user-msg-bg);
            border-bottom-right-radius: 4px;
        }

        .bot .message {
            background-color: var(--bot-msg-bg);
            border-bottom-left-radius: 4px;
        }

        .meta-tags {
            display: flex;
            gap: 6px;
            margin-top: 6px;
            flex-wrap: wrap;
        }

        .tag {
            font-size: 0.7rem;
            padding: 3px 8px;
            border-radius: 12px;
            background-color: var(--bg-color);
            border: 1px solid var(--border-color);
            color: var(--text-muted);
        }

        .tag.intent {
            color: #a855f7;
            border-color: #a855f7;
            background-color: rgba(168, 85, 247, 0.1);
        }

        .tag.emotion {
            color: #ec4899;
            border-color: #ec4899;
            background-color: rgba(236, 72, 153, 0.1);
        }

        /* Input Area */
        .chat-input-area {
            padding: 20px 30px;
            background-color: var(--panel-bg);
            border-top: 1px solid var(--border-color);
        }

        .chat-form {
            display: flex;
            gap: 15px;
        }

        .chat-form input {
            flex: 1;
            background-color: var(--bg-color);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 15px;
            border-radius: 8px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .chat-form input:focus {
            border-color: var(--primary);
        }

        .btn-send {
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 0 25px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .btn-send:hover {
            background-color: var(--primary-hover);
        }
        
        .btn-send:disabled {
            background-color: var(--border-color);
            color: var(--text-muted);
            cursor: not-allowed;
        }

        .loading {
            align-self: flex-start;
            display: none;
            padding: 12px 18px;
            background-color: var(--bot-msg-bg);
            border-radius: 12px;
            border-bottom-left-radius: 4px;
            color: var(--text-muted);
            font-size: 0.9rem;
        }
        
        .loading::after {
            content: '';
            animation: dots 1.5s steps(5, end) infinite;
        }

        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60% { content: '...'; }
            80%, 100% { content: ''; }
        }

    </style>
</head>
<body>

    <div class="sidebar">
        <h1>🛠️ AI Hub v2 Debug</h1>
        
        <div class="input-group">
            <label for="userId">User ID</label>
            <input type="text" id="userId" value="test_user_001">
        </div>

        <div class="input-group">
            <label for="sessionId">Session ID (비우면 자동생성)</label>
            <input type="text" id="sessionId" placeholder="session-uuid">
        </div>

        <button class="btn-reset" id="btnReset">세션 초기화 (새 ID 할당)</button>

        <div style="flex:1"></div>

        <div class="input-group">
            <label>Last Response JSON</label>
            <div class="debug-panel" id="debugPanel">// Waiting for request...</div>
        </div>
    </div>

    <div class="chat-container">
        <div class="chat-messages" id="chatMessages">
            <div class="message-wrapper bot">
                <div class="message">안녕하세요! 테스트를 시작하려면 메시지를 입력해주세요.</div>
            </div>
        </div>
        
        <div class="loading" id="loadingIndicator">응답을 생성하고 있습니다</div>

        <div class="chat-input-area">
            <form class="chat-form" id="chatForm">
                <input type="text" id="msgInput" placeholder="메시지를 입력하세요 (의도, 감정 분석 테스트)..." autocomplete="off" required>
                <button type="submit" class="btn-send" id="btnSend">전송</button>
            </form>
        </div>
    </div>

<script>
    // uuid generator
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    const userIdEl = document.getElementById('userId');
    const sessionIdEl = document.getElementById('sessionId');
    const msgInput = document.getElementById('msgInput');
    const chatForm = document.getElementById('chatForm');
    const chatMessages = document.getElementById('chatMessages');
    const btnReset = document.getElementById('btnReset');
    const debugPanel = document.getElementById('debugPanel');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const btnSend = document.getElementById('btnSend');

    // Init session
    sessionIdEl.value = generateUUID();

    btnReset.addEventListener('click', () => {
        sessionIdEl.value = generateUUID();
        chatMessages.innerHTML = `
            <div class="message-wrapper bot">
                <div class="message">새로운 세션이 시작되었습니다. [${sessionIdEl.value}]</div>
            </div>
        `;
        debugPanel.textContent = '// Session Reset';
    });

    function appendMessage(text, sender, meta = null) {
        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${sender}`;
        
        // Escape HTML
        const safeText = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message';
        // Parse basic markdown like line breaks
        msgDiv.innerHTML = safeText.replace(/\\n/g, '<br>');
        
        wrapper.appendChild(msgDiv);

        if (meta && sender === 'bot') {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'meta-tags';
            
            if (meta.intent) {
                const iTag = document.createElement('span');
                iTag.className = 'tag intent';
                iTag.textContent = `🎯 ${meta.intent}`;
                metaDiv.appendChild(iTag);
            }
            
            if (meta.emotion && meta.emotion.label) {
                const iTag = document.createElement('span');
                iTag.className = 'tag emotion';
                iTag.textContent = `😊 ${meta.emotion.label} (${meta.emotion.intensity})`;
                metaDiv.appendChild(iTag);
            }
            
            wrapper.appendChild(metaDiv);
        }

        chatMessages.insertBefore(wrapper, loadingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = msgInput.value.trim();
        if (!message) return;

        const userId = userIdEl.value.trim() || 'default_user';
        const sessionId = sessionIdEl.value.trim();

        // UI Update
        msgInput.value = '';
        appendMessage(message, 'user');
        
        loadingIndicator.style.display = 'block';
        btnSend.disabled = true;
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    user_message: message,
                    session_id: sessionId || undefined
                })
            });

            const data = await response.json();
            
            loadingIndicator.style.display = 'none';
            btnSend.disabled = false;
            
            // Debug panel update
            debugPanel.textContent = JSON.stringify(data, null, 2);

            if (response.ok) {
                appendMessage(data.response, 'bot', {
                    intent: data.intent,
                    emotion: data.emotion
                });
                
                // Update session id if it was auto-generated by backend
                if (!sessionId && data.session_id) {
                    sessionIdEl.value = data.session_id;
                }
            } else {
                appendMessage(`오류 발생: ${data.error?.message || '알 수 없는 오류'}`, 'bot');
            }

        } catch (err) {
            loadingIndicator.style.display = 'none';
            btnSend.disabled = false;
            appendMessage(`네트워크 오류: ${err.message}`, 'bot');
            debugPanel.textContent = err.toString();
        }
        
        msgInput.focus();
    });
</script>
</body>
</html>
"""

@router.get("/debug", response_class=HTMLResponse)
async def get_debug_page():
    """웹 브라우저 디버깅 페이지"""
    return html_content
