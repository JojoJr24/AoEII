import { elements } from './domElements.js';
import { saveConfig, loadConfig } from './config.js';
import { addMessage, sendMessage, state } from './chat.js';
import { loadConversations, loadConversationsModal, deleteAllConversations, deleteAllTasks } from './conversations.js';
import { fetchSystemMessages, saveSystemMessage, deleteSystemMessage, loadSystemMessage } from './systemMessages.js';
import { toggleDarkMode, setInitialDarkMode, handleImageUpload, setupModalHandlers, setupDragAndDrop, updateThinkDepthMessage, toggleOpenAIBaseUrl, updateLLMStatus, setupModelAutocomplete } from './ui.js';
import { fetchToolModes, setupToolListeners } from './tools.js';

// State variables
let selectedProvider = elements.llmProvider.value;
let selectedModel = elements.llmModel.value;
let availableModels = [];

// Function to fetch available models
export async function fetchModels(provider) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/api/models?provider=${provider}`);
        if (!response.ok) {
            const message = `HTTP error! status: ${response.status}`;
            console.error('Failed to fetch models:', message);
            addMessage(`Error loading models: ${message}`, false)
            elements.llmModel.innerHTML = '<option>Error loading models</option>';
            return null;
        }
        const models = await response.json();
        if (models && models.length > 0) {
            availableModels = models;
            selectedModel = models[0];
            elements.llmModel.value = selectedModel;
            setupModelAutocomplete(models);
            updateLLMStatus(selectedProvider, selectedModel);
            saveConfig();
            return models;
        } else {
            console.error('No models returned from the API.');
            addMessage('No models available for this provider.', false);
            elements.llmModel.value = 'No models available';
            elements.llmModel.setAttribute('list', '');
            return null;
        }
    } catch (error) {
        console.error('Failed to fetch models:', error);
        addMessage(`Error loading models: ${error.message}`, false)
        elements.llmModel.value = 'Error loading models';
        return null;
    }
}

// Function to initialize all data
async function initializeAllData() {
    try {
        // Load config first
        const config = loadConfig();
        
        // Apply config settings
        if (config) {
            if (config.selected_provider) {
                selectedProvider = config.selected_provider;
                elements.llmProvider.value = selectedProvider;
            }
            if (config.openai_base_url) {
                elements.openaiBaseUrlInput.value = config.openai_base_url;
            }
            if (config.think_mode !== undefined) {
                elements.thinkToggle.checked = config.think_mode;
            }
            if (config.think_depth !== undefined) {
                elements.thinkDepth.value = config.think_depth;
                elements.thinkDepth.dispatchEvent(new Event('change'));
            }
        }

        // Load all required data in parallel
        const [models] = await Promise.all([
            fetchModels(selectedProvider),
            fetchSystemMessages(),
            fetchToolModes(),
            loadConversations()
        ]);

        // Apply model from config after models are loaded
        if (config && config.selected_model && models) {
            if (models.includes(config.selected_model)) {
                selectedModel = config.selected_model;
                elements.llmModel.value = selectedModel;
                updateLLMStatus(selectedProvider, selectedModel);
            }
        }

        // Trigger base URL input event if needed
        if (config && config.openai_base_url) {
            elements.openaiBaseUrlInput.dispatchEvent(new Event('input'));
        }


    } catch (error) {
        console.error('Error initializing app:', error);
        addMessage('Error al conectar con el backend. Por favor intente nuevamente.', false);
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize UI
    setInitialDarkMode();
    setupModalHandlers();
    setupDragAndDrop();
    setupToolListeners();

    // Event listener for connect button
    elements.connectBackendButton.addEventListener('click', initializeAllData);

    // Event listener for provider change
    elements.llmProvider.addEventListener('change', async () => {
        selectedProvider = elements.llmProvider.value;
        toggleOpenAIBaseUrl(selectedProvider);
        await fetchModels(selectedProvider);
        updateLLMStatus(selectedProvider, selectedModel);
        saveConfig();
    });

    // Event listener for model change
    elements.llmModel.addEventListener('input', () => {
        selectedModel = elements.llmModel.value;
        updateLLMStatus(selectedProvider, selectedModel);
    });

    // Event listener for model focus (autocomplete)
    elements.llmModel.addEventListener('focus', () => {
        setupModelAutocomplete(availableModels);
    });

    // Event listener for base URL input change
    elements.openaiBaseUrlInput.addEventListener('input', () => {
        if (elements.openaiBaseUrlInput.value.trim() !== '') {
            elements.llmModel.innerHTML = '<option value="Default">Default</option>';
        } else {
            fetchModels(selectedProvider);
        }
    });

    // Event listener for send button
    elements.sendButton.addEventListener('click', async () => {
        const message = elements.userInput.value.trim();
        if (message) {
            addMessage(message);
            state.chatHistory.push({ role: "user", content: message });
            elements.userInput.value = '';
            await sendMessage(message);
        }
    });

    // Event listener for image upload
    elements.uploadButton.addEventListener('click', () => {
        elements.imageUpload.click();
    });

    elements.imageUpload.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            handleImageUpload(file);
        }
    });

    // Event listener for user input keydown
    elements.userInput.addEventListener('keydown', async (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            elements.sendButton.click();
        }
    });

    // Event listener for dark mode toggle
    elements.darkModeToggle.addEventListener('change', () => {
        toggleDarkMode(elements.darkModeToggle.checked);
    });

    // Event listener for system message select
    elements.systemMessageSelect.addEventListener('change', () => {
        loadSystemMessage(elements.systemMessageSelect.value);
    });

    // Event listener for save system message
    elements.saveSystemMessageButton.addEventListener('click', saveSystemMessage);

    // Event listener for delete system message
    elements.deleteSystemMessageButton.addEventListener('click', () => {
        deleteSystemMessage(elements.systemMessageSelect.value);
    });

    // Event listener for stop button
    elements.stopButton.addEventListener('click', async () => {
        try {
            const response = await fetch('http://127.0.0.1:5000/api/stop', {
                method: 'POST'
            });
            if (!response.ok) {
                console.error('Failed to stop streaming:', response.statusText);
            }
        } catch (error) {
            console.error('Error stopping streaming:', error);
        }
    });

    // Event listener for reset button
    elements.resetButton.addEventListener('click', () => {
        state.chatHistory = [];
        elements.chatWindow.innerHTML = '';
        state.currentConversationId = null;
        state.firstMessage = true;
        state.previousResponses = [];
    });

    // Event listener for sidebar toggle
    elements.sidebarToggle.addEventListener('click', () => {
        elements.sidebar.classList.toggle('collapsed');
    });

    // Event listener for show conversations button
    elements.showConversationsButton.addEventListener('click', () => {
        elements.conversationsModal.style.display = 'block';
        loadConversationsModal();
    });

    // Event listener for delete all conversations button
    elements.deleteAllConversationsButton.addEventListener('click', (event) => {
        event.preventDefault();
        deleteAllConversations();
    });

    // Event listener for delete all tasks button
    elements.deleteAllTasksButton.addEventListener('click', deleteAllTasks);

    // Event listener for think depth change
    elements.thinkDepth.addEventListener('change', updateThinkDepthMessage);

    // Event listener for conversation created
    window.addEventListener('conversationCreated', loadConversations);

    // Initialize the application
    initializeAllData();
});
