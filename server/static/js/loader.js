document.addEventListener('DOMContentLoaded', () => {
    const components = [
        '_panel_power_supply.html',
        '_panel_eload.html',
        '_panel_daq.html',
        '_panel_scope.html'
    ];

    const grid = document.querySelector('.instrument-grid');
    const componentPromises = components.map(url => fetch(`/static/components/${url}`).then(res => res.text()));

    Promise.all(componentPromises)
        .then(htmls => {
            grid.innerHTML = htmls.join('');
            // Now that the DOM is updated with the new panels, initialize the app logic
            if (typeof initializeApp === 'function') {
                initializeApp();
            } else {
                console.error('Error: initializeApp function not found. Make sure app.js is loaded correctly.');
            }
        })
        .catch(error => {
            grid.innerHTML = '<p style="color: red;">Error loading instrument panels. Please check the console.</p>';
            console.error('Failed to load panel components:', error);
        });
});
