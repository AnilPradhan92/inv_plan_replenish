import requests
import json
import pandas as pd
import psycopg2
import time
from io import StringIO
from datetime import datetime, timedelta

# PostgreSQL connection settings
DB_NAME = "mydatabase"
DB_USER = "myuser"
DB_PASSWORD = "login"
DB_HOST = "localhost"
DB_PORT = "5432"

# Easyecom credentials
url = 'https://api.easyecom.io/reports/queue'
api_key = '30300d847dbe2d325b032963e2abc446ef289667'
auth_key = ('Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczpcL1wvbG9hZGJhbGFu'
    'Y2VyLW0uZWFzeWVjb20uaW9cL2FjY2Vzc1wvdG9rZW4iLCJpYXQiOjE3NDkwMTM1NTcsImV4cCI6MTc1'
    'Njg5NzU1NywibmJmIjoxNzQ5MDEzNTU3LCJqdGkiOiJUdWRkME03dGF4d2paMTJ0Iiwic3ViIjoyMDIw'
    'MzUsInBydiI6ImE4NGRlZjY0YWQwMTE1ZDVlY2NjMWY4ODQ1YmNkMGU3ZmU2YzRiNjAiLCJ1c2VyX2lk'
    'IjoyMDIwMzUsImNvbXBhbnlfaWQiOjg4MzgzLCJyb2xlX3R5cGVfaWQiOjIsInBpaV9hY2Nlc3MiOjAs'
    'InBpaV9yZXBvcnRfYWNjZXNzIjowLCJyb2xlcyI6bnVsbCwiY19pZCI6ODgzODMsInVfaWQiOjIwMjAz'
    'NSwibG9jYXRpb25fcmVxdWVzdGVkX2ZvciI6ODgzODN9.nTVnUEJoSpJ_LrkCrIBmwmGqZz1wtJxS1PLf5UcICgU')

headers = {
    'x-api-key': api_key,
    'Authorization': auth_key,
    'Content-Type': 'application/json'
}

# Check if table exists and get max date
def get_or_create_table():
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'sales_data'
            );
        """)
        exists = cursor.fetchone()[0]

        if exists:
            cursor.execute("SELECT MAX(order_date) FROM sales_data;")
            max_date = cursor.fetchone()[0] or datetime.strptime("2025-06-01", "%Y-%m-%d").date()
        else:
            cursor.execute("""
                CREATE TABLE sales_data (
                    order_date DATE,
                    sku VARCHAR(255),
                    TS_TRP INT DEFAULT 0,
                    TS_GUR INT DEFAULT 0,
                    TS_BLR INT DEFAULT 0,
                    TS_KOL INT DEFAULT 0,
                    total_sales INT DEFAULT 0
                );
            """)
            conn.commit()
            max_date = datetime.strptime("2025-06-01", "%Y-%m-%d").date()

        cursor.close()
        conn.close()
        return max_date
    except Exception as e:
        print(f"Database error: {e}")
        return datetime.strptime("2025-06-01", "%Y-%m-%d").date()

def fetch_and_append_data(start_date, end_date):
    payload = json.dumps({
        "reportType": "MINI_SALES_REPORT",
        "params": {
            "invoiceType": "ALL",
            "warehouseIds": "ee7811554689,ee9386315689,ne11577975201,en11637447129",
            "dateType": "ORDER_DATE",
            "startDate": start_date.strftime('%Y-%m-%d'),
            "endDate": end_date.strftime('%Y-%m-%d')
        }
    })

    print(f"Fetching data from {start_date} to {end_date}")
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code != 200:
        print(f"Error fetching report ID: {response.json()}")
        return pd.DataFrame()

    report_id = response.json().get("data", {}).get("reportId")
    if not report_id:
        print("No report ID found.")
        return pd.DataFrame()

    # Download with retries
    report_url = f"https://api.easyecom.io/reports/download?reportId={report_id}"
    for i in range(10):
        time.sleep(45)
        r = requests.get(report_url, headers=headers)
        if r.status_code == 200:
            down_url = r.json().get("data", {}).get("downloadUrl", "")
            if down_url:
                file = requests.get(down_url)
                if file.status_code == 200:
                    return pd.read_csv(StringIO(file.text))
        print(f"Retry {i+1} to get download URL...")
    
    print("Failed to download data.")
    return pd.DataFrame()

def process_and_store(df):
    if df.empty:
        return

    df = df[['Client Location', 'Order Date', 'SKU', 'Item Quantity']]
    df["SKU"] = df["SKU"].str.replace("`", "", regex=True)
    df["Client Location"] = df["Client Location"].replace({
        "Technosport Tiruppur": "TS_TRP",
        "Technosport - Gurgaon": "TS_GUR",
        "Technosport": "TS_BLR",
        "Technosport(Kolkata)": "TS_KOL"
    })

    df.rename(columns={
        'Client Location': 'client_location',
        'SKU': 'sku',
        'Order Date': 'order_date',
        'Item Quantity': 'quantity_sold'
    }, inplace=True)

    df['order_date'] = pd.to_datetime(df['order_date']).dt.date

    pivot = df.pivot_table(
        index=['order_date', 'sku'],
        columns='client_location',
        values='quantity_sold',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    pivot['total_sales'] = pivot.drop(columns=['order_date', 'sku']).sum(axis=1)

    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        cursor = conn.cursor()
        for _, row in pivot.iterrows():
            cursor.execute("""
                INSERT INTO sales_data (order_date, sku, TS_TRP, TS_GUR, TS_BLR, TS_KOL, total_sales)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                row['order_date'],
                row['sku'],
                row.get('TS_TRP', 0),
                row.get('TS_GUR', 0),
                row.get('TS_BLR', 0),
                row.get('TS_KOL', 0),
                row.get('total_sales', 0)
            ))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Stored {len(pivot)} rows.")
    except Exception as e:
        print(f"Error storing pivot data: {e}")

# Main logic
max_date = get_or_create_table()
today = datetime.today().date() - timedelta(days=1)

if max_date > today:
    print("No new data to fetch.")
else:
    all_data = pd.DataFrame()
    current = max_date + timedelta(days=1)
    while current <= today:
        next_date = min(current + timedelta(days=14), today)
        df = fetch_and_append_data(current, next_date)
        if not df.empty:
            all_data = pd.concat([all_data, df], ignore_index=True)
        current = next_date + timedelta(days=1)

    process_and_store(all_data)
