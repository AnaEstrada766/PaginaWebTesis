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
lista_negra_table = dynamodb.Table('lista_negra')

# Convertir Decimal a tipos nativos
def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {str(k): convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, decimal.Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj

# Obtener estadísticas
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
        'avg_duration': round(avg_duration, 2),
        'accesos': {k: int(v) for k, v in accesos.items()}
    }

def get_data_from_db():
    items = []
    response = placas_table.scan()
    items.extend(response['Items'])
    while 'LastEvaluatedKey' in response:
        response = placas_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    return items

# Rutas
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

@app.route('/buscar', methods=['GET', 'POST'])
def buscar():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('buscar.html')

@app.route('/lista_negra', methods=['GET', 'POST'])
def lista_negra():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        placa = request.form['placa']
        lista_negra_table.put_item(Item={'placa': placa})
    response = lista_negra_table.scan()
    return render_template('lista_negra.html', data=response['Items'])

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

