import os
import subprocess
from pathlib import Path
from ispawn.domain.exceptions import CertificateError

class CertificateService:
    """Service for managing SSL certificates."""

    def setup_local_certificates(self, domain: str, cert_dir: Path) -> None:
        """Setup local development certificates using mkcert.
        
        This operation requires:
        - Root access (sudo)
        - apt/dnf package manager
        - Internet access for package installation
        
        Args:
            domain: Domain name for certificates
            cert_dir: Directory to store certificates
            
        Raises:
            CertificateError: If certificate setup fails
        """
        # Check if mkcert is installed
        try:
            subprocess.run(["which", "mkcert"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            raise CertificateError("mkcert is not installed. Please install it first.")
        
        # Install root CA
        print("Installing root CA...")
        try:
            subprocess.run(
                ["mkcert", "-install"],
                check=True, capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise CertificateError(f"Failed to install root CA: {e.stderr.decode()}")
        
        # Create certificate directory
        cert_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate wildcard certificate
        domains = [
            f"*.{domain}",  # Wildcard for all subdomains
            domain,         # Base domain
            "localhost"     # Local development
        ]
        
        cert_path = cert_dir / "cert.pem"
        key_path = cert_dir / "key.pem"
        
        try:
            subprocess.run(
                ["mkcert", "-cert-file", cert_path, "-key-file", key_path, *domains],
                check=True, capture_output=True,
                cwd=cert_dir
            )
        except subprocess.CalledProcessError as e:
            raise CertificateError(f"Failed to generate certificates: {e.stderr.decode()}")
        
        # Set permissions
        for path in [cert_path, key_path]:
            os.chmod(path, 0o600)
        
        # Verify certificates
        self._verify_certificates(cert_dir)

    def _verify_certificates(self, cert_dir: Path) -> None:
        """Verify certificate validity using openssl."""
        cert_path = cert_dir / "cert.pem"
        key_path = cert_dir / "key.pem"
        
        try:
            # Verify certificate
            subprocess.run(
                ["openssl", "x509", "-in", cert_path, "-text", "-noout"],
                check=True, capture_output=True
            )
            
            # Verify private key
            subprocess.run(
                ["openssl", "rsa", "-in", key_path, "-check", "-noout"],
                check=True, capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise CertificateError(f"Certificate validation failed: {e.stderr.decode()}")

    def setup_remote_certificates(self, cert_dir: Path, email: str = None) -> None:
        """Setup remote certificates directory.
        
        For Let's Encrypt certificates, this is an integration-only operation that requires:
        - Public domain with DNS access
        - Port 80/443 access
        - Root access
        
        This method only creates the directory with proper permissions.
        Actual certificate generation must be done in an integration environment.
        
        Args:
            cert_dir: Directory for storing certificates
            email: Email for Let's Encrypt registration (required for Let's Encrypt)
        """
        # Create certificate directory
        cert_dir.mkdir(parents=True, exist_ok=True)
        
        # Set directory permissions
        os.chmod(cert_dir, 0o700)

    def validate_certificates(self, cert_dir: Path) -> None:
        """Validate that certificate files exist.
        
        Full certificate validation requires openssl and should be done
        in integration tests.
        
        Args:
            cert_dir: Directory containing certificates
            
        Raises:
            CertificateError: If certificate files are missing
        """
        cert_path = cert_dir / "cert.pem"
        key_path = cert_dir / "key.pem"
        
        if not cert_path.exists():
            raise CertificateError("Certificate file (cert.pem) not found")
        if not key_path.exists():
            raise CertificateError("Private key file (key.pem) not found")
