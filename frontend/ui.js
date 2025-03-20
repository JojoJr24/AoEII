import { elements } from './domElements.js';

export function toggleDarkMode(isDark) {
    document.body.classList.toggle('dark-mode', isDark);
    elements.sidebar.classList.toggle('dark-mode', isDark);
    elements.chatWindow.classList.toggle('dark-mode', isDark);
    elements.inputWithUpload.classList.toggle('dark-mode', isDark);
    elements.formSelects.forEach(select => select.classList.toggle('dark-mode', isDark));
    const messages = document.querySelectorAll('.message');
    messages.forEach(message => message.classList.toggle('dark-mode', isDark));
    toggleModalDarkMode(isDark);
}

export function toggleModalDarkMode(isDark) {
    const modalContent = document.querySelector('.modal-content');
    if (modalContent) {
        modalContent.classList.toggle('dark-mode', isDark);
        const modalTitle = document.querySelector('.modal-title');
        if (modalTitle) {
            modalTitle.classList.toggle('dark-mode', isDark);
        }
    }
}

export function setInitialDarkMode() {
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    elements.darkModeToggle.checked = prefersDark;
    toggleDarkMode(prefersDark);

    // Listen for system dark mode changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        elements.darkModeToggle.checked = e.matches;
        toggleDarkMode(e.matches);
    });
}

export function handleImageUpload(file) {
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.style.maxWidth = '100px';
            // Dispatch custom event with the image
            window.dispatchEvent(new CustomEvent('imageUploaded', { 
                detail: { image: img, file: file }
            }));
        };
        reader.readAsDataURL(file);
    }
}

export function setupModalHandlers() {
    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === elements.conversationsModal) {
            elements.conversationsModal.style.display = 'none';
        }
        if (event.target === elements.taskResponseModal) {
            elements.taskResponseModal.style.display = 'none';
        }
    });

    // Close modal with close button
    elements.closeModalButton.addEventListener('click', () => {
        elements.conversationsModal.style.display = 'none';
    });
}

export function setupDragAndDrop() {
    elements.activeToolsContainer.addEventListener('dragover', (event) => {
        event.preventDefault();
    });

    elements.activeToolsContainer.addEventListener('drop', (event) => {
        event.preventDefault();
        const modeName = event.dataTransfer.getData('text/plain');
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

export function updateThinkDepthMessage() {
    if (elements.thinkDepth.value === '0') {
        elements.thinkDepthMessage.textContent = 'La profundidad se determinará automaticamente';
    } else {
        elements.thinkDepthMessage.textContent = '';
    }
}

export function toggleOpenAIBaseUrl(provider) {
    if (provider === 'openai') {
        elements.openaiBaseUrlGroup.style.display = 'flex';
    } else {
        elements.openaiBaseUrlGroup.style.display = 'none';
    }
}

export function updateLLMStatus(provider, model) {
    elements.llmStatus.textContent = `${provider}, ${model}`;
}

export function setupModelAutocomplete(availableModels) {
    elements.llmModel.innerHTML = '';
    if (availableModels && availableModels.length > 0) {
        availableModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            elements.llmModel.appendChild(option);
        });
    } else {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No models available';
        elements.llmModel.appendChild(option);
    }
}

// Save dark mode preference to localStorage
function saveDarkModePreference(isDark) {
    localStorage.setItem('darkMode', isDark);
}

// Load dark mode preference from localStorage
function loadDarkModePreference() {
    const savedPreference = localStorage.getItem('darkMode');
    if (savedPreference !== null) {
        const isDark = savedPreference === 'true';
        elements.darkModeToggle.checked = isDark;
        toggleDarkMode(isDark);
    }
}

// Initialize dark mode from saved preference
document.addEventListener('DOMContentLoaded', () => {
    loadDarkModePreference();
    elements.darkModeToggle.addEventListener('change', () => {
        const isDark = elements.darkModeToggle.checked;
        toggleDarkMode(isDark);
        saveDarkModePreference(isDark);
    });
});