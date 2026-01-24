"""
Project-level Python site customization.

Purpose: avoid a Windows certificate store parsing crash on Python 3.7
that breaks Streamlit startup. We ignore only the specific "nested asn1"
error and let all other SSL errors surface.
"""
import ssl


_original_load_windows_store_certs = ssl.SSLContext._load_windows_store_certs


def _patched_load_windows_store_certs(self, storename, purpose):
    try:
        return _original_load_windows_store_certs(self, storename, purpose)
    except ssl.SSLError as exc:
        if "nested asn1 error" in str(exc):
            # Skip broken certs from the Windows store and continue.
            return []
        raise


ssl.SSLContext._load_windows_store_certs = _patched_load_windows_store_certs
