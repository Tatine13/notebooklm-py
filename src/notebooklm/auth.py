"""Authentication handling for NotebookLM API.

This module provides authentication utilities for the NotebookLM client:

1. **Cookie-based Authentication**: Loads Google cookies from Playwright storage
   state files created by `notebooklm login`.

2. **Token Extraction**: Fetches CSRF (SNlM0e) and session (FdrFJe) tokens from
   the NotebookLM homepage, required for all RPC calls.

3. **Download Cookies**: Provides httpx-compatible cookies with domain info for
   authenticated downloads from Google content servers.

Usage:
    # Recommended: Use AuthTokens.from_storage() for full initialization
    auth = await AuthTokens.from_storage()
    async with NotebookLMClient(auth) as client:
        ...

    # For authenticated downloads
    cookies = load_httpx_cookies()
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(url)

Security Notes:
    - Storage state files contain sensitive session cookies
    - Path traversal protection is enforced on all file operations
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import httpx

# Minimum required cookies (must have at least SID for basic auth)
MINIMUM_REQUIRED_COOKIES = {"SID"}

# Cookie domains to extract from storage state
# Includes googleusercontent.com for authenticated media downloads
ALLOWED_COOKIE_DOMAINS = {
    ".google.com",
    "notebooklm.google.com",
    ".googleusercontent.com",
}

# Default path for Playwright storage state (shared with notebooklm-tools skill)
DEFAULT_STORAGE_PATH = Path.home() / ".notebooklm" / "storage_state.json"


@dataclass
class AuthTokens:
    """Authentication tokens for NotebookLM API.

    Attributes:
        cookies: Dict of required Google auth cookies
        csrf_token: CSRF token (SNlM0e) extracted from page
        session_id: Session ID (FdrFJe) extracted from page
    """

    cookies: dict[str, str]
    csrf_token: str
    session_id: str

    @property
    def cookie_header(self) -> str:
        """Generate Cookie header value for HTTP requests.

        Returns:
            Semicolon-separated cookie string (e.g., "SID=abc; HSID=def")
        """
        return "; ".join(f"{k}={v}" for k, v in self.cookies.items())

    @classmethod
    async def from_storage(cls, path: Optional[Path] = None) -> "AuthTokens":
        """Create AuthTokens from Playwright storage state file.

        This is the recommended way to create AuthTokens for programmatic use.
        It loads cookies from storage and fetches CSRF/session tokens automatically.

        Args:
            path: Path to storage_state.json. If None, uses default location
                  (~/.notebooklm/storage_state.json).

        Returns:
            Fully initialized AuthTokens ready for API calls.

        Raises:
            FileNotFoundError: If storage file doesn't exist
            ValueError: If required cookies are missing or tokens can't be extracted
            httpx.HTTPError: If token fetch request fails

        Example:
            auth = await AuthTokens.from_storage()
            async with NotebookLMClient(auth) as client:
                notebooks = await client.list_notebooks()
        """
        cookies = load_auth_from_storage(path)
        csrf_token, session_id = await fetch_tokens(cookies)
        return cls(cookies=cookies, csrf_token=csrf_token, session_id=session_id)


def extract_cookies_from_storage(storage_state: dict[str, Any]) -> dict[str, str]:
    """Extract Google cookies from Playwright storage state for NotebookLM auth.

    Filters cookies to include those from .google.com, notebooklm.google.com,
    and .googleusercontent.com domains. The googleusercontent.com cookies are
    needed for authenticated media downloads.

    Args:
        storage_state: Parsed JSON from Playwright's storage state file.

    Returns:
        Dict mapping cookie names to values.

    Raises:
        ValueError: If required cookies (SID) are missing from storage state.
    """
    cookies = {}

    for cookie in storage_state.get("cookies", []):
        domain = cookie.get("domain", "")
        if domain in ALLOWED_COOKIE_DOMAINS:
            name = cookie.get("name")
            if name:
                cookies[name] = cookie.get("value", "")

    missing = MINIMUM_REQUIRED_COOKIES - set(cookies.keys())
    if missing:
        raise ValueError(
            f"Missing required cookies: {missing}\n"
            f"Run 'notebooklm login' to authenticate."
        )

    return cookies


def extract_csrf_from_html(html: str, final_url: str = "") -> str:
    """
    Extract CSRF token (SNlM0e) from NotebookLM page HTML.

    The CSRF token is embedded in the page's WIZ_global_data JavaScript object.
    It's required for all RPC calls to prevent cross-site request forgery.

    Args:
        html: Page HTML content from notebooklm.google.com
        final_url: The final URL after redirects (for error messages)

    Returns:
        CSRF token value (typically starts with "AF1_QpN-")

    Raises:
        ValueError: If token pattern not found in HTML
    """
    # Match "SNlM0e": "<token>" or "SNlM0e":"<token>" pattern
    match = re.search(r'"SNlM0e"\s*:\s*"([^"]+)"', html)
    if not match:
        # Check if we were redirected to login page
        if "accounts.google.com" in final_url or "accounts.google.com" in html:
            raise ValueError(
                "Authentication expired or invalid. "
                "Run 'notebooklm login' to re-authenticate."
            )
        raise ValueError(
            f"CSRF token not found in HTML. Final URL: {final_url}\n"
            "This may indicate the page structure has changed."
        )
    return match.group(1)


def extract_session_id_from_html(html: str, final_url: str = "") -> str:
    """
    Extract session ID (FdrFJe) from NotebookLM page HTML.

    The session ID is embedded in the page's WIZ_global_data JavaScript object.
    It's passed in URL query parameters for RPC calls.

    Args:
        html: Page HTML content from notebooklm.google.com
        final_url: The final URL after redirects (for error messages)

    Returns:
        Session ID value

    Raises:
        ValueError: If session ID pattern not found in HTML
    """
    # Match "FdrFJe": "<session_id>" or "FdrFJe":"<session_id>" pattern
    match = re.search(r'"FdrFJe"\s*:\s*"([^"]+)"', html)
    if not match:
        if "accounts.google.com" in final_url or "accounts.google.com" in html:
            raise ValueError(
                "Authentication expired or invalid. "
                "Run 'notebooklm login' to re-authenticate."
            )
        raise ValueError(
            f"Session ID not found in HTML. Final URL: {final_url}\n"
            "This may indicate the page structure has changed."
        )
    return match.group(1)


def load_auth_from_storage(path: Optional[Path] = None) -> dict[str, str]:
    """Load Google cookies from Playwright storage state file.

    Reads the JSON storage state file created by `notebooklm login` and extracts
    the required Google authentication cookies.

    Args:
        path: Path to storage_state.json. If None, uses ~/.notebooklm/storage_state.json.

    Returns:
        Dict mapping cookie names to values (e.g., {"SID": "...", "HSID": "..."}).

    Raises:
        FileNotFoundError: If storage file doesn't exist.
        ValueError: If required cookies (SID) are missing.
    """
    storage_path = path or DEFAULT_STORAGE_PATH

    if not storage_path.exists():
        raise FileNotFoundError(
            f"Storage file not found: {storage_path}\n"
            f"Run 'notebooklm login' to authenticate first."
        )

    storage_state = json.loads(storage_path.read_text())
    return extract_cookies_from_storage(storage_state)


def _is_allowed_cookie_domain(domain: str) -> bool:
    """Check if a cookie domain is allowed for downloads.

    Uses suffix matching with leading dots to ensure proper subdomain validation.
    The leading dot in suffixes (e.g., '.google.com') provides the boundary check:
    - 'lh3.google.com' ends with '.google.com' → True (valid subdomain)
    - 'evil-google.com' does NOT end with '.google.com' → False (not a subdomain)

    Args:
        domain: Cookie domain to check (e.g., '.google.com', 'lh3.google.com')

    Returns:
        True if domain is allowed for downloads.
    """
    # Exact match against the primary allowlist
    if domain in ALLOWED_COOKIE_DOMAINS:
        return True

    # Suffixes for allowed download domains (leading dot provides boundary check)
    allowed_suffixes = (
        ".google.com",
        ".googleusercontent.com",
        ".usercontent.google.com",
    )

    # Check if domain matches or is a subdomain of allowed suffixes
    for suffix in allowed_suffixes:
        if domain == suffix or domain.endswith(suffix):
            return True

    return False


def load_httpx_cookies(path: Optional[Path] = None) -> "httpx.Cookies":
    """Load cookies as an httpx.Cookies object for authenticated downloads.

    Unlike load_auth_from_storage() which returns a simple dict, this function
    returns a proper httpx.Cookies object with domain information preserved.
    This is required for downloads that follow redirects across Google domains.

    Args:
        path: Path to storage_state.json. If None, uses ~/.notebooklm/storage_state.json.

    Returns:
        httpx.Cookies object with all Google cookies.

    Raises:
        FileNotFoundError: If storage file doesn't exist.
        ValueError: If required cookies are missing.
    """
    storage_path = path or DEFAULT_STORAGE_PATH

    if not storage_path.exists():
        raise FileNotFoundError(
            f"Storage file not found: {storage_path}\n"
            f"Run 'notebooklm login' to authenticate first."
        )

    storage_state = json.loads(storage_path.read_text())

    cookies = httpx.Cookies()
    cookie_names = set()

    for cookie in storage_state.get("cookies", []):
        domain = cookie.get("domain", "")
        name = cookie.get("name", "")
        value = cookie.get("value", "")

        # Only include cookies from explicitly allowed domains
        if _is_allowed_cookie_domain(domain) and name and value:
            cookies.set(name, value, domain=domain)
            cookie_names.add(name)

    # Validate that essential cookies are present
    missing = MINIMUM_REQUIRED_COOKIES - cookie_names
    if missing:
        raise ValueError(
            f"Missing required cookies for downloads: {missing}\n"
            f"Run 'notebooklm login' to re-authenticate."
        )

    return cookies


async def fetch_tokens(cookies: dict[str, str]) -> tuple[str, str]:
    """Fetch CSRF token and session ID from NotebookLM homepage.

    Makes an authenticated request to NotebookLM and extracts the required
    tokens from the page HTML.

    Args:
        cookies: Dict of Google auth cookies

    Returns:
        Tuple of (csrf_token, session_id)

    Raises:
        httpx.HTTPError: If request fails
        ValueError: If tokens cannot be extracted from response
    """
    cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://notebooklm.google.com/",
            headers={"Cookie": cookie_header},
            follow_redirects=True,
            timeout=30.0,
        )
        response.raise_for_status()

        final_url = str(response.url)

        # Check if we were redirected to login
        if "accounts.google.com" in final_url:
            raise ValueError(
                "Authentication expired or invalid. "
                "Redirected to: " + final_url + "\n"
                "Run 'notebooklm login' to re-authenticate."
            )

        csrf = extract_csrf_from_html(response.text, final_url)
        session_id = extract_session_id_from_html(response.text, final_url)

        return csrf, session_id
