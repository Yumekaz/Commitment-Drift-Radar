import json
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from backend.coral_client import CoralClient
from backend.demo_engine import DemoEngine
from backend.explainer import explain_row
from backend.risk import rank_rows

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "static"
CORE_CORAL_QUERY = "coral/queries/commitment_risk.sql"
CORE_CORAL_COMMAND = f"coral sql -f {CORE_CORAL_QUERY} --format json"


class AppHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urlparse(path)
        if parsed.path == "/":
            return str(STATIC_DIR / "index.html")
        if parsed.path.startswith("/static/"):
            return str(ROOT / parsed.path.lstrip("/"))
        return str(STATIC_DIR / parsed.path.lstrip("/"))

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            mode = os.getenv("COMMITMENT_RADAR_MODE", "demo").lower()
            coral_live = mode == "coral"
            self._send_json({
                "ok": True,
                "mode": mode,
                "coral_live": coral_live,
                "coral_command": CORE_CORAL_COMMAND,
                "data_mode": "live Coral SQL" if coral_live else "sample CSV dataset",
                "data_note": (
                    "Rows are returned by the Coral CLI from configured sources."
                    if coral_live
                    else "Rows are computed from data/demo/*.csv so the public app can be reviewed without private credentials."
                ),
                "sources": [
                    "commitments.customer_promises",
                    "linear.issues",
                    "github.pulls",
                    "slack.messages",
                    "intercom.conversations",
                    "stripe.invoices",
                    "launchdarkly.feature_flags",
                ],
                "message": "Commitment Drift Radar API is running."
            })
            return

        if parsed.path == "/api/coral-query":
            try:
                self._send_json({
                    "path": CORE_CORAL_QUERY,
                    "command": CORE_CORAL_COMMAND,
                    "sql": (ROOT / CORE_CORAL_QUERY).read_text(encoding="utf-8"),
                })
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)
            return

        if parsed.path == "/api/risks":
            try:
                rows = load_risks()
                self._send_json({"rows": rows})
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)
            return

        if parsed.path.startswith("/api/evidence/"):
            feature_key = parsed.path.split("/")[-1]
            try:
                rows = load_risks()
                match = next((r for r in rows if r.get("feature_key") == feature_key), None)
                if not match:
                    self._send_json({"error": "feature_key not found"}, status=404)
                    return
                self._send_json({
                    "feature_key": feature_key,
                    "row": match,
                    "explanation": explain_row(match)
                })
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)
            return

        return super().do_GET()


def load_risks():
    mode = os.getenv("COMMITMENT_RADAR_MODE", "demo").lower()
    if mode == "coral":
        client = CoralClient(ROOT)
        rows = client.run_query_file(CORE_CORAL_QUERY)
    else:
        rows = DemoEngine(ROOT / "data" / "demo").compute_risk_rows()

    return rank_rows(rows)


def main():
    host = os.getenv("COMMITMENT_RADAR_HOST", "127.0.0.1")
    port = int(os.getenv("COMMITMENT_RADAR_PORT") or os.getenv("PORT", "8080"))
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Commitment Drift Radar running at http://{host}:{port}")
    print(f"Mode: {os.getenv('COMMITMENT_RADAR_MODE', 'demo')}")
    print(f"Live Coral command: {CORE_CORAL_COMMAND}")
    server.serve_forever()
