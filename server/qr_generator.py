import base64
import json
from io import BytesIO
import os
import time
import brotli
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import qrcode


def generate_rsa():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

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
    


def load_rsa():
    if not os.path.exists("private_key.pem") or not os.path.exists("public_key.pem"):
        generate_rsa()
    with open("private_key.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    with open("public_key.pem", "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())
    return public_key, private_key


def generate_barcode(ticket_id: str, private_key) -> BytesIO:
    timestamp = int(time.time() // 30)
    barcode_data = json.dumps({"ticket_id": ticket_id, "timestamp": timestamp})
    signature = private_key.sign(
        barcode_data.encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
        hashes.SHA256()
    )
    barcode_payload = base64.b64encode(barcode_data.encode()).decode()
    signature_payload = base64.b64encode(signature).decode()
    barcode_final = json.dumps({"data": barcode_payload, "signature": signature_payload})
    compressed_barcode = base64.b64encode(brotli.compress(barcode_final.encode())).decode()
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(compressed_barcode)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer