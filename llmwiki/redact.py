"""Secret redaction for ingested content.

Secrets (API keys, private keys, credentials) must never reach the wiki's
raw pages, search DB, or exports — an AI agent consuming the knowledge base
would happily surface them. This module scrubs high-confidence secret shapes
from arbitrary text at ingest time and again as a last line of defence in the
exporter.

Only high-confidence patterns are included: matching a real secret is more
important than catching every possible one, but false positives that redact
legitimate documentation are worse than a rare miss. Every pattern here has a
distinctive prefix or structure (AKIA…, AIza…, PEM blocks, JWT tri-segments)
or is gated behind an explicit assignment keyword with placeholder filtering.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Minimum length for a credential value to be considered "real" rather than a
# short flag or enum. Placeholders below this never fire.
_MIN_VALUE_LEN = 8


def _marker(kind: str) -> str:
    """Build the redaction placeholder for a given finding kind."""
    return f"«REDACTED:{kind}»"


# --- High-confidence structural secrets -----------------------------------
# Each entry: (kind, compiled_pattern). These replace the entire match with a
# marker because the full match is the secret.
_AWS_ACCESS_KEY = re.compile(r"AKIA[0-9A-Z]{16}")
_GOOGLE_API_KEY = re.compile(r"AIza[0-9A-Za-z_\-]{35}")
_JWT = re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")
# Private-key blocks span multiple lines; DOTALL lets ``.`` cross newlines.
_PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)

_STRUCTURAL_PATTERNS: list[tuple[str, re.Pattern]] = [
    # Private keys first: their base64 body must be swallowed whole before any
    # sub-pattern nibbles at it.
    ("private-key", _PRIVATE_KEY),
    ("jwt", _JWT),
    ("aws-access-key", _AWS_ACCESS_KEY),
    ("google-api-key", _GOOGLE_API_KEY),
]

# --- URL credentials -------------------------------------------------------
# Redact only the password segment of ``scheme://user:password@host`` so the
# rest of the (often useful) URL survives.
_URL_CREDENTIALS = re.compile(r"(://[^/\s:@]+:)(?P<pw>[^/\s:@]+)(@)")

# --- Generic assignment credentials ----------------------------------------
# ``password = "...."``, ``api_key: ...`` etc. Gated behind an explicit keyword
# and a length floor, with placeholder filtering to avoid redacting docs.
_GENERIC_CREDENTIAL = re.compile(
    r"(?P<key>password|passwd|secret|token|api_key|apikey|access_key)"
    r"(?P<sep>\s*[:=]\s*)"
    r"(?P<quote>[\"']?)"
    r"(?P<val>[^\s\"']{" + str(_MIN_VALUE_LEN) + r",})"
    r"(?P=quote)",
    re.IGNORECASE,
)

# Values that are obviously placeholders / indirections, not real secrets.
# «REDACTED included so already-scrubbed text is idempotent: without it, the
# marker itself re-triggers detection and lint flags redacted pages forever.
_PLACEHOLDER_PREFIXES = ("${", "%%", "<", "{{", "$", "os.environ", "process.env",
                         "«REDACTED")
_PLACEHOLDER_WORDS = {"changeme", "password", "example"}

# Unquoted values shaped like code — a call or a dotted attribute path — are
# expressions (``token = fetch_token(user)``, ``key = settings.api.key``), not
# literal secrets. Redacting them mangles legitimate source pages (found by
# dogfooding on llmwiki's own repo, where ``_AWS_ACCESS_KEY = re.compile(...)``
# was scrubbed). Quoted values are always literal and stay candidates.
_CODE_EXPR = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+$")


def _is_placeholder_value(value: str) -> bool:
    """Return True when a credential value is clearly a placeholder.

    Filtering these keeps documentation, templates, and env-var indirections
    (``os.environ[...]``, ``$VAR``, ``${VAR}``, ``%%TOKEN%%``) out of the
    findings so redaction stays high-signal.
    """
    if value.startswith(_PLACEHOLDER_PREFIXES):
        return True
    if value.lower() in _PLACEHOLDER_WORDS:
        return True
    # ``xxxxxxxx``-style single-character repeats (xxxx, 0000, ****).
    if len(set(value)) == 1:
        return True
    return False


def compile_redact_patterns(patterns: list[str] | None) -> list[re.Pattern]:
    """Compile user-supplied extra redaction regexes, skipping invalid ones.

    Mirrors ``crossref.compile_custom_patterns`` so a single bad regex in
    config degrades gracefully instead of crashing ingestion.
    """
    compiled: list[re.Pattern] = []
    for raw in patterns or []:
        try:
            compiled.append(re.compile(raw))
        except re.error as e:
            logger.warning("Invalid security.redact_patterns entry %r: %s", raw, e)
    return compiled


def _apply(text: str, pattern: re.Pattern, kind: str, counts: dict[str, int], repl) -> str:
    """Apply one pattern, counting only replacements that actually fire.

    ``repl`` receives the match and returns either the replacement string or
    ``None`` to signal "not a real finding, leave untouched" (used for
    placeholder filtering).
    """
    def _sub(match: re.Match) -> str:
        replacement = repl(match)
        if replacement is None:
            return match.group(0)
        counts[kind] = counts.get(kind, 0) + 1
        return replacement

    return pattern.sub(_sub, text)


def redact_text(
    text: str,
    extra_patterns: list[re.Pattern] | None = None,
) -> tuple[str, list[dict]]:
    """Redact secrets from text.

    Returns ``(clean_text, findings)`` where ``findings`` is a list of
    ``{"kind": str, "count": int}`` aggregated per kind. Each secret match is
    replaced with ``«REDACTED:<kind>»`` (URL credentials keep everything but
    the password).
    """
    counts: dict[str, int] = {}
    clean = text

    for kind, pattern in _STRUCTURAL_PATTERNS:
        clean = _apply(clean, pattern, kind, counts, lambda m, k=kind: _marker(k))

    # URL credentials: preserve scheme://user: and @host, redact the password.
    clean = _apply(
        clean, _URL_CREDENTIALS, "url-credentials", counts,
        lambda m: m.group(1) + _marker("url-credentials") + m.group(3),
    )

    # Generic assignments: keep key+separator+quote, redact the value, unless
    # the value is a placeholder.
    def _generic_repl(match: re.Match) -> str | None:
        value = match.group("val")
        if _is_placeholder_value(value):
            return None
        if not match.group("quote") and ("(" in value or _CODE_EXPR.match(value)):
            return None
        return (
            match.group("key") + match.group("sep")
            + match.group("quote") + _marker("generic-credential") + match.group("quote")
        )

    clean = _apply(clean, _GENERIC_CREDENTIAL, "generic-credential", counts, _generic_repl)

    for pattern in extra_patterns or []:
        clean = _apply(clean, pattern, "custom", counts, lambda m: _marker("custom"))

    findings = [{"kind": kind, "count": count} for kind, count in sorted(counts.items())]
    return clean, findings


def detect_secrets(
    text: str,
    extra_patterns: list[re.Pattern] | None = None,
) -> list[dict]:
    """Detect secrets without rewriting, for lint/reporting.

    Returns the same findings list as :func:`redact_text` but discards the
    scrubbed text — used by the lint ``secret-suspect`` rule to flag wikis
    built before redaction existed.
    """
    _, findings = redact_text(text, extra_patterns=extra_patterns)
    return findings
