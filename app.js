// Global variables
let lightweightChart = null;
let candlestickSeries = null;
let volumeSeries = null;
let currentSymbol = null;
let currentSymbolName = null;
let currentPeriod = 'daily';
let currentUser = null;
let selectedAvatar = '👤';
let currentPostId = null;
let uploadedProfileImage = null;
let isFullscreen = false;
let showVolume = true;

// API base URL - Railway otomatik olarak doğru portu kullanır
const API_BASE = window.location.origin;

// Utility function for API calls
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok && response.status !== 401 && response.status !== 404) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call error:', error);
        throw error;
    }
}

// Volume toggle
function toggleVolume() {
    showVolume = !showVolume;
    const btn = document.getElementById('volume-toggle');
    
    if (showVolume) {
        btn.innerText = '📊 Hacim: Açık';
        btn.style.background = 'rgba(59, 130, 246, 0.1)';
        btn.style.borderColor = 'rgba(59, 130, 246, 0.3)';
    } else {
        btn.innerText = '📊 Hacim: Kapalı';
        btn.style.background = 'rgba(100, 116, 139, 0.1)';
        btn.style.borderColor = 'rgba(100, 116, 139, 0.3)';
    }
    
    loadCandlestickChart(currentSymbol, currentPeriod);
}

// Fullscreen toggle
function toggleFullscreen() {
    const modalBox = document.getElementById('chart-modal-box');
    isFullscreen = !isFullscreen;
    
    if (isFullscreen) {
        modalBox.classList.add('fullscreen');
    } else {
        modalBox.classList.remove('fullscreen');
    }
    
    setTimeout(() => {
        if (lightweightChart) {
            const chartContainer = document.getElementById('candlestick-chart-container');
            const newHeight = isFullscreen ? window.innerHeight - 200 : 500;
            lightweightChart.applyOptions({
                width: chartContainer.clientWidth,
                height: newHeight
            });
            lightweightChart.timeScale().fitContent();
        }
    }, 100);
}

// Image upload handler
function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (file.size > 2 * 1024 * 1024) {
        alert('Fotoğraf boyutu 2MB\'dan küçük olmalı!');
        return;
    }
    
    if (!file.type.startsWith('image/')) {
        alert('Lütfen geçerli bir resim dosyası seçin!');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        uploadedProfileImage = e.target.result;
        document.getElementById('preview-img').src = uploadedProfileImage;
        document.getElementById('image-preview').style.display = 'block';
        
        document.querySelectorAll('.avatar-option').forEach(opt => {
            opt.classList.remove('selected');
        });
    };
    reader.readAsDataURL(file);
}

function removeProfileImage() {
    uploadedProfileImage = null;
    document.getElementById('image-preview').style.display = 'none';
    document.getElementById('profile-image-input').value = '';
}

// Star rating system
function createStarRating(itemId, itemType, currentAvg, ratingCount) {
    let stars = '';
    for(let i = 1; i <= 5; i++) {
        const filled = i <= Math.round(currentAvg) ? 'filled' : '';
        stars += `<span class="star ${filled}" onmouseover="previewRating(this, ${i})" onmouseout="resetRating(this)" onclick="submitRating('${itemType}', ${itemId}, ${i})" title="⭐ ${i} yıldız ver">★</span>`;
    }
    const avgText = currentAvg > 0 ? currentAvg.toFixed(1) : '0.0';
    const countText = ratingCount > 0 ? `<span class="rating-count" title="${ratingCount} kişi oy verdi">(${avgText} • ${ratingCount} oy)</span>` : '<span class="rating-count">(Henüz oy yok)</span>';
    return `<div class="star-rating" data-avg="${currentAvg}" data-count="${ratingCount}">${stars}${countText}</div>`;
}

function previewRating(star, rating) {
    const container = star.parentElement;
    const stars = container.querySelectorAll('.star');
    stars.forEach((s, idx) => {
        if(idx < rating) {
            s.classList.add('filled');
        } else {
            s.classList.remove('filled');
        }
    });
}

function resetRating(star) {
    const container = star.parentElement;
    const currentAvg = parseFloat(container.dataset.avg) || 0;
    const stars = container.querySelectorAll('.star');
    stars.forEach((s, idx) => {
        if(idx < Math.round(currentAvg)) {
            s.classList.add('filled');
        } else {
            s.classList.remove('filled');
        }
    });
}

