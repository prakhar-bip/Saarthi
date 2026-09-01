import pytest
import os
import sys

# Ensure backend dir is on path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.progress_logger import redact_sensitive_tokens


def test_redact_sensitive_jwt_tokens():
    # Example mock JWT
    raw_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    log_line = f"Connecting to WebSocket: /ws/projects/p123?token={raw_jwt}&other=param"

    sanitized = redact_sensitive_tokens(log_line)
    assert raw_jwt not in sanitized
    assert "[REDACTED_JWT]" in sanitized or "token=[REDACTED]" in sanitized


def test_redact_sensitive_query_parameters():
    query_line = "GET /api/projects/sync?token=secret12345&key=mysecretkey&name=myproject"
    sanitized = redact_sensitive_tokens(query_line)
    assert "secret12345" not in sanitized
    assert "mysecretkey" not in sanitized
    assert "token=[REDACTED]" in sanitized
    assert "key=[REDACTED]" in sanitized
    assert "name=myproject" in sanitized
