"""
Invoice Management Tool — Flask application.

Routes:
  GET  /                    → Main web interface
  GET  /api/clients         → List all client names
  GET  /api/client/<name>   → Client details (for hourly rate lookup)
  POST /api/appointments    → Fetch appointments from Google Calendar
  POST /api/generate-invoice→ Generate PDF invoice from edited data
  GET  /invoices/<filename> → Download a generated invoice PDF
"""

import os
import datetime
import subprocess
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file

from services.client_service import get_all_clients, get_client
from services.calendar_service import get_appointments
from services.invoice_service import generate_invoice
from services.tracker_service import update_tracker, get_tracker_path, get_latest_invoice_number, get_client_folder

app = Flask(__name__)

# ── Pages ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Render the main interface."""
    return render_template("index.html")


# ── API endpoints ────────────────────────────────────────────────────

@app.route("/api/clients", methods=["GET"])
def api_clients():
    """Return list of all client names."""
    try:
        clients = get_all_clients()
        return jsonify({"clients": clients})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/client/<name>", methods=["GET"])
def api_client_detail(name):
    """Return full client details."""
    try:
        client = get_client(name)
        return jsonify({"client": client})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/appointments", methods=["POST"])
def api_appointments():
    """
    Fetch Google Calendar appointments for a client within a date range.
    Body: { "client": "Name", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }
    """
    data = request.get_json()
    client_name = data.get("client")
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    if not all([client_name, start_date, end_date]):
        return jsonify({"error": "Missing required fields: client, start_date, end_date"}), 400

    try:
        # Get client details for hourly rate
        client = get_client(client_name)
        hourly_rate = float(client.get("hourly_rate", 0))

        # Fetch appointments from Google Calendar
        appointments = get_appointments(client_name, start_date, end_date)

        # Enrich appointments with hourly rate and calculated amount
        for apt in appointments:
            apt["hourly_rate"] = hourly_rate
            apt["amount"] = round(apt["duration_hours"] * hourly_rate, 2)

        return jsonify({
            "appointments": appointments,
            "client": client,
        })

    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate-invoice", methods=["POST"])
def api_generate_invoice():
    data = request.get_json()
    client_name = data.get("client_name")
    appointments = data.get("appointments", [])
    is_correction = data.get("is_correction", False)

    if not client_name:
        return jsonify({"error": "Missing client_name"}), 400
    if not appointments:
        return jsonify({"error": "No appointments to invoice"}), 400

    try:
        year = datetime.datetime.now().year
        client = get_client(client_name)

        invoice_number = None
        if is_correction:
            latest = get_latest_invoice_number(client_name, year)
            if latest:
                invoice_number = latest
            else:
                return jsonify({"error": "Aucune facture existante à corriger."}), 400

        filepath, final_invoice_number, total_amount = generate_invoice(
            client, appointments, invoice_number=invoice_number, is_correction=is_correction
        )
        filename = os.path.basename(filepath)

        today_str = datetime.datetime.now().strftime("%d-%m-%Y")
        invoice_data = {
            "date": today_str,
            "invoice_number": final_invoice_number,
            "amount": float(total_amount),
            "path": filepath
        }
        update_tracker(client_name, year, invoice_data, is_correction)

        return jsonify({
            "success": True,
            "filename": filename,
            "download_url": f"/api/download?path={filepath}",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download")
def download_invoice():
    filepath = request.args.get("path")
    if not filepath or not os.path.exists(filepath):
        return "File not found", 404
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))

@app.route("/api/open-tracker", methods=["POST"])
def open_tracker():
    data = request.get_json()
    client_name = data.get("client_name")
    if not client_name:
        return jsonify({"error": "Missing client_name"}), 400

    year = datetime.datetime.now().year
    tracker_path = get_tracker_path(client_name, year)

    if not os.path.exists(tracker_path):
        return jsonify({"error": "Le fichier de suivi n'existe pas encore pour ce client."}), 404

    try:
        subprocess.call(["open", tracker_path])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Run ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(os.path.join(os.path.dirname(__file__), "invoices"), exist_ok=True)
    app.run(debug=True, port=5000)
