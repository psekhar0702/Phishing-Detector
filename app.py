from flask import Flask, render_template, request
import pickle
import re
from urllib.parse import urlparse
import pandas as pd
import scipy.sparse as sp
import os


app = Flask(__name__, static_folder='static')


try:
    with open("model.pkl", "rb") as f:
        model = pickle.load(f)
    with open("vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    print("Model and vectorizer loaded successfully.")
except FileNotFoundError:
    print("Error: model.pkl or vectorizer.pkl not found. Please run train_model.py first.")
    exit()

def is_valid_url(url):
    """Check if URL is valid."""
    regex = r"^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$"
    return re.match(regex, url) is not None

def extract_features(url):
    """
    Extracts manual features from a given URL.
    This function must be identical to the one used in train_model.py.
    """
    parsed = urlparse(url)
    return {
        "url_length": len(url),
        "num_dots": url.count('.'),
        "num_hyphens": url.count('-'),
        "has_https": int(parsed.scheme == 'https')
    }

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/predict', methods=['POST'])
def predict():
    url = request.form['url'].strip()

    if not url:
        return render_template("index.html", error="⚠️ Please enter a URL.")

    if not is_valid_url(url):
        return render_template("index.html", error="⚠️ Invalid URL format. Ensure it's a complete URL (e.g., https://example.com).")

    try:
        url_text_vec = vectorizer.transform([url])
        features = extract_features(url)
        features_df = pd.DataFrame([features])
        X_final = sp.hstack([url_text_vec, features_df], format='csr')

        proba = model.predict_proba(X_final)[0]
        phishing_prob = round(proba[1] * 100, 2)
        safe_prob = round(proba[0] * 100, 2)

        if phishing_prob >= 50:
            label = "Phishing Website"
            display_emoji_class = "phishing-text"
        else:
            label = "Legitimate Website"
            display_emoji_class = "safe-text"

        return render_template(
            "index.html",
            url=url,
            prediction=label,
            phishing_score=phishing_prob,
            safe_score=safe_prob,
            display_emoji_class=display_emoji_class
        )

    except Exception as e:
        print(f"Prediction error: {e}")
        return render_template("index.html", error=f"⚠️ An internal error occurred. Please try again or check server logs.")



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
