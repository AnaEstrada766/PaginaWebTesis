from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
import boto3
import numpy as np

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

# Generar gráfico radial para un conjunto de datos
def generate_radar_chart(data, access):
    labels = ['Entradas', 'Salidas', 'Duración Promedio (h)', 'Menores a 5 min', 'Más de 12 horas']
    entradas = sum(1 for item in data if item.get('acceso') == access and item.get('timestamp_entrada'))
    salidas = sum(1 for item in data if item.get('acceso') == access and item.get('timestamp_salida'))

    durations = [
        (datetime.utcfromtimestamp(int(item['timestamp_salida'])) - datetime.utcfromtimestamp(int(item['timestamp_entrada']))).total_seconds() / 3600
        for item in data
        if item.get('acceso') == access and item.get('timestamp_entrada') and item.get('timestamp_salida')
    ]

    avg_duration = sum(durations) / len(durations) if durations else 0
    short_durations = sum(1 for d in durations if d < 0.1)
    long_durations = sum(1 for d in durations if d > 12)

    values = [entradas, salidas, avg_duration, short_durations, long_durations]
    values += values[:1]  # Cerrar el gráfico

    angles = np.linspace(0, 2 * np.pi, len(values))

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='blue', alpha=0.25)
    ax.plot(angles, values, color='blue', linewidth=2)
    ax.set_yticks([2, 4, 6, 8])
    ax.set_yticklabels(['2', '4', '6', '8'], color="gray", size=10)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=10)
    ax.set_title(f'Gráfico Radial para Acceso {access}', size=14, pad=20)

    # Convertir el gráfico en base64
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close(fig)

    return base64.b64encode(img.getvalue()).decode('utf-8')

# Ruta para generar las gráficas
@app.route('/generate_radar')
def generate_radar():
    data = get_data_from_db()
    radar_1 = generate_radar_chart(data, access=1)
    radar_2 = generate_radar_chart(data, access=2)

    return render_template('radar.html', radar_1=radar_1, radar_2=radar_2)

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
