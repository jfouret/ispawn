"""Tests for configuration manager."""

import pytest
from pathlib import Path
from unittest.mock import patch

from ispawn.domain.proxy import ProxyConfig, ProxyMode, InstallMode
from ispawn.domain.exceptions import ConfigurationError
from ispawn.services.config import ConfigManager

TEST_CONFIGS = [
    pytest.param(
        {
            "config": {
                "install_mode": InstallMode.USER.value,
                "mode": ProxyMode.LOCAL.value,
                "domain": "test.localhost",
                "subnet": "172.31.0.0/24",
                "name": "test-proxy-1",
                "cert_mode": None,
                "cert_dir": None,  # Will be set to tmp_path/certs
                "email": None,
            },
            "force": False,
            "should_succeed": True,
            "description": "Fresh config creation (user mode)",
        },
        id="user-config",
    ),
    pytest.param(
        {
            "config": {
                "install_mode": InstallMode.SYSTEM.value,
                "mode": ProxyMode.LOCAL.value,
                "domain": "test.localhost",
                "subnet": "172.32.0.0/24",
                "name": "test-proxy-2",
                "cert_mode": None,
                "cert_dir": None,  # Will be set to tmp_path/etc/ispawn/certs
                "email": None,
            },
            "force": False,
            "should_succeed": True,
            "description": "System-wide installation (with root)",
        },
        id="system-config-root",
    ),
    pytest.param(
        {
            "config": {
                "install_mode": InstallMode.SYSTEM.value,
                "mode": ProxyMode.LOCAL.value,
                "domain": "test.localhost",
                "subnet": "172.33.0.0/24",
                "name": "test-proxy-3",
                "cert_mode": None,
                "cert_dir": None,
                "email": None,
            },
            "force": False,
            "should_succeed": False,  # Should fail without root
            "description": "System-wide installation (without root)",
        },
        id="system-config-no-root",
    ),
    pytest.param(
        {
            "config": {
                "install_mode": InstallMode.USER.value,
                "mode": ProxyMode.LOCAL.value,
                "domain": "test.localhost",
                "subnet": "172.34.0.0/24",
                "name": "test-proxy-4",  # Different name
                "cert_mode": None,
                "cert_dir": None,
                "email": None,
            },
            "force": False,
            "should_succeed": False,  # Should fail with existing different config
            "description": "Existing config conflict",
            "existing_config": {  # Config to pre-create
                "install_mode": InstallMode.USER.value,
                "mode": ProxyMode.LOCAL.value,
                "domain": "test.localhost",
                "subnet": "172.34.0.0/24",
                "name": "test-proxy-existing",  # Different name
                "cert_mode": None,
                "cert_dir": None,
                "email": None,
            },
        },
        id="existing-config-conflict",
    ),
    pytest.param(
        {
            "config": {
                "install_mode": InstallMode.USER.value,
                "mode": ProxyMode.LOCAL.value,
                "domain": "test.localhost",
                "subnet": "172.35.0.0/24",
                "name": "test-proxy-5",
                "cert_mode": None,
                "cert_dir": None,
                "email": None,
            },
            "force": True,  # Force overwrite
            "should_succeed": True,
            "description": "Force overwrite existing config",
            "existing_config": {
                "install_mode": InstallMode.USER.value,
                "mode": ProxyMode.LOCAL.value,
                "domain": "test.localhost",
                "subnet": "172.35.0.0/24",
                "name": "test-proxy-existing",
                "cert_mode": None,
                "cert_dir": None,
                "email": None,
            },
        },
        id="force-overwrite-existing",
    ),
]


def _run_config_test(proxy_config, test_case, is_system):
    """Run the actual config test with proper mocking."""
    # Initialize and apply config
    manager = ConfigManager(proxy_config, force=test_case["force"])
    manager.apply_config()

    # Verify config was applied
    config_path = Path(proxy_config.config_path)
    compose_path = Path(manager.compose_path)
    traefik_path = Path(manager.traefik_config_path)

    assert config_path.exists(), "Config file not created"
    assert compose_path.exists(), "Compose file not created"
    assert traefik_path.exists(), "Traefik config not created"

    # Verify system-specific requirements
    if is_system:
        # Check file permissions
        assert oct(config_path.stat().st_mode)[-3:] == "644", (
            "Wrong config file permissions"
        )
        # Note: can't check root ownership in tests as we're mocking root
    else:
        assert oct(config_path.stat().st_mode)[-3:] == "600", (
            "Wrong config file permissions"
        )

    if not test_case["should_succeed"]:
        pytest.fail("Expected failure but operation succeeded")

    # Clean up Docker resources
    manager.remove_config()


def _setup_existing_config(tmp_path, config_params, cert_dir):
    """Setup pre-existing config if specified in test case."""
    if not config_params:
        return

    config_params = config_params.copy()
    config_params["cert_dir"] = str(cert_dir)
    existing_config = ProxyConfig(**config_params)

    # Create config file
    config_dir = Path(existing_config.config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)

    with open(existing_config.config_path, "w") as f:
        existing_config.to_yaml(f)


@pytest.mark.parametrize("test_case", TEST_CONFIGS)
def test_config_manager(tmp_path, test_case):
    """Test ConfigManager's core functionality."""
    # Setup directories
    is_system = test_case["config"]["install_mode"] == InstallMode.SYSTEM.value

    if is_system:
        # For system mode, setup mock system dir
        system_dir = tmp_path / "system"
        cert_dir = system_dir / "certs"
    else:
        # For user mode, use ~/.ispawn
        cert_dir = tmp_path / "certs"

    # Update cert_dir in config
    config_params = test_case["config"].copy()
    config_params["cert_dir"] = str(cert_dir)

    # Create proxy config
    proxy_config = ProxyConfig(**config_params)

    # Mock home directory for all tests
    with patch("pathlib.Path.home", return_value=tmp_path):
        # Setup any pre-existing config
        if "existing_config" in test_case:
            _setup_existing_config(
                tmp_path, test_case["existing_config"], cert_dir
            )

        # Additional mocks for system mode
        if is_system:
            # Only mock root for tests that should have root access
            geteuid_value = 0 if test_case["should_succeed"] else 1000
            with (
                patch("os.geteuid", return_value=geteuid_value),
                patch("os.chown", return_value=None),
                patch(
                    "ispawn.domain.proxy.ProxyConfig.get_system_dir",
                    return_value=str(system_dir),
                ),
            ):
                try:
                    _run_config_test(proxy_config, test_case, is_system)
                except ConfigurationError:
                    if test_case["should_succeed"]:
                        raise
        else:
            try:
                _run_config_test(proxy_config, test_case, is_system)
            except ConfigurationError:
                if test_case["should_succeed"]:
                    raise
