// Minimal JavaScript for enhanced UX
document.addEventListener('DOMContentLoaded', function() {
    // Auto-focus first input in forms
    const firstInput = document.querySelector('input[type="text"], input[type="password"]');
    if (firstInput) firstInput.focus();
    
    // Initialize theme
    initTheme();
});

// Theme management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Hamburger menu toggle
function toggleMenu() {
    const menu = document.getElementById('nav-menu');
    menu.classList.toggle('active');
}

// Close menu when clicking outside
document.addEventListener('click', function(event) {
    const menu = document.getElementById('nav-menu');
    const hamburger = document.querySelector('.hamburger');
    const themeToggle = document.querySelector('.theme-toggle');
    
    if (menu && hamburger && !hamburger.contains(event.target) && !menu.contains(event.target) && !themeToggle.contains(event.target)) {
        menu.classList.remove('active');
    }
});