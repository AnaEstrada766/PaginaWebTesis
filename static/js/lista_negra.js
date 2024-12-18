document.addEventListener('DOMContentLoaded', async () => {
    async function cargarListaNegra() {
        try {
            const response = await fetch('/api/lista_negra');
            const data = await response.json();

            const tabla = document.getElementById('listaNegraTabla');
            tabla.innerHTML = '';

            if (data.length === 0) {
                tabla.innerHTML = '<tr><td colspan="2">No hay matrículas en la lista negra.</td></tr>';
                return;
            }

            data.forEach((item, index) => {
                const row = `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${item.placa}</td>
                    </tr>
                `;
                tabla.innerHTML += row;
            });
        } catch (error) {
            console.error("Error al cargar la lista negra:", error);
        }
    }

    cargarListaNegra();
});
