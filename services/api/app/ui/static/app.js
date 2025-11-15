// API Base URL
const API_BASE = '/api';

// State
let currentConversationId = null;
let conversations = [];
let sourceDataCache = {}; // Cache for source data to avoid JSON serialization issues

// DOM Elements
const conversationsList = document.getElementById('conversationsList');
const messagesContainer = document.getElementById('messagesContainer');
const messageForm = document.getElementById('messageForm');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');
const startChatBtn = document.getElementById('startChatBtn');
const deleteChatBtn = document.getElementById('deleteChatBtn');
const emptyState = document.getElementById('emptyState');
const chatContainer = document.getElementById('chatContainer');
const chatTitle = document.getElementById('chatTitle');
const chatSubtitle = document.getElementById('chatSubtitle');
const maxResultsInput = document.getElementById('maxResults');
const sourceModal = document.getElementById('sourceModal');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
const modalCloseBtn = document.getElementById('modalCloseBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadConversations();
    setupEventListeners();
});

function setupEventListeners() {
    messageForm.addEventListener('submit', handleSendMessage);
    newChatBtn.addEventListener('click', createNewConversation);
    startChatBtn.addEventListener('click', createNewConversation);
    deleteChatBtn.addEventListener('click', deleteCurrentConversation);
    
    // Modal event listeners
    modalCloseBtn.addEventListener('click', closeModal);
    document.querySelector('.modal-overlay').addEventListener('click', closeModal);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && sourceModal.classList.contains('active')) {
            closeModal();
        }
    });
    
    // Auto-resize textarea
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';
    });
}

