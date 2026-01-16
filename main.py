import os
import yfinance as yf
from flask import Flask, jsonify, send_from_directory, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'finans_gold_master_2026_super_secret_key_123456')

# CORS - Production için güvenli ayarlar
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
     supports_credentials=True,
     allow_headers=["Content-Type"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Database - PostgreSQL veya SQLite
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Railway PostgreSQL için
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Local development için SQLite
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database.db")}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Session ayarları - Railway için
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 saat

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.String(500), default='')
    avatar = db.Column(db.String(10), default='👤')
    profile_image = db.Column(db.Text)
    joined_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_posts = db.Column(db.Integer, default=0)
    total_comments = db.Column(db.Integer, default=0)

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    likes = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    username = db.Column(db.String(80))
    avatar = db.Column(db.String(10), default='👤')
    comment_count = db.Column(db.Integer, default=0)
    rating_sum = db.Column(db.Integer, default=0)
    rating_count = db.Column(db.Integer, default=0)

class PostComment(db.Model):
    __tablename__ = 'post_comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.Column(db.String(80))
    avatar = db.Column(db.String(10), default='👤')
    rating_sum = db.Column(db.Integer, default=0)
    rating_count = db.Column(db.Integer, default=0)

class AssetComment(db.Model):
    __tablename__ = 'asset_comments'
    id = db.Column(db.Integer, primary_key=True)
    asset_symbol = db.Column(db.String(50), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.Column(db.String(80))
    avatar = db.Column(db.String(10), default='👤')
    rating_sum = db.Column(db.Integer, default=0)
    rating_count = db.Column(db.Integer, default=0)

# Database initialization
with app.app_context():
    try:
        db.create_all()
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")

# --- SYMBOL MAPPING ---
SYMBOL_MAP = {
    'gold_ons': 'GC=F',
    'gold_gram': 'GC=F',
    'usdtry': 'USDTRY=X',
    'bitcoin': 'BTC-USD',
    'ethereum': 'ETH-USD'
}

# --- ROUTES ---

@app.route('/')
def index():
    try:
        return send_from_directory('.', 'index.html')
    except Exception as e:
        logger.error(f"❌ Index error: {e}")
        return jsonify({'error': 'Page not found'}), 404

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'database': 'connected' if db.engine else 'disconnected',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/economic-calendar')
def get_economic_calendar():
    try:
        calendar = {
            'fed_rate': {
                'name': 'FED Faiz Oranı',
                'current': '4.25% - 4.50%',
                'next_meeting': '29 Ocak 2025',
                'icon': '🏦',
                'color': '#10b981',
                'description': 'Federal Reserve Para Politikası Toplantısı'
            },
            'tcmb_rate': {
                'name': 'TCMB Faiz Oranı',
                'current': '47.50%',
                'next_meeting': '23 Ocak 2025',
                'icon': '🇹🇷',
                'color': '#ef4444',
                'description': 'Türkiye Cumhuriyet Merkez Bankası PPK Toplantısı'
            },
            'us_inflation': {
                'name': 'ABD Enflasyon (CPI)',
                'current': '2.7% (Aralık)',
                'next_release': '12 Şubat 2025',
                'icon': '📊',
                'color': '#f59e0b',
                'description': 'Tüketici Fiyat Endeksi - Ocak Verisi'
            },
            'us_jobs': {
                'name': 'ABD İstihdam Verisi',
                'current': '256K (Aralık)',
                'next_release': '7 Şubat 2025',
                'icon': '👔',
                'color': '#8b5cf6',
                'description': 'Tarım Dışı İstihdam (NFP) - Ocak Verisi'
            },
            'tr_inflation': {
                'name': 'Türkiye Enflasyon',
                'current': '44.38% (Aralık)',
                'next_release': '3 Şubat 2025',
                'icon': '📈',
                'color': '#ec4899',
                'description': 'TÜFE Yıllık - Ocak Verisi'
            },
            'ecb_rate': {
                'name': 'ECB Faiz Oranı',
                'current': '3.15%',
                'next_meeting': '30 Ocak 2025',
                'icon': '🇪🇺',
                'color': '#06b6d4',
                'description': 'Avrupa Merkez Bankası Para Politikası Kararı'
            }
        }
        return jsonify(calendar)
    except Exception as e:
        logger.error(f"❌ Economic calendar error: {e}")
        return jsonify({}), 500

@app.route('/api/market-data')
def get_market_data():
    try:
        symbols = ["GC=F", "USDTRY=X", "BTC-USD", "ETH-USD"]
        data = yf.download(symbols, period="1d", interval="1m", progress=False, auto_adjust=True)
        
        last_row = data['Close'].ffill().iloc[-1]
        
        usd_val = float(last_row['USDTRY=X'])
        ons_val = float(last_row['GC=F'])
        btc_val = float(last_row['BTC-USD'])
        eth_val = float(last_row['ETH-USD'])
        
        gram_gold = (ons_val / 31.1035) * usd_val
        
        result = {
            'gold_ons': {'name': 'Altın Ons', 'value': f"${ons_val:,.2f}", 'logo': '🟡'},
            'gold_gram': {'name': 'Gram Altın', 'value': f"{gram_gold:,.2f} ₺", 'logo': '🟨'},
            'usdtry': {'name': 'Dolar/TL', 'value': f"{usd_val:,.2f} ₺", 'logo': '💲'},
            'bitcoin': {'name': 'Bitcoin', 'value': f"${btc_val:,.0f}", 'logo': '🟠'},
            'ethereum': {'name': 'Ethereum', 'value': f"${eth_val:,.2f}", 'logo': '🔵'}
        }
        return jsonify(result)
    except Exception as e:
        logger.error(f"❌ Market data error: {e}")
        # Fallback data
        return jsonify({
            'gold_ons': {'name': 'Altın Ons', 'value': "$2,652.10", 'logo': '🟡'},
            'gold_gram': {'name': 'Gram Altın', 'value': "6,226.40 ₺", 'logo': '🟨'},
            'usdtry': {'name': 'Dolar/TL', 'value': "35.80 ₺", 'logo': '💲'},
            'bitcoin': {'name': 'Bitcoin', 'value': "$95,800", 'logo': '🟠'},
            'ethereum': {'name': 'Ethereum', 'value': "$3,250", 'logo': '🔵'}
        })

@app.route('/api/candlestick/<symbol>')
def get_candlestick(symbol):
    try:
        period_type = request.args.get('period', 'daily')
        yahoo_symbol = SYMBOL_MAP.get(symbol, 'BTC-USD')
        
        period_config = {
            'daily': ('1y', '1d'),
            'weekly': ('3y', '1wk'),
            'monthly': ('5y', '1mo')
        }
        period, interval = period_config.get(period_type, ('1y', '1d'))
        
        ticker = yf.Ticker(yahoo_symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return jsonify({'error': 'Veri bulunamadı'}), 404
        
        if symbol == 'gold_gram':
            try:
                usd_data = yf.download("USDTRY=X", period="1d", interval="1m", progress=False)
                usd_rate = float(usd_data['Close'].ffill().iloc[-1])
                hist[['Open', 'High', 'Low', 'Close']] = hist[['Open', 'High', 'Low', 'Close']].div(31.1035).mul(usd_rate)
            except:
                pass
        
        candlestick_data = [{
            'time': index.strftime('%Y-%m-%d'),
            'open': round(float(row['Open']), 2),
            'high': round(float(row['High']), 2),
            'low': round(float(row['Low']), 2),
            'close': round(float(row['Close']), 2),
            'volume': int(row['Volume']) if 'Volume' in row else 0
        } for index, row in hist.iterrows()]
        
        return jsonify({
            'symbol': symbol,
            'period': period_type,
            'data': candlestick_data
        })
    except Exception as e:
        logger.error(f"❌ Candlestick error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Kullanıcı adı ve şifre gerekli'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Bu kullanıcı adı alınmış'}), 400
        
        import random
        avatars = ['👤', '😎', '🚀', '💎', '🎯', '⚡', '🔥', '🌟', '💰', '🦁']
        
        user = User(
            full_name=data.get('full_name', 'İsimsiz Kullanıcı'),
            username=data['username'],
            password=generate_password_hash(data['password']),
            avatar=random.choice(avatars)
        )
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"✅ New user registered: {data['username']}")
        return jsonify({'success': True, 'message': 'Kayıt başarılı!'})
    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Kayıt işlemi başarısız'}), 500

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Kullanıcı adı ve şifre gerekli'}), 400
        
        user = User.query.get(session['user_id'])
        user.total_comments = max(0, user.total_comments - 1)
        
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Delete asset comment error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/rate-asset-comment', methods=['POST', 'OPTIONS'])
def rate_asset_comment():
    if request.method == 'OPTIONS':
        return '', 204
    if 'user_id' not in session:
        return jsonify({'error': 'Giriş yapmalısınız'}), 401
    
    try:
        data = request.json
        comment = AssetComment.query.get(data['comment_id'])
        rating = int(data['rating'])
        
        if not 1 <= rating <= 5:
            return jsonify({'error': 'Geçersiz oy'}), 400
        
        comment.rating_sum += rating
        comment.rating_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'rating_avg': round(comment.rating_sum / comment.rating_count, 1),
            'rating_count': comment.rating_count
        })
    except Exception as e:
        logger.error(f"❌ Rate asset comment error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('.', path)
    except:
        return send_from_directory('.', 'index.html')

@app.errorhandler(404)
def not_found(e):
    return send_from_directory('.', 'index.html')

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"❌ Internal error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    logger.info(f"🚀 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)filter_by(username=data['username']).first()
        
        if user and check_password_hash(user.password, data['password']):
            session.permanent = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['avatar'] = user.avatar
            logger.info(f"✅ User logged in: {user.username}")
            return jsonify({'username': user.username, 'avatar': user.avatar})
        
        return jsonify({'error': 'Kullanıcı adı veya şifre hatalı'}), 401
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        return jsonify({'error': 'Giriş işlemi başarısız'}), 500

