# - Actualizar transacción (updateTransaction): 
# - Método HTTP: PUT
# - Endpoint: '/transaction/{transaccion_id}'
# - Descripción: Permite modificar los detalles de una transacción existente.

try:
  import unzip_requirements
except ImportError:
  pass

from datetime import datetime
from pymongo import MongoClient
import json, os, uuid

def handler(event, context):

    print(event)
    transaccion_id = event.get("pathParameters", {}).get("transaccion_id")
    if not transaccion_id:
        return {
            "statusCode": 400,
            "body": json.dumps("Parámetro 'transaccion_id' es requerido.")
        }
    
    body_str = event.get('body', '{}')
    print("Received body:", body_str)
    body = json.loads(body_str) if isinstance(body_str, str) else body_str
    
    cliente_id = body.get('cliente_id')
    if cliente_id and not is_valid_uuid(cliente_id):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'cliente_id es incorrecto'})
        }
    fecha = body.get('fecha')
    if fecha and not is_valid_date(fecha):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'fecha es incorrecta'})
        }

    return update_transaction(transaccion_id, body)


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


def update_transaction(transaccion_id, body):
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri)
    
    db = client["transacciones_db"]
    
    try:
        exists = True if db.transacciones.find_one({'transaccion_id': transaccion_id, "is_active": True}) is not None else False
        response = db.transacciones.update_one({'transaccion_id': transaccion_id, 'is_active': True}, {'$set': body})
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error al actualizar transacción: {e}"
        }
    if response.modified_count == 0:
        if db.transacciones.find_one({'transaccion_id': transaccion_id, "is_active": True}) == None:
            return {
                "statusCode": 404,
                "body": f"Transacción {transaccion_id} no encontrada o inactiva."
            }
        else:
            return {
                "statusCode": 400,
                "body": f"La transacción {transaccion_id} existe pero no hay ningún cambio aplicable."
            }
    else:
        return {
            "statusCode": 200,
            "body": f"Transacción {transaccion_id} actualizada correctamente."
        }