// scripts.js

// Llamada a la API para obtener los datos de accesos
fetch('/api/accesos')
  .then(response => response.json())
  .then(data => {
    // Datos para el gráfico de accesos
    const labels = ['Acceso 1', 'Acceso 2', 'Acceso 3', 'Acceso 4'];
    const datosAccesos = [data.acceso1, data.acceso2, data.acceso3, data.acceso4];

    // Crear el gráfico de barras para los accesos
    const ctx1 = document.getElementById('accesosChart').getContext('2d');
    new Chart(ctx1, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Número de Autos por Acceso',
          data: datosAccesos,
          backgroundColor: ['red', 'green', 'blue', 'orange'],
        }]
      }
    });

    // Crear el gráfico de línea para la duración promedio
    const ctx2 = document.getElementById('duracionChart').getContext('2d');
    new Chart(ctx2, {
      type: 'line',
      data: {
        labels: ['Promedio de Duración'],
        datasets: [{
          label: 'Promedio de Duración de Autos (segundos)',
          data: [data.promedioDuracion],
          borderColor: 'blue',
          fill: false,
        }]
      }
    });
  })
  .catch(error => {
    console.error('Error al obtener los datos:', error);
  });
