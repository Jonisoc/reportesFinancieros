# - Obtener transacciones de cliente particular (readUserTransactions): 
# - Método HTTP: GET
# - Endpoint: '/transactions/{cliente_id}'
# - Descripción: Recupera todas las transacciones del usuario indicado.

try:
  import unzip_requirements
except ImportError:
  pass

from pymongo import MongoClient
import json, os

def handler(event, context):
    
    print(event)
    cliente_id = event.get("pathParameters", {}).get("cliente_id")
    if not cliente_id:
        return {
            "statusCode": 400,
            "body": json.dumps("Parámetro 'cliente_id' es requerido.")
        }

    return get_user_transactions(cliente_id)

def format_transaction(transaction):
    transaction["_id"] = str(transaction["_id"])
    transaction["fecha"] = transaction["fecha"].isoformat()
    return transaction

def get_user_transactions(cliente_id):
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri)
    
    db = client["transacciones_db"]
    transacciones = [
        format_transaction(transaccion)
        for transaccion in db.transacciones.find({"cliente_id": cliente_id, "is_active": True}, projection={"is_active": 0})
    ]
    
    if transacciones == []:
        return {
            "statusCode": 404,
            "body": f"No se encontraron transacciones para el cliente {cliente_id}."
        }
    else:
        return {
            "statusCode": 200,
            "body": json.dumps(transacciones)
        }