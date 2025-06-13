import requests
import json
import pandas as pd
import psycopg2
from io import StringIO
from datetime import datetime, timedelta

# PostgreSQL connection settings
DB_NAME = "mydatabase"
DB_USER = "myuser"
DB_PASSWORD = "login"
DB_HOST = "localhost"
DB_PORT = "5432"

api_key = '30300d847dbe2d325b032963e2abc446ef289667'
auth_key = ('Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczpcL1wvbG9hZGJhbGFu'
    'Y2VyLW0uZWFzeWVjb20uaW9cL2FjY2Vzc1wvdG9rZW4iLCJpYXQiOjE3NDkwMTM1NTcsImV4cCI6MTc1'
    'Njg5NzU1NywibmJmIjoxNzQ5MDEzNTU3LCJqdGkiOiJUdWRkME03dGF4d2paMTJ0Iiwic3ViIjoyMDIw'
    'MzUsInBydiI6ImE4NGRlZjY0YWQwMTE1ZDVlY2NjMWY4ODQ1YmNkMGU3ZmU2YzRiNjAiLCJ1c2VyX2lk'
    'IjoyMDIwMzUsImNvbXBhbnlfaWQiOjg4MzgzLCJyb2xlX3R5cGVfaWQiOjIsInBpaV9hY2Nlc3MiOjAs'
    'InBpaV9yZXBvcnRfYWNjZXNzIjowLCJyb2xlcyI6bnVsbCwiY19pZCI6ODgzODMsInVfaWQiOjIwMjAz'
    'NSwibG9jYXRpb25fcmVxdWVzdGVkX2ZvciI6ODgzODN9.nTVnUEJoSpJ_LrkCrIBmwmGqZz1wtJxS1PLf5UcICgU')

def table_exists_and_get_max_date():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'inventory_data'
            );
        """)
        exists = cursor.fetchone()[0]

        if exists:
            cursor.execute("SELECT MAX(report_date) FROM inventory_data;")
            max_date = cursor.fetchone()[0]
        else:
            max_date = None

        cursor.close()
        conn.close()
        return exists, max_date
    except Exception as e:
        print(f"Database error: {e}")
        return False, None

def create_table():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_data (
                report_date TIMESTAMP,
                sku VARCHAR(255),
                TS_BLR INT,
                TS_GUR INT,
                TS_TRP INT,
                TS_KOL INT,
                total_inventory INT
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Table created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")

def fetch_and_process_data(start_date, end_date):
    url = f"https://api.easyecom.io/inventory/getInventorySnapshotApi?start_date={start_date}&end_date={end_date}"
    headers = {
        'x-api-key': api_key,
        'Authorization': auth_key,
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}: {response.text}")
        return pd.DataFrame()

    report_data = response.json()
    links = pd.DataFrame(report_data["data"])
    all_data = pd.DataFrame([])

    for i in range(len(links.index)):
        csv_url = links.iloc[i, 5]
        date = links.iloc[i, 3]
        date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").date()

        inv_data_daily = requests.get(csv_url)
        if inv_data_daily.status_code == 200:
            data_inv = pd.read_csv(StringIO(inv_data_daily.text))
            print(f"CSV data fetched for {date}, rows: {len(data_inv.index)}")
            all_data = pd.concat([all_data, data_inv], ignore_index=True)
        else:
            print(f"Failed to fetch CSV for {date}: {inv_data_daily.status_code}")

    if all_data.empty:
        return all_data

    all_data['Report Generated Date'] = pd.to_datetime(all_data['Report Generated Date']).dt.date
    pivot = pd.pivot_table(
        all_data,
        index=['Report Generated Date','SKU'],
        columns=['Location'],
        values=['Available Quantity'],
        aggfunc='sum',
        fill_value=0
    )

    pivot.columns = pivot.columns.droplevel(0)
    pivot['Total'] = pivot.sum(axis=1)
    pivot = pivot.reset_index()

    pivot.rename(columns={
        'Report Generated Date': 'report_date',
        'SKU': 'sku',
        'Technosport': 'TS_BLR',
        'Technosport - Gurgaon': 'TS_GUR',
        'Technosport Tiruppur': 'TS_TRP',
        'Technosport(Kolkata)': 'TS_KOL',
        'Total': 'total_inventory'
    }, inplace=True)

    pivot["sku"] = pivot["sku"].str.replace("`", "", regex=True)
    return pivot

def store_data_to_db(data):
    if data.empty:
        print("No data to store.")
        return

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        cursor = conn.cursor()
        for _, row in data.iterrows():
            cursor.execute(
                """
                INSERT INTO inventory_data (report_date, sku, TS_BLR, TS_GUR, 
                TS_TRP, TS_KOL, total_inventory)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (row['report_date'], row['sku'], row.get('TS_BLR', 0), row.get('TS_GUR', 0),
                 row.get('TS_TRP', 0), row.get('TS_KOL', 0), row['total_inventory'])
            )
        conn.commit()
        cursor.close()
        conn.close()
        print("Data successfully stored in database.")
    except Exception as e:
        print(f"Error storing data: {e}")

# Main logic
table_exists, max_date = table_exists_and_get_max_date()

if not table_exists:
    create_table()
    start_date = datetime.strptime("2025-06-01", "%Y-%m-%d")
else:
    start_date = max_date + timedelta(days=1)

end_date = datetime.today() - timedelta(days=1)

print(f"Fetching inventory data from {start_date.date()} to {end_date.date()} in 15-day intervals.")

current_date = start_date
while current_date <= end_date:
    interval_end = min(current_date + timedelta(days=14), end_date)
    print(f"Processing interval: {current_date.date()} to {interval_end.date()}")
    data_chunk = fetch_and_process_data(
        current_date.strftime('%Y-%m-%d 00:00:00'),
        interval_end.strftime('%Y-%m-%d 23:59:59')
    )
    store_data_to_db(data_chunk)
    current_date = interval_end + timedelta(days=1)
