document.getElementById('update_graph').addEventListener('click', function() {
    const timeFilter = document.getElementById('time_filter').value;

    // Enviar la solicitud al servidor
    fetch('/get_graph', {
        method: 'POST',
        body: new URLSearchParams({ 'time_filter': timeFilter }),
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    .then(response => response.json())
    .then(data => {
        // Actualizar las imágenes de las gráficas
        document.getElementById('entrances_graph').src = 'data:image/png;base64,' + data.entrances_img;
        document.getElementById('duration_graph').src = 'data:image/png;base64,' + data.duration_img;

        // Actualizar las estadísticas
        document.getElementById('avg_duration').textContent = data.avg_duration;
        document.getElementById('under_5_min').textContent = data.under_5_min;
    })
    .catch(error => console.error('Error al obtener las gráficas:', error));
});
