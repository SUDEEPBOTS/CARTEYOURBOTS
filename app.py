from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from pymongo import MongoClient
import os
import time

app = Flask(__name__)
app.secret_key = "super_secret_pro_key"

# --- CONFIG ---
MONGO_URL = os.getenv("MONGO_URL")
# Database Connect
client = MongoClient(MONGO_URL)
db = client["DeployerBot"]

# --- ADMIN ROUTES (New) ---

@app.route('/admin/update_service', methods=['POST'])
def admin_update_service():
    if 'is_admin' not in session: return jsonify({"status": "error", "message": "Unauthorized"})
    
    data = request.json
    service_name = "Yukki Music Bot" # Filhal hardcoded hai, baad me dynamic kar sakte ho
    
    # Data prepare karo
    update_data = {
        "name": service_name,
        "thumbnail": data.get('thumbnail'), # Thumbnail URL
        "description": data.get('description'),
        "repo_url": data.get('repo_url'),
        "tutorial": data.get('tutorial') # Ye poora List hoga Steps ka
    }
    
    # DB me save karo (Upsert: Agar nahi hai to naya banao)
    db.services.update_one({"name": service_name}, {"$set": update_data}, upsert=True)
    
    return jsonify({"status": "success", "message": "Service Updated!"})

# --- DASHBOARD ROUTE (Updated) ---

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('index'))
    
    # DB se Services uthao
    # Agar DB khali hai to default Music Bot dikhao
    music_bot = db.services.find_one({"name": "Yukki Music Bot"})
    
    if not music_bot:
        # Default Data (Agar Admin ne kuch set nahi kiya)
        music_bot = {
            "name": "Yukki Music Bot",
            "thumbnail": "https://te.legra.ph/file/7e56d987541747806140c.jpg", # Default Image
            "description": "High quality music bot with dashboard support.",
            "tutorial": []
        }
        
    services = [music_bot] # List bana di
    my_bots = list(db.deployed_bots.find({"user_id": session['user']['user_id']}))
    
    return render_template('dashboard.html', user=session['user'], services=services, my_bots=my_bots)

# ... (Baaki saare routes same rahenge: Login, Deploy, etc.) ...

if __name__ == '__main__':
    app.run(debug=True)
