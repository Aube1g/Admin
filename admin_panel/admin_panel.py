# Файл: admin_panel/admin_panel.py
import sqlite3, os, requests, logging
from flask import Flask, jsonify, Response

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN: raise ValueError("Необходимо установить переменную окружения BOT_TOKEN")

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Панель Администратора</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700&display=swap" rel="stylesheet"><script src="https://telegram.org/js/telegram-web-app.js"></script><script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script><style>:root{--bg-color:#1a1029;--primary-color:#2c1c46;--accent-color:#9c27b0;--text-color:#e0e0e0;--text-muted:#a0a0a0;--border-color:#4a3f5f;}*{box-sizing:border-box;margin:0;padding:0;}body{font-family:'Montserrat',sans-serif;background-color:var(--bg-color);color:var(--text-color);overscroll-behavior:none;-webkit-user-select:none;user-select:none;}#preloader{position:fixed;top:0;left:0;width:100%;height:100%;background-color:var(--bg-color);display:flex;justify-content:center;align-items:center;z-index:1000;transition:opacity .5s ease;}.spinner{width:60px;height:60px;border:5px solid var(--border-color);border-top-color:var(--accent-color);border-radius:50%;animation:spin 1s linear infinite;}@keyframes spin{to{transform:rotate(360deg);}}.app-container{padding:20px;opacity:0;}header{text-align:center;margin-bottom:30px;}header h1{font-size:1.8em;color:var(--accent-color);margin-bottom:20px;}nav{display:flex;justify-content:center;gap:10px;}nav button{background:transparent;border:1px solid var(--border-color);color:var(--text-muted);padding:10px 20px;border-radius:20px;cursor:pointer;font-family:'Montserrat',sans-serif;font-weight:500;transition:all .3s ease;}nav button:hover,nav button.active{background-color:var(--accent-color);color:#fff;border-color:var(--accent-color);box-shadow:0 0 15px rgba(156,39,176,.5);}#content{display:grid;gap:20px;}.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;}.stat-card{background-color:var(--primary-color);padding:25px;border-radius:15px;border:1px solid var(--border-color);text-align:center;}.stat-card h3{font-size:2.5em;color:var(--accent-color);}.stat-card p{color:var(--text-muted);font-size:.9em;}.data-card{background-color:var(--primary-color);padding:15px;border-radius:10px;border-left:4px solid var(--accent-color);}.data-card .header{display:flex;justify-content:space-between;align-items:center;font-size:.8em;color:var(--text-muted);margin-bottom:10px;flex-wrap:wrap;}.data-card .body p{margin-bottom:10px;}.data-card .body .message-text{font-style:italic;white-space:pre-wrap;word-break:break-word;}.data-card .media-trigger{background-color:var(--accent-color);color:#fff;border:none;padding:8px 12px;border-radius:5px;cursor:pointer;margin-top:10px;display:inline-block;}.modal{display:none;position:fixed;z-index:100;left:0;top:0;width:100%;height:100%;background-color:rgba(0,0,0,.8);justify-content:center;align-items:center;}.modal-content{max-width:90%;max-height:90%;}.modal-content audio,.modal-content img,.modal-content video{width:100%;height:auto;display:block;max-height:80vh;}.close-btn{position:absolute;top:20px;right:35px;color:#f1f1f1;font-size:40px;font-weight:700;cursor:pointer;}</style></head><body><div id="preloader"><div class="spinner"></div></div><div class="app-container"><header><h1>🟣 Aube1g | Admin Panel</h1><nav><button id="btn-dashboard" class="active">📊 Дашборд</button><button id="btn-messages">📨 Сообщения</button><button id="btn-users">👥 Пользователи</button></nav></header><main id="content"></main></div><div id="media-modal" class="modal"><span class="close-btn">&times;</span><div class="modal-content"></div></div>
<script>document.addEventListener("DOMContentLoaded",()=>{Telegram.WebApp.ready(),Telegram.WebApp.expand();const e=document.getElementById("preloader"),t=document.querySelector(".app-container"),n=document.getElementById("content"),o=document.querySelectorAll("nav button"),a=document.getElementById("media-modal"),d=a.querySelector(".modal-content"),s=a.querySelector(".close-btn");gsap.to(e,{opacity:0,duration:.5,delay:1,onComplete:()=>e.style.display="none"}),gsap.to(t,{opacity:1,duration:.8,delay:1.2}),o.forEach(e=>{e.addEventListener("click",()=>{o.forEach(e=>e.classList.remove("active")),e.classList.add("active"),c(e.id.replace("btn-",""))})});async function c(e){gsap.to(n,{opacity:0,duration:.3,onComplete:async()=>{if(n.innerHTML='<div class="spinner"></div>',gsap.set(n,{opacity:1}),"dashboard"===e)await async function(){const e=await fetch("/api/stats"),t=await e.json();n.innerHTML=`<div class="stats-grid"><div class="stat-card"><h3>${t.users_count}</h3><p>Пользователей</p></div><div class="stat-card"><h3>${t.messages_count}</h3><p>Всего сообщений</p></div><div class="stat-card"><h3>${t.links_count}</h3><p>Создано ссылок</p></div></div>`;}();if("messages"===e)await async function(){const e=await fetch("/api/messages"),t=await e.json();0===t.length?n.innerHTML="<p>Сообщений пока нет.</p>":n.innerHTML=t.map(e=>`<div class="data-card"><div class="header"><span>От: <b>${e.from_username||e.from_first_name}</b> -> Кому: <b>${e.to_username||e.to_first_name}</b></span><span>${new Date(e.created_at).toLocaleString()}</span></div><div class="body">${e.message_text?`<p class="message-text">"${e.message_text}"</p>`:""}${e.file_id?`<button class="media-trigger" data-fileid="${e.file_id}" data-type="${e.message_type}">Посмотреть ${e.message_type}</button>`:""}</div></div>`).join("");}();if("users"===e)await async function(){const e=await fetch("/api/users"),t=await e.json();n.innerHTML=t.map(e=>`<div class="data-card"><div class="header"><span>Пользователь: <b>${e.username||e.first_name}</b> (ID: ${e.user_id})</span><span>Регистрация: ${new Date(e.created_at).toLocaleDateString()}</span></div></div>`).join("");}();gsap.from("#content > *",{opacity:0,y:20,stagger:.05,duration:.4})}})}n.addEventListener("click",e=>{if(e.target.classList.contains("media-trigger")){const t=e.target.dataset.fileid,n=e.target.dataset.type,o=`/api/media/${t}`;let s="";s="photo"===n?`<img src="${o}" alt="Фото">`:"video"===n||"video_note"===n?`<video controls autoplay src="${o}"></video>`:"voice"===n||"audio"===n?`<audio controls autoplay src="${o}"></audio>`:`<p><a href="${o}" target="_blank">Скачать документ/файл</a></p>`,d.innerHTML=s,a.style.display="flex",gsap.from(a,{opacity:0,duration:.3})}}),s.addEventListener("click",()=>{gsap.to(a,{opacity:0,duration:.3,onComplete:()=>{a.style.display="none",d.innerHTML=""}})}),c("dashboard")});</script>
</body></html>"""

app = Flask(__name__)
def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'anon_bot.db')
    conn = sqlite3.connect(db_path, check_same_thread=False); conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index(): return HTML_TEMPLATE

@app.route('/api/stats')
def get_stats():
    conn = get_db_connection();
    stats = {
        'users_count': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'links_count': conn.execute('SELECT COUNT(*) FROM links').fetchone()[0],
        'messages_count': conn.execute('SELECT COUNT(*) FROM messages').fetchone()[0]
    }; conn.close()
    return jsonify(stats)

@app.route('/api/messages')
def get_messages():
    conn = get_db_connection()
    messages = conn.execute('SELECT m.*, uf.username as from_username, uf.first_name as from_first_name, ut.username as to_username, ut.first_name as to_first_name FROM messages m LEFT JOIN users uf ON m.from_user_id = uf.user_id LEFT JOIN users ut ON m.to_user_id = ut.user_id ORDER BY m.created_at DESC LIMIT 100').fetchall()
    conn.close()
    return jsonify([dict(row) for row in messages])

@app.route('/api/users')
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in users])

@app.route('/api/media/<file_id>')
def get_media(file_id):
    try:
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"); r.raise_for_status()
        file_path = r.json()['result']['file_path']
        file_r = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}", stream=True); file_r.raise_for_status()
        return Response(file_r.iter_content(chunk_size=1024), content_type=file_r.headers['Content-Type'])
    except Exception as e:
        logging.error(f"Media error for {file_id}: {e}"); return "File not found", 404

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000, debug=True)
