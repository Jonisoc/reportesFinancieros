import json, os
from dotenv import load_dotenv 
from pymongo import MongoClient
from datetime import datetime
import pandas as pd
import generateReport
load_dotenv()

def main(start_date, end_date, client_id):
    if start_date > end_date:
        print("La fecha de inicio no puede ser mayor a la fecha de fin.")
        return
    
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri)
    
    db = client["transacciones_db"]
    
    if not client_exists(db, client_id):
        print(f"El cliente con ID {client_id} no existe en la base de datos.")
        return
    
    transactions = get_transactions(db, start_date, end_date)
    general = get_general_resume(transactions)
    save_to_json(general, "resumen_general.json")
    
    by_client = get_client_resume(transactions)
    save_to_json(by_client, "resumen_por_cliente.json")
    print("Archivos 'resumen_general.json' y 'resumen_por_cliente.json' generados correctamente.")
    
    
    generateReport.main(client_id, start_date, end_date)


def client_exists(db, client_id):
    return db.transacciones.find_one({"cliente_id": client_id}) is not None


def get_transactions(db, start_date, end_date):
    return [format_transaction(transaccion) for transaccion in db.transacciones.find({"fecha": {"$gte": start_date, "$lte": end_date}, "is_active": True}, projection={"is_active": 0})]


def format_transaction(transaction):
    transaction["_id"] = str(transaction["_id"])
    transaction["fecha"] = transaction["fecha"].isoformat()
    return transaction


def get_general_resume(transactions):
    df = pd.DataFrame(transactions)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["cantidad"] = pd.to_numeric(df["cantidad"])
    
    total_by_category = df.groupby(["tipo", "categoría"])["cantidad"].sum().unstack(fill_value=0)
    total_by_category = total_by_category.to_dict()
    
    summary_by_client = df.groupby("cliente_id")["cantidad"].agg(["sum", "mean"])
    summary_by_client = summary_by_client.to_dict()
    
    return {
        "total_by_category": total_by_category
    }


def get_client_resume(transactions):
    
    df = pd.DataFrame(transactions)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["cantidad"] = pd.to_numeric(df["cantidad"])
    
    income = df[df["tipo"] == "income"].pivot_table(
        index="cliente_id",
        columns="fecha",
        values="cantidad",
        aggfunc="sum",
        fill_value=0
    )
    expense = df[df["tipo"] == "expense"].pivot_table(
        index="cliente_id",
        columns="fecha",
        values="cantidad",
        aggfunc="sum",
        fill_value=0
    )
    
    income["sum"] = df[df["tipo"] == "income"].groupby("cliente_id")["cantidad"].sum()
    income["mean"] = df[df["tipo"] == "income"].groupby("cliente_id")["cantidad"].mean()
    expense["sum"] = df[df["tipo"] == "expense"].groupby("cliente_id")["cantidad"].sum()
    expense["mean"] = df[df["tipo"] == "expense"].groupby("cliente_id")["cantidad"].mean()
    
    all_clients = set(income.index).union(set(expense.index))
    
    for client in all_clients:
        if client not in income.index:
            income.loc[client] = [0] * len(income.columns)
            income.loc[client, 'sum'] = 0
            income.loc[client, 'mean'] = 0

        if client not in expense.index:
            expense.loc[client] = [0] * len(expense.columns)
            expense.loc[client, 'sum'] = 0
            expense.loc[client, 'mean'] = 0

    income_dict = income.reset_index().to_dict(orient="index")
    expense_dict = expense.reset_index().to_dict(orient="index")
    
    income_json = {entry["cliente_id"]: {k: v for k, v in entry.items() if k != "cliente_id"} for entry in income_dict.values()}
    expense_json = {entry["cliente_id"]: {k: v for k, v in entry.items() if k != "cliente_id"} for entry in expense_dict.values()}
    
    return {
        "income": income_json,
        "expense": expense_json
    }


def save_to_json(data, filename):
    def convert_keys(obj):
        if isinstance(obj, dict):
            return {str(k): convert_keys(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_keys(i) for i in obj]
        else:
            return obj

    converted_data = convert_keys(data)
    
    with open(filename, "w") as json_file:
        json.dump(converted_data, json_file, indent=4)







start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 1, 31)
client_id = "123e4567-e89b-12d3-a456-426614174001"

main(start_date, end_date, client_id)