const config = {
    load: () => {
        try {
            const storedConfig = localStorage.getItem('appConfig');
            return storedConfig ? JSON.parse(storedConfig) : {};
        } catch (error) {
            console.error('Error loading config:', error);
            return {};
        }
    },
    save: (newConfig) => {
        try {
            localStorage.setItem('appConfig', JSON.stringify(newConfig));
        } catch (error) {
             console.error('Error saving config:', error);
        }
    },
    apply: (elements) => {
        const savedConfig = config.load();
        elements.forEach(element => {
            if (savedConfig[element.id]) {
                if (element.type === 'checkbox') {
                    element.checked = savedConfig[element.id];
                } else {
                    element.value = savedConfig[element.id];
                }
            }
        });
    },
    collect: (elements) => {
        const currentConfig = {};
        elements.forEach(element => {
            currentConfig[element.id] = element.type === 'checkbox' ? element.checked : element.value;
        });
        return currentConfig;
    }
};

export default config;
