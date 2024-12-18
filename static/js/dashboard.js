document.addEventListener('DOMContentLoaded', async () => {
    const response = await fetch('/api/estadisticas');
    const data = await response.json();

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
        options: { responsive: true, plugins: { legend: { display: false } } }
    });

    new Chart(document.getElementById('duracionPromedioChart'), {
        type: 'doughnut',
        data: {
            labels: ['Duración Promedio (h)', 'Menores a 5 min', 'Mayores a 12 h'],
            datasets: [{
                data: [data.avg_duration, data.short_durations, data.long_durations],
                backgroundColor: ['#2196f3', '#ff9800', '#e91e63'],
            }]
        },
        options: { responsive: true, plugins: { legend: { position: 'top' } } }
    });

    new Chart(document.getElementById('accesosUsadosChart'), {
        type: 'pie',
        data: {
            labels: Object.keys(data.accesos),
            datasets: [{
                data: Object.values(data.accesos).map(Math.round),
                backgroundColor: ['#fbc02d', '#8e24aa', '#43a047', '#0288d1'],
            }]
        },
        options: { responsive: true, plugins: { legend: { position: 'top' } } }
    });
});

