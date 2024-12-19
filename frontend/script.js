document.addEventListener('DOMContentLoaded', () => {
    // Get references to DOM elements
    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const llmProvider = document.getElementById('llm-provider');
    const llmModel = document.getElementById('llm-model');
    const llmStatus = document.getElementById('llm-status');
    const imageUpload = document.getElementById('image-upload');
    const uploadButton = document.getElementById('upload-button');
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const sidebar = document.querySelector('.sidebar');
    const inputWithUpload = document.querySelector('.input-with-upload');
    const formSelects = document.querySelectorAll('.form-group select');
    const resetButton = document.getElementById('reset-button');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const systemMessageTextarea = document.getElementById('system-message');
    const conversationList = document.getElementById('conversation-list');
    const deleteAllConversationsButton = document.getElementById('delete-all-conversations-button');
    const systemMessageSelect = document.getElementById('system-message-select');
    const saveSystemMessageButton = document.getElementById('save-system-message-button');
    const deleteSystemMessageButton = document.getElementById('delete-system-message-button');

    // Initialize variables
    let selectedProvider = llmProvider.value;
    let selectedModel = llmModel.value;
    let uploadedImage = null;
    let chatHistory = []; // Store chat history
    let systemMessage = systemMessageTextarea.value;
    let currentConversationId = null;
    let firstMessage = true; // Flag to track if it's the first message in a new conversation
    let conversationTitle = null;
    let lastResponse = null;
    let previousResponses = [];
    let selectedSystemMessageId = null;

    // Function to add a message to the chat window
    function addMessage(message, isUser = true, messageDiv = null) {
        if (!messageDiv) {
            messageDiv = document.createElement('div');
            messageDiv.classList.add('message', isUser ? 'user-message' : 'llm-message');
        }
        if (typeof message === 'string') {
            if (isUser) {
                messageDiv.textContent = message;
            } else {
                // Parse markdown and highlight code blocks
                messageDiv.innerHTML = marked.parse(message);
                messageDiv.querySelectorAll('pre code').forEach(block => {
                    // Add copy button
                    const copyButton = document.createElement('button');
                    copyButton.innerHTML = '<i class="fas fa-copy"></i>';
                    copyButton.classList.add('copy-button');
                    copyButton.style.position = 'absolute';
                    copyButton.style.top = '0.5em';
                    copyButton.style.right = '0.5em';
                    copyButton.addEventListener('click', () => {
                        navigator.clipboard.writeText(block.textContent).then(() => {
                            copyButton.innerHTML = '<i class="fas fa-check"></i>';
                            setTimeout(() => {
                                copyButton.innerHTML = '<i class="fas fa-copy"></i>';
                            }, 2000);
                        });
                    });
                    const pre = block.parentNode;
                    pre.style.position = 'relative';
                    pre.appendChild(copyButton);
                    hljs.highlightBlock(block);
                });
            }
        } else if (message instanceof HTMLImageElement) {
            messageDiv.appendChild(message);
        }
        
        const deleteButton = document.createElement('button');
        deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
        deleteButton.classList.add('delete-message-button');
        messageDiv.appendChild(deleteButton);
        deleteButton.addEventListener('click', () => {
            const index = Array.from(chatWindow.children).indexOf(messageDiv);
            if (index > -1) {
                chatHistory.splice(index, 1);
            }
            messageDiv.remove();
        });
        if (!messageDiv.parentNode) {
            chatWindow.appendChild(messageDiv);
        }
        chatWindow.scrollTop = chatWindow.scrollHeight;
        return messageDiv;
    }

    // Function to fetch system messages
    async function fetchSystemMessages() {
        try {
            const response = await fetch('http://127.0.0.1:5000/api/system_messages');
            if (!response.ok) {
                console.error('Failed to fetch system messages:', response.statusText);
                return;
            }
            const systemMessages = await response.json();
            systemMessageSelect.innerHTML = '<option value="">None</option>';
            systemMessages.forEach(message => {
                const option = document.createElement('option');
                option.value = message.id;
                option.textContent = `${message.name} (${message.content.length > 50 ? message.content.substring(0, 50) + '...' : message.content})`;
                systemMessageSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error fetching system messages:', error);
        }
    }

    // Function to fetch available models for the selected provider
    async function fetchModels(provider) {
        try {
            const response = await fetch(`http://127.0.0.1:5000/api/models?provider=${provider}`);
            if (!response.ok) {
                const message = `HTTP error! status: ${response.status}`;
                console.error('Failed to fetch models:', message);
                addMessage(`Error loading models: ${message}`, false)
                llmModel.innerHTML = '<option>Error loading models</option>';
                return;
            }
            const models = await response.json();
            llmModel.innerHTML = ''; // Clear existing options
            if (models && models.length > 0) {
                models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    llmModel.appendChild(option);
                });
                selectedModel = models[0];
                llmModel.value = selectedModel;
                updateStatus();
            } else {
                 console.error('No models returned from the API.');
                 addMessage('No models available for this provider.', false);
                 llmModel.innerHTML = '<option>No models available</option>';
            }
        } catch (error) {
            console.error('Failed to fetch models:', error);
            addMessage(`Error loading models: ${error.message}`, false)
            llmModel.innerHTML = '<option>Error loading models</option>';
        }
    }

    // Function to update the status display
    function updateStatus() {
        llmStatus.textContent = `${selectedProvider}, ${selectedModel}`;
    }

    // Function to load conversations
    async function loadConversations() {
        try {
            const response = await fetch('http://127.0.0.1:5000/api/conversations');
            if (!response.ok) {
                console.error('Failed to fetch conversations:', response.statusText);
                return;
            }
            const conversations = await response.json();
            conversationList.innerHTML = '';
            conversations.forEach(conversation => {
                const listItem = document.createElement('li');
                listItem.classList.add('conversation-list-item');
                const title = conversation.title ? `${conversation.title} (${conversation.provider}, ${conversation.model}, ${new Date(conversation.created_at).toLocaleString()})` : `Conversation ${conversation.id} (${conversation.provider}, ${conversation.model}, ${new Date(conversation.created_at).toLocaleString()})`;
                listItem.textContent = title;
                listItem.addEventListener('click', () => loadConversation(conversation.id));

                const deleteButton = document.createElement('button');
                deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
                deleteButton.classList.add('delete-conversation-button');
                deleteButton.addEventListener('click', (event) => {
                    event.stopPropagation(); // Prevent loading the conversation when deleting
                    deleteConversation(conversation.id);
                });
                listItem.appendChild(deleteButton);
                conversationList.appendChild(listItem);
            });
        } catch (error) {
            console.error('Error fetching conversations:', error);
        }
    }

    // Function to load a specific conversation
    async function loadConversation(conversationId) {
        try {
            const response = await fetch(`http://127.0.0.1:5000/api/conversations/${conversationId}`);
            if (!response.ok) {
                console.error('Failed to fetch conversation:', response.statusText);
                return;
            }
            const data = await response.json();
            chatWindow.innerHTML = '';
            chatHistory = [];
            if (data && data.messages) {
                data.messages.forEach(message => {
                    addMessage(message.content, message.role === 'user');
                });
            }
            currentConversationId = conversationId;
        } catch (error) {
            console.error('Error fetching conversation:', error);
        }
    }

    // Event listener for system message select change
    systemMessageSelect.addEventListener('change', () => {
        selectedSystemMessageId = systemMessageSelect.value;
        if (selectedSystemMessageId) {
            fetch(`http://127.0.0.1:5000/api/system_messages/${selectedSystemMessageId}`)
                .then(response => response.json())
                .then(data => {
                    systemMessageTextarea.value = data.content;
                    document.getElementById('system-message-name').value = data.name;
                })
                .catch(error => console.error('Error fetching system message:', error));
        } else {
            systemMessageTextarea.value = '';
            document.getElementById('system-message-name').value = '';
        }
    });

    // Event listener for provider change
    llmProvider.addEventListener('change', async () => {
        selectedProvider = llmProvider.value;
        await fetchModels(selectedProvider);
        updateStatus();
    });

    // Event listener for model change
    llmModel.addEventListener('change', () => {
        selectedModel = llmModel.value;
        updateStatus();
    });

    // Event listener for send button click
    sendButton.addEventListener('click', async () => {
        const message = userInput.value.trim();
        if (message) {
            const userMessageDiv = addMessage(message);
            chatHistory.push({ role: "user", content: message });
            userInput.value = '';
            
            const formData = new FormData();
            formData.append('prompt', message);
            formData.append('model', selectedModel);
            formData.append('provider', selectedProvider) // Send the selected provider
            formData.append('history', JSON.stringify(chatHistory)); // Send chat history
            if (uploadedImage) {
                formData.append('image', uploadedImage);
            }
            
            systemMessage = systemMessageTextarea.value;
            if (!systemMessage) {
                systemMessage = " ";
            }
            formData.append('system_message', systemMessage);
            if (currentConversationId) {
                formData.append('conversation_id', currentConversationId);
            }
            if (firstMessage) {
                conversationTitle = message;
                formData.append('conversation_title', conversationTitle);
            }

            try {
                const response = await fetch('http://127.0.0.1:5000/api/generate', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'Accept': 'text/event-stream'
                    }
                });
                if (!response.ok) {
                    const errorMsg = `HTTP error! status: ${response.status}`;
                    console.error('Failed to send message:', errorMsg);
                    addMessage(`Error generating response: ${errorMsg}`, false);
                    return;
                }
                
                const reader = response.body.getReader();
                let partialResponse = '';
                let llmMessageDiv = null;
                
                while(true) {
                    const { done, value } = await reader.read();
                    if (done) {
                        break;
                    }
                    const text = new TextDecoder().decode(value);
                    const lines = text.split('\n').filter(line => line.startsWith(' '));
                    
                    for (const line of lines) {
                        if (line.trim() === '') {
                            continue;
                        }
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
                            // If parsing fails, still add the partial response
                            if (!llmMessageDiv) {
                                llmMessageDiv = addMessage(partialResponse, false);
                            } else {
                                addMessage(partialResponse, false, llmMessageDiv);
                            }
                        }
                    }
                }
                lastResponse = partialResponse;
                addMessage(partialResponse, false, llmMessageDiv);
                chatHistory.push({ role: "model", content: partialResponse });
                previousResponses.push({
                    prompt: message,
                    response: partialResponse,
                    conversationId: currentConversationId,
                    model: selectedModel,
                    provider: selectedProvider,
                    systemMessage: systemMessage,
                    image: uploadedImage
                });
                uploadedImage = null; // Clear the uploaded image after sending
                if (firstMessage) {
                    firstMessage = false;
                    loadConversations();
                }
            } catch (error) {
                console.error('Failed to send message:', error);
                addMessage(`Error generating response: ${error.message}`, false);
            }
        }
    });

    // Event listener for image upload button click
    uploadButton.addEventListener('click', () => {
        imageUpload.click();
    });

    // Event listener for image upload
    imageUpload.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            uploadedImage = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.style.maxWidth = '100px';
                addMessage(img);
            };
            reader.readAsDataURL(file);
        }
    });

    // Event listener for user input keydown to handle Enter and Shift+Enter
    userInput.addEventListener('keydown', async (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // Prevent the default Enter behavior (new line)
            sendButton.click(); // Trigger the send button click
        } else if (event.key === 'Enter' && event.shiftKey) {
            // Allow new line with Shift+Enter, default behavior
        }
    });

    // Function to toggle dark mode
    function toggleDarkMode(isDark) {
        document.body.classList.toggle('dark-mode', isDark);
        sidebar.classList.toggle('dark-mode', isDark);
        chatWindow.classList.toggle('dark-mode', isDark);
        inputWithUpload.classList.toggle('dark-mode', isDark);
        formSelects.forEach(select => select.classList.toggle('dark-mode', isDark));
        const messages = document.querySelectorAll('.message');
        messages.forEach(message => message.classList.toggle('dark-mode', isDark));
    }

    // Event listener for dark mode toggle
    darkModeToggle.addEventListener('change', () => {
        toggleDarkMode(darkModeToggle.checked);
    });

    // Function to set initial dark mode based on system preference
    function setInitialDarkMode() {
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        darkModeToggle.checked = prefersDark;
        toggleDarkMode(prefersDark);
    }

    // Function to save a system message
    async function saveSystemMessage() {
        const content = systemMessageTextarea.value;
        const name = document.getElementById('system-message-name').value;
        if (content && name) {
            try {
                const response = await fetch('http://127.0.0.1:5000/api/system_messages', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name: name, content: content })
                });
                if (response.ok) {
                    console.log('System message saved.');
                    fetchSystemMessages();
                } else {
                    console.error('Failed to save system message:', response.statusText);
                }
            } catch (error) {
                console.error('Error saving system message:', error);
            }
        }
    }

    // Function to delete a system message
    async function deleteSystemMessage() {
        if (selectedSystemMessageId) {
            try {
                const response = await fetch(`http://127.0.0.1:5000/api/system_messages/${selectedSystemMessageId}`, {
                    method: 'DELETE'
                });
                if (response.ok) {
                    console.log(`System message ${selectedSystemMessageId} deleted.`);
                    systemMessageTextarea.value = '';
                    selectedSystemMessageId = null;
                    fetchSystemMessages();
                } else {
                    console.error('Failed to delete system message:', response.statusText);
                }
            } catch (error) {
                console.error('Error deleting system message:', error);
            }
        }
    }

    // Event listener for save system message button
    saveSystemMessageButton.addEventListener('click', saveSystemMessage);

    // Event listener for delete system message button
    deleteSystemMessageButton.addEventListener('click', deleteSystemMessage);

    // Event listener for reset button
    resetButton.addEventListener('click', () => {
        chatHistory = [];
        chatWindow.innerHTML = '';
        currentConversationId = null;
        firstMessage = true;
        previousResponses = [];
    });

    // Event listener for sidebar toggle
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    // Function to delete a conversation
    async function deleteConversation(conversationId) {
        try {
            const response = await fetch(`http://127.0.0.1:5000/api/conversations/${conversationId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                console.log(`Conversation ${conversationId} deleted.`);
                if (currentConversationId === conversationId) {
                    chatWindow.innerHTML = '';
                    chatHistory = [];
                    currentConversationId = null;
                    firstMessage = true;
                    previousResponses = [];
                }
                await loadConversations();
            } else {
                console.error('Failed to delete conversation:', response.statusText);
            }
        } catch (error) {
            console.error('Error deleting conversation:', error);
        }
    }

    // Event listener for delete all conversations button
    deleteAllConversationsButton.addEventListener('click', async (event) => {
        event.preventDefault();
        try {
            const response = await fetch('http://127.0.0.1:5000/api/conversations', {
                method: 'DELETE'
            });
            if (response.ok) {
                console.log('All conversations deleted.');
                chatWindow.innerHTML = '';
                chatHistory = [];
                currentConversationId = null;
                firstMessage = true;
                previousResponses = [];
                conversationList.innerHTML = '';
            } else {
                console.error('Failed to delete all conversations:', response.statusText);
            }
        } catch (error) {
             console.error('Error deleting all conversations:', error);
        }
    });

    // Initial fetch of models, system messages and conversations
    fetchModels(selectedProvider);
    fetchSystemMessages();
    updateStatus();
    loadConversations();
    setInitialDarkMode();
});
