document.addEventListener('DOMContentLoaded', () => {
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (!darkModeToggle) return; // Pas de bouton, pas d'action

    const icon = darkModeToggle.querySelector('i');

    // Initialiser le mode sombre en fonction de localStorage
    if (localStorage.getItem('dark-mode') === 'enabled') {
        document.body.classList.add('dark-mode');
        icon.classList.replace('fa-moon', 'fa-sun');
    }

    // Basculer le mode sombre et mettre à jour localStorage
    darkModeToggle.addEventListener('click', function () {
        document.body.classList.toggle('dark-mode');
        if (document.body.classList.contains('dark-mode')) {
            icon.classList.replace('fa-moon', 'fa-sun');
            localStorage.setItem('dark-mode', 'enabled');
        } else {
            icon.classList.replace('fa-sun', 'fa-moon');
            localStorage.setItem('dark-mode', 'disabled');
        }
    });
});