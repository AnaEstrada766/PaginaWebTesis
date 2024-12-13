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
        return {str(k): convert_decimal(v) for k, v in obj.items()}  # Asegurar claves como string
    elif isinstance(obj, decimal.Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)  # Convertir a int o float según sea el caso
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

    avg_duration = sum(durations) / len(durations) if durations else 0

    return {
        'entradas': entradas,
        'salidas': salidas,
        'avg_duration': avg_duration,
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

# API para enviar estadísticas en formato JSON
@app.route('/api/estadisticas')
def api_estadisticas():
    stats = obtener_estadisticas()
    print(f"Datos antes de conversión: {stats}")  # Inspeccionar los datos
    stats = convert_decimal(stats)  # Convertir Decimals a tipos nativos
    print(f"Datos después de conversión: {stats}")
    return jsonify(stats)

# Ruta principal (Dashboard)
@app.route('/')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# Ruta para iniciar sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validar usuario
        response = usuarios_table.get_item(Key={'username': username})
        user = response.get('Item')

        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = "Usuario o contraseña incorrectos"
            return render_template('login.html', error=error)

    return render_template('login.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

