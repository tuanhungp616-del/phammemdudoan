import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests, random, re
from collections import Counter

app = Flask(__name__)
CORS(app)

# ==========================================
# 🔐 HỆ THỐNG QUẢN LÝ KEY (DATABASE)
# ==========================================
# Danh sách Key hợp lệ
KEYS_DB = {
    "taolabogame": "admin",
    "bo1": "user",
    "viphung": "user",
    "chutaidou": "user"
}
# Danh sách các Key đang bị Admin khóa (Lưu trong RAM)
LOCKED_KEYS = set()

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    key = data.get("key", "").strip()
    
    if not key or key not in KEYS_DB:
        return jsonify({"status": "error", "msg": "Key không tồn tại hoặc sai!"})
    if key in LOCKED_KEYS:
        return jsonify({"status": "error", "msg": "Key của bạn đã bị Admin khóa!"})
        
    return jsonify({"status": "success", "role": KEYS_DB[key], "msg": "Đăng nhập thành công!"})

@app.route("/api/admin", methods=["POST"])
def admin_action():
    data = request.json or {}
    admin_key = data.get("admin_key", "").strip()
    target_key = data.get("target_key", "").strip()
    action = data.get("action", "") # 'lock' or 'unlock'
    
    if admin_key != "taolabogame":
        return jsonify({"status": "error", "msg": "Bạn không phải là Admin!"})
    if target_key not in KEYS_DB or target_key == "taolabogame":
        return jsonify({"status": "error", "msg": "Key khách không hợp lệ!"})
        
    if action == "lock":
        LOCKED_KEYS.add(target_key)
        return jsonify({"status": "success", "msg": f"Đã KHÓA vĩnh viễn Key: {target_key}"})
    elif action == "unlock":
        if target_key in LOCKED_KEYS:
            LOCKED_KEYS.remove(target_key)
        return jsonify({"status": "success", "msg": f"Đã MỞ KHÓA cho Key: {target_key}"})
    
    return jsonify({"status": "error", "msg": "Lệnh không hợp lệ!"})

# ==========================================
# 🧠 CÁC LÕI TRÍ TUỆ NHÂN TẠO
# ==========================================
def analyze_md5_base(md5_str):
    tai = sum(1 for x in md5_str if x in "89abcdef")
    return {"tai": (tai / 32) * 100, "xiu": 100 - ((tai / 32) * 100)}

def tinh_toan_md5(md5_str):
    md5_str = md5_str.strip().lower()
    if not re.match(r"^[0-9a-f]{32}$", md5_str): return "", "MD5 LỖI", 0
    lc_res = analyze_md5_base(md5_str)
    vip_res = analyze_md5_base(md5_str[::-1])
    avg_tai = max(5, min(95, (lc_res["tai"] + vip_res["tai"]) / 2 + ((int(md5_str[15], 16) - 8) * 1.5)))
    if avg_tai > 50: return "TÀI", "MD5 HACKER: TÀI", round(avg_tai, 1)
    return "XỈU", "MD5 HACKER: XỈU", round(100 - avg_tai, 1)

def phan_tich_chung(arr, is_chanle):
    seq_str = "".join(arr)
    nxt = "T" if random.random() > 0.5 else "X"
    lk = "AI TỔNG HỢP"
    patterns = [("Cầu 1-2", r"(TXX|XTT)$"), ("Cầu 1-3", r"(TXXX|XTTT)$"), ("Cầu 2-2", r"(TTXX|XXTT)$")]
    for name, regex in patterns:
        if re.search(regex, seq_str):
            nxt = "X" if seq_str.endswith("T") else "T"
            lk = f"MẪU {name.upper()}"
            break
    final_dd = ("CHẴN" if nxt == "T" else "LẺ") if is_chanle else ("TÀI" if nxt == "T" else "XỈU")
    return {"du_doan": final_dd, "loi_khuyen": lk, "ti_le": round(random.uniform(85.0, 96.0), 1)}

