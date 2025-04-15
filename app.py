from flask import Flask, render_template, request, send_from_directory
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["receipt"]
        if file:
            file.save(os.path.join("static/uploads", file.filename))

    # Find the hashed JS file in dist/assets/
    assets_dir = "static/dist/assets"
    js_file = next((f for f in os.listdir(assets_dir) if f.endswith(".js")), None)
    return render_template("index.html", js_file=js_file)

@app.route("/static/dist/<path:filename>")
def serve_static(filename):
    return send_from_directory("static/dist", filename)


@app.route("/static/dist/<path:filename>")
def serve_static(filename):
    return send_from_directory("static/dist", filename)

if __name__ == "__main__":
    os.makedirs("static/uploads", exist_ok=True)
    app.run(debug=True, host='0.0.0.0')
