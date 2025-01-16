from datetime import datetime
import pandas as pd
import uploadFile, os, xlsxwriter
from dotenv import load_dotenv
load_dotenv()

BUCKET_NAME = os.getenv("BUCKET_NAME")

def main(client_id, start_date, end_date):
    print(f"\nGenerando reporte para el cliente {client_id} desde {start_date} hasta {end_date}")
    
    start_date = str(start_date).split(" ")[0]
    end_date = str(end_date).split(" ")[0]
    timestamp = int(datetime.now().timestamp())
    file_name = f"{client_id}_{start_date}_{end_date}_report_{timestamp}.xlsx"
    workbook = xlsxwriter.Workbook(file_name)
    
    global_chart(workbook)
    client_chart(workbook, client_id)

    workbook.close()
    
    url = uploadFile.upload_to_s3(file_name, BUCKET_NAME)
    if url:
        print(f"\nURL prefirmada: {url}")


def global_chart(workbook):
    worksheet = workbook.add_worksheet("Transacciones Generales")
    cell_format = workbook.add_format({'color': 'white', 'bg_color': '#0793a8', 'size': 13, 'align': 'center', 'valign': 'vcenter', 'border': 1})
    titles_format = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#026f80', 'size': 14, 'align': 'center', 'valign': 'vcenter', 'border': 1})
    
    df = pd.read_json("resumen_general.json")
    categories = df['total_by_category']

    chart = workbook.add_chart({'type': 'bar'})
    worksheet.set_column('B:D', 14)
    worksheet.set_row(1, 30)
    worksheet.write(1, 1, "Categoría", titles_format)
    worksheet.write(1, 2, "Ingreso", titles_format)
    worksheet.write(1, 3, "Gastos", titles_format)
    
    for row, (category, values) in enumerate(categories.items(), start=2):
        worksheet.write(row, 1, category, titles_format)
        worksheet.set_row(row, 25)
        for col, value in enumerate(values, start=2):
            worksheet.write(row, col, values[value], cell_format)
        chart.add_series({'values': ["Transacciones Generales", row, 2, row, 3], 'name': f'{category}'})
    
    chart.set_y_axis({'name': 'Gastos (1) / Ingresos (2)', 'font': {'size': 30, 'bold': True}})
    chart.set_legend({'font': {'size': 16, 'bold': True}, 'position': 'bottom'})
    chart.set_size({'width': 750, 'height': 530})
    chart.set_title({'name': 'Resumen de transacciones por categoría', 'name_font': {'size': 20, 'bold': True}})
    worksheet.insert_chart('H2', chart)


def client_chart(workbook, client_id):
    data = pd.read_json("resumen_por_cliente.json")
    
    income = data["income"].get(client_id, {})
    expense = data["expense"].get(client_id, {})
    
    income_df = pd.DataFrame(list(income.items()), columns=["Fecha", "Ingreso"]).sort_values(by="Fecha")
    expense_df = pd.DataFrame(list(expense.items()), columns=["Fecha", "Egreso"]).sort_values(by="Fecha")
    income_df["Fecha"] = income_df["Fecha"].str.split(" ").str[0]
    expense_df["Fecha"] = expense_df["Fecha"].str.split(" ").str[0]
    income_df["Fecha"] = income_df["Fecha"].replace({"mean": "promedio", "sum": "suma"})
    expense_df["Fecha"] = expense_df["Fecha"].replace({"mean": "promedio", "sum": "suma"})
    
    common_dates = sorted(set(income_df["Fecha"]).union(set(expense_df["Fecha"])))
    income_df = income_df.set_index("Fecha").reindex(common_dates, fill_value=0).reset_index()
    expense_df = expense_df.set_index("Fecha").reindex(common_dates, fill_value=0).reset_index()
    
    worksheet = workbook.add_worksheet("Transacciones Cliente")
    cell_format = workbook.add_format({'color': 'black', 'size': 11, 'align': 'center', 'border': 1})
    titles_format = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#026f80', 'size': 13, 'align': 'center', 'border': 1})
    
    worksheet.write("B2", "Tabla de Ingresos", titles_format)
    worksheet.write("B3", "Fecha", titles_format)
    worksheet.write("C3", "Ingreso", titles_format)
    for row, (fecha, ingreso) in enumerate(zip(income_df["Fecha"], income_df["Ingreso"]), start=3):
        worksheet.write(row, 1, fecha, cell_format)
        worksheet.write(row, 2, ingreso, cell_format)

    worksheet.write("E2", "Tabla de Egresos", titles_format)
    worksheet.write("E3", "Fecha", titles_format)
    worksheet.write("F3", "Egreso", titles_format)
    for row, (fecha, egreso) in enumerate(zip(expense_df["Fecha"], expense_df["Egreso"]), start=3):
        worksheet.write(row, 4, fecha, cell_format)
        worksheet.write(row, 5, egreso, cell_format)
    
    worksheet.set_column('B:B', 15)
    worksheet.set_column('D:D', 4)
    worksheet.set_column('E:E', 15)

    income_df_filtered = income_df[["Fecha", "Ingreso"]].head(-2)
    expense_df_filtered = expense_df[["Fecha", "Egreso"]].head(-2)
    
    chart = workbook.add_chart({'type': 'line'})
    chart.add_series({
        'name': 'Ingresos',
        'categories': ["Transacciones Cliente", 3, 1, 3 + len(income_df_filtered) - 1, 1],
        'values': ["Transacciones Cliente", 3, 2, 3 + len(income_df_filtered) - 1, 2],
        'line': {'color': 'green'},
    })
    chart.add_series({
        'name': 'Egresos',
        'categories': ["Transacciones Cliente", 3, 4, 3 + len(expense_df_filtered) - 1, 4],
        'values': ["Transacciones Cliente", 3, 5, 3 + len(expense_df_filtered) - 1, 5],
        'line': {'color': 'red'},
    })

    max_value = max(income_df_filtered["Ingreso"].max(), expense_df_filtered["Egreso"].max()) * 1.3
    min_value = min(income_df_filtered["Ingreso"].min(), expense_df_filtered["Egreso"].min()) * 0.7
    
    chart.set_y_axis({'name': 'Monto', 'min': min_value, 'max': max_value})
    chart.set_x_axis({'name': 'Fecha'})
    chart.set_legend({'position': 'bottom'})
    chart.set_title({'name': f'Transacciones de Cliente {client_id}'})
    chart.set_size({'width': 750, 'height': 450})

    worksheet.insert_chart('H2', chart)