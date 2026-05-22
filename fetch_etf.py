import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import os
from datetime import datetime

# ─── CONFIGURACIÓN ────────────────────────────────────────────────
TICKERS = [
    "VOO", "XLE", "KO",
    "TSLA", "AAPL", "NVDA", "MSFT", "AMZN",
    "XLK", "XLV", "XLF", "XLI",
    "QQQ", "VTI", "VEA", "VWO",
    "GLD", "SLV", "USO", "DJP",
    "BTC-USD", "ETH-USD", "XRP-USD"]  # Agrega más tickers aquí cuando quieras

SHEET_ID = "1V5zqEIKrMTQoaCrmD5hEnEbNcy0vQYRQHirOtE0hP1U"
SHEET_NAME = "Precios"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ─── AUTENTICACIÓN CON GOOGLE ─────────────────────────────────────
creds_json = os.environ["GOOGLE_CREDENTIALS"]
creds_dict = json.loads(creds_json)
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

# ─── ABRIR SHEET ──────────────────────────────────────────────────
spreadsheet = client.open_by_key(SHEET_ID)

try:
    worksheet = spreadsheet.worksheet(SHEET_NAME)
except gspread.exceptions.WorksheetNotFound:
    worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=100000, cols=10)

# ─── DESCARGAR DATOS ──────────────────────────────────────────────
print(f"Descargando datos para: {TICKERS}")

all_data = []

for ticker in TICKERS:
    print(f"  → {ticker}...")
    stock = yf.Ticker(ticker)
    hist = stock.history(period="10y")

    if hist.empty:
        print(f"  ✗ Sin datos para {ticker}")
        continue

    hist = hist.reset_index()
    hist["Ticker"] = ticker
    hist["Date"] = hist["Date"].dt.strftime("%Y-%m-%d")

    df = hist[["Date", "Ticker", "Open", "High", "Low", "Close", "Volume"]].copy()
    df = df.round(4)
    all_data.append(df)

if not all_data:
    print("No se obtuvo ningún dato.")
    exit(1)

final_df = pd.concat(all_data, ignore_index=True)
final_df = final_df.sort_values(["Ticker", "Date"]).reset_index(drop=True)

print(f"Total de filas: {len(final_df)}")

# ─── ESCRIBIR EN GOOGLE SHEETS ────────────────────────────────────
print("Escribiendo en Google Sheets...")

worksheet.clear()

headers = ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume"]
rows = [headers] + final_df.values.tolist()

worksheet.update(range_name="A1", values=rows)

print(f"✓ Listo. {len(final_df)} filas escritas el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