async function submitRating(itemType, itemId, rating) {
    let endpoint = '';
    let payload = { rating: rating };
    
    if(itemType === 'post') {
        endpoint = '/api/rate-post';
        payload.post_id = itemId;
    } else if(itemType === 'post-comment') {
        endpoint = '/api/rate-post-comment';
        payload.comment_id = itemId;
    } else if(itemType === 'asset-comment') {
        endpoint = '/api/rate-asset-comment';
        payload.comment_id = itemId;
    }
    
    try {
        const data = await apiCall(endpoint, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        
        if(data.error) {
            alert(data.error);
        } else {
            if(itemType === 'post') {
                fetchFeed();
            } else if(itemType === 'post-comment') {
                loadPostComments(currentPostId);
            } else if(itemType === 'asset-comment') {
                loadComments(currentSymbol);
            }
        }
    } catch(err) {
        alert('Oy kullanılamadı!');
    }
}

// Auth functions
async function logout() {
    try {
        await apiCall('/api/logout', { method: 'POST' });
        location.reload();
    } catch(err) {
        alert('Çıkış yapılamadı!');
    }
}

function showSection(section) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.getElementById(section + '-section').classList.add('active');
    event.target.classList.add('active');
    
    if(section === 'profile') loadProfile();
    else if(section === 'feed') fetchFeed();
}

// Data fetching functions
async function fetchEconomicCalendar() {
    try {
        const data = await apiCall('/api/economic-calendar');
        let html = "";
        for(let key in data) {
            const item = data[key];
            html += `<div class="economic-card" style="border-color: ${item.color};">
                <div class="economic-icon">${item.icon}</div>
                <div class="economic-name">${item.name}</div>
                <div class="economic-value" style="color: ${item.color};">${item.current}</div>
                <div class="economic-date">📅 ${item.next_meeting || item.next_release}</div>
                <div class="economic-description">${item.description}</div>
            </div>`;
        }
        document.getElementById('economic-calendar').innerHTML = html;
    } catch(err) {
        console.error('Economic calendar error:', err);
        document.getElementById('economic-calendar').innerHTML = '<p style="text-align:center; color:#64748b;">Veri yüklenemedi</p>';
    }
}

async function fetchMarket() {
    try {
        const data = await apiCall('/api/market-data');
        let html = "";
        for(let key in data) {
            html += `<div class="card clickable" onclick="openAsset('${key}', '${data[key].name}')">
                <div class="card-logo">${data[key].logo}</div>
                <div class="card-name">${data[key].name}</div>
                <div class="price">${data[key].value}</div>
            </div>`;
        }
        document.getElementById('market-list').innerHTML = html;
    } catch(err) {
        console.error('Market error:', err);
        document.getElementById('market-list').innerHTML = '<p style="text-align:center; color:#64748b;">Veri yüklenemedi</p>';
    }
}

async function fetchFeed() {
    try {
        const data = await apiCall('/api/feed');
        let html = "";
        data.forEach(p => {
            const isOwner = currentUser && p.user === currentUser;
            const actionsHtml = isOwner ? `
                <div style="position: absolute; top: 10px; right: 10px; display: flex; gap: 5px;">
                    <button onclick="event.stopPropagation(); editPost(${p.id}, '${escapeHtml(p.content)}');" class="mini-btn" title="Düzenle">✏️</button>
                    <button onclick="event.stopPropagation(); deletePost(${p.id});" class="mini-btn delete-btn" title="Sil">🗑️</button>
                </div>
            ` : '';
            
            html += `<div class="post" onclick="openPostDetail(${p.id})">
                ${actionsHtml}
                <div class="post-header">
                    <div class="post-avatar">${p.avatar}</div>
                    <div style="flex:1;"><b style="color:var(--primary);">@${p.user}</b><div style="color:#64748b; font-size:12px;">${p.timestamp}</div></div>
                </div>
                <p style="margin:0; color:#cbd5e1;">${p.content}</p>
                <div class="post-stats">
                    <div>💬 ${p.comment_count} yorum</div>
                    <div onclick="event.stopPropagation();">${createStarRating(p.id, 'post', p.rating_avg, p.rating_count)}</div>
                </div>
            </div>`;
        });
        document.getElementById('global-feed').innerHTML = html || '<p style="text-align:center; color:#64748b;">Henüz gönderi yok. İlk sen ol! 🚀</p>';
    } catch(err) {
        console.error('Feed error:', err);
        document.getElementById('global-feed').innerHTML = '<p style="text-align:center; color:#64748b;">Veri yüklenemedi</p>';
    }
}

