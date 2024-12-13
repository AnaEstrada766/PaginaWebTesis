from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
import boto3
import decimal

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Conexión a DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
placas_table = dynamodb.Table('placas')
usuarios_table = dynamodb.Table('usuarios')

# Función para convertir Decimal a tipos nativos
def convert_decimal(obj):
    """Convierte objetos Decimal a tipos nativos de Python."""
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
    entradas, salidas, durations, accesos = 0, 0, [], {}

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

    avg_duration = sum(durations) / len(durations) if durations else 0

    return {
        'entradas': entradas,
        'salidas': salidas,
        'avg_duration': avg_duration,
        'accesos': accesos
    }

def get_data_from_db():
    items = []
    response = placas_table.scan()
    items.extend(response['Items'])
    while 'LastEvaluatedKey' in response:
        response = placas_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    return items

@app.route('/api/estadisticas')
def api_estadisticas():
    stats = obtener_estadisticas()
    stats = convert_decimal(stats)
    return jsonify(stats)

@app.route('/')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

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
