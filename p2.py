from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
import boto3
import decimal

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Conexión a DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
placas_table = dynamodb.Table('placas')
lista_negra_table = dynamodb.Table('lista_negra')
usuarios_table = dynamodb.Table('usuarios')

# Función para convertir Decimal a tipos nativos
def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {str(k): convert_decimal(v) for k, v in obj.items()} 
    elif isinstance(obj, decimal.Decimal):
        return int(obj) if obj % 1 == 0 else float(obj) 
    else:
        return obj

# Función para obtener estadísticas
def obtener_estadisticas():
    data = get_data_from_db()
    entradas, salidas, durations, short_durations, long_durations, accesos = 0, 0, [], 0, 0, {}

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
            if duration < 0.1:
                short_durations += 1
            if duration > 12:
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

# Obtener datos de la base de datos
def get_data_from_db():
    items = []
    response = placas_table.scan()
    items.extend(response['Items'])
    while 'LastEvaluatedKey' in response:
        response = placas_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    return items

# Dashboard principal
@app.route('/')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/api/estadisticas')
def api_estadisticas():
    stats = obtener_estadisticas()
    stats = convert_decimal(stats)
    return jsonify(stats)

# Búsqueda avanzada
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

# Lista Negra - Ver
@app.route('/api/lista_negra', methods=['GET'])
def api_lista_negra():
    try:
        response = lista_negra_table.scan()
        items = response.get('Items', [])
        return jsonify(items)
    except Exception as e:
        print("Error al obtener la lista negra:", str(e))
        return jsonify({"error": "No se pudo obtener la lista negra"}), 500

@app.route('/lista_negra')
def lista_negra():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('lista_negra.html')

# Lista Negra - Agregar
@app.route('/agregar_lista_negra', methods=['GET', 'POST'])
def agregar_lista_negra():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        placa = request.form.get('placa')
        if placa:
            lista_negra_table.put_item(Item={'placa': placa})
    return render_template('agregar_lista_negra.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        response = usuarios_table.get_item(Key={'username': username})
        user = response.get('Item')

        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = "Usuario o contraseña incorrectos"
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
