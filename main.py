import requests
from bs4 import BeautifulSoup
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask
from threading import Thread
import time
import os

# === CONFIG ===
URL = "https://www.google.com/finance/quote/EUR-USD?hl=it"
CREDENTIALS_FILE = "/etc/secrets/progetto-signal-e95160b2462f.json"  # Percorso segreto su Render
SPREADSHEET_NAME = "eur_usd"
WORKSHEET_NAME = "data"
SLEEP_SECONDS = 60

# === FLASK APP ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot attivo"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

Thread(target=run_flask).start()

# === FUNZIONI ===
def fetch_eur_usd():
    try:
        print("🔍 Inizio scraping...")
        response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        tag = soup.find("div", class_="YMlKec fxKbKc")
        if tag:
            text = tag.text.replace(".", "").replace(",", ".")
            price = float(text)
            print(f"✅ Prezzo trovato: {price}")
            return price
        else:
            print("⚠️ Tag HTML non trovato.")
    except Exception as e:
        print("❌ Errore scraping:", e)
    return None

def connect_to_sheet():
    print("🔗 Connessione a Google Sheet...")
    scopes = ["https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME)
    try:
        ws = sheet.worksheet(WORKSHEET_NAME)
        print("📄 Worksheet trovato.")
    except gspread.exceptions.WorksheetNotFound:
        print("🆕 Worksheet non trovato, lo creo...")
        ws = sheet.add_worksheet(title=WORKSHEET_NAME, rows="10000", cols="2")
        ws.append_row(["timestamp", "eur_usd"])
    return ws

# === LOOP ===
print("🚀 Avvio bot EUR/USD...")
worksheet = connect_to_sheet()

try:
    while True:
        price = fetch_eur_usd()
        if price:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"📥 Scrivo riga: {timestamp}, {price}")
            worksheet.append_row([timestamp, price])
        else:
            print("⚠️ Prezzo non disponibile, salto scrittura.")
        time.sleep(SLEEP_SECONDS)
except KeyboardInterrupt:
    print("⏹️ Bot interrotto.")
