import time
from pathlib import Path
from typing import Any

import requests


def read_biotools_token(token_path: str | None = None) -> str | None:
    """Read bio.tools API token from .bt_token file.

    Args:
        token_path: Optional path to token file. If None, uses .bt_token in repo root.

    Returns:
        Token string with whitespace stripped, or None if file doesn't exist.

    """
    path: Path
    if token_path is None:
        # Default to .bt_token in repository root
        path = Path(".bt_token")
    else:
        path = Path(token_path)

    try:
        if path.exists():
            token = path.read_text(encoding="utf-8").strip()
            return token if token else None
        return None
    except Exception:
        # Silently return None if file can't be read
        return None


def fetch_biotools_entry(
    tool_id: str,
    api_base: str = "https://bio.tools/api/tool/",
    token: str | None = None,
) -> dict[str, Any] | None:
    """Query the bio.tools API for a given tool ID.

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
            result: dict[str, Any] = resp.json()
            return result
        elif resp.status_code == 404:
            return None
        else:
            resp.raise_for_status()
            return None
    except Exception as exc:
        # For network errors, propagate or log as needed
        raise RuntimeError(f"bio.tools API error for {tool_id}: {exc}")


def validate_biotools_entry(
    entry: dict[str, Any],
    api_base: str = "https://bio.tools/api/tool/validate/",
    token: str | None = None,
) -> dict[str, Any]:
    """Validate a bio.tools entry against the bio.tools schema using the validation API.

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


def create_biotools_entry(
    entry: dict[str, Any],
    api_base: str = "https://bio.tools/api/tool/",
    token: str | None = None,
    timeout: int = 30,
    retry_attempts: int = 3,
    retry_delay: float = 1.0,
) -> dict[str, Any]:
    """Create a new bio.tools entry via POST with retry logic.

    Args:
        entry: The tool entry to create (dict matching biotoolsSchema)
        api_base: Base URL for the bio.tools API
        token: Optional authentication token
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts for transient errors
        retry_delay: Initial delay in seconds for exponential backoff

    Returns:
        Dictionary with creation results:
        {
            "success": bool,
            "biotools_id": str,  # if success
            "error": str,  # if failure
            "status_code": int,
        }

    """
    url = api_base.rstrip("/")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Token {token}"

    # Retry logic for transient errors
    attempt = 0
    current_delay = retry_delay

    while attempt <= retry_attempts:
        try:
            resp = requests.post(url, json=entry, headers=headers, timeout=timeout)

            if resp.status_code == 201:
                # Created successfully
                try:
                    response_data = resp.json()
                    biotools_id = response_data.get("biotoolsID") or entry.get(
                        "biotoolsID"
                    )
                    return {
                        "success": True,
                        "biotools_id": biotools_id,
                        "error": None,
                        "status_code": 201,
                    }
                except Exception:
                    return {
                        "success": True,
                        "biotools_id": entry.get("biotoolsID"),
                        "error": None,
                        "status_code": 201,
                    }
            elif resp.status_code == 400:
                # Validation error - don't retry
                error_msg = _extract_error_message(resp)
                return {
                    "success": False,
                    "biotools_id": None,
                    "error": f"Validation error: {error_msg}",
                    "status_code": 400,
                }
            elif resp.status_code == 401:
                # Unauthorized - don't retry
                return {
                    "success": False,
                    "biotools_id": None,
                    "error": "Authentication failed. Check token validity.",
                    "status_code": 401,
                }
            elif resp.status_code == 409:
                # Conflict - entry exists - don't retry
                return {
                    "success": False,
                    "biotools_id": entry.get("biotoolsID"),
                    "error": "Entry already exists on bio.tools (409 Conflict)",
                    "status_code": 409,
                }
            elif resp.status_code >= 500:
                # Server error - retry with backoff
                if attempt < retry_attempts:
                    time.sleep(current_delay)
                    current_delay *= 2
                    attempt += 1
                    continue
                else:
                    # Exhausted retries
                    return {
                        "success": False,
                        "biotools_id": None,
                        "error": f"Server error after {retry_attempts} retries: {resp.status_code}",
                        "status_code": resp.status_code,
                    }
            else:
                # Other error
                return {
                    "success": False,
                    "biotools_id": None,
                    "error": f"API error {resp.status_code}: {resp.text[:200]}",
                    "status_code": resp.status_code,
                }

        except requests.exceptions.Timeout:
            if attempt < retry_attempts:
                time.sleep(current_delay)
                current_delay *= 2
                attempt += 1
                continue
            else:
                return {
                    "success": False,
                    "biotools_id": None,
                    "error": f"Request timeout after {retry_attempts} retries",
                    "status_code": 0,
                }
        except Exception as exc:
            if attempt < retry_attempts:
                time.sleep(current_delay)
                current_delay *= 2
                attempt += 1
                continue
            else:
                return {
                    "success": False,
                    "biotools_id": None,
                    "error": f"Request failed after {retry_attempts} retries: {str(exc)}",
                    "status_code": 0,
                }

    # Should not reach here
    return {
        "success": False,
        "biotools_id": None,
        "error": "Unknown error during upload",
        "status_code": 0,
    }


def _extract_error_message(resp: requests.Response) -> str:
    """Extract error message from API response."""
    try:
        error_data = resp.json()
        if isinstance(error_data, dict):
            if "errors" in error_data:
                errors = (
                    error_data["errors"]
                    if isinstance(error_data["errors"], list)
                    else [str(error_data["errors"])]
                )
                return "; ".join(str(e) for e in errors)
            elif "error" in error_data:
                return str(error_data["error"])
            elif "message" in error_data:
                return str(error_data["message"])
            else:
                # Flatten all error messages
                messages = []
                for key, value in error_data.items():
                    if isinstance(value, list):
                        messages.extend([f"{key}: {str(v)}" for v in value])
                    else:
                        messages.append(f"{key}: {str(value)}")
                return "; ".join(messages)
        elif isinstance(error_data, list):
            return "; ".join(str(e) for e in error_data)
        else:
            return str(error_data)
    except Exception:
        text: str = resp.text[:200]
        return text
