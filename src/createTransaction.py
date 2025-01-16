# - Crear registro de transacción (createTransaction):
# - Método HTTP: POST
# - Endpoint: '/transaction'
# - Descripción: Permite registrar una nueva transacción.

try:
  import unzip_requirements
except ImportError:
  pass

from datetime import datetime
from pymongo import MongoClient
import uuid, json, os

def handler(event, context):
    print(event)
    
    body_str = event.get('body', '{}')
    print("Received body:", body_str)
    body = json.loads(body_str) if isinstance(body_str, str) else body_str
    
    cliente_id = body.get('cliente_id')
    if not cliente_id or not is_valid_uuid(cliente_id):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'cliente_id es incorrecto o no existe'})
        }
    fecha = body.get('fecha')
    if not fecha or not is_valid_date(fecha):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'fecha es incorrecta o no existe'})
        }
    
    return create_transaction(body)


def is_valid_uuid(value):
    try:
        uuid.UUID(value, version=4)
        return True
    except ValueError:
        return False

def is_valid_date(value):
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False


def create_transaction(data):
    print("Entró 1")
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri)
    
    transaccion_id = str(uuid.uuid4())
    
    db = client["transacciones_db"]
    db.transacciones.insert_one({
        "transaccion_id": transaccion_id,
        "cliente_id": data["cliente_id"],
        "cantidad": round(float(data["cantidad"]), 2),
        "categoría": data["categoría"],
        "fecha": datetime.strptime(data["fecha"], "%Y-%m-%d"),
        "tipo": data["tipo"],
        "is_active": True
    })
    return({
        "statusCode": 200,
        "body": f"Transacción {transaccion_id} creada correctamente."
    })