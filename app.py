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

# Función para eliminar duplicados basados en la placa
def remove_duplicates(data):
    seen = set()
    unique_data = []
    for item in data:
        if item['placa'] not in seen:
            unique_data.append(item)
            seen.add(item['placa'])
    return unique_data

# Obtener datos de la base de datos con paginación
def get_data_from_db():
    items = []
    response = placas_table.scan()
    items.extend(response['Items'])

    # Manejar paginación
    while 'LastEvaluatedKey' in response:
        response = placas_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])

    # Eliminar duplicados basados en 'placa'
    return remove_duplicates(items)

# Filtrar datos según el tiempo
def filter_data_by_time(data, time_filter, month_filter=None, year_filter=None):
    now = datetime.utcnow()
    filtered_data = []

    if time_filter == 'day':
        start_timestamp = now - timedelta(days=1)
        filtered_data = [
            item for item in data
            if 'timestamp_entrada' in item and datetime.utcfromtimestamp(int(item['timestamp_entrada'])) >= start_timestamp
        ]
    elif time_filter == 'week':
        start_timestamp = now - timedelta(weeks=1)
        filtered_data = [
            item for item in data
            if 'timestamp_entrada' in item and datetime.utcfromtimestamp(int(item['timestamp_entrada'])) >= start_timestamp
        ]
    elif time_filter == 'month':
        start_timestamp = now - timedelta(days=30)
        filtered_data = [
            item for item in data
            if 'timestamp_entrada' in item and datetime.utcfromtimestamp(int(item['timestamp_entrada'])) >= start_timestamp
        ]
    elif time_filter == 'year':
        start_timestamp = now - timedelta(days=365)
        filtered_data = [
            item for item in data
            if 'timestamp_entrada' in item and datetime.utcfromtimestamp(int(item['timestamp_entrada'])) >= start_timestamp
        ]
    elif month_filter:  # Filtrar por un mes específico
        try:
            year, month = map(int, month_filter.split('-'))
            filtered_data = [
                item for item in data
                if 'timestamp_entrada' in item and
                   datetime.utcfromtimestamp(int(item['timestamp_entrada'])).year == year and
                   datetime.utcfromtimestamp(int(item['timestamp_entrada'])).month == month
            ]
        except ValueError:
            return [], "Formato de mes inválido. Use 'YYYY-MM'."
    elif year_filter:  # Filtrar por un año específico
        try:
            year = int(year_filter)
            filtered_data = [
                item for item in data
                if 'timestamp_entrada' in item and
                   datetime.utcfromtimestamp(int(item['timestamp_entrada'])).year == year
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

    print(f"Datos obtenidos de DynamoDB: {data}")  # Imprimir los datos completos para depuración

    filtered_data, error = filter_data_by_time(data, time_filter, month_filter, year_filter)

    if error:
        return jsonify({"message": error}), 400

    if not filtered_data:
        return jsonify({"message": "No hay datos disponibles para este filtro."})

    entradas = 0
    salidas = 0
    durations = []
    short_durations = 0
    long_durations = 0

    # Imprimir los datos filtrados para depuración
    print(f"Datos filtrados: {len(filtered_data)} registros")

    for item in filtered_data:
        entrada = item.get('timestamp_entrada')
        salida = item.get('timestamp_salida')


        # Contar entradas y salidas
        if entrada:  # Si tiene timestamp_entrada, cuenta como una entrada
            entradas += 1
        if salida:  # Si tiene timestamp_salida, cuenta como una salida
            salidas += 1

        # Calcular duraciones solo si hay entrada y salida
        if entrada and salida:
            entrada_dt = datetime.utcfromtimestamp(int(entrada))
            salida_dt = datetime.utcfromtimestamp(int(salida))
            duration = (salida_dt - entrada_dt).total_seconds() / 3600  # Duración en horas
            durations.append(duration)
            if duration < 0.1:  # Menos de 5 minutos
                short_durations += 1
            if duration > 12:  # Más de 12 horas
                long_durations += 1

    avg_duration = sum(durations) / len(durations) if durations else 0

    # Imprimir entradas, salidas y demás para depuración
    print(f"Entradas: {entradas}, Salidas: {salidas}")
    print(f"Duración Promedio: {avg_duration} horas")
    print(f"Duraciones menores a 5 minutos: {short_durations}")
    print(f"Duraciones mayores a 12 horas: {long_durations}")

    # Crear gráfico
    fig, ax = plt.subplots()
    ax.bar(
        ['Total Accesos', 'Duración Promedio (h)', 'Menores a 5 min', 'Más de 12 horas'],
        [entradas, avg_duration, short_durations, long_durations],
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
        total_accesses=entradas,
        avg_duration=avg_duration,
        short_durations=short_durations,
        long_durations=long_durations,
        entradas=entradas,
        salidas=salidas
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
