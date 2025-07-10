from flask import Flask, render_template, request, redirect, session, url_for
import os
import pickle
import re
import json
from urllib.parse import urlparse
import pandas as pd
import scipy.sparse as sp
from datetime import datetime
import pytz  

app = Flask(__name__, static_folder='static')
app.secret_key = "your_super_secret_key"

USERS_FILE = 'users.json'
HISTORY_FILE = 'history.json'

try:
    with open("model.pkl", "rb") as f:
        model = pickle.load(f)
    with open("vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    print("Model and vectorizer loaded successfully.")
except FileNotFoundError:
    print("Error: model.pkl or vectorizer.pkl not found.")
    exit()

for file in [USERS_FILE, HISTORY_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump({}, f)


def is_valid_url(url):
    regex = r"^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$"
    return re.match(regex, url) is not None

def extract_features(url):
    parsed = urlparse(url)
    return {
        "url_length": len(url),
        "num_dots": url.count('.'),
        "num_hyphens": url.count('-'),
        "has_https": int(parsed.scheme == 'https')
    }

@app.route('/')
def home():
    if 'email' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/phishing', methods=['GET', 'POST'])
def phishing():
    if 'email' not in session:
        return redirect('/login')

    prediction = None
    phishing_prob = legitimate_prob = 0

    if request.method == 'POST':
        url = request.form['url'].strip()

        if not url:
            return render_template("index.html", error="⚠️ Please enter a URL.")
        if not is_valid_url(url):
            return render_template("index.html", error="⚠️ Invalid URL format.")

        try:
            vec = vectorizer.transform([url])
            features = extract_features(url)
            features_df = pd.DataFrame([features])
            X_final = sp.hstack([vec, features_df], format='csr')

            proba = model.predict_proba(X_final)[0]
            phishing_prob = round(proba[1] * 100, 2)
            legitimate_prob = round(proba[0] * 100, 2)

            prediction = "Phishing Website" if phishing_prob > 50 else "Legitimate Website"

        
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            timestamp = now.strftime("%I:%M %p")  
            date = now.strftime("%d-%m-%Y")       

            with open(HISTORY_FILE, 'r+') as f:
                data = json.load(f)
                user_history = data.get(session['email'], [])
                user_history.insert(0, {
                    "url": url,
                    "prediction": prediction,
                    "time": timestamp,
                    "date": date
                })
                data[session['email']] = user_history[:10]
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()

        except Exception as e:
            print(f"Prediction error: {e}")
            return render_template("index.html", error="⚠️ Internal error occurred.")

    return render_template("index.html", prediction=prediction,
                           phishing_prob=phishing_prob,
                           legitimate_prob=legitimate_prob)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        with open(USERS_FILE, 'r+') as f:
            users = json.load(f)
            if email in users:
                return render_template("register.html", error="⚠️ Email already registered.")
            users[email] = {'name': name, 'password': password}
            f.seek(0)
            json.dump(users, f)
            f.truncate()

        return redirect('/login')
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            user = users.get(email)
            if user and user['password'] == password:
                session['username'] = user['name']
                session['email'] = email
                return redirect('/dashboard')

            return render_template("login.html", error="⚠️ Invalid credentials.")
    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')
    return render_template("dashboard.html", name=session['username'])

@app.route('/history')
def history():
    if 'email' not in session:
        return redirect('/login')

    with open(HISTORY_FILE, 'r') as f:
        data = json.load(f)
        history = data.get(session['email'], [])
    return render_template("history.html", history=history)

@app.route('/clear-history', methods=['POST'])
def clear_history():
    if 'email' in session:
        with open(HISTORY_FILE, 'r+') as f:
            data = json.load(f)
            data[session['email']] = []
            f.seek(0)
            json.dump(data, f)
            f.truncate()
    return redirect('/history')

@app.route('/safety-tips')
def safety_tips():
    return render_template("safety_tips.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