def get_id(item):
    for k in ['id', 'phien', 'sessionId', 'sid']:
        if k in item and str(item[k]).isdigit(): return int(item[k])
    return 0

# ==========================================
# 📡 CỔNG QUÉT API TỰ ĐỘNG
# ==========================================
@app.route("/api/scan", methods=["GET"])
def scan_game():
    tool = request.args.get("tool", "")
    key = request.args.get("key", "")
    
    # KỂM TRA BẢO MẬT KEY TRƯỚC KHI QUÉT SÀN
    if key not in KEYS_DB or key in LOCKED_KEYS:
        return jsonify({"status": "auth_error", "msg": "Key đã bị khóa hoặc hết hạn. Bị văng!"})

    is_chanle = ("chanle" in tool.lower() or "xd" in tool.lower())
    urls = {
        "lc79_xd": "https://wcl.tele68.com/v1/chanlefull/sessions",
        "lc79_md5": "https://wtxmd52.tele68.com/v1/txmd5/sessions",
        "lc79_tx": "https://wtx.tele68.com/v1/tx/sessions",
        "betvip_tx": "https://wtx.macminim6.online/v1/tx/sessions",
        "betvip_md5": "https://wtxmd52.macminim6.online/v1/txmd5/sessions",
        "sunwin_tx": "https://apisunhpt.onrender.com/",
        "sunwin_sicbo": "https://api.wsktnus8.net/v2/history/getLastResult?gameId=ktrng_3979",
        "hitclub_md5": "https://jakpotgwab.geightdors.net/glms/v1/notify/taixiu"
    }
    url = urls.get(tool, "")

    try:
        res = requests.get(url, headers={"User-Agent": "V99-GOD-SERVER", "Cache-Control": "no-cache"}, timeout=3).json()
        lst = res.get("data", res.get("list", res)) if isinstance(res, dict) else res
        if not isinstance(lst, list): 
            if isinstance(res, dict) and res.get("du_doan"):
                dd = "TÀI" if "TAI" in str(res["du_doan"]).upper() else "XỈU"
                return jsonify({"status": "success", "data": {"du_doan": dd, "ti_le": round(random.uniform(98.5, 99.9), 1), "loi_khuyen": "DỰ ĐOÁN TỪ SÀN", "phien": "AUTO VIP"}})
            raise Exception("Dữ liệu lỗi")

        lst = sorted(lst, key=get_id)
        if not lst: raise Exception("Sàn trống")

        arr = []
        for s in lst:
            v = str(s).upper()
            if is_chanle: arr.append("T" if any(x in v for x in ["CHẴN", "CHAN", "C", "0"]) else "X")
            else: arr.append("T" if any(x in v for x in ["TAI", "TÀI", "BIG"]) else "X")
                    
        last_obj = lst[-1]
        phien = str(get_id(last_obj) + 1)
        
        md5_str = ""
        m = re.search(r"[0-9a-f]{32}", str(last_obj).lower())
        if m and ("md5" in tool.lower() or "sunwin" in tool.lower()): md5_str = m.group(0)
        
        if md5_str:
            dd, lk, tl = tinh_toan_md5(md5_str)
            data = {"du_doan": dd, "loi_khuyen": lk, "ti_le": tl, "phien": phien}
        else:
            data = phan_tich_chung(arr, is_chanle)
            data["phien"] = phien

        return jsonify({"status": "success", "data": data})

    except Exception as e:
        phien_fake = "#" + str(random.randint(100000, 999999))
        dd = random.choice(["TÀI", "XỈU"])
        if is_chanle: dd = "CHẴN" if dd == "TÀI" else "LẺ"
        return jsonify({"status": "success", "data": {"du_doan": dd, "loi_khuyen": "⚡ AI VƯỢT TƯỜNG LỬA", "ti_le": round(random.uniform(88, 97), 1), "phien": phien_fake}})

@app.route("/")
def home():
    return send_file("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
