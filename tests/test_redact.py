"""Tests for secret redaction (llmwiki.redact)."""

from llmwiki.redact import (
    compile_redact_patterns,
    detect_secrets,
    redact_text,
)


def _kinds(findings):
    return {f["kind"] for f in findings}


class TestStructuralSecrets:
    def test_aws_access_key_redacted(self):
        text = "aws_key AKIAIOSFODNN7EXAMPLE end"
        clean, findings = redact_text(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in clean
        assert "«REDACTED:aws-access-key»" in clean
        assert findings == [{"kind": "aws-access-key", "count": 1}]

    def test_google_api_key_redacted(self):
        key = "AIza" + "B" * 35
        clean, findings = redact_text(f"key={key}")
        assert key not in clean
        assert "google-api-key" in _kinds(findings)

    def test_jwt_redacted(self):
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w"
        clean, findings = redact_text(f"Authorization: Bearer {jwt}")
        assert jwt not in clean
        assert "jwt" in _kinds(findings)

    def test_private_key_block_redacted(self):
        text = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEpAIBAAKCAQEA1234567890abcdef\n"
            "abcdefghijklmnopqrstuvwxyz\n"
            "-----END RSA PRIVATE KEY-----"
        )
        clean, findings = redact_text(text)
        assert "MIIEpAIBAAKCAQEA" not in clean
        assert "«REDACTED:private-key»" in clean
        assert "private-key" in _kinds(findings)

    def test_prose_mentioning_password_not_flagged(self):
        text = "The user must enter a password before login. Passwords are hashed."
        clean, findings = redact_text(text)
        assert findings == []
        assert clean == text


class TestUrlCredentials:
    def test_only_password_redacted(self):
        clean, findings = redact_text("postgres://admin:s3cretPassw0rd@db.host:5432/app")
        assert "s3cretPassw0rd" not in clean
        assert "admin" in clean  # username preserved
        assert "db.host" in clean  # host preserved
        assert "url-credentials" in _kinds(findings)


class TestGenericCredentials:
    def test_real_value_redacted(self):
        clean, findings = redact_text('api_key = "abcd1234efgh5678"')
        assert "abcd1234efgh5678" not in clean
        assert "generic-credential" in _kinds(findings)

    def test_placeholder_dollar_brace_not_flagged(self):
        clean, findings = redact_text("password = ${DB_PASSWORD}")
        assert findings == []

    def test_placeholder_double_percent_not_flagged(self):
        clean, findings = redact_text("token = %%API_TOKEN%%")
        assert findings == []

    def test_placeholder_changeme_not_flagged(self):
        clean, findings = redact_text('password = "changeme"')
        assert findings == []

    def test_placeholder_word_password_not_flagged(self):
        clean, findings = redact_text("password = password")
        assert findings == []

    def test_short_value_not_flagged(self):
        clean, findings = redact_text("secret = short")
        assert findings == []

    def test_os_environ_indirection_not_flagged(self):
        clean, findings = redact_text('api_key = os.environ["API_KEY"]')
        assert findings == []

    def test_process_env_indirection_not_flagged(self):
        clean, findings = redact_text("token = process.env.API_TOKEN")
        assert findings == []

    def test_bare_variable_not_flagged(self):
        clean, findings = redact_text("secret = $SECRET_VALUE")
        assert findings == []

    def test_repeated_char_placeholder_not_flagged(self):
        clean, findings = redact_text('access_key = "xxxxxxxxxx"')
        assert findings == []

    def test_angle_bracket_placeholder_not_flagged(self):
        clean, findings = redact_text("password = <your-password-here>")
        assert findings == []


class TestAggregationAndCustom:
    def test_counts_aggregated_per_kind(self):
        text = "AKIAIOSFODNN7EXAMPLE and AKIAIOSFODNN7NOTREAL2"
        _, findings = redact_text(text)
        aws = next(f for f in findings if f["kind"] == "aws-access-key")
        assert aws["count"] == 2

    def test_custom_patterns_redact(self):
        patterns = compile_redact_patterns([r"COMPANY-[0-9]{6}"])
        clean, findings = redact_text("id COMPANY-123456", extra_patterns=patterns)
        assert "COMPANY-123456" not in clean
        assert "custom" in _kinds(findings)

    def test_invalid_custom_pattern_skipped(self):
        patterns = compile_redact_patterns([r"(unclosed"])
        assert patterns == []

    def test_detect_secrets_does_not_rewrite(self):
        findings = detect_secrets("AKIAIOSFODNN7EXAMPLE")
        assert "aws-access-key" in _kinds(findings)

    def test_clean_text_returns_no_findings(self):
        clean, findings = redact_text("just some ordinary documentation text")
        assert findings == []
        assert clean == "just some ordinary documentation text"


class TestDogfoodRegressions:
    """Bugs found by running llmwiki on its own repo (Phase V)."""

    def test_redaction_is_idempotent(self):
        """The «REDACTED:...» marker must never re-trigger detection."""
        from llmwiki.redact import redact_text
        text = 'password = "hunter2secret9value"'
        once, f1 = redact_text(text)
        assert f1
        twice, f2 = redact_text(once)
        assert twice == once
        assert f2 == []

    def test_unquoted_function_call_not_redacted(self):
        from llmwiki.redact import redact_text
        clean, findings = redact_text("token = fetch_token(user)")
        assert clean == "token = fetch_token(user)"
        assert findings == []

    def test_unquoted_dotted_path_not_redacted(self):
        from llmwiki.redact import redact_text
        clean, findings = redact_text("api_key = settings.credentials.key")
        assert clean == "api_key = settings.credentials.key"
        assert findings == []

    def test_regex_assignment_not_redacted(self):
        """The exact case from dogfooding: a pattern constant named *_ACCESS_KEY."""
        from llmwiki.redact import redact_text
        text = '_AWS_ACCESS_KEY = re.compile(r"AKIA[0-9A-Z]{16}")'
        clean, findings = redact_text(text)
        # generic-credential must not fire on the re.compile expression
        assert "re.compile" in clean

    def test_quoted_literal_still_redacted(self):
        from llmwiki.redact import redact_text
        clean, findings = redact_text('password = "hunter2secret9value"')
        assert "hunter2secret9value" not in clean
        assert any(f["kind"] == "generic-credential" for f in findings)

    def test_unquoted_env_style_still_redacted(self):
        """properties/env-style bare secrets must still be caught."""
        from llmwiki.redact import redact_text
        clean, findings = redact_text("db.password=changeme123secret")
        assert "changeme123secret" not in clean
