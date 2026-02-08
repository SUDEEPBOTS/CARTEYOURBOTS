from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
import requests
import os

app = Flask(__name__)
app.secret_key = "super_secret_pro_key"


# ================= CONFIG =================

DEV_MODE = True   # 👈 True = Login Skip | False = Real Login

MONGO_URL = os.getenv("MONGO_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

UPTIME_URL = "https://uptimebot-rvni.onrender.com/add"


# ================= DATABASE =================

client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
db = client["DeployerBot"]


# ================= FORCE JOIN CHECK =================

def check_join(user_id):

    if DEV_MODE:
        return True   # Dev Mode me skip

    if not BOT_TOKEN or not CHANNEL_ID:
        return True

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={user_id}"
        res = requests.get(url).json()

        status = res.get("result", {}).get("status")

        return status in ["member", "administrator", "creator"]

    except:
        return False


# ================= ROUTES =================


@app.route('/')
def index():

    # Dev Mode me auto login
    if DEV_MODE:
        session["user"] = {
            "user_id": 999999,
            "name": "Dev User",
            "username": "developer",
            "photo": "https://i.pravatar.cc/150"
        }

        return redirect("/dashboard")


    if 'user' in session:
        return redirect('/dashboard')

    return render_template('login.html')


# ================= TELEGRAM LOGIN =================


@app.route('/auth/telegram', methods=['POST'])
def telegram_auth():

    if DEV_MODE:
        return jsonify({"status": "success"})


    data = request.json
    user_id = data.get('id')


    # Force Join Check
    if not check_join(user_id):

        return jsonify({
            "status": "error",
            "message": "Join Channel First!",
            "redirect": f"https://t.me/{CHANNEL_ID.replace('@','')}"
        })


    user = {
        "user_id": user_id,
        "name": data.get('first_name'),
        "username": data.get('username'),
        "photo": data.get('photo_url')
    }


    # Save in DB
    db.users.update_one(
        {"user_id": user_id},
        {"$set": user},
        upsert=True
    )


    session['user'] = user

    return jsonify({"status": "success"})


# ================= DASHBOARD =================


@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/')


    # Real Time Join Check (Only if not Dev Mode)
    if not DEV_MODE:

        if not check_join(session['user']['user_id']):

            session.clear()
            return redirect('/')


    # Fetch Services
    services = list(db.services.find({}))


    if not services:

        services = [{
            "name": "Yukki Music Bot",
            "thumbnail": "https://te.legra.ph/file/7e56d987541747806140c.jpg",
            "desc": "Best High Quality Music Bot",
            "repo": "https://github.com/TeamYukki/YukkiMusicBot",
            "tutorial": []
        }]


    # Fetch My Bots
    my_bots = list(
        db.deployed_bots.find({
            "user_id": session['user']['user_id']
        })
    )


    return render_template(
        'dashboard.html',
        user=session['user'],
        services=services,
        my_bots=my_bots
    )



# ================= DEPLOY API =================


@app.route('/api/deploy', methods=['POST'])
def deploy_api():

    if 'user' not in session:

        return jsonify({
            "status": "error",
            "message": "Login First"
        })


    data = request.json


    bot_name = data.get("name", "Music Bot")


    # ⚠️ Yahan apna real deploy logic daalna


    # Demo URLs
    render_url = "https://dashboard.render.com"
    bot_live_url = "https://music-bot.onrender.com"



    # Save in DB
    db.deployed_bots.insert_one({

        "user_id": session['user']['user_id'],
        "name": bot_name,

        "dash_url": render_url,
        "app_url": bot_live_url,

        "status": "Active"
    })


    return jsonify({
        "status": "success",
        "message": "Bot Deployed"
    })



# ================= LOGOUT =================


@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')



# ================= RUN =================


if __name__ == '__main__':

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
