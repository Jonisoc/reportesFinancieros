# - Obtener transacciones (readTransactions):
# - Método HTTP: GET
# - Endpoint: '/transactions'
# - Descripción: Recupera todas las transacciones.

try:
  import unzip_requirements
except ImportError:
  pass

from pymongo import MongoClient
import json, os

def handler(event, context):
    print(event)
    return get_transactions()

def format_transaction(transaction):
    transaction["_id"] = str(transaction["_id"])
    transaction["fecha"] = transaction["fecha"].isoformat()
    return transaction

def get_transactions():
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri)
    
    db = client["transacciones_db"]
    transacciones = [
        format_transaction(transaccion) for transaccion in db.transacciones.find({"is_active": True}, projection={"is_active": 0})
    ]
    return({
        "statusCode": 200,
        "body": json.dumps(transacciones)
    })