import { elements } from './domElements.js';

// State variables
let chatHistory = [];
let uploadedImage = null;
let systemMessage = '';
let currentConversationId = null;
let firstMessage = true;
let conversationTitle = null;
let lastResponse = null;
let previousResponses = [];
let selectedSystemMessageId = null;
let responseStartTime = null;

export function addMessage(message, isUser = true, messageDiv = null) {
    if (!messageDiv) {
        messageDiv = document.createElement('div');
        messageDiv.classList.add('message', isUser ? 'user-message' : 'llm-message');
        
        // Create avatar
        const avatar = document.createElement('div');
        avatar.classList.add('message-avatar');
        avatar.innerHTML = isUser ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        messageDiv.appendChild(avatar);

        // Create content container
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        messageDiv.appendChild(contentDiv);

        // Create actions container
        const actionsDiv = document.createElement('div');
        actionsDiv.classList.add('message-actions');
        messageDiv.appendChild(actionsDiv);

        // Add action buttons
        if (isUser) {
            const editButton = document.createElement('button');
            editButton.innerHTML = '<i class="fas fa-edit"></i>';
            editButton.classList.add('message-button');
            editButton.title = 'Editar mensaje';
            actionsDiv.appendChild(editButton);

            editButton.addEventListener('click', () => handleEditMessage(contentDiv, messageDiv));
        } else {
            const regenerateButton = document.createElement('button');
            regenerateButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
            regenerateButton.classList.add('message-button');
            regenerateButton.title = 'Regenerar respuesta';
            actionsDiv.appendChild(regenerateButton);
            regenerateButton.addEventListener('click', () => regenerateResponse(messageDiv));
        }

        const deleteButton = document.createElement('button');
        deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
        deleteButton.classList.add('message-button');
        deleteButton.title = 'Eliminar mensaje';
        actionsDiv.appendChild(deleteButton);
        deleteButton.addEventListener('click', () => {
            const index = Array.from(elements.chatWindow.children).indexOf(messageDiv);
            if (index > -1) chatHistory.splice(index, 1);
            messageDiv.remove();
        });
    }

    const contentDiv = messageDiv.querySelector('.message-content');
    if (typeof message === 'string') {
        if (isUser) {
            contentDiv.innerHTML = message.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, '<br>').replace(/  /g, '&nbsp; ');
            contentDiv.style.whiteSpace = 'pre-wrap';
        } else {
            contentDiv.innerHTML = window.marked.parse(message);
            contentDiv.querySelectorAll('pre code').forEach(block => {
                const copyButton = document.createElement('button');
                copyButton.innerHTML = '<i class="fas fa-copy"></i>';
                copyButton.classList.add('copy-button');
                copyButton.title = 'Copiar código';
                copyButton.addEventListener('click', () => {
                    navigator.clipboard.writeText(block.textContent).then(() => {
                        copyButton.innerHTML = '<i class="fas fa-check"></i>';
                        setTimeout(() => copyButton.innerHTML = '<i class="fas fa-copy"></i>', 2000);
                    });
                });
                const pre = block.parentNode;
                pre.style.position = 'relative';
                pre.appendChild(copyButton);
                window.hljs.highlightBlock(block);
            });
        }
    } else if (message instanceof HTMLImageElement) {
        contentDiv.appendChild(message);
    }
    
    if (!messageDiv.parentNode) {
        elements.chatWindow.appendChild(messageDiv);
    }
    
    if (document.body.classList.contains('dark-mode')) {
        messageDiv.classList.add('dark-mode');
    }
    
    elements.chatWindow.scrollTop = elements.chatWindow.scrollHeight;
    return messageDiv;
}

async function handleEditMessage(contentDiv, messageDiv) {
    const messageText = contentDiv.innerHTML;
    const inputField = document.createElement('textarea');
    inputField.value = messageText.replace(/<br>/g, '\n').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&nbsp; /g, ' ');
    contentDiv.innerHTML = '';
    contentDiv.appendChild(inputField);
    inputField.focus();

    const buttonsDiv = document.createElement('div');
    buttonsDiv.style.marginTop = '8px';
    buttonsDiv.style.display = 'flex';
    buttonsDiv.style.gap = '8px';
    contentDiv.appendChild(buttonsDiv);

    const saveButton = document.createElement('button');
    saveButton.innerHTML = '<i class="fas fa-check"></i>';
    saveButton.classList.add('message-button');
    saveButton.title = 'Guardar cambios';
    buttonsDiv.appendChild(saveButton);

    const cancelButton = document.createElement('button');
    cancelButton.innerHTML = '<i class="fas fa-times"></i>';
    cancelButton.classList.add('message-button');
    cancelButton.title = 'Cancelar edición';
    buttonsDiv.appendChild(cancelButton);

    saveButton.addEventListener('click', () => handleSaveEdit(inputField.value, messageDiv, contentDiv));
    cancelButton.addEventListener('click', () => contentDiv.innerHTML = messageText);
}

async function handleSaveEdit(editedMessage, messageDiv, contentDiv) {
    const messageId = Array.from(elements.chatWindow.children).indexOf(messageDiv);
    
    // Remove subsequent messages
    const messagesToRemove = Array.from(elements.chatWindow.children).slice(messageId + 1);
    messagesToRemove.forEach(msg => msg.remove());
    
    // Update chat history
    chatHistory = chatHistory.slice(0, messageId + 1);
    chatHistory[messageId] = { role: "user", content: editedMessage };
    previousResponses = previousResponses.slice(0, messageId);
    
    // Update edited message content
    contentDiv.innerHTML = editedMessage.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, '<br>').replace(/  /g, '&nbsp; ');
    
    await sendMessage(editedMessage);
}

