#!/usr/bin/env python3
"""Static URL safety checks shared by OpenDevIndex validators."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


def is_safe_https_url(value: object) -> bool:
    """Accept public-looking HTTPS URLs without performing DNS/network access."""
    if not isinstance(value, str):
        return False

    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError:
        return False

    if parsed.scheme != "https" or not parsed.hostname:
        return False
    if parsed.username or parsed.password:
        return False
    if port not in (None, 443):
        return False

    hostname = parsed.hostname.rstrip(".").casefold()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        return False

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return True
    return address.is_global
