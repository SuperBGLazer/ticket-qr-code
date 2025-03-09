from flask import Flask, jsonify, request, send_file, render_template
from PIL import Image

from qr_generator import generate_barcode, load_rsa
from tickets import Ticket, delete_ticket, get_all_tickets, save_ticket, get_ticket, scan_ticket

# Initialize Flask app
app = Flask(__name__)

public_key, private_key = load_rsa()

@app.route('/api/barcode/<ticket_id>', methods=['GET'])
def get_barcode(ticket_id):
    return send_file(generate_barcode(ticket_id, private_key), mimetype='image/png')

@app.route('/api/display/<ticket_id>', methods=['GET'])
def home(ticket_id):
    return render_template('barcode.html', ticket_id=ticket_id)


@app.route('/api/ticket', methods=['POST'])
def create_ticket():
    data = request.get_json()
    ticket = Ticket(ticket_id='', section=data['section'], row=data['row'], seat=data['seat'])
    save_ticket(ticket)
    return jsonify(ticket.to_dict())


@app.route('/api/ticket/<ticket_id>', methods=['GET'])
def retrieve_ticket(ticket_id):
    ticket = get_ticket(ticket_id)
    if ticket is None:
        return jsonify({"error": "Ticket not found"}), 404
    return jsonify(ticket.to_dict())

@app.route('/api/create-ticket', methods=['GET'])
def create_ticket_page():
    return render_template('create_ticket.html')


@app.route('/api/tickets', methods=['GET'])
def list_tickets():
    tickets = get_all_tickets()
    return jsonify([ticket.to_dict() for ticket in tickets])

@app.route('/api/list-tickets', methods=['GET'])
def list_tickets_page():
    return render_template('list_tickets.html')

@app.route('/api/ticket/<ticket_id>', methods=['DELETE'])
def delete_ticket_endpoint(ticket_id):
    result = delete_ticket(ticket_id)
    return jsonify({"success": result})


@app.route('/api/scan-ticket/<ticket_id>', methods=['GET'])
def scan_ticket_endpoint(ticket_id):
    success = scan_ticket(ticket_id)
    return jsonify({"success": success})
    


@app.route('/api/public-key', methods=['GET'])
def get_public_key():
    return send_file("public_key.pem", as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
