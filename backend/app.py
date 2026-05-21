from flask import Flask, request, jsonify
from database import get_user, create_user, deduct_points, get_points, save_leave
from pdf_generator import generate_document

app = Flask(__name__)
API_SECRET_KEY = "MySecretKey2024"

@app.route("/create-leave", methods=["POST"])
def create_leave():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token != API_SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    telegram_id = data.get("telegram_id")
    
    if not telegram_id:
        return jsonify({"error": "telegram_id required"}), 400
    
    user = get_user(telegram_id)
    if not user:
        user = create_user(telegram_id, data.get("full_name", f"User_{telegram_id}"))
    
    if not user:
        return jsonify({"error": "Failed to create user"}), 500
    
    if user["points"] < 1:
        return jsonify({"error": f"Insufficient points. You have {user['points']} points"}), 400
    
    try:
        doc_path = generate_document(data)
    except Exception as e:
        return jsonify({"error": f"Document generation failed: {str(e)}"}), 500
    
    save_leave(user["id"], data, doc_path)
    deduct_points(telegram_id)
    
    return jsonify({
        "success": True,
        "document_path": doc_path,
        "remaining_points": user["points"] - 1,
        "national_id": data.get("national_id")
    }), 200

@app.route("/points/<int:telegram_id>", methods=["GET"])
def get_user_points(telegram_id):
    points = get_points(telegram_id)
    return jsonify({"telegram_id": telegram_id, "points": points})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    print("🚀 Backend running on http://localhost:5000")
    app.run(debug=True, port=5000)