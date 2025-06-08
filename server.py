from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import datetime
import os
import sqlite3

app = Flask(__name__)

# تحميل مفتاح التشفير
key = open("secret.key", "rb").read()
fernet = Fernet(key)

# تهيئة قاعدة البيانات وإنشاء الجدول لو مش موجود
def init_db():
    conn = sqlite3.connect('codes.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS codes (
            encrypted_code TEXT PRIMARY KEY,
            device_id TEXT,
            start_date TEXT,
            duration_days INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return "Server is running", 200

@app.route('/add_code', methods=['POST'])
def add_code():
    data = request.json
    encrypted_code = data.get("encrypted_code")
    duration_days = data.get("duration_days")

    if not encrypted_code or not duration_days:
        return jsonify({"error": "البيانات ناقصة"}), 400

    conn = sqlite3.connect('codes.db')
    c = conn.cursor()
    c.execute('SELECT * FROM codes WHERE encrypted_code = ?', (encrypted_code,))
    if c.fetchone():
        conn.close()
        return jsonify({"error": "الكود موجود مسبقاً"}), 400

    c.execute('INSERT INTO codes (encrypted_code, device_id, start_date, duration_days) VALUES (?, ?, ?, ?)',
              (encrypted_code, None, None, duration_days))
    conn.commit()
    conn.close()

    return jsonify({"message": "تم إضافة الكود بنجاح"}), 200

@app.route('/verify', methods=['POST'])
def verify_code():
    data = request.json
    encrypted_code = data.get("encrypted_code")
    device_id = data.get("device_id")

    if not encrypted_code or not device_id:
        return jsonify({"error": "البيانات ناقصة"}), 400

    conn = sqlite3.connect('codes.db')
    c = conn.cursor()
    c.execute('SELECT device_id, start_date, duration_days FROM codes WHERE encrypted_code = ?', (encrypted_code,))
    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify({"status": "كود غير صالح"}), 400

    db_device_id, db_start_date, duration_days = row

    if db_device_id is None:
        # أول استخدام، نسجل الجهاز وتاريخ البداية
        start_date = datetime.datetime.now()
        c.execute('UPDATE codes SET device_id = ?, start_date = ? WHERE encrypted_code = ?',
                  (device_id, start_date.isoformat(), encrypted_code))
        conn.commit()
        conn.close()
        return jsonify({"status": "الكود صالح"}), 200

    if db_device_id != device_id:
        conn.close()
        return jsonify({"status": "الكود مربوط بجهاز آخر"}), 400

    start_date = datetime.datetime.fromisoformat(db_start_date)
    expiry_date = start_date + datetime.timedelta(days=duration_days)

    if datetime.datetime.now() > expiry_date:
        conn.close()
        return jsonify({"status": "الكود منتهي الصلاحية"}), 400

    conn.close()
    return jsonify({"status": "الكود صالح"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
