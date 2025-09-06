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
# SOSTITUISCI CON IL SELETTORE CORRETTO!
HTML_ELEMENT_TAG = "div"
HTML_ELEMENT_CLASS = "YMlKec fxKbKc" # <-- Probabilmente da cambiare!

CREDENTIALS_FILE = "/etc/secrets/progetto-signal-e95160b2462f.json"
SPREADSHEET_NAME = "eur_usd"
WORKSHEET_NAME = "data"
SLEEP_SECONDS = 60

# === FLASK APP (invariato) ===
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
        response.raise_for_status() # Controlla se la richiesta ha avuto successo
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Aggiorna qui con il selettore corretto trovato ispezionando la pagina
        tag = soup.find(HTML_ELEMENT_TAG, class_=HTML_ELEMENT_CLASS) 
        
        if tag:
            text = tag.text.replace(".", "").replace(",", ".")
            price = float(text)
            print(f"✅ Prezzo trovato: {price}")
            return price
        else:
            print("⚠️ Tag HTML non trovato. Controlla il selettore.")
    except Exception as e:
        print(f"❌ Errore durante lo scraping: {e}")
    return None

def connect_to_sheet():
    try:
        print("🔗 Connessione a Google Sheet...")
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
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
    except Exception as e:
        print(f"❌ Errore durante la connessione a Google Sheets: {e}")
        return None

# === LOOP ===
print("🚀 Avvio bot EUR/USD...")

try:
    while True:
        price = fetch_eur_usd()
        
        if price:
            # SPOSTATA LA CONNESSIONE ALL'INTERNO DEL LOOP
            # per evitare la scadenza del token di autenticazione.
            worksheet = connect_to_sheet()
            
            if worksheet:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"📥 Scrivo riga: {timestamp}, {price}")
                try:
                    worksheet.append_row([timestamp, price])
                except Exception as e:
                    print(f"❌ Errore durante la scrittura su Google Sheet: {e}")
            else:
                print("⚠️ Connessione al foglio non riuscita, salto scrittura.")
        else:
            print("⚠️ Prezzo non disponibile, salto scrittura.")
            
        print(f"😴 Attendo {SLEEP_SECONDS} secondi...")
        time.sleep(SLEEP_SECONDS)
        
except KeyboardInterrupt:
    print("⏹️ Bot interrotto.")