// Helper function to escape HTML
function escapeHtml(text) {
    return text.replace(/'/g, "\\'").replace(/"/g, '\\"');
}

async function loadProfile() {
    if(!currentUser) return;
    try {
        const data = await apiCall(`/api/profile/${currentUser}`);
        
        const avatarElement = document.getElementById('profile-avatar');
        if (data.profile_image) {
            avatarElement.innerHTML = `<img src="${data.profile_image}" alt="Profile">`;
        } else {
            avatarElement.innerHTML = data.avatar;
        }
        
        document.getElementById('profile-username').innerText = '@' + data.username;
        document.getElementById('profile-fullname').innerText = data.full_name;
        
        const bioElement = document.getElementById('profile-bio');
        if (data.bio && data.bio.trim()) {
            bioElement.innerText = data.bio;
            bioElement.style.display = 'block';
        } else {
            bioElement.style.display = 'none';
        }
        
        document.getElementById('profile-posts').innerText = data.total_posts;
        document.getElementById('profile-comments').innerText = data.total_comments;
        document.getElementById('profile-joined').innerText = data.joined_date.split('-')[0];
        
        let postsHtml = "";
        data.posts.forEach(p => {
            postsHtml += `<div class="post" onclick="openPostDetail(${p.id})">
                <div class="post-header">
                    <div class="post-avatar">${p.avatar}</div>
                    <div style="flex:1;"><b style="color:var(--primary);">@${data.username}</b><div style="color:#64748b; font-size:12px;">${p.timestamp}</div></div>
                </div>
                <p style="margin:0; color:#cbd5e1;">${p.content}</p>
                <div class="post-stats">
                    <div>💬 ${p.comment_count} yorum</div>
                    <div onclick="event.stopPropagation();">${createStarRating(p.id, 'post', p.rating_avg || 0, p.rating_count || 0)}</div>
                </div>
            </div>`;
        });
        document.getElementById('profile-posts-list').innerHTML = postsHtml || '<p style="text-align:center; color:#64748b;">Henüz gönderi yok.</p>';
    } catch(err) {
        console.error('Profile error:', err);
    }
}

// Post functions
async function openPostDetail(postId) {
    currentPostId = postId;
    try {
        const data = await apiCall('/api/feed');
        const post = data.find(p => p.id === postId);
        if(!post) return;
        
        document.getElementById('post-detail-content').innerHTML = `
            <div class="post" style="cursor:default;">
                <div class="post-header">
                    <div class="post-avatar">${post.avatar}</div>
                    <div style="flex:1;"><b style="color:var(--primary);">@${post.user}</b><div style="color:#64748b; font-size:12px;">${post.timestamp}</div></div>
                </div>
                <p style="margin:0; color:#cbd5e1; font-size:16px;">${post.content}</p>
                <div class="post-stats">
                    <div>💬 ${post.comment_count} yorum</div>
                    <div>${createStarRating(post.id, 'post', post.rating_avg, post.rating_count)}</div>
                </div>
            </div>
        `;
        document.getElementById('post-modal').style.display = 'flex';
        loadPostComments(postId);
    } catch(err) {
        console.error('Post detail error:', err);
    }
}

async function loadPostComments(postId) {
    try {
        const data = await apiCall(`/api/post-comments/${postId}`);
        let html = "";
        data.forEach(c => {
            const isOwner = currentUser && c.username === currentUser;
            const deleteBtn = isOwner ? `<button onclick="deletePostComment(${c.id})" class="mini-btn delete-btn" style="margin-left: auto;" title="Sil">🗑️</button>` : '';
            
            html += `<div class="comment">
                <div class="comment-avatar">${c.avatar}</div>
                <div style="flex:1;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <div style="display:flex; gap:10px; align-items:center; flex:1;">
                            <b style="color:var(--primary);">@${c.username}</b>
                            <span style="color:#64748b; font-size:11px;">${c.timestamp}</span>
                        </div>
                        ${deleteBtn}
                    </div>
                    <p style="margin:0; color:#cbd5e1; font-size:14px;">${c.content}</p>
                    <div style="margin-top:8px;">${createStarRating(c.id, 'post-comment', c.rating_avg, c.rating_count)}</div>
                </div>
            </div>`;
        });
        document.getElementById('post-comments-list').innerHTML = html || '<p style="text-align:center; color:#64748b;">Henüz yorum yok. İlk yorumu sen yap! 💬</p>';
    } catch(err) {
        console.error('Comments error:', err);
    }
}

