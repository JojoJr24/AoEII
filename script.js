document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const llmProvider = document.getElementById('llm-provider');
    const llmModel = document.getElementById('llm-model');
    const llmStatus = document.getElementById('llm-status');
    const imageUpload = document.getElementById('image-upload');
    const uploadButton = document.getElementById('upload-button');

    let selectedProvider = llmProvider.value;
    let selectedModel = llmModel.value;
    let uploadedImage = null;

    // Function to add a message to the chat window
    function addMessage(message, isUser = true) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', isUser ? 'user-message' : 'llm-message');
        
        if (typeof message === 'string') {
            messageDiv.textContent = message;
        } else if (message instanceof HTMLImageElement) {
            messageDiv.appendChild(message);
        }
        
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll
    }

    // Function to fetch available models for the selected provider
    async function fetchModels(provider) {
        try {
            const response = await fetch(`/api/models?provider=${provider}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const models = await response.json();
            llmModel.innerHTML = ''; // Clear existing options
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                llmModel.appendChild(option);
            });
            selectedModel = models[0];
            llmModel.value = selectedModel;
            updateStatus();
        } catch (error) {
            console.error('Failed to fetch models:', error);
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
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    body: formData,
                });
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                addMessage(data.response, false);
                uploadedImage = null; // Clear the uploaded image after sending
            } catch (error) {
                console.error('Failed to send message:', error);
                addMessage('Error generating response.', false);
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

    // Initial fetch of models
    fetchModels(selectedProvider);
    updateStatus();
});
