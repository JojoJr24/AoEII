import { elements } from './domElements.js';
import { fetchModels } from './main.js';

// Configuration management
export function saveConfig() {
    const config = {
        selected_provider: elements.llmProvider.value,
        selected_model: elements.llmModel.value,
        selected_conversation_id: "",
        selected_system_message_id: "",
        selected_modes: [],
        think_mode: elements.thinkToggle.checked,
        think_depth: parseInt(elements.thinkDepth.value),
        openai_base_url: elements.openaiBaseUrlInput.value
    };

    localStorage.setItem('config', JSON.stringify(config));
    console.log('Config saved in localStorage!');
}


export function loadConfig() {
     const config = JSON.parse(localStorage.getItem('config'));
     console.log('Loaded config:', config);
     if (config) {
         let selectedProvider = config.selected_provider;
         let selectedModel = config.selected_model;
         let currentConversationId = config.selected_conversation_id;
         let selectedSystemMessageId = config.selected_system_message_id;
         elements.thinkToggle.checked = config.think_mode;
         elements.thinkDepth.value = config.think_depth;
         elements.openaiBaseUrlInput.value = config.openai_base_url;
         elements.llmProvider.value = selectedProvider;
         elements.llmModel.value = selectedModel;
         if (selectedProvider === 'openai') {
             elements.openaiBaseUrlGroup.style.display = 'flex';
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
         const savedModes = config.selected_modes;
         if (savedModes && savedModes.length > 0) {
             savedModes.forEach(modeName => {
                 const toolTag = document.createElement('span');
                 toolTag.classList.add('tool-tag', 'active-tool-tag');
                 toolTag.textContent = modeName;
                 const deleteButton = document.createElement('button');
                 deleteButton.innerHTML = '<i class="fas fa-times"></i>';
                 deleteButton.classList.add('delete-active-tool-button');
                 deleteButton.addEventListener('click', () => {
                     toolTag.remove();
                 });
                 toolTag.appendChild(deleteButton);
                 elements.activeToolsContainer.appendChild(toolTag);
             });
         }
     }
 }