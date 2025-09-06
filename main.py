
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask
from threading import Thread
import time

# === CONFIG ===
URL = "https://www.google.com/finance/quote/EUR-USD?hl=it"
CREDENTIALS_FILE = "/etc/secrets/progetto-signal-e95160b2462f.json"  # cambia con il tuo vero nome file
SPREADSHEET_NAME = "eur_usd"
WORKSHEET_NAME = "data"
SLEEP_SECONDS = 60

# === FLASK APP PER UPTIMEROBOT ===
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot attivo"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# === FUNZIONI ===
def fetch_eur_usd():
    try:
        response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        tag = soup.find("div", class_="YMlKec fxKbKc")
        if tag:
            text = tag.text.replace(".", "").replace(",", ".")
            return float(text)
        return None
    except Exception as e:
        print("❌ Errore scraping:", e)
        return None

def connect_to_sheet():
    scopes = ["https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME)
    try:
        ws = sheet.worksheet(WORKSHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=WORKSHEET_NAME, rows="1000", cols="2")
        ws.append_row(["timestamp", "eur_usd"])
    return ws

# === LOOP AUTOMATICO ===
print("🚀 Avvio bot EUR/USD...")

worksheet = connect_to_sheet()

try:
    while True:
        price = fetch_eur_usd()
        if price:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([timestamp, price])
            print(f"✅ {timestamp} → {price}")
        else:
            print("⚠️ Prezzo non trovato.")
        time.sleep(SLEEP_SECONDS)
except KeyboardInterrupt:
    print("⏹️ Bot interrotto.")
