import os
import uuid
import io
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from services.text_to_speech import convert_text_to_speech
from services.video_to_audio import convert_video_to_audio_text_and_braille
from services.braille_converter import convert_text_to_braille
from services.file_extractor import extract_text_from_file
from services.image_processor import process_image

# Initialize Flask app and configurations
app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Directories for uploads and static files
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
AUDIO_DIR = os.path.join(os.getcwd(), "static", "audio")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.route("/")
def index():
    return "EduAccess Backend is Running!"

@app.route("/api/text-to-audio", methods=["POST"])
def api_text_to_audio():
    """
    Convert text to audio using Azure TTS
    """
    try:
        data = request.get_json()
        text = data.get("text")
        if not text:
            return jsonify({"error": "No text provided"}), 400

        output_filename = convert_text_to_speech(text, AUDIO_DIR)
        return jsonify({"audio_file": output_filename})
    except Exception as e:
        print(f"Error in /api/text-to-audio: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/video-to-audio", methods=["POST"])
def api_video_to_audio():
    """
    Convert video to audio
    """
    if "file" not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    video_file = request.files["file"]
    if video_file.filename == "":
        return jsonify({"error": "No video filename provided"}), 400

    try:
        result = convert_video_to_audio_text_and_braille(video_file)
        audio_file_path = result.get("audio_file_path")

        if not audio_file_path or not os.path.exists(audio_file_path):
            return jsonify({"error": "Audio file was not generated."}), 500

        return send_file(audio_file_path, as_attachment=True)
    except Exception as e:
        print(f"Error in /api/video-to-audio: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/text-to-braille", methods=["POST"])
def api_text_to_braille():
    """
    Convert text to Braille representation
    """
    try:
        data = request.get_json()
        text = data.get("text")
        if not text:
            return jsonify({"error": "No text provided"}), 400

        braille_text = convert_text_to_braille(text)
        return jsonify({"braille": braille_text})
    except Exception as e:
        print(f"Error in /api/text-to-braille: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/audio/<path:filename>", methods=["GET"])
def download_audio(filename):
    """
    Download or stream the audio file
    """
    try:
        return send_from_directory(AUDIO_DIR, filename, as_attachment=False)
    except Exception as e:
        print(f"Error in /api/audio/<path:filename>: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/upload-text-file", methods=["POST"])
def upload_text_file():
    """
    Upload and extract text from a text file.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        # Save the uploaded file to a temporary location
        temp_file_path = os.path.join(UPLOAD_FOLDER, secure_filename(uploaded_file.filename))
        uploaded_file.save(temp_file_path)

        # Extract text from the saved file
        extracted_text = extract_text_from_file(temp_file_path)

        # Clean up: Remove the temporary file
        os.remove(temp_file_path)

        return jsonify({"text": extracted_text})
    except Exception as e:
        print(f"Error in /api/upload-text-file: {e}")
        return jsonify({"error": f"Failed to extract text: {str(e)}"}), 500


@app.route("/api/analyze-image", methods=["POST"])
def analyze_image_route():
    """
    Analyze an image and return extracted data.
    """
    try:
        if "file" not in request.files:
            return jsonify({"error": "No image file uploaded"}), 400

        uploaded_file = request.files["file"]
        if uploaded_file.filename == "":
            return jsonify({"error": "No image file selected"}), 400

        image_data = uploaded_file.read()
        # Process the image using the Azure Vision API
        result = process_image(image_data, AUDIO_DIR)

        return jsonify(result)
    except Exception as e:
        print(f"Error in /api/analyze-image: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/video-to-text-and-braille", methods=["POST"])
def api_video_to_text_and_braille():
    """
    Converts video to text and braille by extracting its audio.
    """
    if "file" not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    video_file = request.files["file"]
    if video_file.filename == "":
        return jsonify({"error": "No video filename provided"}), 400

    try:
        result = convert_video_to_audio_text_and_braille(video_file)
        return jsonify(result)
    except Exception as e:
        print(f"Error in /api/video-to-text-and-braille: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)