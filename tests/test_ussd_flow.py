"""
End-to-end USSD flow test hitting the FastAPI TestClient, using an
in-memory sqlite DB via a monkeypatched session factory.

This is a starting skeleton — wire up a proper DB override before relying on
it for CI; for the hackathon, manual testing against the AT simulator is the
priority.
"""
import pytest


@pytest.mark.skip(reason="wire up a test DB override before enabling in CI")
def test_log_sale_full_session():
    pass
