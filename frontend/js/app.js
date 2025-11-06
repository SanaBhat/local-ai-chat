class LocalAIChat {
    constructor() {
        this.currentConversation = null;
        this.uploadedDocuments = [];
        this.currentJsonSchema = null;
        this.isGenerating = false;
        
        this.initializeApp();
    }

    async initializeApp() {
        this.bindEvents();
        await this.loadModels();
        await this.checkServerStatus();
        
        // Auto-load first model if available
        setTimeout(() => this.autoLoadModel(), 1000);
    }

    bindEvents() {
        // Chat input
        document.getElementById('send-btn').addEventListener('click', () => this.sendMessage());
        document.getElementById('chat-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // File upload
        document.getElementById('upload-area').addEventListener('click', () => {
            document.getElementById('file-input').click();
        });
        document.getElementById('file-input').addEventListener('change', (e) => this.handleFileUpload(e));
        document.getElementById('upload-trigger').addEventListener('click', () => {
            document.getElementById('file-input').click();
        });

        // Model management
        document.getElementById('load-model-btn').addEventListener('click', () => this.loadSelectedModel());

        // JSON mode
        document.getElementById('json-mode-btn').addEventListener('click', () => this.toggleJsonModal());
        document.getElementById('apply-json-btn').addEventListener('click', () => this.applyJsonSchema());
        document.getElementById('clear-json-btn').addEventListener('click', () => this.clearJsonSchema());
        document.querySelector('.close-btn').addEventListener('click', () => this.closeJsonModal());

        // Chat actions
        document.getElementById('new-chat-btn').addEventListener('click', () => this.startNewChat());
        document.getElementById('clear-chat-btn').addEventListener('click', () => this.clearChat());
        document.getElementById('branch-chat-btn').addEventListener('click', () => this.branchConversation());

        // Modal backdrop close
        document.getElementById('json-modal').addEventListener('click', (e) => {
            if (e.target.id === 'json-modal') this.closeJsonModal();
        });
    }

    async checkServerStatus() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            if (data.offline) {
                this.updateModelStatus(data.model_loaded ? 'loaded' : 'no_model');
            }
        } catch (error) {
            console.error('Server not reachable:', error);
            this.showError('Server not running. Please start the backend server.');
        }
    }

    async loadModels() {
        try {
            const response = await fetch('/api/models');
            const models = await response.json();
            
            const select = document.getElementById('model-select');
            select.innerHTML = '';
            
            if (models.length === 0) {
                select.innerHTML = '<option value="">No models found</option>';
                return;
            }
            
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.filename;
                option.textContent = `${model.filename} (${model.size_gb}GB) - ${model.description}`;
                select.appendChild(option);
            });
            
            // Check current model
            await this.checkCurrentModel();
        } catch (error) {
            console.error('Error loading models:', error);
        }
    }

    async checkCurrentModel() {
        try {
            const response = await fetch('/api/models/current');
            const data = await response.json();
            
            if (data.loaded) {
                this.updateModelStatus('loaded', data.name);
            }
        } catch (error) {
            console.error('Error checking current model:', error);
        }
    }

    async loadSelectedModel() {
        const select = document.getElementById('model-select');
        const modelName = select.value;
        
        if (!modelName) {
            this.showError('Please select a model first');
            return;
        }
        
        this.updateModelStatus('loading');
        
        try {
            const response = await fetch(`/api/models/load/${encodeURIComponent(modelName)}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.updateModelStatus('loaded', modelName);
                this.showMessage('Model loaded successfully!', 'success');
            } else {
                throw new Error(result.detail || 'Failed to load model');
            }
        } catch (error) {
            this.updateModelStatus('error');
            this.showError(`Error loading model: ${error.message}`);
        }
    }

    async autoLoadModel() {
        const select = document.getElementById('model-select');
        if (select.value && !this.isGenerating) {
            await this.loadSelectedModel();
        }
    }

    updateModelStatus(status, modelName = '') {
        const statusElement = document.getElementById('model-status');
        
        switch (status) {
            case 'loaded':
                statusElement.textContent = `Model: ${modelName}`;
                statusElement.className = 'status-online';
                break;
            case 'loading':
                statusElement.textContent = 'Loading model...';
                statusElement.className = 'status-offline';
                break;
            case 'error':
                statusElement.textContent = 'Error loading model';
                statusElement.className = 'status-offline';
                break;
            default:
                statusElement.textContent = 'No model loaded';
                statusElement.className = 'status-offline';
        }
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || this.isGenerating) return;
        
        if (!await this.ensureModelLoaded()) {
            this.showError('Please load a model first');
            return;
        }
        
        this.isGenerating = true;
        input.value = '';
        this.adjustTextareaHeight(input);
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.currentConversation,
                    documents: this.uploadedDocuments.map(doc => doc.content),
                    json_schema: this.currentJsonSchema,
                    max_tokens: 2048
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Failed to get response');
            }
            
            // Remove typing indicator
            this.removeTypingIndicator();
            
            // Add assistant response
            this.addMessage('assistant', data.response, data.model);
            
            // Update conversation
            this.currentConversation = data.conversation_id;
            
        } catch (error) {
            this.removeTypingIndicator();
            this.showError(`Chat error: ${error.message}`);
        } finally {
            this.isGenerating = false;
        }
    }

    async ensureModelLoaded() {
        try {
            const response = await fetch('/api/models/current');
            const data = await response.json();
            return data.loaded;
        } catch (error) {
            return false;
        }
    }

    addMessage(role, content, model = null) {
        const messagesContainer = document.getElementById('chat-messages');
        
        // Remove welcome message if it's the first real message
        if (messagesContainer.querySelector('.welcome-message')) {
            messagesContainer.innerHTML = '';
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = this.formatMessage(content);
        
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        metaDiv.textContent = role === 'user' ? 'You' : (model || 'Assistant');
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(metaDiv);
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatMessage(content) {
        // Simple markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
            .replace(/\n/g, '<br>');
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant';
        typingDiv.id = 'typing-indicator';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        typingDiv.appendChild(contentDiv);
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    async handleFileUpload(event) {
        const files = event.target.files;
        
        for (let file of files) {
            await this.uploadFile(file);
        }
        
        // Reset file input
        event.target.value = '';
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.uploadedDocuments.push({
                    id: result.file_id,
                    filename: file.name,
                    content: result.content
                });
                
                this.updateUploadedFilesList();
                this.showMessage(`File "${file.name}" uploaded successfully`, 'success');
            } else {
                throw new Error(result.detail || 'Upload failed');
            }
        } catch (error) {
            this.showError(`Upload error: ${error.message}`);
        }
    }

    updateUploadedFilesList() {
        const container = document.getElementById('uploaded-files');
        container.innerHTML = '';
        
        this.uploadedDocuments.forEach(doc => {
            const fileDiv = document.createElement('div');
            fileDiv.className = 'uploaded-file';
            fileDiv.innerHTML = `
                <span>${doc.filename}</span>
                <span class="file-remove" data-id="${doc.id}">×</span>
            `;
            container.appendChild(fileDiv);
        });
        
        // Add remove event listeners
        container.querySelectorAll('.file-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.target.getAttribute('data-id');
                this.removeUploadedFile(id);
            });
        });
    }

    removeUploadedFile(id) {
        this.uploadedDocuments = this.uploadedDocuments.filter(doc => doc.id !== id);
        this.updateUploadedFilesList();
    }

    toggleJsonModal() {
        const modal = document.getElementById('json-modal');
        modal.style.display = modal.style.display === 'block' ? 'none' : 'block';
    }

    closeJsonModal() {
        document.getElementById('json-modal').style.display = 'none';
    }

    applyJsonSchema() {
        const schemaInput = document.getElementById('json-schema-input').value;
        
        try {
            if (schemaInput.trim()) {
                this.currentJsonSchema = JSON.parse(schemaInput);
                this.showMessage('JSON schema applied successfully', 'success');
            } else {
                this.currentJsonSchema = null;
                this.showMessage('JSON schema cleared', 'info');
            }
            this.closeJsonModal();
        } catch (error) {
            this.showError('Invalid JSON schema');
        }
    }

    clearJsonSchema() {
        this.currentJsonSchema = null;
        document.getElementById('json-schema-input').value = '';
        this.showMessage('JSON schema cleared', 'info');
        this.closeJsonModal();
    }

    startNewChat() {
        this.currentConversation = null;
        document.getElementById('chat-messages').innerHTML = `
            <div class="welcome-message">
                <h3>Welcome to LocalAI Chat!</h3>
                <p>This application runs completely offline on your laptop.</p>
                <p>Load a model to start chatting with AI without any internet connection.</p>
            </div>
        `;
        document.getElementById('chat-title').textContent = 'New Chat';
    }

    clearChat() {
        if (confirm('Are you sure you want to clear this chat?')) {
            this.startNewChat();
        }
    }

    async branchConversation() {
        if (!this.currentConversation) {
            this.showError('No active conversation to branch');
            return;
        }
        
        // Simple implementation - branch from last message
        try {
            const response = await fetch('/api/conversations/branch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    conversation_id: this.currentConversation,
                    branch_point: 2 // This would need to be calculated based on message count
                })
            });
            
            if (response.ok) {
                const newConversation = await response.json();
                this.currentConversation = newConversation.id;
                this.showMessage('Conversation branched successfully', 'success');
            }
        } catch (error) {
            this.showError(`Branching error: ${error.message}`);
        }
    }

    adjustTextareaHeight(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    showMessage(message, type = 'info') {
        // Simple notification system
        console.log(`[${type}] ${message}`);
        // In a real implementation, you'd show this in the UI
        alert(`[${type.toUpperCase()}] ${message}`);
    }

    showError(message) {
        this.showMessage(message, 'error');
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new LocalAIChat();
});
