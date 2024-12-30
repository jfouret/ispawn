import pytest
import time
import requests
from pathlib import Path
import docker
import subprocess
import os
import tempfile
import yaml
from typing import Generator

from ispawn.config import Config, Mode, CertMode

def run_cli_command(command: str) -> subprocess.CompletedProcess:
    """Run an ispawn CLI command."""
    return subprocess.run(
        f"ispawn {command}",
        shell=True,
        capture_output=True,
        text=True,
        check=True
    )

@pytest.fixture(scope="module")
def temp_config() -> Generator[Path, None, None]:
    """Create temporary configuration for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "ispawn"
        config_dir.mkdir()
        config_file = config_dir / "config.yml"
        
        # Create test configuration
        config = {
            "name": "ispawn-test",
            "web": {
                "domain": "test.localhost",
                "subnet": "172.30.0.0/24",
                "mode": Mode.LOCAL.value,
                "ssl": {
                    "cert_mode": CertMode.PROVIDED.value,
                    "cert_dir": str(config_dir / "certs")
                }
            },
            "logs": {
                "dir": str(config_dir / "logs")
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        yield config_file

@pytest.mark.e2e
class TestWorkflow:
    """End-to-end workflow tests."""
    
    def test_local_workflow(self, temp_config):
        """Test local workflow with mkcert certificates."""
        try:
            # 1. Setup environment
            print("Setting up environment...")
            run_cli_command(f"setup --config {temp_config} --mode local")
            
            # 2. Build test image
            print("Building test image...")
            run_cli_command(
                f"image build --config {temp_config} "
                "--base ubuntu:20.04 "
                "--name test "
                "--service jupyter"
            )
            
            # 3. Run container
            print("Running container...")
            result = run_cli_command(
                f"run --config {temp_config} "
                "--name test-e2e "
                "--image ispawn-test-ubuntu:20.04 "
                "--service jupyter"
            )
            
            # 4. Wait for services to start
            print("Waiting for services to start...")
            time.sleep(10)
            
            # 5. List containers to verify
            result = run_cli_command(f"list --config {temp_config}")
            assert "test-e2e" in result.stdout
            assert "running" in result.stdout
            
            # 6. Check logs
            result = run_cli_command(f"logs --config {temp_config} test-e2e")
            assert "Jupyter" in result.stdout
            
            # 7. Cleanup
            print("Cleaning up...")
            run_cli_command(f"image remove --config {temp_config} ispawn-test-ubuntu:20.04")
            
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Local workflow test failed:\nCommand: {e.cmd}\nOutput:\n{e.output}")

    @pytest.mark.skipif(not os.path.exists("/etc/hosts"),
                       reason="Requires /etc/hosts file")
    def test_remote_workflow(self, temp_config):
        """Test remote workflow with provided certificates."""
        try:
            # 1. Setup environment
            print("Setting up environment...")
            run_cli_command(
                f"setup --config {temp_config} "
                "--mode remote "
                "--cert-mode provided "
                "--domain test.example.com"
            )
            
            # 2. Build test image
            print("Building test image...")
            run_cli_command(
                f"image build --config {temp_config} "
                "--base ubuntu:20.04 "
                "--name test "
                "--service jupyter"
            )
            
            # 3. Run container
            print("Running container...")
            run_cli_command(
                f"run --config {temp_config} "
                "--name test-e2e "
                "--image ispawn-test-ubuntu:20.04 "
                "--service jupyter"
            )
            
            # 4. Wait for services to start
            print("Waiting for services to start...")
            time.sleep(10)
            
            # 5. List containers to verify
            result = run_cli_command(f"list --config {temp_config}")
            assert "test-e2e" in result.stdout
            assert "running" in result.stdout
            
            # 6. Check logs
            result = run_cli_command(f"logs --config {temp_config} test-e2e")
            assert "Jupyter" in result.stdout
            
            # 7. Cleanup
            print("Cleaning up...")
            run_cli_command(f"image remove --config {temp_config} ispawn-test-ubuntu:20.04")
            
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Remote workflow test failed:\nCommand: {e.cmd}\nOutput:\n{e.output}")

    def test_multiple_services(self, temp_config):
        """Test running multiple services in the same container."""
        try:
            # 1. Build test image with multiple services
            print("Building test image...")
            run_cli_command(
                f"image build --config {temp_config} "
                "--base ubuntu:20.04 "
                "--name test "
                "--service jupyter "
                "--service rstudio"
            )
            
            # 2. Run container
            print("Running container...")
            run_cli_command(
                f"run --config {temp_config} "
                "--name test-e2e "
                "--image ispawn-test-ubuntu:20.04 "
                "--service jupyter "
                "--service rstudio"
            )
            
            # 3. Wait for services to start
            print("Waiting for services to start...")
            time.sleep(10)
            
            # 4. List containers to verify
            result = run_cli_command(f"list --config {temp_config}")
            assert "test-e2e" in result.stdout
            assert "running" in result.stdout
            
            # 5. Check logs
            result = run_cli_command(f"logs --config {temp_config} test-e2e")
            assert "Jupyter" in result.stdout
            assert "RStudio" in result.stdout
            
            # 6. Cleanup
            print("Cleaning up...")
            run_cli_command(f"image remove --config {temp_config} ispawn-test-ubuntu:20.04")
            
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Multiple services test failed:\nCommand: {e.cmd}\nOutput:\n{e.output}")
