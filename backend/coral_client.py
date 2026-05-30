import json
import subprocess
from pathlib import Path


class CoralClient:
    """Small wrapper around the official Coral CLI.

    This intentionally calls `coral sql` instead of manually fetching provider APIs.
    That keeps Coral as the retrieval/correlation engine.
    """

    def __init__(self, root: Path):
        self.root = Path(root)

    def run_query_file(self, relative_sql_path: str):
        sql_path = self.root / relative_sql_path
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL file not found: {sql_path}")

        cmd = ["coral", "sql", "-f", str(sql_path), "--format", "json"]

        try:
            completed = subprocess.run(
                cmd,
                cwd=str(self.root),
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Coral CLI was not found. Install Coral first or run in demo mode: "
                "COMMITMENT_RADAR_MODE=demo python run.py"
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                "Coral query failed.\n\n"
                f"Command: {' '.join(cmd)}\n\n"
                f"stderr:\n{exc.stderr}\n\n"
                f"stdout:\n{exc.stdout}"
            )

        try:
            parsed = json.loads(completed.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(
                "Coral returned non-JSON output. Try running the query manually:\n"
                f"coral sql -f {sql_path} --format json\n\n"
                f"Output:\n{completed.stdout[:1000]}"
            )

        if isinstance(parsed, dict) and "rows" in parsed:
            return parsed["rows"]
        if isinstance(parsed, list):
            return parsed

        raise RuntimeError(f"Unexpected Coral JSON shape: {type(parsed).__name__}")
