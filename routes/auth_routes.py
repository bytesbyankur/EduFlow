from flask import Blueprint, jsonify
from utils.auth import generate_token
from camera_service import capture_teacher_face

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/teacher/login_face", methods=["POST"])
def teacher_login_face():
    teacher_id = capture_teacher_face()

    if not teacher_id:
        return jsonify({"error": "Face not recognized"}), 401

    token = generate_token({"teacher_id": teacher_id})

    return jsonify({
        "token": token,
        "teacher_id": teacher_id
    }), 200
