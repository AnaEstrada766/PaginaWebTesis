import boto3
import json

# Configurar DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Cambia la región si es necesario
table = dynamodb.Table('placas')  # Nombre de la tabla

# Cargar los datos desde el archivo 'data.json_'
with open('data.json', 'r') as file:
    data = json.load(file)

# Insertar los datos en la tabla
for item in data:
    table.put_item(Item=item)

print("Datos insertados exitosamente.")
