import os
import logging
from flask import Flask, request, jsonify, render_template
from utils.hybrid_pipeline import HybridPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize Flask App
app = Flask(__name__)

# Pre-load the Hybrid Pipeline at startup
logger.info("Initializing Hybrid NLP Pipeline (Rule Engine + T5-Small)...")
try:
    pipeline = HybridPipeline()
    logger.info("✅ Hybrid NLP Pipeline successfully loaded into memory!")
except Exception as e:
    logger.error(f"❌ Failed to load Hybrid Pipeline: {str(e)}")
    pipeline = None

# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def index():
    """Serves the main frontend webpage."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint for deployment monitoring."""
    status = "healthy" if pipeline is not None else "degraded"
    return jsonify({
        "status": status,
        "model_loaded": pipeline is not None
    }), 200 if pipeline is not None else 500


@app.route("/api/convert", methods=["POST"])
def convert_text():
    """
    Main API endpoint for informal-to-formal conversion.
    
    Expected Request JSON:
        { "text": "hey can u send me the report asap?" }
        
    Response JSON:
        {
            "success": true,
            "original": "hey can u send me the report asap?",
            "rule_based": "Hey can you send me the report as soon as possible?",
            "hybrid": "Could you please send me the report as soon as possible?",
            "error": null
        }
    """
    if pipeline is None:
        return jsonify({
            "success": False,
            "original": "",
            "rule_based": "",
            "hybrid": "",
            "error": "NLP model pipeline is not loaded on server."
        }), 500

    # Ensure request contains JSON or form payload
    if not request.is_json and not request.form:
        # Fallback check if user sent raw json header without content-type
        try:
            data = request.get_json(force=True)
        except Exception:
            return jsonify({
                "success": False,
                "original": "",
                "rule_based": "",
                "hybrid": "",
                "error": "Request body must be valid JSON with 'Content-Type: application/json'."
            }), 400
    else:
        data = request.get_json(silent=True) or request.form

    if not data or "text" not in data:
        return jsonify({
            "success": False,
            "original": "",
            "rule_based": "",
            "hybrid": "",
            "error": "Missing required field 'text' in request body."
        }), 400

    raw_text = data.get("text", "")

    # Execute Hybrid Pipeline
    try:
        result = pipeline.process(raw_text)
        
        if not result["success"]:
            return jsonify(result), 400
            
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}")
        return jsonify({
            "success": False,
            "original": raw_text,
            "rule_based": "",
            "hybrid": "",
            "error": "An unexpected error occurred during processing."
        }), 500


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Endpoint not found."}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"success": False, "error": "HTTP method not allowed."}), 405

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "error": "Internal server error."}), 500


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":
    # Get port from environment variable (useful for Render deployment)
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    logger.info(f"Starting Flask server on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)