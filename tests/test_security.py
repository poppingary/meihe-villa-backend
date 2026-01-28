"""Tests for core security functions."""

import pytest
from datetime import timedelta

from app.core.security import (
    create_access_token,
    verify_token,
    verify_password,
    get_password_hash,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_get_password_hash_returns_hashed_value(self):
        """Test that password hashing returns a different value."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_different_passwords_produce_different_hashes(self):
        """Test that different passwords produce different hashes."""
        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password2")
        assert hash1 != hash2

    def test_same_password_produces_different_hashes(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # Both should verify correctly but be different due to salt
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Tests for JWT token functions."""

    def test_create_access_token_returns_string(self):
        """Test that token creation returns a string."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_valid(self):
        """Test verification of a valid token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"

    def test_verify_token_invalid(self):
        """Test verification of an invalid token."""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)
        assert payload is None

    def test_verify_token_empty(self):
        """Test verification of an empty token."""
        payload = verify_token("")
        assert payload is None

    def test_create_token_with_custom_expiry(self):
        """Test token creation with custom expiry."""
        data = {"sub": "user123"}
        expires = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires)
        payload = verify_token(token)
        assert payload is not None
        assert "exp" in payload

    def test_token_contains_exp_claim(self):
        """Test that token contains expiration claim."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload is not None
        assert "exp" in payload
