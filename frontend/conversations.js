import { elements } from './domElements.js';
import { state, addMessage } from './chat.js';

export async function loadConversations() {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/conversations');
        if (!response.ok) {
            console.error('Failed to fetch conversations:', response.statusText);
            return;
        }
        const conversations = await response.json();
        elements.conversationList.innerHTML = '';
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
            elements.conversationList.appendChild(listItem);
        });
    } catch (error) {
        console.error('Error fetching conversations:', error);
    }
}

export async function loadConversation(conversationId) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/api/conversations/${conversationId}`);
        if (!response.ok) {
            console.error('Failed to fetch conversation:', response.statusText);
            return;
        }
        const data = await response.json();
        elements.chatWindow.innerHTML = '';
        state.chatHistory = [];
        if (data && data.messages) {
            data.messages.forEach(message => {
                addMessage(message.content, message.role === 'user');
            });
        }
        state.currentConversationId = conversationId;
    } catch (error) {
        console.error('Error fetching conversation:', error);
    }
}

export async function deleteConversation(conversationId) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/api/conversations/${conversationId}`, {
            method: 'DELETE'
        });
        if (response.ok) {
            console.log(`Conversation ${conversationId} deleted.`);
            if (state.currentConversationId === conversationId) {
                elements.chatWindow.innerHTML = '';
                state.chatHistory = [];
                state.currentConversationId = null;
                state.firstMessage = true;
                state.previousResponses = [];
            }
            await loadConversations();
        } else {
            console.error('Failed to delete conversation:', response.statusText);
        }
    } catch (error) {
        console.error('Error deleting conversation:', error);
    }
}

export async function deleteAllConversations() {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/conversations', {
            method: 'DELETE'
        });
        if (response.ok) {
            console.log('All conversations deleted.');
            elements.chatWindow.innerHTML = '';
            state.chatHistory = [];
            state.currentConversationId = null;
            state.firstMessage = true;
            state.previousResponses = [];
            elements.conversationList.innerHTML = '';
        } else {
            console.error('Failed to delete all conversations:', response.statusText);
        }
    } catch (error) {
        console.error('Error deleting all conversations:', error);
    }
}

// Modal related functions
export function loadConversationsModal() {
    try {
        fetch('http://127.0.0.1:5000/api/simple_responses')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch simple responses: ' + response.statusText);
                }
                return response.json();
            })
            .then(simpleResponses => {
                elements.conversationsListModal.innerHTML = '';
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
                    elements.conversationsListModal.appendChild(listItem);
                });

                // Add event listeners to delete buttons
                elements.conversationsListModal.querySelectorAll('.delete-task-button').forEach(button => {
                    button.addEventListener('click', (event) => {
                        event.stopPropagation();
                        const taskId = button.getAttribute('data-task-id');
                        deleteSimpleResponse(taskId);
                    });
                });
            });
    } catch (error) {
        console.error('Error in loadConversationsModal:', error);
    }
}

export async function showTaskResponse(taskId) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/api/simple_responses`);
        if (!response.ok) {
            console.error('Failed to fetch simple responses:', response.statusText);
            return;
        }
        const simpleResponses = await response.json();
        const task = simpleResponses.find(task => task.id === taskId);
        if (task) {
            elements.taskResponseContent.textContent = task.response;
            hljs.highlightBlock(elements.taskResponseContent);
            elements.taskResponseModal.style.display = 'block';
        } else {
            console.error('Task not found:', taskId);
        }
    } catch (error) {
        console.error('Error fetching task response:', error);
    }
}

export async function deleteSimpleResponse(taskId) {
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

export async function deleteAllTasks() {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/simple_responses', {
            method: 'DELETE'
        });
        if (response.ok) {
            console.log('All simple responses deleted.');
            loadConversationsModal();
            elements.taskResponseModal.style.display = 'none';
        } else {
            console.error('Failed to delete all simple responses:', response.statusText);
        }
    } catch (error) {
        console.error('Error deleting all simple responses:', error);
    }
}