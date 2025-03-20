// Configuration management
export function saveConfig() {
    const config = {
        selected_provider: "",
        selected_model: "",
        selected_conversation_id: "",
        selected_system_message_id: "",
        selected_modes: [],
        think_mode: false,
        think_depth: 0,
        openai_base_url: ""
    };

    localStorage.setItem('config', JSON.stringify(config));
    console.log('Config saved in localStorage!');
}

export function loadConfig() {
    const configStr = localStorage.getItem('config');
    if (configStr) {
        try {
            const config = JSON.parse(configStr);
            // Apply loaded configuration
            return config;
        } catch (e) {
            console.error('Error parsing config:', e);
            return null;
        }
    }
    return null;
}