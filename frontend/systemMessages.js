import { elements } from './domElements.js';

export async function fetchSystemMessages() {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/system_messages');
        if (!response.ok) {
            console.error('Failed to fetch system messages:', response.statusText);
            return;
        }
        const systemMessages = await response.json();
        elements.systemMessageSelect.innerHTML = '<option value="">None</option>';
        systemMessages.forEach(message => {
            const option = document.createElement('option');
            option.value = message.id;
            option.textContent = `${message.name} (${message.content.length > 50 ? message.content.substring(0, 50) + '...' : message.content})`;
            elements.systemMessageSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error fetching system messages:', error);
    }
}

export async function saveSystemMessage() {
    const content = elements.systemMessageTextarea.value;
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

export async function deleteSystemMessage(messageId) {
    if (messageId) {
        try {
            const response = await fetch(`http://127.0.0.1:5000/api/system_messages/${messageId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                console.log(`System message ${messageId} deleted.`);
                elements.systemMessageTextarea.value = '';
                fetchSystemMessages();
            } else {
                console.error('Failed to delete system message:', response.statusText);
            }
        } catch (error) {
            console.error('Error deleting system message:', error);
        }
    }
}

export async function loadSystemMessage(messageId) {
    if (messageId) {
        try {
            const response = await fetch(`http://127.0.0.1:5000/api/system_messages/${messageId}`);
            if (response.ok) {
                const data = await response.json();
                elements.systemMessageTextarea.value = data.content;
                document.getElementById('system-message-name').value = data.name;
            } else {
                console.error('Failed to load system message:', response.statusText);
            }
        } catch (error) {
            console.error('Error loading system message:', error);
        }
    } else {
        elements.systemMessageTextarea.value = '';
        document.getElementById('system-message-name').value = '';
    }
}