import time
import json
import base64
import qrcode
from flask import Flask, jsonify, send_file, render_template
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import brotli
from PIL import Image
from io import BytesIO

# Initialize Flask app
app = Flask(__name__)

# Generate RSA keys for signing barcodes
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
public_key = private_key.public_key()

# Save keys (optional for persistence)
with open("private_key.pem", "wb") as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

with open("public_key.pem", "wb") as f:
    f.write(public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

# Function to generate a barcode
def generate_barcode(ticket_id: str) -> str:
    timestamp = int(time.time() // 30)  # Rotates every 15 sec

    # Create barcode data (ticket + timestamp)
    barcode_data = json.dumps({
        "ticket_id": ticket_id,
        "timestamp": timestamp
    })

    # Sign the barcode data
    signature = private_key.sign(
        barcode_data.encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )

    # Encode barcode data + signature
    barcode_payload = base64.b64encode(barcode_data.encode()).decode()
    signature_payload = base64.b64encode(signature).decode()

    barcode_final = json.dumps({
        "data": barcode_payload,
        "signature": signature_payload
    })

    compressed_barcode = base64.b64encode(brotli.compress(barcode_final.encode())).decode()

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(compressed_barcode)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

@app.route('/barcode', methods=['GET'])
def get_barcode():
    barcode_buffer = generate_barcode('12345')
    return send_file(barcode_buffer, mimetype='image/png')


@app.route('/')
def home():
    return render_template('barcode.html')


@app.route('/api/public-key', methods=['GET'])
def get_public_key():
    return send_file("public_key.pem", as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
