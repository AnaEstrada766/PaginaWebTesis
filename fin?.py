from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
import boto3
from decimal import Decimal

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Conexión a DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
placas_table = dynamodb.Table('placas')
usuarios_table = dynamodb.Table('usuarios')


def convert_decimal_to_float(data):
    """Convierte valores Decimal a float en los datos."""
    if isinstance(data, list):
        return [convert_decimal_to_float(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_decimal_to_float(value) for key, value in data.items()}
    elif isinstance(data, Decimal):
        return float(data)
    return data


def obtener_estadisticas():
    data = get_data_from_db()

    entradas, salidas, durations, short_durations, long_durations = 0, 0, [], 0, 0
    accesos = {}

    for item in data:
        entrada = item.get('timestamp_entrada')
        salida = item.get('timestamp_salida')
        acceso = item.get('acceso', 'Desconocido')

        if entrada:
            entradas += 1
            accesos[acceso] = accesos.get(acceso, 0) + 1
        if salida:
            salidas += 1

        if entrada and salida:
            entrada_dt = datetime.fromisoformat(entrada)
            salida_dt = datetime.fromisoformat(salida)
            duration = (salida_dt - entrada_dt).total_seconds() / 3600
            durations.append(duration)

            if duration < 0.083:  # Menos de 5 minutos
                short_durations += 1
            if duration > 12:  # Más de 12 horas
                long_durations += 1

    avg_duration = sum(durations) / len(durations) if durations else 0

    stats = {
        'entradas': entradas,
        'salidas': salidas,
        'avg_duration': avg_duration,
        'short_durations': short_durations,
        'long_durations': long_durations,
        'accesos': {key: round(value) for key, value in accesos.items()}
    }

    return convert_decimal_to_float(stats)


def get_data_from_db():
    items = []
    response = placas_table.scan()
    items.extend(response['Items'])

    while 'LastEvaluatedKey' in response:
        response = placas_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])

    return convert_decimal_to_float(items)


@app.route('/')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    stats = obtener_estadisticas()
    return render_template('dashboard.html', stats=stats)


@app.route('/api/estadisticas')
def api_estadisticas():
    if 'username' not in session:
        return jsonify({"message": "No autorizado"}), 401

    stats = obtener_estadisticas()
    return jsonify(stats)


@app.route('/buscar', methods=['GET', 'POST'])
def buscar():
    if 'username' not in session:
        return redirect(url_for('login'))

    data = get_data_from_db()
    if request.method == 'POST':
        placa_filter = request.form.get('placa')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        if placa_filter:
            data = [item for item in data if item.get('placa') == placa_filter]

        if start_date and end_date:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
            data = [
                item for item in data
                if 'timestamp_entrada' in item and
                   start_date <= datetime.fromisoformat(item['timestamp_entrada']) <= end_date
            ]

    return render_template('buscar.html', data=data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            response = usuarios_table.get_item(Key={'username': username})
            user = response.get('Item')

            if user and user['password'] == password:
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error="Usuario o contraseña incorrectos.")
        except Exception as e:
            return render_template('login.html', error="Error al validar usuario: " + str(e))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
