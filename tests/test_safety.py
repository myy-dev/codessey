import pytest

from ai_gitgen.safety import mask, sensitive_path


@pytest.mark.parametrize(
    "secret",
    [
        "sk-proj-" + "SYNTHETIC123" * 4,
        "ghp_" + "f" * 36,
        "github_pat_" + "f" * 40,
        "AKIA" + "A" * 16,
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJkZW1vIn0.signature",
        "xoxb-1234567890-synthetic",
        "person@example.com",
        "Bearer fake-example-value",
        "Basic dXNlcjpwYXNz",
    ],
)
def test_known_patterns(secret):
    assert secret not in mask(f"before {secret} after")
    assert "[REDACTED]" in mask(secret)


@pytest.mark.parametrize(
    "assignment",
    [
        'API_KEY="fake-sensitive"',
        "password = 'fake-sensitive'",
        '"client_secret": "fake-sensitive"',
        "access_token: fake-sensitive",
        "DATABASE_PASSWORD=fake-sensitive",
        "api-key: fake-sensitive",
    ],
)
def test_assignments(assignment):
    assert "fake-sensitive" not in mask(assignment)


def test_url_credentials_and_multiline_private_key():
    assert "hunter2" not in mask("postgres://user:hunter2@host/db")
    assert "secretdata" not in mask(
        "+-----BEGIN PRIVATE KEY-----\n+secretdata\n+-----END PRIVATE KEY-----"
    )


def test_terminal_controls_and_actual_key_always_removed():
    value = "hi\x1b[31mred\x1b[0m\x1b]52;c;payload\x07\u202esecret\x00\nend"
    cleaned = mask(value, "secret", patterns=False)
    assert "\x1b" not in cleaned
    assert "\u202e" not in cleaned
    assert "payload" not in cleaned
    assert "secret" not in cleaned
    assert "\nend" in cleaned


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        ".env.local",
        "nested/.env.prod",
        "keys/id_rsa",
        ".aws/credentials",
        "server.key",
        "config/credentials.json",
        "a/.ssh/config",
        "C:\\repo\\key.pem",
    ],
)
def test_sensitive_paths(path):
    assert sensitive_path(path)


def test_safe_source_path():
    assert not sensitive_path("ai_gitgen/safety.py")
