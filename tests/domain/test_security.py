"""
Domain Layer Test Example

This test module demonstrates testing a pure domain function that:
1. Has no external dependencies (only uses Python standard library)
2. Is deterministic (same input always produces same output pattern)
3. Has clear business rules that can be verified

Key testing concepts demonstrated:
- Pure unit testing (no mocks needed)
- Multiple test cases for different scenarios
- Testing both valid and edge cases
- Clear test naming and documentation
"""

import string
from ispawn.domain.security import generate_password


def test_generate_password_default_length():
    """
    Test password generation with default length.

    This test verifies that:
    1. Default length is 12 characters
    2. Password contains all required character types
    3. Function works without any parameters
    """
    password = generate_password()

    # Verify length requirement
    assert len(password) == 12

    # Verify character type requirements
    # These are business rules: password must contain at least one of each type
    assert any(c in string.ascii_letters for c in password), "Missing letters"
    assert any(c in string.digits for c in password), "Missing digits"
    assert any(c in string.punctuation for c in password), (
        "Missing special chars"
    )


def test_generate_password_custom_length():
    """
    Test password generation with custom length.

    This test verifies that:
    1. Custom length is respected
    2. All character type requirements are still met
    3. Function works with explicit parameters
    """
    test_length = 16  # Arbitrary length for testing
    password = generate_password(test_length)

    # Verify custom length
    assert len(password) == test_length

    # Verify character requirements still met with custom length
    assert any(c in string.ascii_letters for c in password), "Missing letters"
    assert any(c in string.digits for c in password), "Missing digits"
    assert any(c in string.punctuation for c in password), (
        "Missing special chars"
    )


def test_generate_password_minimum_requirements():
    """
    Test password meets minimum requirements.

    This test verifies edge cases:
    1. Minimum possible length (3 chars for one of each type)
    2. All requirements still met at minimum length
    3. Function handles edge case correctly
    """
    min_length = 3  # Minimum possible: 1 letter + 1 digit + 1 special
    password = generate_password(min_length)

    # Verify minimum length
    assert len(password) == min_length

    # Verify all requirements still met at minimum length
    assert any(c in string.ascii_letters for c in password), "Missing letters"
    assert any(c in string.digits for c in password), "Missing digits"
    assert any(c in string.punctuation for c in password), (
        "Missing special chars"
    )