async function submitPostComment() {
    const content = document.getElementById('post-comment-input').value;
    if(!content.trim()) {
        alert('Lütfen bir yorum yazın!');
        return;
    }
    
    try {
        const data = await apiCall('/api/post-comment', {
            method: 'POST',
            body: JSON.stringify({post_id: currentPostId, content: content})
        });
        
        if(data.error) {
            alert(data.error);
        } else {
            document.getElementById('post-comment-input').value = '';
            loadPostComments(currentPostId);
            fetchFeed();
        }
    } catch(err) {
        alert('Yorum paylaşılamadı!');
    }
}

function closePostModal() {
    document.getElementById('post-modal').style.display = 'none';
}

// Asset functions
function openAsset(symbol, name) {
    currentSymbol = symbol;
    currentSymbolName = name;
    document.getElementById('asset-modal').style.display = 'flex';
    document.getElementById('modal-title').innerText = name + ' - Mum Grafiği';
    loadCandlestickChart(symbol, 'daily');
    loadComments(symbol);
}

function changePeriod(period) {
    currentPeriod = period;
    document.querySelectorAll('.period-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    loadCandlestickChart(currentSymbol, period);
}

async function loadCandlestickChart(symbol, period) {
    try {
        const data = await apiCall(`/api/candlestick/${symbol}?period=${period}`);
        
        if(data.error) {
            alert('Veri yüklenemedi');
            return;
        }
        
        const container = document.getElementById('candlestick-chart-container');
        
        if (lightweightChart) {
            lightweightChart.remove();
        }
        
        lightweightChart = LightweightCharts.createChart(container, {
            width: container.clientWidth,
            height: 500,
            layout: {
                background: { color: '#1c2128' },
                textColor: '#8b98a5',
            },
            grid: {
                vertLines: { color: '#30363d' },
                horzLines: { color: '#30363d' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#30363d',
            },
            timeScale: {
                borderColor: '#30363d',
                timeVisible: true,
            },
        });
        
        candlestickSeries = lightweightChart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderUpColor: '#10b981',
            borderDownColor: '#ef4444',
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        });
        
        const chartData = data.data.map(d => ({
            time: d.time,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close
        }));
        
        candlestickSeries.setData(chartData);
        
        if (showVolume && data.data[0].volume > 0) {
            volumeSeries = lightweightChart.addHistogramSeries({
                color: 'rgba(59, 130, 246, 0.3)',
                priceFormat: { type: 'volume' },
                priceScaleId: '',
            });
            
            const volumeData = data.data.map(d => ({
                time: d.time,
                value: d.volume,
                color: d.close >= d.open ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'
            }));
            
            volumeSeries.setData(volumeData);
        }
        
        lightweightChart.timeScale().fitContent();
    } catch(err) {
        console.error('Chart error:', err);
        alert('Grafik yüklenemedi!');
    }
}

async function loadComments(symbol) {
    try {
        const data = await apiCall(`/api/asset-comments/${symbol}`);
        let html = "";
        data.forEach(c => {
            const isOwner = currentUser && c.username === currentUser;
            const deleteBtn = isOwner ? `<button onclick="deleteAssetComment(${c.id})" class="mini-btn delete-btn" style="margin-left: auto;" title="Sil">🗑️</button>` : '';
            
            html += `<div class="comment">
                <div class="comment-avatar">${c.avatar}</div>
                <div style="flex:1;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <div style="display:flex; gap:10px; align-items:center; flex:1;">
                            <b style="color:var(--primary);">@${c.username}</b>
                            <span style="color:#64748b; font-size:11px;">${c.timestamp}</span>
                        </div>
                        ${deleteBtn}
                    </div>
                    <p style="margin:0; color:#cbd5e1; font-size:14px;">${c.content}</p>
                    <div style="margin-top:8px;">${createStarRating(c.id, 'asset-comment', c.rating_avg, c.rating_count)}</div>
                </div>
            </div>`;
        });
        document.getElementById('comments-list').innerHTML = html || '<p style="text-align:center; color:#64748b;">Henüz yorum yok 💬</p>';
    } catch(err) {
        console.error('Comments error:', err);
    }
}

