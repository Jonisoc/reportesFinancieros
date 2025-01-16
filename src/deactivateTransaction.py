# - Desactivar transacción (deactivateTransaction):
# - Método HTTP: DELETE
# - Endpoint: '/transaction/{transaccion_id}'
# - Descripción: Desactiva una transacción en lugar de eliminarla. Las transacciones desactivadas ya no pueden ser editadas.

try:
  import unzip_requirements
except ImportError:
  pass

from pymongo import MongoClient
import json, os

def handler(event, context):

    transaccion_id = event.get("pathParameters", {}).get("transaccion_id")
    if not transaccion_id:
        return {
            "statusCode": 400,
            "body": json.dumps("Parámetro 'transaccion_id' es requerido.")
        }

    return deactivate_transaction(transaccion_id)


def deactivate_transaction(transaccion_id):
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri)
    
    db = client["transacciones_db"]
    
    try:
        response = db.transacciones.update_one({'transaccion_id': transaccion_id}, {'$set': {"is_active": False}})
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error al desactivar transacción: {e}"
        }
    if response.modified_count == 0:
        return {
            "statusCode": 404,
            "body": f"Transacción {transaccion_id} no encontrada o ya está desactivada."
        }
    else:
        return {
            "statusCode": 200,
            "body": f"Transacción {transaccion_id} desactivada correctamente."
        }