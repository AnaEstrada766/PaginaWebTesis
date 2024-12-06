import random
import datetime
import boto3
import json

# Generate random timestamps for the year 2024
def generate_random_timestamps(year=2024):
    start_date = datetime.datetime(year, 1, 1)
    end_date = datetime.datetime(year, 12, 31, 23, 59, 59)
    delta = end_date - start_date
    random_seconds = random.randint(0, int(delta.total_seconds()))
    timestamp_entrada = start_date + datetime.timedelta(seconds=random_seconds)
    
    # Determine the duration
    durations = [
        random.randint(6 * 3600, 8 * 3600),  # 6-8 hours in seconds
        random.randint(12 * 3600, 24 * 3600),  # More than 12 hours
        random.randint(2 * 60, 4 * 60)  # 2-4 minutes
    ]
    duration = random.choice(durations)
    timestamp_salida = timestamp_entrada + datetime.timedelta(seconds=duration)
    
    return int(timestamp_entrada.timestamp()), int(timestamp_salida.timestamp())

# Generate random plates
def generate_random_plate():
    letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
    numbers = ''.join(random.choices('0123456789', k=3))
    return letters + numbers

# Generate random JSON data
def generate_json_data(entries=50, year=2024):
    data = []
    for _ in range(entries):
        placa = generate_random_plate()
        acceso = str(random.randint(1, 2))  # Random acceso value
        timestamp_entrada, timestamp_salida = generate_random_timestamps(year)
        data.append({
            "placa": placa,
            "acceso": acceso,
            "timestamp_entrada": timestamp_entrada,
            "timestamp_salida": timestamp_salida
        })
    return data

# Send data to DynamoDB
def send_to_dynamodb(table_name, region, data):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('placas')
    
    for item in data:
        table.put_item(Item=item)
        print(f"Inserted: {item}")

# Main execution
if __name__ == "__main__":
    # Generate 100 records
    json_data = generate_json_data(entries=100, year=2024)

    # DynamoDB table and region configuration
    table_name = 'placas'  # Replace with your table name
    region = 'us-east-1'  # Replace with your DynamoDB region

    # Send data to DynamoDB
    send_to_dynamodb(table_name, region, json_data)
