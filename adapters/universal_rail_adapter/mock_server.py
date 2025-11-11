from flask import Flask, request, jsonify

app = Flask(__name__)

 @app.route("/anchor", methods=["POST"])
def anchor():
    content_hash = request.get_json(force=True).get("content_hash")
    if not content_hash:
        return jsonify({"error": "missing content_hash"}), 400
    return jsonify({"anchorRef": f"mock-anchor-{content_hash[:12]}", "status": "anchored"}), 200

if __name__ == "__main__":
    app.run(port=8080, debug=True)
