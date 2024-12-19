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
    const conversationSelect = document.getElementById('conversation-select');
    const deleteConversationButton = document.getElementById('delete-conversation-button');
    const regenerateButton = document.getElementById('regenerate-button');
    const backButton = document.getElementById('back-button');

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

    // Function to add a message to the chat window
    function addMessage(message, isUser = true, messageDiv = null) {
        if (!messageDiv) {
            messageDiv = document.createElement('div');
            messageDiv.classList.add('message', isUser ? 'user-message' : 'llm-message');
        }
        
        if (typeof message === 'string') {
            if (isUser) {
                messageDiv.textContent = message;
                chatHistory.push({ role: "user", content: message }); // Add user message to history
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
                chatHistory.push({ role: "model", content: message }); // Add LLM message to history with role "model"
            }
        } else if (message instanceof HTMLImageElement) {
            messageDiv.appendChild(message);
        }
        
        if (!messageDiv.parentNode) {
            chatWindow.appendChild(messageDiv);
        }
        chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll
        return messageDiv;
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
            conversationSelect.innerHTML = '<option value="">New Conversation</option>';
            conversations.forEach(conversation => {
                const option = document.createElement('option');
                option.value = conversation.id;
                option.textContent = conversation.title ? `${conversation.title} (${conversation.provider}, ${conversation.model}, ${new Date(conversation.created_at).toLocaleString()})` : `Conversation ${conversation.id} (${conversation.provider}, ${conversation.model}, ${new Date(conversation.created_at).toLocaleString()})`;
                conversationSelect.appendChild(option);
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
            deleteConversationButton.style.display = 'inline-block';
        } catch (error) {
            console.error('Error fetching conversation:', error);
        }
    }

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
            addMessage(message);
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

    // Event listener for reset button
    resetButton.addEventListener('click', () => {
        chatHistory = [];
        chatWindow.innerHTML = '';
        currentConversationId = null;
        conversationSelect.value = "";
        deleteConversationButton.style.display = 'none';
        firstMessage = true;
        previousResponses = [];
    });

    // Event listener for sidebar toggle
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    // Event listener for conversation selection
    conversationSelect.addEventListener('change', async () => {
        const selectedConversationId = conversationSelect.value;
        if (selectedConversationId) {
            await loadConversation(selectedConversationId);
            firstMessage = false;
        } else {
            chatWindow.innerHTML = '';
            chatHistory = [];
            currentConversationId = null;
            deleteConversationButton.style.display = 'none';
            firstMessage = true;
        }
    });

    // Event listener for delete conversation button
    deleteConversationButton.addEventListener('click', async () => {
        if (currentConversationId) {
            try {
                const response = await fetch(`http://127.0.0.1:5000/api/conversations/${currentConversationId}`, {
                    method: 'DELETE'
                });
                if (response.ok) {
                    console.log(`Conversation ${currentConversationId} deleted.`);
                    chatWindow.innerHTML = '';
                    chatHistory = [];
                    currentConversationId = null;
                    conversationSelect.value = "";
                    deleteConversationButton.style.display = 'none';
                    await loadConversations();
                    firstMessage = true;
                } else {
                    console.error('Failed to delete conversation:', response.statusText);
                }
            } catch (error) {
                console.error('Error deleting conversation:', error);
            }
        }
    });

    // Event listener for regenerate button
    regenerateButton.addEventListener('click', async () => {
        if (previousResponses.length > 0) {
            const last = previousResponses[previousResponses.length - 1];
            const { prompt, conversationId, model, provider, systemMessage, image } = last;
            
            // Remove the last message from the chat window
            const lastMessage = chatWindow.lastElementChild;
            if (lastMessage) {
                chatWindow.removeChild(lastMessage);
            }
            
            // Remove the last message from the chat history
            if (chatHistory.length > 0) {
                chatHistory.pop();
            }
            
            const formData = new FormData();
            formData.append('prompt', prompt);
            formData.append('model', model);
            formData.append('provider', provider)
            formData.append('history', JSON.stringify(chatHistory));
            if (image) {
                formData.append('image', image);
            }
            if (systemMessage) {
                formData.append('system_message', systemMessage);
            }
            if (conversationId) {
                formData.append('conversation_id', conversationId);
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
                    console.error('Failed to regenerate response:', errorMsg);
                    addMessage(`Error regenerating response: ${errorMsg}`, false);
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
                previousResponses[previousResponses.length - 1].response = partialResponse;
            } catch (error) {
                 console.error('Failed to regenerate response:', error);
                 addMessage(`Error regenerating response: ${error.message}`, false);
            }
        } else {
            chatWindow.innerHTML = '';
            chatHistory = [];
            previousResponses = [];
        }
    });

    // Event listener for back button
    backButton.addEventListener('click', async () => {
        if (previousResponses.length > 0) {
            // Remove the last message from the chat window
            const lastMessage = chatWindow.lastElementChild;
            if (lastMessage) {
                chatWindow.removeChild(lastMessage);
            }
            
            // Remove the last message from the chat history
            if (chatHistory.length > 0) {
                chatHistory.pop();
            }
            
            previousResponses.pop();
            
            if (previousResponses.length > 0) {
                const previous = previousResponses[previousResponses.length - 1];
                chatWindow.innerHTML = '';
                chatHistory = [];
                currentConversationId = previous.conversationId;
                
                try {
                    const response = await fetch(`http://127.0.0.1:5000/api/conversations/${currentConversationId}`);
                    if (!response.ok) {
                        console.error('Failed to fetch conversation:', response.statusText);
                        return;
                    }
                    const data = await response.json();
                    if (data && data.messages) {
                        data.messages.forEach(message => {
                            addMessage(message.content, message.role === 'user');
                        });
                    }
                } catch (error) {
                    console.error('Error fetching conversation:', error);
                }
                
                addMessage(previous.response, false);
                lastResponse = previous.response;
            } else {
                chatWindow.innerHTML = '';
                chatHistory = [];
                previousResponses = [];
            }
        } else {
            chatWindow.innerHTML = '';
            chatHistory = [];
            previousResponses = [];
        }
    });

    // Initial fetch of models and conversations
    fetchModels(selectedProvider);
    updateStatus();
    loadConversations();
    setInitialDarkMode();
});
