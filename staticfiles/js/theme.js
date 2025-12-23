document.addEventListener('DOMContentLoaded', function() {
    const themeToggleBtn = document.getElementById('theme-toggle');
    
   
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeButton(savedTheme);
    
   
    themeToggleBtn.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
       
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        

        updateThemeButton(newTheme);
    });
    
    function updateThemeButton(theme) {
        themeToggleBtn.textContent = theme === 'light' ? '🌙' : '☀️';
        themeToggleBtn.title = theme === 'light' ? 'Включить темную тему' : 'Включить светлую тему';
    }
});