// API Functions
async function fetchAPI(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function loadConversations() {
    try {
        conversationsList.innerHTML = '<div class="loading">Loading conversations...</div>';
        const data = await fetchAPI(`${API_BASE}/conversations/`);
        conversations = data;
        renderConversations();
    } catch (error) {
        conversationsList.innerHTML = '<div class="loading">Failed to load conversations</div>';
    }
}

async function createNewConversation() {
    try {
        const title = `Chat ${new Date().toLocaleString()}`;
        const data = await fetchAPI(`${API_BASE}/conversations/`, {
            method: 'POST',
            body: JSON.stringify({ title }),
        });
        
        conversations.unshift(data);
        renderConversations();
        selectConversation(data.id);
    } catch (error) {
        alert('Failed to create conversation');
    }
}

async function deleteCurrentConversation() {
    if (!currentConversationId) return;
    
    if (!confirm('Are you sure you want to delete this conversation?')) return;
    
    try {
        await fetchAPI(`${API_BASE}/conversations/${currentConversationId}`, {
            method: 'DELETE',
        });
        
        conversations = conversations.filter(c => c.id !== currentConversationId);
        renderConversations();
        
        // Show empty state
        currentConversationId = null;
        showEmptyState();
    } catch (error) {
        alert('Failed to delete conversation');
    }
}

async function loadMessages(conversationId) {
    try {
        messagesContainer.innerHTML = '<div class="message-loading"><div class="spinner"></div>Loading messages...</div>';
        const messages = await fetchAPI(`${API_BASE}/conversations/${conversationId}/messages`);
        renderMessages(messages);
    } catch (error) {
        messagesContainer.innerHTML = '<div class="message-loading">Failed to load messages</div>';
    }
}

async function sendMessage(conversationId, query, maxResults, searchProvider) {
    try {
        const data = await fetchAPI(`${API_BASE}/conversations/${conversationId}/messages`, {
            method: 'POST',
            body: JSON.stringify({
                user_query: query,
                max_results: maxResults,
                search_provider: searchProvider
            }),
        });
        
        return data;
    } catch (error) {
        throw error;
    }
}

// UI Functions
function renderConversations() {
    if (conversations.length === 0) {
        conversationsList.innerHTML = '<div class="loading">No conversations yet.<br>Start a new chat!</div>';
        return;
    }
    
    conversationsList.innerHTML = conversations.map(conv => `
        <div class="conversation-item ${conv.id === currentConversationId ? 'active' : ''}" 
             data-id="${conv.id}"
             onclick="selectConversation(${conv.id})">
            <div class="conversation-title">${escapeHtml(conv.title)}</div>
            <div class="conversation-meta">
                <span>${conv.message_count || 0} messages</span>
                <span>${formatDate(conv.updated_at)}</span>
            </div>
        </div>
    `).join('');
}

function selectConversation(conversationId) {
    currentConversationId = conversationId;
    const conversation = conversations.find(c => c.id === conversationId);
    
    if (!conversation) return;
    
    // Update UI
    emptyState.style.display = 'none';
    chatContainer.style.display = 'flex';
    chatTitle.textContent = conversation.title;
    chatSubtitle.textContent = `${conversation.message_count || 0} messages`;
    
    // Update active state
    renderConversations();
    
    // Load messages
    loadMessages(conversationId);
    
    // Focus input
    messageInput.focus();
}

function renderMessages(messages) {
    if (messages.length === 0) {
        messagesContainer.innerHTML = '<div class="message-loading">No messages yet. Start by asking a question!</div>';
        return;
    }
    
    // Clear source data cache before rendering new messages
    sourceDataCache = {};
    
    messagesContainer.innerHTML = messages.map(msg => `
        <div class="message">
            <!-- User Query -->
            <div class="message-user">
                <div class="message-bubble">${escapeHtml(msg.user_query)}</div>
            </div>
            
            <!-- Agent Response -->
            <div class="message-agent">
                <div class="message-header">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                    ANIP Assistant • ${formatDate(msg.created_at)}
                </div>
                
                ${msg.summary ? `
                    <div class="message-summary">
                        <strong>Summary:</strong> ${escapeHtml(msg.summary)}
                    </div>
                ` : ''}
                
                ${msg.answer ? `
                    <div class="message-answer">
                        ${escapeHtml(msg.answer)}
                    </div>
                ` : ''}
                
                ${msg.query_intent ? `
                    <div style="margin-bottom: 1rem; font-size: 0.875rem; color: var(--text-secondary);">
                        <strong>Intent:</strong> ${escapeHtml(msg.query_intent)}
                    </div>
                ` : ''}
                
                <div class="message-sources">
                    ${renderSources(msg)}
                </div>
            </div>
        </div>
    `).join('');
    
    // Add event listeners for collapsible sources and source items
    attachSourceEventListeners();
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function renderSources(message) {
    let html = '';
    
    // DuckDuckGo Results
    if (message.duckduckgo_results && message.duckduckgo_results.length > 0) {
        html += `
            <div class="source-section" data-section-id="ddg-${Date.now()}">
                <div class="source-header">
                    <div class="source-header-left">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <path d="m21 21-4.35-4.35"></path>
                        </svg>
                        DuckDuckGo Results
                        <span class="source-count">${message.duckduckgo_count}</span>
                    </div>
                    <svg class="source-toggle" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </div>
                <div class="source-items expanded">
                    ${message.duckduckgo_results.map(result => renderSourceItem(result)).join('')}
                </div>
            </div>
        `;
    }
    
    // Database Results
    if (message.database_results && message.database_results.length > 0) {
        html += `
            <div class="source-section" data-section-id="db-${Date.now()}">
                <div class="source-header">
                    <div class="source-header-left">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
                            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
                            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
                        </svg>
                        Database Results
                        <span class="source-count">${message.database_count}</span>
                    </div>
                    <svg class="source-toggle" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </div>
                <div class="source-items expanded">
                    ${message.database_results.map(result => renderSourceItem(result)).join('')}
                </div>
            </div>
        `;
    }
    
    return html;
}

function renderSourceItem(result) {
    // Generate unique ID for this source item
    const sourceId = `source_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    // Store the full data in cache to avoid JSON serialization issues
    sourceDataCache[sourceId] = result;
    
    // Show preview of content (first 200 chars)
    const preview = result.content ? result.content.substring(0, 200) + (result.content.length > 200 ? '...' : '') : '';
    
    return `
        <div class="source-item" data-source-id="${sourceId}">
            <div class="source-item-title">
                ${escapeHtml(result.title)}
            </div>
            <div class="source-item-meta">
                ${result.source ? `<span>${escapeHtml(result.source)}</span>` : ''}
                ${result.topic ? `<span class="badge badge-topic">${escapeHtml(result.topic)}</span>` : ''}
                ${result.sentiment ? `<span class="badge badge-sentiment-${result.sentiment}">${escapeHtml(result.sentiment)}</span>` : ''}
                ${result.relevance_score ? `<span class="badge badge-relevance">Relevance: ${(result.relevance_score * 100).toFixed(0)}%</span>` : ''}
                ${result.published_at ? `<span>${formatDate(result.published_at)}</span>` : ''}
            </div>
            ${preview ? `
                <div class="source-item-snippet">${escapeHtml(preview)}</div>
            ` : ''}
        </div>
    `;
}

function showEmptyState() {
    emptyState.style.display = 'flex';
    chatContainer.style.display = 'none';
}

async function handleSendMessage(e) {
    e.preventDefault();
    
    const query = messageInput.value.trim();
    if (!query) return;
    
    if (!currentConversationId) {
        alert('Please select or create a conversation first');
        return;
    }
    
    const maxResults = parseInt(maxResultsInput.value) || 5;
    const searchProvider = document.querySelector('input[name="searchProvider"]:checked').value;
    
    // Disable input
    messageInput.disabled = true;
    sendBtn.disabled = true;
    
    // Add user message to UI immediately
    const userMessageHtml = `
        <div class="message">
            <div class="message-user">
                <div class="message-bubble">${escapeHtml(query)}</div>
            </div>
            <div class="message-loading">
                <div class="spinner"></div>
                Searching news sources...
            </div>
        </div>
    `;
    messagesContainer.insertAdjacentHTML('beforeend', userMessageHtml);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    try {
        // Send message
        await sendMessage(currentConversationId, query, maxResults, searchProvider);
        
        // Reload messages
        await loadMessages(currentConversationId);
        
        // Update conversation list
        await loadConversations();
        
    } catch (error) {
        alert('Failed to send message. Please try again.');
        console.error('Send message error:', error);
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

// Collapsible Sources and Modal Functions
function attachSourceEventListeners() {
    // Collapsible source headers
    document.querySelectorAll('.source-header').forEach(header => {
        header.addEventListener('click', toggleSourceSection);
    });
    
    // Source items - open modal
    document.querySelectorAll('.source-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const sourceId = item.getAttribute('data-source-id');
            if (sourceId && sourceDataCache[sourceId]) {
                openSourceModal(sourceDataCache[sourceId]);
            } else {
                console.error('Source data not found in cache:', sourceId);
            }
        });
    });
}

function toggleSourceSection(e) {
    const header = e.currentTarget;
    const section = header.closest('.source-section');
    const items = section.querySelector('.source-items');
    const toggle = header.querySelector('.source-toggle');
    
    if (items.classList.contains('expanded')) {
        items.classList.remove('expanded');
        toggle.classList.add('collapsed');
    } else {
        items.classList.add('expanded');
        toggle.classList.remove('collapsed');
    }
}

function openSourceModal(source) {
    modalTitle.textContent = 'Source Details';
    modalBody.innerHTML = `
        <div class="modal-section">
            <div class="modal-section-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                </svg>
                Title
            </div>
            <div class="modal-section-content">
                ${escapeHtml(source.title)}
            </div>
        </div>
        
        ${source.url ? `
            <div class="modal-section">
                <div class="modal-section-title">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                    </svg>
                    URL
                </div>
                <div class="modal-section-content">
                    <a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer" class="modal-link">
                        ${escapeHtml(source.url)}
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                            <polyline points="15 3 21 3 21 9"></polyline>
                            <line x1="10" y1="14" x2="21" y2="3"></line>
                        </svg>
                    </a>
                </div>
            </div>
        ` : ''}
        
        ${source.content ? `
            <div class="modal-section">
                <div class="modal-section-title">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                    Content
                </div>
                <div class="modal-section-content">
                    ${escapeHtml(source.content)}
                </div>
            </div>
        ` : ''}
        
        <div class="modal-section">
            <div class="modal-section-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="2" y1="12" x2="22" y2="12"></line>
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                </svg>
                Metadata
            </div>
            <div class="modal-meta">
                ${source.source ? `<span><strong>Source:</strong> ${escapeHtml(source.source)}</span>` : ''}
                ${source.topic ? `<span class="badge badge-topic">${escapeHtml(source.topic)}</span>` : ''}
                ${source.sentiment ? `<span class="badge badge-sentiment-${source.sentiment}">${escapeHtml(source.sentiment)}</span>` : ''}
                ${source.relevance_score ? `<span class="badge badge-relevance">Relevance: ${(source.relevance_score * 100).toFixed(0)}%</span>` : ''}
                ${source.published_at ? `<span><strong>Published:</strong> ${formatDate(source.published_at)}</span>` : ''}
                ${source.author ? `<span><strong>Author:</strong> ${escapeHtml(source.author)}</span>` : ''}
            </div>
        </div>
    `;
    
    sourceModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    sourceModal.classList.remove('active');
    document.body.style.overflow = '';
}

// Utility Functions
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
}

