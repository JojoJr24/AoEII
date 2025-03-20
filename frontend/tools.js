import { elements } from './domElements.js';

export async function fetchToolModes() {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/tool_modes');
        if (!response.ok) {
            console.error('Failed to fetch modes:', response.statusText);
            return null;
        }
        const toolNames = await response.json();
        elements.toolsContainer.innerHTML = '';
        toolNames.forEach(toolName => {
            const toolTag = document.createElement('span');
            toolTag.classList.add('tool-tag', 'draggable-tool');
            toolTag.textContent = toolName;
            toolTag.title = toolName;
            
            toolTag.draggable = true;
            toolTag.addEventListener('dragstart', handleDragStart);
            elements.toolsContainer.appendChild(toolTag);
        });
        return modes;
    } catch (error) {
        console.error('Error fetching modes:', error);
        return null;
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
    modeName = modeName.trim();

    // Check if tool already exists
    const existingTool = Array.from(elements.activeToolsContainer.querySelectorAll('.active-tool-tag'))
        .find(tool => tool.textContent.trim() === modeName);

    if (existingTool) {
        console.log('Tool already exists:', modeName);
        return; // Don't add if already exists
    }

    const toolTag = document.createElement('span');
    toolTag.classList.add('tool-tag', 'active-tool-tag');
    toolTag.textContent = modeName;

    const deleteButton = document.createElement('button');
    deleteButton.textContent = '×';
    deleteButton.classList.add('delete-active-tool-button');
    deleteButton.addEventListener('click', (e) => {
        e.stopPropagation();
        toolTag.remove();
    });

    toolTag.appendChild(deleteButton);
    elements.activeToolsContainer.appendChild(toolTag);
}

export function setupToolListeners() {
    let isDragging = false;
    
    // Setup drag and drop for tools
    elements.activeToolsContainer.addEventListener('dragenter', (event) => {
        event.preventDefault();
        isDragging = true;
    });

    elements.activeToolsContainer.addEventListener('dragleave', () => {
        isDragging = false;
    });

    elements.activeToolsContainer.addEventListener('dragover', (event) => {
        event.preventDefault();
        if (!isDragging) {
            isDragging = true;
        }
    });

    elements.activeToolsContainer.addEventListener('drop', (event) => {
        event.preventDefault();
        event.stopPropagation();
        isDragging = false;
        
        const modeName = event.dataTransfer.getData('text/plain');
        if (!modeName || !modeName.trim()) return;

        const trimmedModeName = modeName.trim();

        // Check if tool already exists
        const existingTool = Array.from(elements.activeToolsContainer.querySelectorAll('.active-tool-tag'))
            .find(tool => tool.textContent.trim() === trimmedModeName);

        if (existingTool) {
            console.log('Tool already exists:', trimmedModeName);
            return;
        }

        console.log('Adding new tool:', trimmedModeName);
        addActiveTool(trimmedModeName);
    });
}