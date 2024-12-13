document.addEventListener('DOMContentLoaded', async () => {
    const response = await fetch('/api/estadisticas');
    const data = await response.json();

    // Gráfico de Entradas y Salidas
    new Chart(document.getElementById('entradasSalidasChart'), {
        type: 'bar',
        data: {
            labels: ['Entradas', 'Salidas'],
            datasets: [{
                label: 'Cantidad',
                data: [data.entradas, data.salidas],
                backgroundColor: ['#4caf50', '#f44336'],
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
            },
        }
    });

    // Gráfico de Duración Promedio
    new Chart(document.getElementById('duracionPromedioChart'), {
        type: 'doughnut',
        data: {
            labels: ['Duración Promedio'],
            datasets: [{
                data: [data.avg_duration],
                backgroundColor: ['#2196f3'],
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
            },
        }
    });

    // Gráfico de Accesos Más Usados
    new Chart(document.getElementById('accesosChart'), {
        type: 'pie',
        data: {
            labels: Object.keys(data.accesos),
            datasets: [{
                data: Object.values(data.accesos),
                backgroundColor: ['#ff9800', '#9c27b0', '#3f51b5', '#009688', '#e91e63'],
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' },
            },
        }
    });
});