@app.route('/api/check-session')
def check_session():
    if 'username' in session:
        return jsonify({
            'logged_in': True,
            'username': session['username'],
            'avatar': session.get('avatar', '👤')
        })
    return jsonify({'logged_in': False})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/profile/<username>')
def get_profile(username):
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
        
        posts = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.desc()).all()
        
        return jsonify({
            'username': user.username,
            'full_name': user.full_name,
            'bio': user.bio,
            'avatar': user.avatar,
            'profile_image': user.profile_image,
            'joined_date': user.joined_date.strftime('%Y-%m-%d'),
            'total_posts': user.total_posts,
            'total_comments': user.total_comments,
            'posts': [{
                'id': p.id,
                'content': p.content,
                'timestamp': p.timestamp.strftime('%Y-%m-%d %H:%M'),
                'likes': p.likes,
                'comment_count': p.comment_count,
                'avatar': p.avatar,
                'rating_avg': round(p.rating_sum / p.rating_count, 1) if p.rating_count else 0,
                'rating_count': p.rating_count or 0
            } for p in posts]
        })
    except Exception as e:
        logger.error(f"❌ Profile error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Giriş yapmalısınız'}), 401
    
    try:
        data = request.json
        user = User.query.get(session['user_id'])
        
        if 'bio' in data:
            user.bio = data['bio']
        if 'avatar' in data:
            user.avatar = data['avatar']
            session['avatar'] = data['avatar']
        if 'profile_image' in data:
            user.profile_image = data['profile_image']
        if data.get('remove_image'):
            user.profile_image = None
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Profile update error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/post', methods=['POST', 'OPTIONS'])
def add_post():
    if request.method == 'OPTIONS':
        return '', 204
        
    if 'user_id' not in session:
        return jsonify({'error': 'Giriş yapmalısınız'}), 401
    
    try:
        data = request.json
        post = Post(
            content=data['content'],
            user_id=session['user_id'],
            username=session['username'],
            avatar=session.get('avatar', '👤')
        )
        db.session.add(post)
        
        user = User.query.get(session['user_id'])
        user.total_posts += 1
        
        db.session.commit()
        return jsonify({'success': True, 'post_id': post.id})
    except Exception as e:
        logger.error(f"❌ Post creation error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/post/<int:post_id>', methods=['DELETE', 'PUT', 'OPTIONS'])
def manage_post(post_id):
    if request.method == 'OPTIONS':
        return '', 204
        
    if 'user_id' not in session:
        return jsonify({'error': 'Giriş yapmalısınız'}), 401
    
    try:
        post = Post.query.get(post_id)
        if not post:
            return jsonify({'error': 'Gönderi bulunamadı'}), 404
        
        if post.user_id != session['user_id']:
            return jsonify({'error': 'Yetkiniz yok'}), 403
        
        if request.method == 'DELETE':
            PostComment.query.filter_by(post_id=post_id).delete()
            db.session.delete(post)
            user = User.query.get(session['user_id'])
            user.total_posts = max(0, user.total_posts - 1)
            db.session.commit()
            return jsonify({'success': True})
        
        elif request.method == 'PUT':
            data = request.json
            post.content = data['content']
            db.session.commit()
            return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Post management error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/feed')
def get_feed():
    try:
        posts = Post.query.order_by(Post.timestamp.desc()).limit(50).all()
        return jsonify([{
            'id': p.id,
            'user': p.username,
            'avatar': p.avatar,
            'content': p.content,
            'likes': p.likes,
            'comment_count': p.comment_count,
            'timestamp': p.timestamp.strftime('%Y-%m-%d %H:%M'),
            'rating_avg': round(p.rating_sum / p.rating_count, 1) if p.rating_count else 0,
            'rating_count': p.rating_count or 0
        } for p in posts])
    except Exception as e:
        logger.error(f"❌ Feed error: {e}")
        return jsonify([])

@app.route('/api/rate-post', methods=['POST', 'OPTIONS'])
def rate_post():
    if request.method == 'OPTIONS':
        return '', 204
    if 'user_id' not in session:
        return jsonify({'error': 'Giriş yapmalısınız'}), 401
    
    try:
        data = request.json
        post = Post.query.get(data['post_id'])
        rating = int(data['rating'])
        
        if not 1 <= rating <= 5:
            return jsonify({'error': 'Geçersiz oy'}), 400
        
        post.rating_sum += rating
        post.rating_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'rating_avg': round(post.rating_sum / post.rating_count, 1),
            'rating_count': post.rating_count
        })
    except Exception as e:
        logger.error(f"❌ Rate post error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/post-comments/<int:post_id>')
def get_post_comments(post_id):
    try:
        comments = PostComment.query.filter_by(post_id=post_id).order_by(PostComment.timestamp.desc()).all()
        return jsonify([{
            'id': c.id,
            'username': c.username,
            'avatar': c.avatar,
            'content': c.content,
            'timestamp': c.timestamp.strftime('%Y-%m-%d %H:%M'),
            'rating_avg': round(c.rating_sum / c.rating_count, 1) if c.rating_count else 0,
            'rating_count': c.rating_count or 0
        } for c in comments])
    except Exception as e:
        logger.error(f"❌ Post comments error: {e}")
        return jsonify([])

@app.route('/api/post-comment', methods=['POST', 'OPTIONS'])
def add_post_comment():
    if request.method == 'OPTIONS':
        return '', 204
    if 'user_id' not in session:
        return jsonify({'error': 'Giriş yapmalısınız'}), 401
    
    try:
        data = request.json
        comment = PostComment(
            post_id=data['post_id'],
            content=data['content'],
            user_id=session['user_id'],
            username=session['username'],
            avatar=session.get('avatar', '👤')
        )
        db.session.add(comment)
        
        post = Post.query.get(data['post_id'])
        post.comment_count += 1
        
        user = User.query.get(session['user_id'])
        user.total_comments += 1
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Post comment error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/post-comment/<int:comment_id>', methods=['DELETE', 'OPTIONS'])
def delete_post_comment(comment_id):
    if request.method == 'OPTIONS':
        return '', 204
    if 'user_id' not in session:
        return jsonify({'error': 'Giriş yapmalısınız'}), 401
    
    try:
        comment = PostComment.query.get(comment_id)
        if not comment or comment.user_id != session['user_id']:
            return jsonify({'error': 'Yetkiniz yok'}), 403
        
        post = Post.query.get(comment.post_id)
        post.comment_count = max(0, post.comment_count - 1)
        
        user = User.query.get(session['user_id'])
        user.total_comments = max(0, user.total_comments - 1)
        
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Delete comment error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/rate-post-comment', methods=['POST', 'OPTIONS'])
def rate_post_comment():
    if request.method == 'OPTIONS':
        return '', 204
    if 'user_id' not in session:
        return jsonify({'error': 'Giriş yapmalısınız'}), 401
    
    try:
        data = request.json
        comment = PostComment.query.get(data['comment_id'])
        rating = int(data['rating'])
        
        if not 1 <= rating <= 5:
            return jsonify({'error': 'Geçersiz oy'}), 400
        
        comment.rating_sum += rating
        comment.rating_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'rating_avg': round(comment.rating_sum / comment.rating_count, 1),
            'rating_count': comment.rating_count
        })
    except Exception as e:
        logger.error(f"❌ Rate comment error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/asset-comments/<symbol>')
def get_asset_comments(symbol):
    try:
        comments = AssetComment.query.filter_by(asset_symbol=symbol).order_by(AssetComment.timestamp.desc()).limit(50).all()
        return jsonify([{
            'id': c.id,
            'username': c.username,
            'avatar': c.avatar,
            'content': c.content,
            'timestamp': c.timestamp.strftime('%Y-%m-%d %H:%M'),
            'rating_avg': round(c.rating_sum / c.rating_count, 1) if c.rating_count else 0,
            'rating_count': c.rating_count or 0
        } for c in comments])
    except Exception as e:
        logger.error(f"❌ Asset comments error: {e}")
        return jsonify([])

@app.route('/api/asset-comment', methods=['POST', 'OPTIONS'])
def add_asset_comment():
    if request.method == 'OPTIONS':
        return '', 204
    if 'user_id' not in session:
        return jsonify({'error': 'Giriş yapmalısınız'}), 401
    
    try:
        data = request.json
        comment = AssetComment(
            asset_symbol=data['symbol'],
            content=data['content'],
            user_id=session['user_id'],
            username=session['username'],
            avatar=session.get('avatar', '👤')
        )
        db.session.add(comment)
        
        user = User.query.get(session['user_id'])
        user.total_comments += 1
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Asset comment error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/asset-comment/<int:comment_id>', methods=['DELETE', 'OPTIONS'])
def delete_asset_comment(comment_id):
    if request.method == 'OPTIONS':
        return '', 204
    if 'user_id' not in session:
        return jsonify({'error': 'Giriş yapmalısınız'}), 401
    
    try:
        comment = AssetComment.query.get(comment_id)
        if not comment or comment.user_id != session['user_id']:
            return jsonify({'error': 'Yetkiniz yok'}), 403
        
        user = User.query.
