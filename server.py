from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import datetime
import os

app = Flask(__name__)

# تحميل مفتاح التشفير
key = open("secret.key", "rb").read()
fernet = Fernet(key)

# قاعدة بيانات مؤقتة (ممكن تستبدلها بقاعدة بيانات حقيقية لاحقاً)
codes_db = {
    # مثال: "ENCRYPTED_CODE": {"device_id": None, "start_date": None, "duration_days": 30}
}

@app.route('/add_code', methods=['POST'])
def add_code():
    data = request.json
    encrypted_code = data.get("encrypted_code")
    duration_days = data.get("duration_days")

    if not encrypted_code or not duration_days:
        return jsonify({"error": "البيانات ناقصة"}), 400

    if encrypted_code in codes_db:
        return jsonify({"error": "الكود موجود مسبقاً"}), 400

    codes_db[encrypted_code] = {"device_id": None, "start_date": None, "duration_days": duration_days}
    return jsonify({"message": "تم إضافة الكود بنجاح"}), 200

@app.route('/verify', methods=['POST'])
def verify_code():
    data = request.json
    encrypted_code = data.get("encrypted_code")
    device_id = data.get("device_id")

    if not encrypted_code or not device_id:
        return jsonify({"error": "البيانات ناقصة"}), 400

    code_info = codes_db.get(encrypted_code)
    if not code_info:
        return jsonify({"status": "كود غير صالح"}), 400

    if code_info["device_id"] is None:
        # أول استخدام، نسجل الجهاز وتاريخ البداية
        code_info["device_id"] = device_id
        code_info["start_date"] = datetime.datetime.now()

    elif code_info["device_id"] != device_id:
        return jsonify({"status": "الكود مربوط بجهاز آخر"}), 400

    start_date = code_info["start_date"]
    duration = code_info["duration_days"]
    expiry_date = start_date + datetime.timedelta(days=duration)

    if datetime.datetime.now() > expiry_date:
        return jsonify({"status": "الكود منتهي الصلاحية"}), 400

    return jsonify({"status": "الكود صالح"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
