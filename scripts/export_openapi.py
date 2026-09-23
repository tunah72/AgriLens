"""Script to export OpenAPI schema from the FastAPI app as a static JSON file."""

import json
import os
import sys

# Ensure the project root is in the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Skip database initialization during schema generation
os.environ["SKIP_DB_INIT"] = "true"

try:
    from backend.app.main import app
except ImportError as e:
    print(f"Error: Could not import backend.app.main. Make sure Python path is set correctly. Detail: {e}")
    sys.exit(1)


def export_openapi() -> None:
    """Generate and write the OpenAPI schema to docs/api/openapi.json."""
    openapi_schema = app.openapi()

    docs_dir = os.path.join(PROJECT_ROOT, "docs", "api")
    os.makedirs(docs_dir, exist_ok=True)

    output_path = os.path.join(docs_dir, "openapi.json")
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(openapi_schema, file, indent=2, ensure_ascii=False)

    rel_path = os.path.relpath(output_path, PROJECT_ROOT)
    print(f"Successfully exported OpenAPI schema to {rel_path}")


if __name__ == "__main__":
    export_openapi()
