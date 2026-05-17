from urllib.parse import urlparse

MAX_URL_LENGTH = 2048

BLOCKED_DOMAINS = {
    "evil.com",
    "malware.example.com",
    "phishing.example.com",
}


def is_blocked_domain(hostname: str | None) -> bool:
    if hostname is None:
        return True
    return hostname.lower() in BLOCKED_DOMAINS


def validate_url(url: str) -> str:
    """Format check, normalization, and blocklist validation."""
    # TODO: Implement this function
    #
    # Design decision: normalization keeps the same destination URL mapping to
    # the same token (no duplicates); blocklist validation prevents short links
    # from becoming phishing vectors.
    #
    # Hints:
    # 1. Validate: length within MAX_URL_LENGTH, scheme is http/https via
    #    urlparse(), hostname is not in is_blocked_domain(). Raise ValueError otherwise.
    # 2. Normalize and return: lowercase, strip trailing slash, upgrade http→https.

    if len(url) > MAX_URL_LENGTH:
        raise ValueError(f"URL exceeds maximum length of {MAX_URL_LENGTH} characters")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must have http or https scheme")

    if is_blocked_domain(parsed.hostname):
        raise ValueError("URL contains a blocked domain")

    # Normalize the URL
    normalized = url.lower().rstrip("/")
    if parsed.scheme == "http":
        normalized = normalized.replace("http://", "https://")

    return normalized
