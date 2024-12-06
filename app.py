from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
from datetime import datetime, timedelta
import boto3
import json

app = Flask(__name__)

# Conexión a DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
placas_table = dynamodb.Table('placas')

# Función para obtener los datos de la tabla
def get_data_from_db():
    response = placas_table.scan()
    items = response['Items']
    print(f"Datos obtenidos de DynamoDB: {items}")  # Verificación de los datos obtenidos
    return items

# Función para filtrar los datos según el tiempo
def filter_data_by_time(data, time_filter):
    """
    Filtra los datos según el filtro de tiempo seleccionado (día, semana, mes).
    """
    now = datetime.utcnow()
    if time_filter == 'day':
        start_timestamp = now - timedelta(days=1)
    elif time_filter == 'week':
        start_timestamp = now - timedelta(weeks=1)
    elif time_filter == 'month':
        start_timestamp = now - timedelta(days=30)
    else:
        raise ValueError("Filtro de tiempo inválido")

    print(f"Start Timestamp: {start_timestamp}")  # Verificación del timestamp de inicio

    # Filtra los datos basados en el timestamp de entrada
    filtered_data = []
    for item in data:
        if 'timestamp_entrada' in item:
            try:
                # Verifica el tipo de dato antes de convertirlo
                print(f"timestamp_entrada antes de convertir: {item['timestamp_entrada']}")
                item_timestamp = datetime.utcfromtimestamp(int(float(item['timestamp_entrada'])))
                print(f"timestamp_entrada convertido: {item_timestamp}")  # Verificación de la conversión
                if item_timestamp >= start_timestamp:
                    filtered_data.append(item)
            except Exception as e:
                print(f"Error procesando el timestamp de entrada: {e}")
        else:
            print(f"Elemento sin 'timestamp_entrada': {item}")

    return filtered_data

# Ruta para la página principal
@app.route('/')
def home():
    return render_template('index.html')

# Ruta para generar el gráfico
@app.route('/generate_plot')
def generate_plot():
    time_filter = request.args.get('time_filter', 'day')  # Filtro de tiempo por defecto es 'day'
    data = get_data_from_db()  # Obtén los datos de la base de datos
    filtered_data = filter_data_by_time(data, time_filter)  # Filtra los datos según el filtro de tiempo

    # Verificar si los datos están vacíos después de la filtración
    if not filtered_data:
        print("No hay datos para graficar.")
        return jsonify({"message": "No hay datos para graficar."})

    # Procesa los datos para el gráfico
    timestamps = [datetime.utcfromtimestamp(int(item['timestamp_entrada'])) for item in filtered_data]
    access_counts = [int(item['acceso']) for item in filtered_data]

    print(f"Timestamps: {timestamps}")
    print(f"Access Counts: {access_counts}")

    # Crear gráfico
    fig, ax = plt.subplots()
    ax.plot(timestamps, access_counts, label='Accesos')
    ax.set_xlabel('Tiempo')
    ax.set_ylabel('Número de accesos')
    ax.set_title('Accesos de placas según el tiempo')
    ax.legend()

    # Guardar el gráfico como imagen en base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

    return render_template('plot.html', plot_url=img_base64)

# Ruta para obtener estadísticas
@app.route('/get_statistics')
def get_statistics():
    time_filter = request.args.get('time_filter', 'day')
    data = get_data_from_db()
    filtered_data = filter_data_by_time(data, time_filter)
    
    # Verificar si los datos están vacíos después de la filtración
    if not filtered_data:
        return jsonify({"total_accesses": 0, "average_accesses": 0})

    # Calcular estadísticas (por ejemplo, promedio de accesos)
    access_counts = [int(item['acceso']) for item in filtered_data]
    total_accesses = sum(access_counts)
    avg_accesses = total_accesses / len(filtered_data) if filtered_data else 0
    
    return jsonify({
        'total_accesses': total_accesses,
        'average_accesses': avg_accesses
    })

# Manejo de error 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
