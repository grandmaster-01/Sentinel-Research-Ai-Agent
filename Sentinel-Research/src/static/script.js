document.addEventListener('DOMContentLoaded', () => {

    // --- Elements ---
    const queryInput = document.getElementById('query-input');
    const searchBtn = document.getElementById('search-btn');
    const chatStream = document.getElementById('chat-stream');
    const welcomeScreen = document.getElementById('welcome-screen');
    const historyList = document.getElementById('history-list');
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.getElementById('status-text');
    const newChatBtn = document.getElementById('new-chat-btn');
    const chips = document.querySelectorAll('.chip');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');

    const modeToggleBtn = document.getElementById('mode-toggle-btn');
    const modeText = document.getElementById('mode-text');
    const modeIcon = document.getElementById('mode-icon');
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const attachmentPreview = document.getElementById('attachment-preview');
    const attachmentName = document.getElementById('attachment-name');
    const removeAttachment = document.getElementById('remove-attachment');

    // RAG Elements
    const ragToggle = document.getElementById('rag-toggle');
    const ragBody = document.getElementById('rag-body');
    const ragStats = document.getElementById('rag-stats');
    const ragFiles = document.getElementById('rag-files');
    const ragFileInput = document.getElementById('rag-file-input');
    const ragUploadStatus = document.getElementById('rag-upload-status');
    const ragStatusDot = document.getElementById('rag-status-dot');

    // ── Mode Configuration ─────────────────────────────────────────────────────
    const MODES = [
        {
            id: 'fast',
            label: 'Fast',
            icon: 'flash',
            model: 'Llama 3.2',
            statusText: 'Searching quickly...',
            cssClass: 'mode-fast',
        },
        {
            id: 'deep',
            label: 'Deep',
            icon: 'planet',
            model: 'Gemma 3',
            statusText: 'Researching deeply...',
            cssClass: 'mode-deep',
        },
        {
            id: 'rag',
            label: 'RAG',
            icon: 'library',
            model: 'Phi 3.5',
            statusText: 'Querying knowledge base...',
            cssClass: 'mode-rag',
        },
        {
            id: 'coding',
            label: 'Coding',
            icon: 'code-slash',
            model: 'Qwen 2.5',
            statusText: 'Generating code...',
            cssClass: 'mode-coding',
        },
    ];

    // --- State ---
    let currentTaskId = null;
    let isProcessing = false;
    let currentModeIndex = 0;
    let localChatHistory = [];
    let attachedFileContent = null;
    let attachedFileName = null;
    let sessionId = null;   // shared across all messages in one chat session
    let isSessionStart = true;   // true until first message of a new session is sent

    function currentMode() { return MODES[currentModeIndex]; }

    // --- Init ---
    updateModeUI();
    loadHistory();
    setupTheme();
    autoResizeTextarea();

    // --- Event Listeners ---

    searchBtn.addEventListener('click', () => submitQuery());
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitQuery();
        }
    });

    newChatBtn.addEventListener('click', () => {
        welcomeScreen.classList.remove('hidden');
        chatStream.classList.add('hidden');
        chatStream.innerHTML = '';
        queryInput.value = '';
        currentTaskId = null;
        sessionId = null;
        isSessionStart = true;
        localChatHistory = [];
        clearAttachment();
        autoResizeTextarea();
    });

    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            const text = chip.querySelector('span')?.textContent || chip.textContent;
            queryInput.value = text;
            // Auto-switch to coding mode when coding chip is clicked
            if (text.toLowerCase().includes('python') || text.toLowerCase().includes('code') || text.toLowerCase().includes('scraper')) {
                const codingIdx = MODES.findIndex(m => m.id === 'coding');
                if (codingIdx !== -1) { currentModeIndex = codingIdx; updateModeUI(); }
            }
            submitQuery();
        });
    });

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    }

    // Cycle through MODES on click
    if (modeToggleBtn) {
        modeToggleBtn.addEventListener('click', () => {
            currentModeIndex = (currentModeIndex + 1) % MODES.length;
            updateModeUI();
        });
    }

    function updateModeUI() {
        if (!modeText || !modeIcon || !modeToggleBtn) return;
        const m = currentMode();
        modeText.textContent = m.label;
        modeIcon.setAttribute('name', m.icon);

        // Clear all mode classes and apply current
        MODES.forEach(mode => modeToggleBtn.classList.remove(mode.cssClass));
        modeToggleBtn.classList.add(m.cssClass);
    }

    // --- File Upload ---
    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
                const maxSize = 5 * 1024 * 1024;

                if (file.size > maxSize) {
                    showToast('File too large. Max 5MB.');
                    fileInput.value = '';
                    return;
                }

                const reader = new FileReader();
                reader.onload = (ev) => {
                    attachedFileContent = ev.target.result;
                    attachedFileName = file.name;
                    attachmentName.textContent = file.name;
                    attachmentPreview.classList.remove('hidden');
                    uploadBtn.style.color = 'var(--accent)';
                };
                reader.onerror = () => showToast('Failed to read file.');
                reader.readAsText(file);
            }
        });
    }

    if (removeAttachment) {
        removeAttachment.addEventListener('click', clearAttachment);
    }

    function clearAttachment() {
        attachedFileContent = null;
        attachedFileName = null;
        fileInput.value = '';
        attachmentPreview.classList.add('hidden');
        uploadBtn.style.color = '';
    }

    // --- Auto-resize Textarea ---
    function autoResizeTextarea() {
        queryInput.addEventListener('input', () => {
            queryInput.style.height = 'auto';
            queryInput.style.height = Math.min(queryInput.scrollHeight, 150) + 'px';
        });
    }

    // --- Core Logic ---

    async function submitQuery() {
        const query = queryInput.value.trim();
        if (!query || isProcessing) return;

        const mode = currentMode();
        isProcessing = true;
        welcomeScreen.classList.add('hidden');
        chatStream.classList.remove('hidden');
        searchBtn.classList.add('disabled');
        statusIndicator.classList.remove('hidden');
        statusText.textContent = mode.statusText;

        let displayQuery = query;
        if (attachedFileName) {
            displayQuery = `📎 ${attachedFileName}\n\n${query}`;
        }
        addMessage('user', displayQuery);
        localChatHistory.push(`User: ${query}`);
        queryInput.value = '';
        queryInput.style.height = 'auto';

        const loadingId = addMessage('ai', '', true);

        try {
            const requestBody = {
                query,
                mode: mode.id,
                chat_history: localChatHistory,
                session_id: sessionId,     // null on first message; set for follow-ups
            };

            if (attachedFileContent) {
                requestBody.file_content = attachedFileContent;
            }

            const response = await fetch('/research', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody),
            });

            if (!response.ok) throw new Error('Server Error');
            const data = await response.json();
            currentTaskId = data.task_id;

            clearAttachment();
            pollStatus(currentTaskId, loadingId, mode);

            // Track session: first message sets sessionId for all follow-ups
            if (isSessionStart) {
                sessionId = currentTaskId;
                isSessionStart = false;
            }

        } catch (error) {
            updateMessage(loadingId, `<p style="color:#ff5546;">Error: ${error.message}</p>`);
            isProcessing = false;
            searchBtn.classList.remove('disabled');
            statusIndicator.classList.add('hidden');
        }
    }

    async function pollStatus(taskId, messageElementId, mode) {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`/research/${taskId}`);
                const data = await response.json();

                if (data.status === 'completed') {
                    clearInterval(interval);
                    const html = renderMarkdown(data.result || 'No result.');
                    const badge = `<div class="model-badge model-badge--${mode.id}">`
                        + `<ion-icon name="${mode.icon}"></ion-icon>`
                        + `<span>${mode.model}</span></div>`;
                    updateMessage(messageElementId, badge + html);
                    localChatHistory.push(`AI: ${data.result}`);
                    isProcessing = false;
                    searchBtn.classList.remove('disabled');
                    statusIndicator.classList.add('hidden');
                    // Only refresh history sidebar on first message of session
                    if (data.task_id === sessionId || !data.session_id) {
                        loadHistory();
                    }
                } else if (data.status === 'failed') {
                    clearInterval(interval);
                    updateMessage(messageElementId, `<p style="color:#ff5546;">Failed: ${data.error || 'Unknown error'}</p>`);
                    isProcessing = false;
                    searchBtn.classList.remove('disabled');
                    statusIndicator.classList.add('hidden');
                } else {
                    statusText.textContent = capitalize(data.status) + '...';
                }
            } catch (e) { /* ignore transient */ }
        }, 1500);
    }

    // --- History ---

    async function loadHistory() {
        try {
            const response = await fetch('/history');
            const history = await response.json();

            historyList.innerHTML = '';

            if (history.length === 0) {
                historyList.innerHTML = `
                    <div class="history-placeholder">
                        <ion-icon name="chatbubbles-outline"></ion-icon>
                        <span>No conversations yet</span>
                    </div>`;
                return;
            }

            history.forEach(item => {
                const div = document.createElement('div');
                div.className = 'history-item';
                div.innerHTML = `
                    <span>${escapeHtml(item.query)}</span>
                    <button class="delete-btn" title="Delete"><ion-icon name="trash-outline"></ion-icon></button>
                `;
                div.querySelector('span').addEventListener('click', () => loadPastChat(item.task_id, item.query));
                div.querySelector('.delete-btn').addEventListener('click', (e) => {
                    e.stopPropagation();
                    deleteChat(item.task_id);
                });
                historyList.appendChild(div);
            });
        } catch (e) {
            console.error('Failed to load history', e);
        }
    }

    async function deleteChat(taskId) {
        if (!confirm('Delete this conversation?')) return;
        try {
            const res = await fetch(`/history/${taskId}`, { method: 'DELETE' });
            if (res.ok) {
                loadHistory();
                if (currentTaskId === taskId) newChatBtn.click();
            }
        } catch (e) { showToast('Failed to delete.'); }
    }

    // Restore a full conversation session from history
    async function loadPastChat(sessionId, firstQuery) {
        welcomeScreen.classList.remove('hidden');
        chatStream.classList.remove('hidden');
        chatStream.innerHTML = '';
        welcomeScreen.classList.add('hidden');
        localChatHistory = [];

        try {
            const res = await fetch(`/session/${sessionId}`);
            const messages = await res.json();

            if (!messages || messages.length === 0) {
                // Fallback: just show the first message
                addMessage('user', firstQuery);
                addMessage('ai', 'Session data not found.');
                return;
            }

            for (const msg of messages) {
                addMessage('user', msg.query);
                // Pick mode badge based on model field
                const modeObj = MODES.find(m => msg.model && msg.model.includes(m.model.split(' ')[0].toLowerCase()))
                    || MODES[1];
                const badge = `<div class="model-badge model-badge--${modeObj.id}">`
                    + `<ion-icon name="${modeObj.icon}"></ion-icon>`
                    + `<span>${msg.model || modeObj.model}</span></div>`;
                const html = renderMarkdown(msg.report || '');
                addMessage('ai', badge + html);
                localChatHistory.push(`User: ${msg.query}`);
                localChatHistory.push(`AI: ${msg.report}`);
            }

            // Resume session so follow-ups are still linked
            window.sessionId = sessionId;
            window.isSessionStart = false;

        } catch (e) {
            addMessage('ai', 'Error loading conversation.');
        }
    }

    // ── Markdown + Code Copy ──────────────────────────────────────────────────

    function renderMarkdown(text) {
        const html = marked.parse(text || '');
        // Inject copy button into every <pre><code> block
        return html.replace(
            /<pre><code([^>]*)>([\/\s\S]*?)<\/code><\/pre>/g,
            (_, attrs, code) =>
                `<div class="code-block-wrapper">`
                + `<button class="copy-code-btn" onclick="copyCode(this)" title="Copy code">`
                + `<ion-icon name="copy-outline"></ion-icon><span>Copy</span></button>`
                + `<pre><code${attrs}>${code}</code></pre></div>`
        );
    }

    function addMessage(role, content, isLoading = false) {
        const id = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 4);
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.id = id;

        const avatar = document.createElement('div');
        avatar.className = `avatar ${role}`;
        avatar.innerHTML = role === 'ai'
            ? '<ion-icon name="planet"></ion-icon>'
            : '<ion-icon name="person"></ion-icon>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content markdown-body';
        if (isLoading) {
            contentDiv.innerHTML = `<div class="loader-sm"></div>`;
        } else {
            contentDiv.innerHTML = role === 'user'
                ? escapeHtml(content).replace(/\n/g, '<br>')
                : content;
        }

        div.appendChild(avatar);
        div.appendChild(contentDiv);
        chatStream.appendChild(div);
        chatStream.scrollTop = chatStream.scrollHeight;
        return id;
    }

    function updateMessage(id, html) {
        const el = document.getElementById(id);
        if (el) {
            el.querySelector('.message-content').innerHTML = html;
            chatStream.scrollTop = chatStream.scrollHeight;
        }
    }

    // --- Theme ---
    function setupTheme() {
        const savedTheme = localStorage.getItem('sentinel-theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);
        themeIcon.setAttribute('name', savedTheme === 'dark' ? 'moon' : 'sunny');

        themeToggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('sentinel-theme', next);
            themeIcon.setAttribute('name', next === 'dark' ? 'moon' : 'sunny');
        });
    }

    // --- Helpers ---
    function capitalize(str) { return str ? str.charAt(0).toUpperCase() + str.slice(1) : ''; }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function showToast(msg) {
        const toast = document.createElement('div');
        toast.textContent = msg;
        toast.style.cssText = `
            position:fixed;bottom:5rem;left:50%;transform:translateX(-50%);
            background:var(--surface);color:var(--text-primary);
            padding:0.75rem 1.5rem;border-radius:100px;font-size:0.85rem;
            border:1px solid var(--border);box-shadow:var(--shadow-md);
            z-index:999;animation:msgSlideIn 0.3s ease-out;
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    // ── RAG Knowledge Base ────────────────────────────────────────────────────

    let ragOpen = true;
    if (ragToggle) {
        ragToggle.addEventListener('click', () => {
            ragOpen = !ragOpen;
            ragBody.style.display = ragOpen ? '' : 'none';
        });
    }

    async function loadKBStatus() {
        try {
            const res = await fetch('/ingest/status');
            const data = await res.json();

            if (ragStatusDot) ragStatusDot.className = 'rag-status-dot ' + (data.status || 'empty');

            if (ragStats) {
                if (data.status === 'ready') ragStats.textContent = `${data.count} chunks indexed`;
                else if (data.status === 'empty') ragStats.textContent = 'No documents ingested yet';
                else ragStats.textContent = data.message || 'Unknown status';
            }
        } catch (e) {
            if (ragStats) ragStats.textContent = 'KB unavailable';
        }
    }

    async function loadKBFiles() {
        try {
            const res = await fetch('/ingest/files');
            const data = await res.json();
            if (!ragFiles) return;
            ragFiles.innerHTML = '';
            if (data.files && data.files.length > 0) {
                data.files.forEach(f => {
                    const item = document.createElement('div');
                    item.className = 'rag-file-item';
                    item.innerHTML = `<ion-icon name="document-text-outline"></ion-icon>`
                        + `<span>${escapeHtml(f.name)}</span>`
                        + `<span style="margin-left:auto;color:var(--text-muted)">${f.size_kb}KB</span>`;
                    ragFiles.appendChild(item);
                });
            }
        } catch (e) { /* silent */ }
    }

    if (ragFileInput) {
        ragFileInput.addEventListener('change', async (e) => {
            if (!e.target.files.length) return;
            const file = e.target.files[0];

            if (ragUploadStatus) {
                ragUploadStatus.textContent = `Uploading ${file.name}...`;
                ragUploadStatus.className = 'rag-upload-status';
                ragUploadStatus.classList.remove('hidden');
            }

            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/ingest', { method: 'POST', body: formData });
                const data = await res.json();

                if (res.ok) {
                    if (ragUploadStatus) {
                        ragUploadStatus.textContent = `✓ Indexing ${file.name}...`;
                        ragUploadStatus.className = 'rag-upload-status success';
                    }
                    setTimeout(() => {
                        loadKBStatus();
                        loadKBFiles();
                        if (ragUploadStatus) ragUploadStatus.classList.add('hidden');
                    }, 3000);
                } else {
                    throw new Error(data.detail || 'Upload failed');
                }
            } catch (err) {
                if (ragUploadStatus) {
                    ragUploadStatus.textContent = `✗ ${err.message}`;
                    ragUploadStatus.className = 'rag-upload-status error';
                }
            }

            ragFileInput.value = '';
        });
    }

    loadKBStatus();
    loadKBFiles();
});

// ── Global: copy code block to clipboard ──────────────────────────────────────
function copyCode(btn) {
    const code = btn.parentElement.querySelector('code');
    if (!code) return;
    navigator.clipboard.writeText(code.innerText).then(() => {
        btn.innerHTML = '<ion-icon name="checkmark-outline"></ion-icon><span>Copied!</span>';
        setTimeout(() => {
            btn.innerHTML = '<ion-icon name="copy-outline"></ion-icon><span>Copy</span>';
        }, 2000);
    }).catch(() => {
        // Fallback for browsers without clipboard API
        const ta = document.createElement('textarea');
        ta.value = code.innerText;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        ta.remove();
        btn.innerHTML = '<ion-icon name="checkmark-outline"></ion-icon><span>Copied!</span>';
        setTimeout(() => {
            btn.innerHTML = '<ion-icon name="copy-outline"></ion-icon><span>Copy</span>';
        }, 2000);
    });
}
