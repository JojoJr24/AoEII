document.addEventListener('DOMContentLoaded', () => {
    // Get references to DOM elements
    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const llmProvider = document.getElementById('llm-provider');
    const llmModel = document.getElementById('llm-model');
    const llmStatus = document.getElementById('llm-status');
    let availableModels = [];
    const imageUpload = document.getElementById('image-upload');
    const uploadButton = document.getElementById('upload-button');
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const sidebar = document.querySelector('.sidebar');
    const inputWithUpload = document.querySelector('.input-with-upload');
    const formSelects = document.querySelectorAll('.form-group select');
    const resetButton = document.getElementById('reset-button');
    const stopButton = document.getElementById('stop-button');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const systemMessageTextarea = document.getElementById('system-message');
    const conversationList = document.getElementById('conversation-list');
    const deleteAllConversationsButton = document.getElementById('delete-all-conversations-button');
    const systemMessageSelect = document.getElementById('system-message-select');
    const saveSystemMessageButton = document.getElementById('save-system-message-button');
    const deleteSystemMessageButton = document.getElementById('delete-system-message-button');
    const toolsContainer = document.getElementById('tools-container');
    const activeToolsContainer = document.getElementById('active-tools-container');
    const thinkToggle = document.getElementById('think-toggle');
    const thinkDepth = document.getElementById('think-depth');
    const thinkDepthMessage = document.getElementById('think-depth-message');
    const openaiBaseUrlGroup = document.getElementById('openai-base-url-group');
    const openaiBaseUrlInput = document.getElementById('openai-base-url');
    const showConversationsButton = document.getElementById('show-conversations-button');
    const conversationsModal = document.getElementById('conversations-modal');
    const conversationsListModal = document.getElementById('conversations-list-modal');
    const closeModalButton = document.querySelector('.close-button');
    const deleteAllTasksButton = document.getElementById('delete-all-tasks-button');
    const taskResponseModal = document.getElementById('task-response-modal');
    const taskResponseContent = document.getElementById('task-response-content');

    // Function to save the current configuration
    function saveConfig() {
        const config = {
            selected_provider: "",
            selected_model: "",
            selected_conversation_id: "",
            selected_system_message_id: "",
            selected_tools: [],
            think_mode: false,
            think_depth: 0,
            openai_base_url: ""
        };
    
        localStorage.setItem('config', JSON.stringify(config));
        console.log('Config saved in localStorage!');
    }
    
    function loadConfig() {
       /* const config = JSON.parse(localStorage.getItem('config'));
        console.log('Loaded config:', config);
        if (config) {
            selectedProvider = config.selected_provider;
            selectedModel = config.selected_model;
            currentConversationId = config.selected_conversation_id;
            selectedSystemMessageId = config.selected_system_message_id;
            thinkToggle.checked = config.think_mode;
            thinkDepth.value = config.think_depth;
            openaiBaseUrlInput.value = config.openai_base_url;
            llmProvider.value = selectedProvider;
            llmModel.value = selectedModel;
            if (selectedProvider === 'openai') {
                openaiBaseUrlGroup.style.display = 'flex';
            }
            fetchModels(selectedProvider);
            if (currentConversationId) {
                loadConversation(currentConversationId);
            }
            if (selectedSystemMessageId) {
                fetch(`http://127.0.0.1:5000/api/system_messages/${selectedSystemMessageId}`)
                    .then(response => response.json())
                    .then(data => {
                        systemMessageTextarea.value = data.content;
                        document.getElementById('system-message-name').value = data.name;
                    })
                    .catch(error => console.error('Error fetching system message:', error));
            }
            const savedTools = config.selected_tools;
            if (savedTools && savedTools.length > 0) {
                savedTools.forEach(toolName => {
                    const toolTag = document.createElement('span');
                    toolTag.classList.add('tool-tag', 'active-tool-tag');
                    toolTag.textContent = toolName;
                    const deleteButton = document.createElement('button');
                    deleteButton.innerHTML = '<i class="fas fa-times"></i>';
                    deleteButton.classList.add('delete-active-tool-button');
                    deleteButton.addEventListener('click', () => {
                        toolTag.remove();
                    });
                    toolTag.appendChild(deleteButton);
                    activeToolsContainer.appendChild(toolTag);
                });
            }
        }*/
    }
    

    // Initialize variables
    let selectedProvider = llmProvider.value;
    let selectedModel = llmModel.value;
    let uploadedImage = null;
    let chatHistory = [];
    let systemMessage = systemMessageTextarea.value;
    let currentConversationId = null;
    let firstMessage = true;
    let conversationTitle = null;
    let lastResponse = null;
    let previousResponses = [];
    let selectedSystemMessageId = null;
    let responseStartTime = null;
    const tokensPerSecondDisplay = document.getElementById('tokens-per-second');

    // Function to add a message to the chat window
    function addMessage(message, isUser = true, messageDiv = null) {
        if (!messageDiv) {
            messageDiv = document.createElement('div');
            messageDiv.classList.add('message', isUser ? 'user-message' : 'llm-message');
        }
        if (typeof message === 'string') {
            if (isUser) {
                messageDiv.innerHTML = message.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, '<br>').replace(/  /g, '&nbsp; ');
                messageDiv.style.whiteSpace = 'pre-wrap';
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

        if (!isUser) {
            const regenerateButton = document.createElement('button');
            regenerateButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
            regenerateButton.classList.add('regenerate-button');
            messageDiv.appendChild(regenerateButton);
            regenerateButton.addEventListener('click', () => {
                regenerateResponse(messageDiv);
            });
        }
        if (!messageDiv.parentNode) {
            chatWindow.appendChild(messageDiv);
        }
        if (document.body.classList.contains('dark-mode')) {
            messageDiv.classList.add('dark-mode');
        }
        chatWindow.scrollTop = chatWindow.scrollHeight;
        return messageDiv;
    }

    // Function to regenerate a response
    async function regenerateResponse(messageDiv) {
        const index = Array.from(chatWindow.children).indexOf(messageDiv);
        if (index > -1) {
            // Remove all messages after the clicked message, including the clicked message
            const messagesToRemove = Array.from(chatWindow.children).slice(index);
            messagesToRemove.forEach(msg => msg.remove());
            
            // Rebuild chat history
            chatHistory = chatHistory.slice(0, index);
            previousResponses = previousResponses.slice(0, index);

            const message = previousResponses[index - 1];
            if (message) {
                const userMessageDiv = addMessage(message.prompt);
                chatHistory.push({ role: "user", content: message.prompt });
                
                const formData = new FormData();
                formData.append('prompt', message.prompt);
                formData.append('model', message.model);
                formData.append('provider', message.provider)
                formData.append('history', JSON.stringify(chatHistory));
                if (message.image) {
                    formData.append('image', message.image);
                }
                formData.append('system_message', message.systemMessage);
                if (message.conversationId) {
                    formData.append('conversation_id', message.conversationId);
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
                        prompt: message.prompt,
                        response: partialResponse,
                        conversationId: message.conversationId,
                        model: message.model,
                        provider: message.provider,
                        systemMessage: message.systemMessage,
                        image: message.image
                    });
                } catch (error) {
                    console.error('Failed to send message:', error);
                    addMessage(`Error generating response: ${error.message}`, false);
                }
            }
        }
    }

    // Event listener for delete all tasks button
    deleteAllTasksButton.addEventListener('click', async () => {
        try {
            const response = await fetch('http://127.0.0.1:5000/api/simple_responses', {
                method: 'DELETE'
            });
            if (response.ok) {
                console.log('All simple responses deleted.');
                loadConversationsModal();
                taskResponseModal.style.display = 'none';
            } else {
                console.error('Failed to delete all simple responses:', response.statusText);
            }
        } catch (error) {
            console.error('Error deleting all simple responses:', error);
        }
    });

    // Event listener to close task response modal
    taskResponseModal.addEventListener('click', (event) => {
        if (event.target === taskResponseModal) {
            taskResponseModal.style.display = 'none';
        }
    });

    // Function to fetch and display tools
    async function fetchTools() {
        try {
            const response = await fetch('http://127.0.0.1:5000/api/tools');
            if (!response.ok) {
                console.error('Failed to fetch tools:', response.statusText);
                return;
            }
            const tools = await response.json();
            toolsContainer.innerHTML = '';
            tools.forEach(tool => {
                const toolTag = document.createElement('span');
                toolTag.classList.add('tool-tag', 'draggable-tool');
                toolTag.textContent = tool.name;
                toolTag.title = tool.description;
                
                toolTag.draggable = true;
                toolTag.addEventListener('dragstart', handleDragStart);
                toolsContainer.appendChild(toolTag);
            });
        } catch (error) {
            console.error('Error fetching tools:', error);
        }
    }

    function handleDragStart(event) {
        event.dataTransfer.setData('text/plain', event.target.textContent);
    }

    activeToolsContainer.addEventListener('dragover', (event) => {
        event.preventDefault();
    });

    activeToolsContainer.addEventListener('drop', (event) => {
        event.preventDefault();
        const toolName = event.dataTransfer.getData('text/plain');
        const toolTag = document.createElement('span');
        toolTag.classList.add('tool-tag', 'active-tool-tag');
        toolTag.textContent = toolName;
        const deleteButton = document.createElement('button');
        deleteButton.innerHTML = '<i class="fas fa-times"></i>';
        deleteButton.classList.add('delete-active-tool-button');
        deleteButton.addEventListener('click', () => {
            toolTag.remove();
        });
        toolTag.appendChild(deleteButton);
        activeToolsContainer.appendChild(toolTag);
    });

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
            if (models && models.length > 0) {
                availableModels = models;
                selectedModel = models[0];
                llmModel.value = selectedModel;
                updateStatus();
            } else {
                 console.error('No models returned from the API.');
                 addMessage('No models available for this provider.', false);
                 llmModel.value = 'No models available';
            }
        } catch (error) {
            console.error('Failed to fetch models:', error);
            addMessage(`Error loading models: ${error.message}`, false)
            llmModel.value = 'Error loading models';
        }
    }

    // Function to update the status display
    function updateStatus() {
        llmStatus.textContent = `${selectedProvider}, ${selectedModel}`;
    }
    
    // Set initial status
    updateStatus();

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
                const title = conversation.title ? conversation.title : `Conversation ${conversation.id}`;
                listItem.textContent = `${title} (${conversation.provider}, ${conversation.model}, ${new Date(conversation.created_at).toLocaleString()})`;
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
            if (data && data.conversation && data.conversation.title) {
                conversationTitle = data.conversation.title;
            } else {
                conversationTitle = `Conversation ${conversationId}`;
            }
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

    // Event listener for show conversations button
    showConversationsButton.addEventListener('click', () => {
        conversationsModal.style.display = 'block';
        loadConversationsModal();
    });

    // Event listener for close modal button
    closeModalButton.addEventListener('click', () => {
        conversationsModal.style.display = 'none';
    });

    // Event listener for closing modal when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === conversationsModal) {
            conversationsModal.style.display = 'none';
        }
    });

    // Function to toggle dark mode on modal
    function toggleModalDarkMode(isDark) {
        const modalContent = document.querySelector('.modal-content');
        if (modalContent) {
            modalContent.classList.toggle('dark-mode', isDark);
            const modalTitle = document.querySelector('.modal-title');
            if (modalTitle) {
                modalTitle.classList.toggle('dark-mode', isDark);
            }
        }
    }

    // Function to load simple responses into the modal
    async function loadConversationsModal() {
        try {
            const response = await fetch('http://127.0.0.1:5000/api/simple_responses');
            if (!response.ok) {
                console.error('Failed to fetch simple responses:', response.statusText);
                return;
            }
            const simpleResponses = await response.json();
            conversationsListModal.innerHTML = '';
            simpleResponses.forEach(response => {
                const listItem = document.createElement('li');
                listItem.classList.add('task-list-item');
                listItem.innerHTML = `
                    <div class="task-item-content">
                        <strong>${response.prompt}</strong>
                        <small>Date: ${new Date(response.created_at).toLocaleString()}</small>
                    </div>
                    <button class="delete-task-button" data-task-id="${response.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                `;
                listItem.addEventListener('click', () => showTaskResponse(response.id));
                conversationsListModal.appendChild(listItem);
            });
            // Add event listeners to delete buttons
            conversationsListModal.querySelectorAll('.delete-task-button').forEach(button => {
                button.addEventListener('click', (event) => {
                    event.stopPropagation();
                    const taskId = button.getAttribute('data-task-id');
                    deleteSimpleResponse(taskId);
                });
            });
        } catch (error) {
            console.error('Error fetching simple responses:', error);
        }
    }

    // Function to show task response
    async function showTaskResponse(taskId) {
        try {
            const response = await fetch(`http://127.0.0.1:5000/api/simple_responses`);
             if (!response.ok) {
                console.error('Failed to fetch simple responses:', response.statusText);
                return;
            }
            const simpleResponses = await response.json();
            const task = simpleResponses.find(task => task.id === taskId);
            if (task) {
                taskResponseContent.textContent = task.response;
                hljs.highlightBlock(taskResponseContent);
                taskResponseModal.style.display = 'block';
            } else {
                console.error('Task not found:', taskId);
            }
        } catch (error) {
            console.error('Error fetching task response:', error);
        }
    }

    // Function to delete a simple response
    async function deleteSimpleResponse(taskId) {
        try {
            const response = await fetch(`http://127.0.0.1:5000/api/simple_responses/${taskId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                console.log(`Simple response ${taskId} deleted.`);
                loadConversationsModal();
            } else {
                console.error('Failed to delete simple response:', response.statusText);
            }
        } catch (error) {
            console.error('Error deleting simple response:', error);
        }
    }

    // Event listener for think depth change
    thinkDepth.addEventListener('change', () => {
        if (thinkDepth.value === '0') {
            thinkDepthMessage.textContent = 'La profundidad se determinará automaticamente';
        } else {
            thinkDepthMessage.textContent = '';
        }
    });

    // Event listener for provider change
    llmProvider.addEventListener('change', async () => {
        selectedProvider = llmProvider.value;
        if (selectedProvider === 'openai') {
            openaiBaseUrlGroup.style.display = 'flex';
            if (openaiBaseUrlInput.value.trim() !== '') {
                llmModel.innerHTML = '<option value="Default">Default</option>';
            }
        } else {
            openaiBaseUrlGroup.style.display = 'none';
        }
        await fetchModels(selectedProvider);
        updateStatus();
        saveConfig();
    });

    // Event listener for model input change
    llmModel.addEventListener('input', () => {
        selectedModel = llmModel.value;
        updateStatus();
    });

    // Event listener for model input focus to show autocomplete
    llmModel.addEventListener('focus', () => {
        const datalistId = 'models-list';
        let datalist = document.getElementById(datalistId);
        if (!datalist) {
            datalist = document.createElement('datalist');
            datalist.id = datalistId;
            document.body.appendChild(datalist);
        }
        datalist.innerHTML = '';
        availableModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            datalist.appendChild(option);
        });
        llmModel.setAttribute('list', datalistId);
    });

    // Event listener for base URL input change
    openaiBaseUrlInput.addEventListener('input', () => {
        if (openaiBaseUrlInput.value.trim() !== '') {
            llmModel.innerHTML = '<option value="Default">Default</option>';
        } else {
            fetchModels(selectedProvider);
        }
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
            const activeTools = Array.from(activeToolsContainer.querySelectorAll('.active-tool-tag')).map(tool => tool.textContent);
            formData.append('selected_tools', JSON.stringify(activeTools));
            formData.append('think', thinkToggle.checked);
            formData.append('think_depth', thinkDepth.value);
            if (selectedProvider === 'openai' && openaiBaseUrlInput.value.trim() !== '') {
                formData.append('base_url', openaiBaseUrlInput.value.trim());
                formData.append('model', '');
            }
            if (firstMessage) {
                conversationTitle = message;
                formData.append('conversation_title', conversationTitle);
            }

            let apiUrl = 'http://127.0.0.1:5000/api/generate';
            if (thinkToggle.checked) {
                apiUrl = 'http://127.0.0.1:5000/api/think';
            }

            try {
                const response = await fetch(apiUrl, {
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
                responseStartTime = performance.now();
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
                const responseEndTime = performance.now();
                const elapsedTime = (responseEndTime - responseStartTime) / 1000;
                const tokens = partialResponse.split(/\s+/).length;
                const tokensPerSecond = (tokens / elapsedTime).toFixed(2);
                tokensPerSecondDisplay.textContent = `${tokensPerSecond} tokens/sec`;
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
        toggleModalDarkMode(darkModeToggle.checked);
    });

    // Function to set initial dark mode based on system preference
    function setInitialDarkMode() {
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        darkModeToggle.checked = prefersDark;
        toggleDarkMode(prefersDark);
        toggleModalDarkMode(prefersDark);
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

    // Event listener for stop button
    stopButton.addEventListener('click', async () => {
        try {
            const response = await fetch('http://127.0.0.1:5000/api/stop', {
                method: 'POST'
            });
            if (response.ok) {
                console.log('Streaming stopped.');
            } else {
                console.error('Failed to stop streaming:', response.statusText);
            }
        } catch (error) {
            console.error('Error stopping streaming:', error);
        }
    });

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
    fetchTools();
    updateStatus();
    loadConversations();
    setInitialDarkMode();
    setTimeout(loadConfig, 2000);
});
