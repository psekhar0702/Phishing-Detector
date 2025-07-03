import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle
from urllib.parse import urlparse
import scipy.sparse as sp

data = pd.read_csv("phishing_site_urls.csv")
data = data.sample(frac=1, random_state=42).reset_index(drop=True)

def extract_features(url):
    parsed = urlparse(url)
    return {
        "url_length": len(url),
        "num_dots": url.count('.'),
        "num_hyphens": url.count('-'),
        "has_https": int(parsed.scheme == 'https')
    }

X_features = data["URL"].apply(lambda x: pd.Series(extract_features(x)))
X_text = data["URL"]
y = data["Label"]

vectorizer = TfidfVectorizer(max_features=5000)
X_text_vec = vectorizer.fit_transform(X_text)
X_final = sp.hstack([X_text_vec, X_features], format='csr')

X_train, X_test, y_train, y_test = train_test_split(X_final, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
print(f"✅ Model trained & saved! Accuracy: {accuracy:.4f}")

with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)
