"""Flask API for fall detection inference."""

import os
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from logic.detector import detect_fall, get_video_metadata

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "mp4", "avi", "mov", "mkv"}
MAX_FILE_SIZE = 1024 * 1024 * 500  # 500MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


def allowed_file(filename):
    """Check if file has allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class LogCapture:
    """Capture log messages for API response."""

    def __init__(self):
        self.logs = []

    def append(self, message):
        """Append log message."""
        self.logs.append(message)

    def clear(self):
        """Clear logs."""
        self.logs = []

    def get_logs(self):
        """Get all logs."""
        return self.logs


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Fall Detection API is running"})


@app.route("/api/models", methods=["GET"])
def get_models():
    """Get list of available models."""
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    models = []

    if os.path.exists(assets_dir):
        for folder in sorted(os.listdir(assets_dir)):
            model_path = os.path.join(assets_dir, folder, "best.pt")
            if os.path.isfile(model_path):
                models.append(
                    {
                        "name": folder,
                        "path": f"{folder}/best.pt",
                    }
                )

    return jsonify({"models": models})


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Upload file for detection."""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Get video metadata if it's a video
    metadata = None
    if filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
        metadata = get_video_metadata(filepath)
        if metadata:
            fps, frame_count, duration_sec = metadata
            metadata = {
                "fps": fps,
                "frame_count": int(frame_count),
                "duration_sec": duration_sec,
            }

    return jsonify(
        {
            "success": True,
            "filename": filename,
            "filepath": filepath,
            "metadata": metadata,
        }
    )


@app.route("/api/detect", methods=["POST"])
def detect():
    """Run fall detection on uploaded file."""
    data = request.get_json()

    if not data or "filepath" not in data or "model_name" not in data:
        return jsonify({"error": "Missing filepath or model_name"}), 400

    filepath = data.get("filepath")
    model_name = data.get("model_name")
    use_filter_person = data.get("use_filter_person", False)
    use_filter_static = data.get("use_filter_static", False)
    frame_interval = data.get("frame_interval", 1)

    # Validate filepath exists
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    # Validate model exists
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    model_path = os.path.join(assets_dir, model_name)
    if not os.path.isfile(model_path):
        return jsonify({"error": "Model not found"}), 404

    # Prepare log capture
    log_capture = LogCapture()

    # Run detection
    try:
        output_subdir = model_name.split("/")[0]
        result_path = detect_fall(
            path=filepath,
            model_path=model_path,
            output_subdir=output_subdir,
            use_filter_person=use_filter_person,
            use_filter_static=use_filter_static,
            log_area=log_capture,
            frame_interval=frame_interval,
        )

        if result_path:
            return jsonify(
                {
                    "success": True,
                    "result_path": result_path,
                    "logs": log_capture.get_logs(),
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "error": "Detection failed",
                    "logs": log_capture.get_logs(),
                }
            )
    except Exception as e:
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "logs": log_capture.get_logs(),
            }
        ), 500


@app.route("/api/download/<path:filename>", methods=["GET"])
def download_file(filename):
    """Download result file."""
    filepath = os.path.join("outputs", filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    return send_file(filepath, as_attachment=True)


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({"error": "File too large"}), 413


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
