from flask import Flask, render_template, request, redirect, url_for, session
import boto3
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Conexión a DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
placas_table = dynamodb.Table('placas')  # Tabla de datos
usuarios_table = dynamodb.Table('usuarios')  # Tabla de usuarios

# Validar usuario
def validar_usuario(username, password):
    try:
        print(f"Buscando usuario con username: {username}")
        
        # Consulta en DynamoDB
        response = usuarios_table.get_item(Key={'username': username})
        user = response.get('Item')

        if not user:
            return False, "Usuario no encontrado"

        # Comparar contraseñas en texto plano
        if user['password'] == password:
            return True, None  # Usuario válido
        else:
            return False, "Contraseña incorrecta"
    except Exception as e:
        print(f"Error al validar usuario: {e}")
        return False, "Error del servidor"

# Ruta de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validar usuario
        is_valid, error_message = validar_usuario(username, password)
        if is_valid:
            session['username'] = username  # Crear sesión para el usuario
            return redirect(url_for('dashboard'))  # Redirigir al dashboard
        else:
            return render_template('login.html', error=error_message)
    return render_template('login.html')

# Ruta protegida (dashboard)
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirigir si no está autenticado

    # Obtener datos de la base de datos
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

    return render_template('dashboard.html', data=data)

# Cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Obtener datos de DynamoDB
def get_data_from_db():
    response = placas_table.scan()
    return response['Items']

# Ruta principal
@app.route('/')
def home():
    return redirect(url_for('login'))

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
