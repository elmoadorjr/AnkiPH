"""
Simple API client for Nottorney Add-on.

Replace the repository's Nottorney_Addon/api_client.py with this file to
remove merge conflict markers and provide a minimal, robust API client.

Exports:
- api: ApiClient instance
- NottorneyAPIError: exception class used across the add-on
"""

from __future__ import annotations
import json
import time
from typing import Any, Dict, Optional

# Primary API base (kept from your docs)
API_BASE = "https://ladvckxztcleljbiomcf.supabase.co/functions/v1"

# Prefer requests if available; fall back to urllib to avoid runtime import errors.
try:
    import requests  # type: ignore
    _HAS_REQUESTS = True
except Exception:
    import urllib.request as _urllib_request
    import urllib.error as _urllib_error
    _HAS_REQUESTS = False


class NottorneyAPIError(Exception):
    """Raised for API-level errors (non-2xx or well-formed error responses)."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class ApiClient:
    """Minimal API client used by the add-on."""

    def __init__(self, access_token: Optional[str] = None, base_url: str = API_BASE):
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")

    def _headers(self, include_auth: bool = True) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if include_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _full_url(self, path: str) -> str:
        if path.startswith("/"):
            path = path[1:]
        return f"{self.base_url}/{path}"

    def post(self, path: str, json_body: Optional[Dict[str, Any]] = None, require_auth: bool = True, timeout: int = 15) -> Any:
        url = self._full_url(path)
        headers = self._headers(include_auth=require_auth)

        if _HAS_REQUESTS:
            try:
                resp = requests.post(url, headers=headers, json=json_body, timeout=timeout)
            except Exception as e:
                raise NottorneyAPIError(f"Network error: {e}") from e

            # try parse JSON, but if not possible, raise
            try:
                data = resp.json()
            except Exception:
                text = resp.text if hasattr(resp, "text") else None
                raise NottorneyAPIError("Invalid JSON response from server", status_code=resp.status_code, details=text)

            if not resp.ok:
                # prefer structured error details if present
                err_msg = None
                if isinstance(data, dict):
                    err_msg = data.get("error") or data.get("message") or data.get("detail")
                raise NottorneyAPIError(err_msg or f"HTTP {resp.status_code}", status_code=resp.status_code, details=data)

            return data

        # urllib fallback
        try:
            req_data = (json.dumps(json_body) if json_body is not None else "").encode("utf-8")
            req = _urllib_request.Request(url, data=req_data, headers=headers, method="POST")
            with _urllib_request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                try:
                    data = json.loads(raw.decode("utf-8"))
                except Exception:
                    raise NottorneyAPIError("Invalid JSON response from server", status_code=resp.getcode(), details=raw)
                if resp.getcode() >= 400:
                    err_msg = data.get("error") if isinstance(data, dict) else None
                    raise NottorneyAPIError(err_msg or f"HTTP {resp.getcode()}", status_code=resp.getcode(), details=data)
                return data
        except _urllib_error.HTTPError as he:
            try:
                body = he.read()
                parsed = json.loads(body.decode("utf-8"))
            except Exception:
                parsed = None
            raise NottorneyAPIError("HTTP error", status_code=getattr(he, "code", None), details=parsed or str(he)) from he
        except Exception as e:
            raise NottorneyAPIError(f"Network error: {e}") from e

    # Convenience methods used by the addon:
    def login(self, email: str, password: str) -> Dict[str, Any]:
        return self.post("/addon-login", json_body={"email": email, "password": password}, require_auth=False)

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        return self.post("/addon-refresh-token", json_body={"refresh_token": refresh_token}, require_auth=False)

    def get_purchases(self) -> Dict[str, Any]:
        return self.post("/addon-get-purchases")

    def download_deck(self, deck_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        payload = {"deck_id": deck_id}
        if version:
            payload["version"] = version
        return self.post("/addon-download-deck", json_body=payload)

    # Add additional convenience wrappers as needed by the addon...


# single shared instance used by the add-on modules
api = ApiClient()

# allow a simple helper to configure token from other modules
def set_access_token(token: Optional[str]) -> None:
    api.access_token = token