from flask import Flask, render_template, jsonify, request, redirect, url_for
import yfinance as yf
from datetime import datetime

app = Flask(__name__)

# Gerçek paylaşımlar buraya gelecek, şimdilik boş
all_posts = []

def get_financial_data():
    symbols = {
        'btc': 'BTC-USD', 'gold': 'GC=F', 'silver': 'SI=F',
        'copper': 'HG=F', 'usd_try': 'USDTRY=X', 'eur_try': 'EURTRY=X',
        'bist100': '^XU100'
    }
    prices = {}
    try:
        for key, symbol in symbols.items():
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')
            if not data.empty:
                prices[key] = data['Close'].iloc[-1]
        
        if prices.get('gold') and prices.get('usd_try'):
            # Orijinal Gram Altın TL Hesaplama Mantığı
            prices['gram_altin'] = (prices['gold'] / 31.1035) * prices['usd_try']
    except Exception as e:
        print(f"Hata: {e}")
    prices['timestamp'] = datetime.now().isoformat()
    return prices

@app.route('/')
def index():
    return render_template('index.html', page="markets")

@app.route('/feed')
def feed():
    return render_template('index.html', page="feed", posts=all_posts)

@app.route('/kesfet')
def kesfet():
    return render_template('index.html', page="explore", posts=all_posts)

@app.route('/@<username>')
def profile(username):
    user_posts = [p for p in all_posts if p['username'] == username]
    return render_template('index.html', page="profile", username=username, posts=user_posts)

@app.route('/post', methods=['POST'])
def create_post():
    content = request.form.get('content')
    if content:
        new_post = {
            "username": "misafir", # Kayıt sistemiyle burası değişecek
            "content": content,
            "stars": 0, "votes": 0, "time": "Şimdi"
        }
        all_posts.insert(0, new_post)
    return redirect(url_for('feed'))

@app.route('/api/prices')
def prices():
    return jsonify(get_financial_data())

@app.route('/api/calendar')
def calendar():
    # Orijinal geniş takvim verileri
    return jsonify({
        "fed_rate": {"current": 4.50, "next_meeting": "2026-01-28"},
        "nonfarm_payroll": {"label": "Tarım Dışı İstihdam", "value": "215K", "previous": "190K", "date": "2026-02-06"},
        "unemployment": {"label": "İşsizlik Oranı", "value": "3.9%", "previous": "4.0%", "date": "2026-02-06"},
        "inflation": {"label": "TR Enflasyon (TÜFE)", "value": "44.2%", "previous": "45.1%", "date": "2026-02-03"}
    })

if __name__ == '__main__':
    app.run(debug=True)
