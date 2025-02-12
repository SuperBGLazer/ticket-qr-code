from flask import Flask, jsonify, send_file, render_template
from PIL import Image

from qr_generator import generate_barcode, load_rsa

# Initialize Flask app
app = Flask(__name__)

public_key, private_key = load_rsa()

@app.route('/api/barcode', methods=['GET'])
def get_barcode():
    return send_file(generate_barcode('12345', private_key), mimetype='image/png')

@app.route('/api/display')
def home():
    return render_template('barcode.html')

@app.route('/api/public-key', methods=['GET'])
def get_public_key():
    return send_file("public_key.pem", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