async function submitComment() {
    const content = document.getElementById('comment-input').value;
    if(!content.trim()) {
        alert('Lütfen bir yorum yazın!');
        return;
    }
    
    try {
        await apiCall('/api/asset-comment', {
            method: 'POST',
            body: JSON.stringify({symbol: currentSymbol, content: content})
        });
        
        document.getElementById('comment-input').value = '';
        loadComments(currentSymbol);
    } catch(err) {
        alert('Yorum paylaşılamadı!');
    }
}

function closeAssetModal() {
    document.getElementById('asset-modal').style.display = 'none';
    const modalBox = document.getElementById('chart-modal-box');
    modalBox.classList.remove('fullscreen');
    isFullscreen = false;
}

// Profile functions
function openProfileEdit() {
    document.getElementById('profile-edit-modal').style.display = 'flex';
    document.getElementById('edit-bio').value = document.getElementById('profile-bio').innerText;
    
    uploadedProfileImage = null;
    document.getElementById('image-preview').style.display = 'none';
    document.getElementById('profile-image-input').value = '';
    
    const currentAvatar = document.getElementById('profile-avatar').innerText;
    selectedAvatar = currentAvatar;
    
    apiCall(`/api/profile/${currentUser}`)
        .then(data => {
            if (data.profile_image) {
                uploadedProfileImage = data.profile_image;
                document.getElementById('preview-img').src = data.profile_image;
                document.getElementById('image-preview').style.display = 'block';
            }
        });
    
    setTimeout(() => {
        document.querySelectorAll('.avatar-option').forEach(opt => {
            opt.classList.remove('selected');
            if(opt.innerText === currentAvatar) {
                opt.classList.add('selected');
            }
        });
    }, 100);
}

function closeProfileEdit() {
    document.getElementById('profile-edit-modal').style.display = 'none';
}

