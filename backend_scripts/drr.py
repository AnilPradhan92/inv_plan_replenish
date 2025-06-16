import pandas as pd
import numpy as np
import psycopg2
from datetime import datetime, timedelta

# PostgreSQL connection settings
DB_NAME = "mydatabase"
DB_USER = "myuser"
DB_PASSWORD = "login"
DB_HOST = "localhost"
DB_PORT = "5432"

# Connect to PostgreSQL and fetch inventory and sales data
conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)
cursor = conn.cursor()

# Fetch inventory data
inventory_query = "SELECT report_date, sku, total_inventory FROM inventory_data"
inventory_df = pd.read_sql(inventory_query, conn)
inventory_df = inventory_df.rename(columns={"report_date": "Date", "total_inventory": "Inventory"})

# Fetch sales data
sales_query = "SELECT order_date, sku, total_sales FROM sales_data"
sales_df = pd.read_sql(sales_query, conn)
sales_df = sales_df.rename(columns={"order_date": "Date", "total_sales": "Sales"})

# Convert to date format
inventory_df["Date"] = pd.to_datetime(inventory_df["Date"]).dt.date
sales_df["Date"] = pd.to_datetime(sales_df["Date"]).dt.date

# Filter and clean
inventory_df = inventory_df[['Date', 'sku', 'Inventory']]
sales_df = sales_df[['Date', 'sku', 'Sales']]

# Merge inventory and sales data
merged_df = pd.merge(sales_df, inventory_df, on=["Date", "sku"], how="outer")
merged_df['Sales'] = merged_df['Sales'].fillna(0)

# Latest date from both dataframes
latest_date = max(inventory_df['Date'].max(), sales_df['Date'].max())
last15_start = latest_date - timedelta(days=14)
d30_start = latest_date - timedelta(days=44)
d60_start = latest_date - timedelta(days=104)

# Function to drop sales spikes
def remove_spike_and_log(df, threshold_factor=5):
    df = df.copy()
    df['Dropped'] = 0
    non_zero_sales = df[df['Sales'] > 0]['Sales']
    if len(non_zero_sales) < 3:
        return df
    unique_sales = np.sort(non_zero_sales.unique())
    median_unique = np.median(unique_sales)
    threshold = threshold_factor * median_unique
    drop_mask = df['Sales'] > threshold
    df.loc[drop_mask, 'Dropped'] = 1
    return df[~drop_mask | (df['Sales'] == 0)]

# DRR logic
def compute_drr_window_cleaned(df, start_date, end_date, threshold_factor):
    full_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    daily = df.groupby('Date').agg({'Sales': 'sum', 'Inventory': 'last'}).reindex(full_dates)
    daily.index.name = 'Date'
    daily['Sales'] = daily['Sales'].fillna(0)
    daily['Inventory'] = daily['Inventory'].fillna(0)
    daily_cleaned = remove_spike_and_log(daily, threshold_factor=threshold_factor)
    valid_days = daily_cleaned[daily_cleaned['Inventory'] > 3]
    if valid_days.shape[0] < 5:
        return 0
    return valid_days['Sales'].sum() / valid_days.shape[0]

# DRR Calculations for Each sku
first_inv_dates = inventory_df.groupby('sku')['Date'].min().to_dict()
latest_inv = inventory_df.sort_values('Date').groupby('sku').last()['Inventory'].to_dict()

results = []

for sku, group in merged_df.groupby('sku'):
    sku_first_date = first_inv_dates.get(sku, group['Date'].min())
    overall_drr = compute_drr_window_cleaned(group, sku_first_date, latest_date, threshold_factor=5)
    drr_last15 = compute_drr_window_cleaned(group, last15_start, latest_date, threshold_factor=5)
    drr_d30 = compute_drr_window_cleaned(group, d30_start, latest_date - timedelta(days=15), threshold_factor=5)
    drr_d60 = compute_drr_window_cleaned(group, d60_start, latest_date - timedelta(days=45), threshold_factor=5)

    if all(isinstance(val, (int, float)) for val in [drr_last15, drr_d30, drr_d60]):
        if (drr_last15 > drr_d30) and (drr_d30 > drr_d60):
            trend = "Growth"
        elif (drr_last15 < drr_d30) and (drr_d30 < drr_d60):
            trend = "Decline"
        else:
            trend = "Stable"
    else:
        trend = "Insufficient Data"

    recently_launched = (latest_date - sku_first_date).days <= 10 if pd.notnull(sku_first_date) else False
    latest_inventory = latest_inv.get(sku, np.nan)

    results.append({
        'sku': sku,
        'overall_drr': overall_drr,
        'drr_l15d': drr_last15,
        'drr_l30d': drr_d30,
        'drr_l60d': drr_d60,
        'drr_trajectory': trend,
        'recently_launched': recently_launched,
        'latest_inventory': latest_inventory
    })

# Save results to a new table
for _, row in results.iterrows():
    cursor.execute("""
        INSERT INTO drr_output (
            sku, overall_drr, drr_l15d, drr_l30d, drr_l60d, 
            drr_trajectory, recently_launched, latest_inventory
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        str(row['SKU']),
        float(row['Overall_DRR']),
        float(row['DRR_L15D']),
        float(row['DRR_L30D']),
        float(row['DRR_L60D']),
        str(row['DRR_Trajectory']),
        bool(row['Recently_Launched']),
        int(row['Latest_Inventory']) if not pd.isna(row['Latest_Inventory']) else None
    ))


conn.commit()

# Clear existing data
cursor.execute("DELETE FROM drr_output")
conn.commit()

# Insert new results
for row in results:
    cursor.execute("""
        INSERT INTO drr_output (
            sku, overall_drr, drr_l15d, drr_l30d, drr_l60d,
            drr_trajectory, recently_launched, latest_inventory
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row['sku'], row['overall_drr'], row['drr_l15d'], row['drr_l30d'],
        row['drr_l60d'], row['drr_trajectory'], row['recently_launched'], row['latest_inventory']
    ))
conn.commit()
cursor.close()
conn.close()

#import ace_tools as tools; tools.display_dataframe_to_user(name="DRR Output Preview", dataframe=pd.DataFrame(results).head())
