from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
import boto3

app = Flask(__name__)

# Conexión a DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
placas_table = dynamodb.Table('placas')

# Obtener datos de la base de datos
def get_data_from_db():
    response = placas_table.scan()
    items = response['Items']
    return items

# Filtrar datos según rango de tiempo
def filter_data_by_time(data, time_filter, month_filter=None, year_filter=None):
    now = datetime.utcnow()
    filtered_data = []

    if time_filter == 'day':
        start_timestamp = now - timedelta(days=1)
        filtered_data = [
            item for item in data
            if datetime.utcfromtimestamp(int(item['timestamp_entrada'])) >= start_timestamp
        ]
    elif time_filter == 'week':
        start_timestamp = now - timedelta(weeks=1)
        filtered_data = [
            item for item in data
            if datetime.utcfromtimestamp(int(item['timestamp_entrada'])) >= start_timestamp
        ]
    elif time_filter == 'month':
        start_timestamp = now - timedelta(days=30)
        filtered_data = [
            item for item in data
            if datetime.utcfromtimestamp(int(item['timestamp_entrada'])) >= start_timestamp
        ]
    elif time_filter == 'year':
        start_timestamp = now - timedelta(days=365)
        filtered_data = [
            item for item in data
            if datetime.utcfromtimestamp(int(item['timestamp_entrada'])) >= start_timestamp
        ]
    elif month_filter:  # Filtrar por un mes específico
        try:
            year, month = map(int, month_filter.split('-'))
            filtered_data = [
                item for item in data
                if datetime.utcfromtimestamp(int(item['timestamp_entrada'])).year == year and
                   datetime.utcfromtimestamp(int(item['timestamp_entrada'])).month == month
            ]
        except ValueError:
            return [], "Formato de mes inválido. Use 'YYYY-MM'."
    elif year_filter:  # Filtrar por un año específico
        try:
            year = int(year_filter)
            filtered_data = [
                item for item in data
                if datetime.utcfromtimestamp(int(item['timestamp_entrada'])).year == year
            ]
        except ValueError:
            return [], "Formato de año inválido. Use 'YYYY'."
    else:
        return [], "Filtro de tiempo inválido."

    return filtered_data, None

# Generar gráfico y estadísticas
@app.route('/generate_plot')
def generate_plot():
    time_filter = request.args.get('time_filter', 'day')
    month_filter = request.args.get('month')  # Ejemplo: "2024-11"
    year_filter = request.args.get('year')  # Ejemplo: "2024"
    data = get_data_from_db()

    filtered_data, error = filter_data_by_time(data, time_filter, month_filter, year_filter)

    if error:
        return jsonify({"message": error}), 400

    if not filtered_data:
        return jsonify({"message": "No hay datos disponibles para este filtro."})

    durations = []
    short_durations = 0
    long_durations = 0
    total_accesses = len(filtered_data)

    for item in filtered_data:
        entrada = datetime.utcfromtimestamp(int(item['timestamp_entrada']))
        salida = datetime.utcfromtimestamp(int(item['timestamp_salida']))
        duration = (salida - entrada).total_seconds() / 3600  # Duración en horas
        durations.append(duration)
        if duration < 0.1:  # Menos de 5 minutos
            short_durations += 1
        if duration > 12:  # Más de 12 horas
            long_durations += 1

    avg_duration = sum(durations) / len(durations) if durations else 0

    # Crear gráfico
    fig, ax = plt.subplots()
    ax.bar(
        ['Total Accesos', 'Duración Promedio (h)', 'Menores a 5 min', 'Más de 12 horas'],
        [total_accesses, avg_duration, short_durations, long_durations],
        color=['blue', 'green', 'red', 'orange']
    )
    ax.set_ylabel('Cantidad')
    ax.set_title(f"Estadísticas para {month_filter if month_filter else year_filter if year_filter else f'últimos {time_filter}'}")

    # Guardar gráfico como imagen en base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

    return render_template(
        'plot.html',
        plot_url=img_base64,
        total_accesses=total_accesses,
        avg_duration=avg_duration,
        short_durations=short_durations,
        long_durations=long_durations
    )

# Ruta principal
@app.route('/')
def home():
    return render_template('index.html')

# Manejo de error 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