export async function sendMessage(message, isEdited = false) {
    const formData = new FormData();
    formData.append('prompt', message);
    formData.append('model', elements.llmModel.value);
    formData.append('provider', elements.llmProvider.value);
    formData.append('history', JSON.stringify(chatHistory));
    
    if (uploadedImage) {
        formData.append('image', uploadedImage);
    }
    
    systemMessage = elements.systemMessageTextarea.value;
    if (!systemMessage) {
        systemMessage = " ";
    }
    formData.append('system_message', systemMessage);
    
    if (currentConversationId) {
        formData.append('conversation_id', currentConversationId);
    }
    
    const activeModes = Array.from(elements.activeToolsContainer.querySelectorAll('.active-tool-tag')).map(tool => tool.textContent);
    formData.append('selected_modes', JSON.stringify(activeModes));
    formData.append('think', elements.thinkToggle.checked);
    formData.append('think_depth', elements.thinkDepth.value);
    
    if (elements.llmProvider.value === 'openai' && elements.openaiBaseUrlInput.value.trim() !== '') {
        formData.append('base_url', elements.openaiBaseUrlInput.value.trim());
        formData.append('model', '');
    }
    
    if (firstMessage) {
        conversationTitle = message;
        formData.append('conversation_title', conversationTitle);
    }

    let apiUrl = 'http://127.0.0.1:5000/api/generate';
    if (elements.thinkToggle.checked) {
        apiUrl = 'http://127.0.0.1:5000/api/think';
    }

    try {
        // Add typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('typing-indicator');
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.classList.add('typing-dot');
            typingDiv.appendChild(dot);
        }
        elements.chatWindow.appendChild(typingDiv);
        elements.chatWindow.scrollTop = elements.chatWindow.scrollHeight;

        const response = await fetch(apiUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'text/event-stream'
            }
        });

        // Remove typing indicator on error
        if (!response.ok) {
            typingDiv.remove();
            const errorMsg = `HTTP error! status: ${response.status}`;
            console.error('Failed to send message:', errorMsg);
            addMessage(`Error generating response: ${errorMsg}`, false);
            return;
        }
        
        const reader = response.body.getReader();
        let partialResponse = '';
        let llmMessageDiv = null;
        responseStartTime = performance.now();

        // Remove typing indicator when response begins
        typingDiv.remove();
        
        while(true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const text = new TextDecoder().decode(value);
            const lines = text.split('\n').filter(line => line.startsWith(' '));
            
            for (const line of lines) {
                if (line.trim() === '') continue;
                
                try {
                    const jsonString = line.substring(1);
                    const data = JSON.parse(jsonString);
                    partialResponse += data.response;
                    if (!llmMessageDiv) {
                        llmMessageDiv = addMessage(partialResponse, false);
                    } else {
                        addMessage(partialResponse, false, llmMessageDiv);
                    }
                } catch (e) {
                    console.error('Error parsing JSON:', e, line);
                    if (!llmMessageDiv) {
                        llmMessageDiv = addMessage(partialResponse, false);
                    } else {
                        addMessage(partialResponse, false, llmMessageDiv);
                    }
                }
            }
        }
        
        lastResponse = partialResponse;
        const responseEndTime = performance.now();
        const elapsedTime = (responseEndTime - responseStartTime) / 1000;
        const tokens = partialResponse.split(/\s+/).length;
        const tokensPerSecond = (tokens / elapsedTime).toFixed(2);
        elements.tokensPerSecondDisplay.textContent = `${tokensPerSecond} tokens/sec`;
        
        addMessage(partialResponse, false, llmMessageDiv);
        chatHistory.push({ role: "model", content: partialResponse });
        previousResponses.push({
            prompt: message,
            response: partialResponse,
            conversationId: currentConversationId,
            model: elements.llmModel.value,
            provider: elements.llmProvider.value,
            systemMessage: systemMessage,
            image: uploadedImage
        });
        
        uploadedImage = null; // Clear the uploaded image after sending
        
        if (firstMessage) {
            firstMessage = false;
            // Trigger conversation list update
            window.dispatchEvent(new CustomEvent('conversationCreated'));
        }
    } catch (error) {
        console.error('Failed to send message:', error);
        addMessage(`Error generating response: ${error.message}`, false);
    }
}

export async function regenerateResponse(messageDiv) {
    const index = Array.from(elements.chatWindow.children).indexOf(messageDiv);
    if (index > -1) {
        // Remove all messages after the clicked message, including the clicked message
        const messagesToRemove = Array.from(elements.chatWindow.children).slice(index);
        messagesToRemove.forEach(msg => msg.remove());
        
        // Rebuild chat history
        chatHistory = chatHistory.slice(0, index);
        previousResponses = previousResponses.slice(0, index);

        const message = previousResponses[index - 1];
        if (message) {
            const userMessageDiv = addMessage(message.prompt);
            chatHistory.push({ role: "user", content: message.prompt });
            await sendMessage(message.prompt, true);
        }
    }
}

// Export state variables and functions that need to be accessed from other modules
export const state = {
    get chatHistory() { return chatHistory; },
    set chatHistory(value) { chatHistory = value; },
    get currentConversationId() { return currentConversationId; },
    set currentConversationId(value) { currentConversationId = value; },
    get firstMessage() { return firstMessage; },
    set firstMessage(value) { firstMessage = value; },
    get previousResponses() { return previousResponses; },
    set previousResponses(value) { previousResponses = value; }
};