function selectAvatar(emoji) {
    selectedAvatar = emoji;
    document.querySelectorAll('.avatar-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    event.target.classList.add('selected');
}

async function saveProfile() {
    const payload = {
        bio: document.getElementById('edit-bio').value
    };
    
    if (uploadedProfileImage) {
        payload.profile_image = uploadedProfileImage;
        payload.avatar = '';
    } else if (selectedAvatar) {
        payload.avatar = selectedAvatar;
        payload.remove_image = true;
    }
    
    try {
        const data = await apiCall('/api/profile/update', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        
        if(data.error) {
            alert(data.error);
        } else {
            closeProfileEdit();
            loadProfile();
            if (uploadedProfileImage) {
                document.getElementById('user-avatar').innerHTML = `<img src="${uploadedProfileImage}" style="width:24px; height:24px; border-radius:50%; object-fit:cover;">`;
            } else {
                document.getElementById('user-avatar').innerText = selectedAvatar;
            }
        }
    } catch(err) {
        alert('Profil güncellenemedi!');
    }
}

// Auth modal functions
function closeAuthModal() {
    document.getElementById('auth-modal').style.display = 'none';
}

function openAuth(mode) {
    document.getElementById('auth-modal').style.display = 'flex';
    document.getElementById('reg-fields').style.display = mode === 'reg' ? 'block' : 'none';
    document.getElementById('auth-title').innerText = mode === 'reg' ? '🎯 Yeni Hesap' : '🔐 Giriş Yap';
    document.getElementById('af-btn').innerText = mode === 'reg' ? 'Kaydol' : 'Giriş Yap';
    document.getElementById('af-btn').onclick = async () => {
        const payload = {
            full_name: document.getElementById('af-fn').value,
            username: document.getElementById('af-un').value,
            password: document.getElementById('af-ps').value
        };
        
        try {
            const data = await apiCall('/api/' + (mode === 'reg' ? 'register' : 'login'), {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            
            if(data.error) {
                alert('❌ ' + data.error);
            } else {
                location.reload();
            }
        } catch(err) {
            alert('Bağlantı hatası!');
        }
    };
}

async function submitPost() {
    const content = document.getElementById('post-input').value;
    if(!content.trim()) {
        alert('Lütfen bir içerik yazın!');
        return;
    }
    
    try {
        const data = await apiCall('/api/post', {
            method: 'POST',
            body: JSON.stringify({content: content})
        });
        
        if(data.error) {
            alert(data.error);
        } else {
            document.getElementById('post-input').value = '';
            fetchFeed();
        }
    } catch(err) {
        alert('Gönderi paylaşılamadı!');
    }
}

async function deletePost(postId) {
    if(!confirm('Bu gönderiyi silmek istediğinize emin misiniz?')) return;
    
    try {
        const data = await apiCall(`/api/post/${postId}`, {
            method: 'DELETE'
        });
        
        if(data.error) {
            alert(data.error);
        } else {
            fetchFeed();
            loadProfile();
        }
    } catch(err) {
        alert('Gönderi silinemedi!');
    }
}

async function editPost(postId, currentContent) {
    const newContent = prompt('Gönderiyi düzenle:', currentContent);
    if(!newContent || !newContent.trim()) return;
    
    try {
        const data = await apiCall(`/api/post/${postId}`, {
            method: 'PUT',
            body: JSON.stringify({content: newContent})
        });
        
        if(data.error) {
            alert(data.error);
        } else {
            fetchFeed();
            loadProfile();
        }
    } catch(err) {
        alert('Gönderi düzenlenemedi!');
    }
}

async function deletePostComment(commentId) {
    if(!confirm('Bu yorumu silmek istediğinize emin misiniz?')) return;
    
    try {
        const data = await apiCall(`/api/post-comment/${commentId}`, {
            method: 'DELETE'
        });
        
        if(data.error) {
            alert(data.error);
        } else {
            loadPostComments(currentPostId);
            fetchFeed();
        }
    } catch(err) {
        alert('Yorum silinemedi!');
    }
}

async function deleteAssetComment(commentI<function_calls>
<invoke name="artifacts">
<parameter name="command">update</parameter>
<parameter name="id">railway_javascript</parameter>
<parameter name="old_str">async function deleteAssetComment(commentI</parameter>
<parameter name="new_str">async function deleteAssetComment(commentId) {
if(!confirm('Bu yorumu silmek istediğinize emin misiniz?')) return;
try {
    const data = await apiCall(`/api/asset-comment/${commentId}`, {
        method: 'DELETE'
    });
    
    if(data.error) {
        alert(data.error);
    } else {
        loadComments(currentSymbol);
    }
} catch(err) {
    alert('Yorum silinemedi!');
}
}
// Initialize app
async function initApp() {
try {
const sessionData = await apiCall('/api/check-session');
    if(sessionData.logged_in) {
        currentUser = sessionData.username;
        document.getElementById('auth-ui').style.display = 'none';
        document.getElementById('user-ui').style.display = 'block';
        document.getElementById('nav-links').style.display = 'flex';
        document.getElementById('post-box').style.display = 'block';
        document.getElementById('comment-box').style.display = 'block';
        document.getElementById('post-comment-box').style.display = 'block';
        document.getElementById('user-name').innerText = '@' + sessionData.username;
        document.getElementById('user-avatar').innerText = sessionData.avatar;
    }
} catch(err) {
    console.error('Session check error:', err);
}

fetchEconomicCalendar();
fetchMarket();
fetchFeed();

// Auto-refresh intervals
setInterval(fetchEconomicCalendar, 3600000); // 1 hour
setInterval(fetchMarket, 30000); // 30 seconds
setInterval(fetchFeed, 60000); // 1 minute
}
// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
if (e.key === 'Escape') {
const assetModal = document.getElementById('asset-modal');
const postModal = document.getElementById('post-modal');
if (assetModal.style.display === 'flex') {
closeAssetModal();
} else if (postModal.style.display === 'flex') {
closePostModal();
}
}
if (e.key === 'f' || e.key === 'F') {
    const assetModal = document.getElementById('asset-modal');
    if (assetModal.style.display === 'flex') {
        e.preventDefault();
        toggleFullscreen();
    }
}
});
// Start app when DOM is ready
if (document.readyState === 'loading') {
document.addEventListener('DOMContentLoaded', initApp);
} else {
initApp();
}</parameter>
