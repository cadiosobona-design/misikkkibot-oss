from misikkki_security import PermissionError, SecretValue, assert_no_withdrawal_permissions, redact_payload


def test_redaction_removes_secret_typed_values_and_keys():
    payload = {
        "api_key": "abc",
        "nested": {"token": SecretValue("secret-token"), "safe": "value"},
    }

    assert redact_payload(payload) == {
        "api_key": "<redacted>",
        "nested": {"token": "<redacted>", "safe": "value"},
    }


def test_withdrawal_permissions_are_rejected():
    try:
        assert_no_withdrawal_permissions(["read", "trade", "withdraw"])
    except PermissionError as exc:
        assert "withdraw" in str(exc)
    else:
        raise AssertionError("withdraw permission was unexpectedly accepted")
