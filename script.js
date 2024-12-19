document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const llmProvider = document.getElementById('llm-provider');
    const llmModel = document.getElementById('llm-model');
    const llmStatus = document.getElementById('llm-status');
    const imageUpload = document.getElementById('image-upload');
    const uploadButton = document.getElementById('upload-button');
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const darkModeToggleHeader = document.getElementById('dark-mode-toggle-header');
    const sidebar = document.querySelector('.sidebar');
    const inputWithUpload = document.querySelector('.input-with-upload');
    const formSelects = document.querySelectorAll('.form-group select');


    let selectedProvider = llmProvider.value;
    let selectedModel = llmModel.value;
    let uploadedImage = null;

    // Function to add a message to the chat window
    function addMessage(message, isUser = true) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', isUser ? 'user-message' : 'llm-message');
        
        if (typeof message === 'string') {
            if (isUser) {
                messageDiv.textContent = message;
            } else {
                // Parse markdown and highlight code blocks
                messageDiv.innerHTML = marked.parse(message);
                messageDiv.querySelectorAll('pre code').forEach(block => {
                    hljs.highlightBlock(block);
                    // Add copy button
                    const copyButton = document.createElement('button');
                    copyButton.textContent = 'Copiar';
                    copyButton.classList.add('copy-button');
                    copyButton.addEventListener('click', () => {
                        navigator.clipboard.writeText(block.textContent).then(() => {
                            copyButton.textContent = 'Copiado!';
                            setTimeout(() => {
                                copyButton.textContent = 'Copiar';
                            }, 2000);
                        });
                    });
                    block.parentNode.insertBefore(copyButton, block);
                });
            }
        } else if (message instanceof HTMLImageElement) {
            messageDiv.appendChild(message);
        }
        
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll
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
        llmStatus.textContent = `Proveedor seleccionado: ${selectedProvider}, Modelo seleccionado: ${selectedModel}`;
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
            if (uploadedImage) {
                formData.append('image', uploadedImage);
            }

            try {
                const response = await fetch('http://127.0.0.1:5000/api/generate', {
                    method: 'POST',
                    body: formData,
                });
                if (!response.ok) {
                    const errorMsg = `HTTP error! status: ${response.status}`;
                    console.error('Failed to send message:', errorMsg);
                    addMessage(`Error generating response: ${errorMsg}`, false);
                    return;
                }
                const data = await response.json();
                addMessage(data.response, false);
                uploadedImage = null; // Clear the uploaded image after sending
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
    function toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
        sidebar.classList.toggle('dark-mode');
        chatWindow.classList.toggle('dark-mode');
        inputWithUpload.classList.toggle('dark-mode');
        formSelects.forEach(select => select.classList.toggle('dark-mode'));
        const messages = document.querySelectorAll('.message');
        messages.forEach(message => message.classList.toggle('dark-mode'));
    }

    // Event listener for dark mode toggle
    darkModeToggle.addEventListener('change', toggleDarkMode);
    darkModeToggleHeader.addEventListener('change', toggleDarkMode);

    // Initial fetch of models
    fetchModels(selectedProvider);
    updateStatus();
});
