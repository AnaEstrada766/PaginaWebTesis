from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
import boto3

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Conexión a DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
placas_table = dynamodb.Table('placas')
usuarios_table = dynamodb.Table('usuarios')

# Función para obtener estadísticas
def obtener_estadisticas():
    data = get_data_from_db()

    entradas, salidas, durations, short_durations, long_durations = 0, 0, [], 0, 0
    accesos = {}

    for item in data:
        entrada = item.get('timestamp_entrada')
        salida = item.get('timestamp_salida')
        acceso = item.get('acceso', 'Desconocido')

        # Contar entradas y salidas
        if entrada:
            entradas += 1
            accesos[acceso] = accesos.get(acceso, 0) + 1
        if salida:
            salidas += 1

        # Calcular duraciones si hay entrada y salida
        if entrada and salida:
            entrada_dt = datetime.fromisoformat(entrada)
            salida_dt = datetime.fromisoformat(salida)
            duration = (salida_dt - entrada_dt).total_seconds() / 3600  # Duración en horas
            durations.append(duration)
            if duration < 0.1:  # Menos de 5 minutos
                short_durations += 1
            if duration > 12:  # Más de 12 horas
                long_durations += 1

    avg_duration = sum(durations) / len(durations) if durations else 0

    return {
        'entradas': entradas,
        'salidas': salidas,
        'avg_duration': avg_duration,
        'short_durations': short_durations,
        'long_durations': long_durations,
        'accesos': accesos
    }

# Función para obtener datos de la base de datos
def get_data_from_db():
    items = []
    response = placas_table.scan()
    items.extend(response['Items'])

    # Manejar paginación
    while 'LastEvaluatedKey' in response:
        response = placas_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])

    return items

# Ruta principal (Dashboard)
@app.route('/')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    stats = obtener_estadisticas()

    # Crear gráfico de accesos
    fig, ax = plt.subplots()
    ax.bar(stats['accesos'].keys(), stats['accesos'].values(), color='skyblue')
    ax.set_ylabel('Cantidad de accesos')
    ax.set_title('Accesos más usados')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf-8')

    return render_template('dashboard.html', stats=stats, plot_url=plot_url)

# Ruta para búsqueda avanzada
@app.route('/buscar', methods=['GET', 'POST'])
def buscar():
    if 'username' not in session:
        return redirect(url_for('login'))

    data = get_data_from_db()
    if request.method == 'POST':
        placa_filter = request.form.get('placa')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Filtrar por matrícula
        if placa_filter:
            data = [item for item in data if item.get('placa') == placa_filter]

        # Filtrar por rango de fechas
        if start_date and end_date:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
            data = [
                item for item in data
                if 'timestamp_entrada' in item and
                   start_date <= datetime.fromisoformat(item['timestamp_entrada']) <= end_date
            ]

    return render_template('buscar.html', data=data)

# Cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
