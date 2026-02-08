from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
import requests
import os
import secrets
import time

app = Flask(__name__)
app.secret_key = "super_secret_pro_key"

# --- CONFIG ---
MONGO_URL = os.getenv("MONGO_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Apne Bot ka Token daal (Force Join check karne ke liye)
CHANNEL_ID = os.getenv("CHANNEL_ID") # e.g. "@SudeepBots" (Admin hona chahiye bot wahan)
UPTIME_URL = "https://uptimebot-rvni.onrender.com/add"

# Fixed Credentials (Backup)
FIXED_API_KEY = "rnd_NTH8vbRYrb6wSPjI9EWW8iP1z3cV"
FIXED_OWNER_ID = "tea-d5kdaj3e5dus73a6s9e0"

client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
db = client["DeployerBot"]

# --- HELPER: CHECK FORCE JOIN ---
def check_join(user_id):
    if not BOT_TOKEN or not CHANNEL_ID: return True # Agar config nahi hai to jane do
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={user_id}"
        res = requests.get(url).json()
        status = res.get("result", {}).get("status")
        return status in ["member", "administrator", "creator"]
    except:
        return False

# --- ROUTES ---

@app.route('/')
def index():
    if 'user' in session: return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/auth/telegram', methods=['POST'])
def telegram_auth():
    data = request.json
    user_id = data.get('id')
    
    # 1. Force Join Check
    if not check_join(user_id):
        return jsonify({"status": "error", "message": "Join Channel First!", "redirect": f"https://t.me/{CHANNEL_ID.replace('@','')}"})

    # 2. Save User
    user = {
        "user_id": user_id,
        "name": data.get('first_name'),
        "username": data.get('username'),
        "photo": data.get('photo_url')
    }
    db.users.update_one({"user_id": user_id}, {"$set": user}, upsert=True)
    session['user'] = user
    return jsonify({"status": "success"})

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('index'))
    
    # Real-time Check (Har baar dashboard kholne par check karega)
    if not check_join(session['user']['user_id']):
        session.pop('user', None) # Logout kar do agar leave kiya
        return redirect(url_for('index'))

    # Services Fetch Karo
    services = list(db.services.find({}))
    if not services:
        # Default Service agar DB khali hai
        services = [{
            "name": "Yukki Music Bot",
            "thumbnail": "https://te.legra.ph/file/7e56d987541747806140c.jpg",
            "desc": "Best High Quality Music Bot",
            "repo": "https://github.com/TeamYukki/YukkiMusicBot",
            "tutorial": []
        }]

    my_bots = list(db.deployed_bots.find({"user_id": session['user']['user_id']}))
    return render_template('dashboard.html', user=session['user'], services=services, my_bots=my_bots)

@app.route('/api/deploy', methods=['POST'])
def deploy_api():
    if 'user' not in session: return jsonify({"status": "error", "message": "Login First"})
    
    # ... (Tera Wahi Purana Deploy Code Same Rahega) ...
    # BAS END ME YE ADD KARNA HAI (DB ME SAVE KARNE KE LIYE):
    
    # Example Logic (Replace with actual render logic):
    # render_url = "https://dashboard.render.com..."
    # bot_live_url = "https://music-bot.onrender.com"
    
    # if success:
    #     db.deployed_bots.insert_one({
    #         "user_id": session['user']['user_id'],
    #         "name": "Music Bot",
    #         "dash_url": render_url,
    #         "app_url": bot_live_url,
    #         "status": "Active"
    #     })
    
    # Filhal purana wala code use kar, bas DB save logic add kar lena
    return jsonify({"status": "error", "message": "Paste your full deploy logic here"})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
    
