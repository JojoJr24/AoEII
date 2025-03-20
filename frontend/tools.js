import { elements } from './domElements.js';

export async function fetchToolModes() {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/tool_modes');
        if (!response.ok) {
            console.error('Failed to fetch modes:', response.statusText);
            return;
        }
        const modes = await response.json();
        elements.toolsContainer.innerHTML = '';
        modes.forEach(mode => {
            const toolTag = document.createElement('span');
            toolTag.classList.add('tool-tag', 'draggable-tool');
            toolTag.textContent = mode;
            toolTag.title = mode;
            
            toolTag.draggable = true;
            toolTag.addEventListener('dragstart', handleDragStart);
            elements.toolsContainer.appendChild(toolTag);
        });
    } catch (error) {
        console.error('Error fetching modes:', error);
    }
}

function handleDragStart(event) {
    event.dataTransfer.setData('text/plain', event.target.textContent);
}

export function getActiveTools() {
    return Array.from(elements.activeToolsContainer.querySelectorAll('.active-tool-tag'))
        .map(tool => tool.textContent);
}

export function clearActiveTools() {
    elements.activeToolsContainer.innerHTML = '';
}

export function addActiveTool(modeName) {
    const toolTag = document.createElement('span');
    toolTag.classList.add('tool-tag', 'active-tool-tag');
    toolTag.textContent = modeName;
    
    const deleteButton = document.createElement('button');
    deleteButton.innerHTML = '<i class="fas fa-times"></i>';
    deleteButton.classList.add('delete-active-tool-button');
    deleteButton.addEventListener('click', () => toolTag.remove());
    
    toolTag.appendChild(deleteButton);
    elements.activeToolsContainer.appendChild(toolTag);
}

export function setupToolListeners() {
    // Setup drag and drop for tools
    elements.activeToolsContainer.addEventListener('dragover', (event) => {
        event.preventDefault();
    });

    elements.activeToolsContainer.addEventListener('drop', (event) => {
        event.preventDefault();
        const modeName = event.dataTransfer.getData('text/plain');
        addActiveTool(modeName);
    });
}