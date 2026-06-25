"""Flask API for fall detection inference."""

import os
import threading
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import torch

from logic.detector import detect_fall, get_video_metadata

app = Flask(__name__)

# Model cache and preloading
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_CACHE = {}  # Cache for loaded models
PRELOAD_STATUS = {"status": "idle", "model": None, "message": ""}
PRELOAD_LOCK = threading.Lock()  # Thread-safe access to preload status

# Configuration
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUTS_DIR = BASE_DIR / "outputs"
UPLOAD_FOLDER = OUTPUTS_DIR / "uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "mp4", "avi", "mov", "mkv"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
MAX_FILE_SIZE = 1024 * 1024 * 500  # 500MB

allowed_origins = os.getenv(
    "FALL_DETECTION_CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]
        }
    },
)

OUTPUTS_DIR.mkdir(exist_ok=True)
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


def allowed_file(filename):
    """Check if file has allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def make_upload_filename(filename):
    """Create a collision-resistant server filename while preserving the extension."""
    original = Path(filename)
    stem = secure_filename(original.stem)[:80] or "upload"
    suffix = original.suffix.lower()
    return f"{uuid4().hex}_{stem}{suffix}"


def resolve_child_path(base_dir, relative_path):
    """Resolve a user supplied relative path under base_dir."""
    rel_path = Path(relative_path or "")
    if rel_path.is_absolute() or ".." in rel_path.parts:
        raise ValueError("Invalid path")

    candidate = (base_dir / rel_path).resolve()
    candidate.relative_to(base_dir.resolve())
    return candidate


def resolve_upload_path(file_ref):
    """Resolve an uploaded file reference to an upload-folder path."""
    if not file_ref:
        raise ValueError("Missing file_id")

    # Backward compatibility for older clients that sent an absolute filepath:
    # only the basename is used, never the client supplied directory.
    filename = Path(file_ref).name
    return resolve_child_path(UPLOAD_FOLDER, filename)


def load_model(model_path_str):
    """Load a YOLO model into the cache."""
    model_path_str = str(model_path_str)
    if model_path_str in MODEL_CACHE:
        return MODEL_CACHE[model_path_str]
    
    try:
        model = YOLO(model_path_str).to(DEVICE)
        MODEL_CACHE[model_path_str] = model
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {str(e)}")


def get_available_models():
    """Get list of available models."""
    models = []
    if ASSETS_DIR.exists():
        for folder in sorted(ASSETS_DIR.iterdir()):
            model_path = folder / "best.pt"
            if folder.is_dir() and model_path.is_file():
                models.append((folder.name, str(model_path)))
    return models


def preload_model_background():
    """Preload the first available model in background."""
    with PRELOAD_LOCK:
        PRELOAD_STATUS["status"] = "loading"
        PRELOAD_STATUS["message"] = "Initializing model preloader..."
    
    try:
        models = get_available_models()
        if not models:
            with PRELOAD_LOCK:
                PRELOAD_STATUS["status"] = "idle"
                PRELOAD_STATUS["message"] = "No models found"
            return
        
        model_name, model_path = models[0]
        
        with PRELOAD_LOCK:
            PRELOAD_STATUS["status"] = "loading"
            PRELOAD_STATUS["message"] = f"Preloading model: {model_name}"
        
        # Load the model
        load_model(model_path)
        
        with PRELOAD_LOCK:
            PRELOAD_STATUS["status"] = "ready"
            PRELOAD_STATUS["model"] = model_name
            PRELOAD_STATUS["message"] = f"Model preloaded: {model_name}"
            
    except Exception as e:
        with PRELOAD_LOCK:
            PRELOAD_STATUS["status"] = "error"
            PRELOAD_STATUS["message"] = f"Preload error: {str(e)}"


def resolve_model_path(model_name):
    """Resolve a model name to a model file under assets."""
    model_path = resolve_child_path(ASSETS_DIR, model_name)
    if model_path.suffix != ".pt":
        raise ValueError("Invalid model file")
    return model_path


def output_relative_path(result_path):
    """Return a browser-safe output-relative path."""
    result = Path(result_path).resolve()
    return result.relative_to(OUTPUTS_DIR.resolve()).as_posix()


class LogCapture:
    """Capture log messages for API response."""

    def __init__(self):
        self.logs = []

    def append(self, message):
        """Append log message."""
        self.logs.append(str(message))

    def clear(self):
        """Clear logs."""
        self.logs = []

    def get_logs(self):
        """Get all logs."""
        return self.logs


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    with PRELOAD_LOCK:
        preload_status = dict(PRELOAD_STATUS)
    
    return jsonify({
        "status": "ok",
        "message": "Fall Detection API is running",
        "device": DEVICE,
        "preload": preload_status
    })


@app.route("/api/models", methods=["GET"])
def get_models():
    """Get list of available models."""
    models = []

    if ASSETS_DIR.exists():
        for folder in sorted(ASSETS_DIR.iterdir()):
            model_path = folder / "best.pt"
            if folder.is_dir() and model_path.is_file():
                # Check if model is in cache
                is_cached = str(model_path) in MODEL_CACHE
                models.append(
                    {
                        "name": folder.name,
                        "path": f"{folder.name}/best.pt",
                        "cached": is_cached,
                    }
                )
    
    with PRELOAD_LOCK:
        preload_status = dict(PRELOAD_STATUS)

    return jsonify({
        "models": models,
        "preload": preload_status
    })


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

    filename = make_upload_filename(file.filename)
    filepath = UPLOAD_FOLDER / filename
    file.save(filepath)

    # Get video metadata if it's a video
    metadata = None
    if filepath.suffix.lower() in VIDEO_EXTENSIONS:
        metadata = get_video_metadata(str(filepath))
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
            "original_filename": file.filename,
            "file_id": filename,
            "metadata": metadata,
        }
    )


@app.route("/api/detect", methods=["POST"])
def detect():
    """Run fall detection on uploaded file."""
    data = request.get_json(silent=True)

    if not data or "model_name" not in data:
        return jsonify({"error": "Missing file_id or model_name"}), 400

    file_ref = data.get("file_id") or data.get("filename") or data.get("filepath")
    model_name = data.get("model_name")
    use_filter_person = data.get("use_filter_person", False)
    use_filter_static = data.get("use_filter_static", False)
    try:
        frame_interval = int(data.get("frame_interval", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "frame_interval must be an integer"}), 400

    if frame_interval < 1 or frame_interval > 30:
        return jsonify({"error": "frame_interval must be between 1 and 30"}), 400

    # Validate filepath exists
    try:
        filepath = resolve_upload_path(file_ref)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not filepath.is_file():
        return jsonify({"error": "File not found"}), 404

    # Validate model exists
    try:
        model_path = resolve_model_path(model_name)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not model_path.is_file():
        return jsonify({"error": "Model not found"}), 404

    # Prepare log capture
    log_capture = LogCapture()
    
    # Try to use cached model if available, otherwise load it
    try:
        if str(model_path) in MODEL_CACHE:
            log_capture.append("✓ Using cached model")
        else:
            log_capture.append("Loading model (first use, will be cached)...")
            load_model(str(model_path))
            log_capture.append("✓ Model loaded and cached")
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Model loading failed: {str(e)}",
            "logs": log_capture.get_logs(),
        }), 500

    # Run detection
    try:
        output_subdir = Path(model_name).parts[0]
        result_path = detect_fall(
            path=str(filepath),
            model_path=str(model_path),
            output_subdir=output_subdir,
            use_filter_person=use_filter_person,
            use_filter_static=use_filter_static,
            log_area=log_capture,
            frame_interval=frame_interval,
            preview_result=False,
        )

        if result_path:
            result_rel_path = output_relative_path(result_path)
            return jsonify(
                {
                    "success": True,
                    "result_path": result_rel_path,
                    "download_url": f"/api/download/{quote(result_rel_path)}",
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
    parts = Path(filename).parts
    if parts and parts[0] == "outputs":
        filename = Path(*parts[1:]).as_posix()

    try:
        filepath = resolve_child_path(OUTPUTS_DIR, filename)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not filepath.is_file():
        return jsonify({"error": "File not found"}), 404

    return send_file(filepath, as_attachment=True)


@app.route("/api/preload-status", methods=["GET"])
def get_preload_status():
    """Get model preload status."""
    with PRELOAD_LOCK:
        status = dict(PRELOAD_STATUS)
    
    # Add cache info
    cached_models = list(MODEL_CACHE.keys())
    status["cached_models_count"] = len(cached_models)
    
    return jsonify(status)


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({"error": "File too large"}), 413


def startup_model_preloader():
    """Start model preloader in background thread on app startup."""
    preload_thread = threading.Thread(target=preload_model_background, daemon=True)
    preload_thread.start()


if __name__ == "__main__":
    # Start model preloader in background
    startup_model_preloader()
    
    debug = os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(debug=debug, host="127.0.0.1", port=5000)
