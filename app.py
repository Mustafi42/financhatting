from flask import Flask, render_template, jsonify, request, redirect, url_for
import yfinance as yf
from datetime import datetime

app = Flask(__name__)

all_posts = []

def get_financial_data():
    symbols = {
        'btc': 'BTC-USD', 'gold': 'GC=F', 'silver': 'SI=F',
        'usd_try': 'USDTRY=X', 'eur_try': 'EURTRY=X', 'bist100': '^XU100'
    }
    prices = {}
    try:
        for key, symbol in symbols.items():
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')
            if not data.empty:
                prices[key] = data['Close'].iloc[-1]
        
        # Gram Altın TL Hesaplama (Bozulmadı)
        if prices.get('gold') and prices.get('usd_try'):
            prices['gram_altin'] = (prices['gold'] / 31.1035) * prices['usd_try']
    except Exception as e:
        print(f"Hata: {e}")
    return prices

@app.route('/')
def index():
    return render_template('index.html', page="markets")

@app.route('/feed')
def feed():
    return render_template('index.html', page="feed", posts=all_posts)

@app.route('/api/prices')
def prices():
    return jsonify(get_financial_data())

@app.route('/api/calendar')
def calendar():
    # Orijinal Detaylı Takvim Verileri
    return jsonify([
        {"country": "🇺🇸", "name": "FED Faiz Kararı", "impact": "Yüksek", "actual": "4.50%", "forecast": "4.50%", "status": "badge-blue"},
        {"country": "🇺🇸", "name": "Tarım Dışı İstihdam", "impact": "Yüksek", "actual": "215K", "forecast": "200K", "status": "badge-green"},
        {"country": "🇹🇷", "name": "TÜFE (Yıllık Enflasyon)", "impact": "Kritik", "actual": "44.2%", "forecast": "44.5%", "status": "badge-red"},
        {"country": "🇪🇺", "name": "ECB Faiz Kararı", "impact": "Yüksek", "actual": "4.25%", "forecast": "4.25%", "status": "badge-blue"},
        {"country": "🇺🇸", "name": "İşsizlik Oranı", "impact": "Orta", "actual": "3.9%", "forecast": "4.0%", "status": "badge-green"}
    ])

if __name__ == '__main__':
    app.run(debug=True)
