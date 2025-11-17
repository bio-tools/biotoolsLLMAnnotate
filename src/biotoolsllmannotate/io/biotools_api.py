import requests
from pathlib import Path
from typing import Optional, Dict, Any, List


def read_biotools_token(token_path: Optional[str] = None) -> Optional[str]:
    """
    Read bio.tools API token from .bt_token file.

    Args:
        token_path: Optional path to token file. If None, uses .bt_token in repo root.

    Returns:
        Token string with whitespace stripped, or None if file doesn't exist.
    """
    if token_path is None:
        # Default to .bt_token in repository root
        token_path = Path(".bt_token")
    else:
        token_path = Path(token_path)

    try:
        if token_path.exists():
            token = token_path.read_text(encoding="utf-8").strip()
            return token if token else None
        return None
    except Exception:
        # Silently return None if file can't be read
        return None


def fetch_biotools_entry(
    tool_id: str,
    api_base: str = "https://bio.tools/api/tool/",
    token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Query the bio.tools API for a given tool ID.

    Args:
        tool_id: The bio.tools ID to query
        api_base: Base URL for the bio.tools API
        token: Optional authentication token

    Returns:
        JSON record if found, or None if not found (404), or raises for network errors.
    """
    url = api_base.rstrip("/") + f"/{tool_id}?format=json"
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Token {token}"

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            return None
        else:
            resp.raise_for_status()
    except Exception as exc:
        # For network errors, propagate or log as needed
        raise RuntimeError(f"bio.tools API error for {tool_id}: {exc}")


def validate_biotools_entry(
    entry: Dict[str, Any],
    api_base: str = "https://bio.tools/api/tool/validate/",
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate a bio.tools entry against the bio.tools schema using the validation API.

    Args:
        entry: The tool entry to validate (dict matching biotoolsSchema)
        api_base: Base URL for the validation endpoint
        token: Optional authentication token for dev server access

    Returns:
        Dictionary with validation results:
        {
            "valid": bool,  # True if valid, False if invalid
            "errors": List[str],  # List of validation error messages
            "warnings": List[str],  # List of validation warnings (optional)
        }
    """
    url = api_base.rstrip("/")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Token {token}"

    try:
        resp = requests.post(url, json=entry, headers=headers, timeout=30)

        if resp.status_code == 200:
            # Entry is valid
            return {
                "valid": True,
                "errors": [],
                "warnings": [],
            }
        elif resp.status_code == 400:
            # Validation errors
            try:
                error_data = resp.json()
                # bio.tools API returns validation errors in various formats
                # Try to extract error messages
                errors = []

                if isinstance(error_data, dict):
                    # Check for common error fields
                    if "errors" in error_data:
                        errors = (
                            error_data["errors"]
                            if isinstance(error_data["errors"], list)
                            else [str(error_data["errors"])]
                        )
                    elif "error" in error_data:
                        errors = [str(error_data["error"])]
                    elif "message" in error_data:
                        errors = [str(error_data["message"])]
                    else:
                        # Flatten all error messages from the response
                        for key, value in error_data.items():
                            if isinstance(value, list):
                                errors.extend([f"{key}: {str(v)}" for v in value])
                            else:
                                errors.append(f"{key}: {str(value)}")
                elif isinstance(error_data, list):
                    errors = [str(e) for e in error_data]
                else:
                    errors = [str(error_data)]

                return {
                    "valid": False,
                    "errors": (
                        errors
                        if errors
                        else [f"Validation failed with status {resp.status_code}"]
                    ),
                    "warnings": [],
                }
            except Exception:
                # Couldn't parse error response
                return {
                    "valid": False,
                    "errors": [f"Validation failed: {resp.text[:200]}"],
                    "warnings": [],
                }
        else:
            # Other errors
            return {
                "valid": False,
                "errors": [f"API error {resp.status_code}: {resp.text[:200]}"],
                "warnings": [],
            }

    except requests.exceptions.Timeout:
        return {
            "valid": False,
            "errors": ["Validation request timed out"],
            "warnings": [],
        }
    except Exception as exc:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(exc)}"],
            "warnings": [],
        }
