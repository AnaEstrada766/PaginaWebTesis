from flask import Flask, jsonify
import boto3
from datetime import datetime

app = Flask(__name__)

# Conectar a DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Asegúrate de que la región esté correcta
table = dynamodb.Table('Placas')  # Nombre de la tabla en DynamoDB

@app.route('/api/accesos')
def obtener_accesos():
    # Obtener datos de DynamoDB (rango de fechas de ejemplo)
    fecha_inicio = "2024-11-01"
    fecha_fin = "2024-11-30"
    datos = obtener_datos(fecha_inicio, fecha_fin)  # Llama a la función que consulta DynamoDB

    # Procesar datos (cuenta de accesos)
    accesos = {'acceso1': 0, 'acceso2': 0, 'acceso3': 0, 'acceso4': 0}
    for item in datos:
        acceso = item.get('acceso', 'acceso1')
        if acceso in accesos:
            accesos[acceso] += 1

    # Calcular duración promedio y autos que duran menos de 5 minutos
    promedio_duracion, count_menos_5_minutos = calcular_promedios(datos)

    # Retornar los resultados en formato JSON
    return jsonify({
        'acceso1': accesos['acceso1'],
        'acceso2': accesos['acceso2'],
        'acceso3': accesos['acceso3'],
        'acceso4': accesos['acceso4'],
        'promedioDuracion': promedio_duracion,
        'countMenos5Minutos': count_menos_5_minutos
    })

# Funciones adicionales para consultar DynamoDB y calcular promedios
def obtener_datos(fecha_inicio, fecha_fin):
    start_timestamp = int(datetime.strptime(fecha_inicio, "%Y-%m-%d").timestamp())
    end_timestamp = int(datetime.strptime(fecha_fin, "%Y-%m-%d").timestamp())
    
    response = table.scan(
        FilterExpression="timestamp BETWEEN :start_date AND :end_date",
        ExpressionAttributeValues={
            ":start_date": start_timestamp,
            ":end_date": end_timestamp
        }
    )
    return response['Items']

def calcular_promedios(items):
    total_duracion = 0
    count = 0
    count_menos_5_minutos = 0
    for item in items:
        if 'timestamp_salida' in item:
            duracion = item['timestamp_salida'] - item['timestamp']
            total_duracion += duracion
            count += 1
            if duracion < 300:
                count_menos_5_minutos += 1
    promedio_duracion = total_duracion / count if count > 0 else 0
    return promedio_duracion, count_menos_5_minutos

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)  # Permite que sea accesible externamente
