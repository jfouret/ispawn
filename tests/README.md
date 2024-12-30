# Testing Strategy

## Overview

The test suite is organized to match the project's layered architecture:

```
tests/
├── domain/         # Domain model tests
├── services/       # Service layer tests
├── commands/       # Command layer tests
└── e2e/           # End-to-end workflow tests
```

## Test Types

### Domain Tests

Domain tests focus on business logic and are pure unit tests:
- No external dependencies
- No file system access
- No network calls
- Fast execution

Example from `test_security.py`:
```python
def test_generate_password_default_length():
    """Test password generation with default length."""
    password = generate_password()
    
    # Check default length
    assert len(password) == 12
    
    # Check character types
    assert any(c in string.ascii_letters for c in password)
    assert any(c in string.digits for c in password)
    assert any(c in string.punctuation for c in password)
```

### Service Tests

Service tests combine unit tests and integration tests:

1. Unit Tests with Mocking:
   ```python
   @patch('subprocess.run')  # Mock external command
   def test_setup_local_certificates_mkcert_not_installed(mock_run):
       mock_run.side_effect = subprocess.CalledProcessError(1, ["which", "mkcert"])
       
       with pytest.raises(CertificateError, match="mkcert is not installed"):
           cert_service.setup_local_certificates("test.local", cert_dir)
   ```

2. Integration Tests:
   ```python
   @pytest.mark.skipif(
       subprocess.run(["which", "mkcert"], capture_output=True).returncode != 0,
       reason="mkcert is not installed"
   )
   def test_setup_local_certificates_with_mkcert():
       """Only runs if mkcert is installed."""
       cert_service.setup_local_certificates("test.local", cert_dir)
       assert (cert_dir / "cert.pem").exists()
   ```

## Key Testing Concepts

### Fixtures

Fixtures provide reusable test setup:
```python
@pytest.fixture
def cert_dir(tmp_path):
    """Create a temporary directory for certificates."""
    cert_dir = tmp_path / "certs"
    cert_dir.mkdir()
    return cert_dir
```

### Mocking

Mock external dependencies for unit tests:
```python
@patch('docker.from_env')  # Mock Docker client
def test_create_network(mock_client):
    mock_client.return_value.networks.create = Mock()
    docker_service.create_network("test-net")
```

### Test Markers

Mark tests for special handling:
```python
@pytest.mark.integration  # Mark as integration test
@pytest.mark.skipif(    # Skip if condition met
    os.geteuid() != 0,
    reason="Requires root access"
)
def test_setup_certificates(): ...
```

### Temporary Files

Use pytest's `tmp_path` for file operations:
```python
def test_with_files(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    assert test_file.exists()
```

## Running Tests

1. All tests:
   ```bash
   pytest
   ```

2. Specific module:
   ```bash
   pytest tests/domain/test_container.py
   ```

3. With coverage:
   ```bash
   pytest --cov=ispawn
   ```

4. Skip integration tests:
   ```bash
   pytest -m "not integration"
   ```

## Test Organization Guidelines

1. **Test File Structure**
   - Match source file structure
   - Use descriptive test names
   - Group related tests in classes

2. **Test Independence**
   - Each test should be independent
   - Use fixtures for setup/teardown
   - Clean up resources after tests

3. **Test Coverage**
   - Aim for high coverage in domain layer
   - Mock external dependencies in service layer
   - Focus on critical paths in command layer

4. **Integration Tests**
   - Mark with `@pytest.mark.integration`
   - Document requirements (e.g., "requires root")
   - Handle cleanup properly
