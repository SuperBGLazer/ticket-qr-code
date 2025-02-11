import json
import base64
import pyzbar.pyzbar as pyzbar
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization, hashes
import time
import brotli
import cv2
import requests

# Load Public Key for signature verification
public_key_pem = requests.get("http://localhost:5000/public-key").text.encode()
public_key = serialization.load_pem_public_key(public_key_pem)

if not isinstance(public_key, rsa.RSAPublicKey):
    print("Mismatch key type: cannot verify the signature with PSS padding.")
    exit()

# Open webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Could not open webcam")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # Decode any barcodes in the frame
    decoded_objects = pyzbar.decode(frame)
    if not decoded_objects:
        cv2.imshow('Webcam', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    # Extract barcode data (assumes only one barcode)
    barcode_data = decoded_objects[0].data.decode("utf-8")

    # Decompress barcode data
    compressed_data = base64.b64decode(barcode_data)
    decompressed_data = brotli.decompress(compressed_data).decode()

    # Parse barcode JSON
    barcode_json = json.loads(decompressed_data)
    data_str = base64.b64decode(barcode_json["data"]).decode()
    signature = base64.b64decode(barcode_json["signature"])

    # Verify signature
    try:
        public_key.verify(
            signature,
            data_str.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        print("✅ Signature Verified: Barcode is authentic")
    except Exception:
        print("❌ Invalid Signature: Barcode has been tampered with!")
        break

    # Validate timestamp
    barcode_info = json.loads(data_str)
    timestamp = barcode_info["timestamp"]
    current_timestamp = int(time.time() // 30)

    if timestamp == current_timestamp:
        print("✅ Barcode is valid for entry")
    else:
        print("❌ Expired Barcode")

    print("Ticket ID:", barcode_info["ticket_id"])
    break

cap.release()
cv2.destroyAllWindows()
