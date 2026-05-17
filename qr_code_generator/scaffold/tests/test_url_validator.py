import pytest
from app.url_validator import validate_url, is_blocked_domain


# Good URLs that should pass validation
GOOD_URLS = [
    "https://example.com",
    "http://example.com",
    "https://Example.com/path",
    "https://example.com/path/",
    "https://sub.example.com",
]

# Bad URLs that should raise ValueError
BAD_URLS = [
    "https://" + "a" * 3000,  # Too long
    "ftp://example.com",  # Wrong scheme
    "https://evil.com",  # Blocked domain
    "https://malware.example.com",  # Blocked domain
    "https://",  # No hostname
]


def test_good_urls():
    for url in GOOD_URLS:
        normalized = validate_url(url)
        assert isinstance(normalized, str)
        assert normalized.startswith("https://")
        assert not normalized.endswith("/")
        assert len(normalized) <= 2048


def test_bad_urls():
    for url in BAD_URLS:
        with pytest.raises(ValueError):
            validate_url(url)


def test_is_blocked_domain():
    assert is_blocked_domain("evil.com") is True
    assert is_blocked_domain("Evil.com") is True
    assert is_blocked_domain("good.com") is False
    assert is_blocked_domain(None) is True

