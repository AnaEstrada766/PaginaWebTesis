	// Esperar a que el DOM esté cargado
document.addEventListener('DOMContentLoaded', () => {
    // Validación del formulario de login
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', (event) => {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();

            if (username === '' || password === '') {
                event.preventDefault();
                alert('Por favor, completa todos los campos.');
            }
        });
    }

    // Animación para estadísticas
    const stats = document.querySelectorAll('.stat h2');
    stats.forEach(stat => {
        const target = parseInt(stat.innerText);
        let count = 0;

        const increment = target / 50; // Ajusta la velocidad de la animación
        const updateCounter = () => {
            count += increment;
            if (count < target) {
                stat.innerText = Math.ceil(count);
                requestAnimationFrame(updateCounter);
            } else {
                stat.innerText = target;
            }
        };

        updateCounter();
    });

    // Confirmación de acciones
    const logoutBtn = document.querySelector('a[href="/logout"]');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (event) => {
            if (!confirm('¿Estás seguro de que deseas cerrar sesión?')) {
                event.preventDefault();
            }
        });
    }
});

