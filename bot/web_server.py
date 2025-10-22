from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Discord Bot is running!"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "NS-CTG Discord Bot"}, 200

def run():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = Thread(target=run)
    t.start()
