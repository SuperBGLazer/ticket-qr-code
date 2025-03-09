import redis
import json

r = redis.Redis(host='redis', port=6379, db=0)

TICKET_KEY_PREFIX = "ticket:"

class Ticket:

    def __init__(self, ticket_id: str, section: str, row: str, seat: str, scanned: bool = False):
        self.ticket_id = ticket_id
        self.section = section
        self.row = row
        self.seat = seat
        self.scanned = scanned
    
    def to_dict(self):
        return {
            "ticket_id": self.ticket_id,
            "section": self.section,
            "row": self.row,
            "seat": self.seat,
            "scanned": self.scanned
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            data.get("ticket_id", ""),
            data.get("section", ""),
            data.get("row", ""),
            data.get("seat", 0),
            data.get("scanned", False)
        )


def save_ticket(ticket: Ticket):
    ticket.ticket_id = str(r.incr("ticket_counter"))

    r.set(TICKET_KEY_PREFIX + ticket.ticket_id, json.dumps(ticket.to_dict()))
    return ticket


def get_ticket(ticket_id: str):
    ticket_data = r.get(TICKET_KEY_PREFIX + ticket_id)
    if ticket_data is None:
        return None
    return Ticket.from_dict(json.loads(ticket_data.decode('utf-8')))


def delete_ticket(ticket_id: str):
    r.delete(TICKET_KEY_PREFIX + ticket_id)
    return True


def get_all_tickets() -> list[Ticket]:
    keys = r.keys(TICKET_KEY_PREFIX)
    tickets = []
    for key in r.scan_iter(TICKET_KEY_PREFIX + "*"):
        ticket_data = r.get(key)
        if ticket_data is not None:
            tickets.append(Ticket.from_dict(json.loads(ticket_data.decode('utf-8'))))
    return tickets


def scan_ticket(ticket_id: str):
    ticket = get_ticket(ticket_id)
    
    if ticket is None or ticket.scanned:
        return False
    
    ticket.scanned = True
    r.set(TICKET_KEY_PREFIX + ticket_id, json.dumps(ticket.to_dict()))
    return True