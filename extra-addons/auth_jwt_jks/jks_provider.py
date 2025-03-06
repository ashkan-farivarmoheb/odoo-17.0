import os
import logging
import threading
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12

from .models.aws_ssm_client import AwsSsmClient
from .models.azure_key_vault_client import AzureKeyVaultClient
from . import strtobool
_logger = logging.getLogger(__name__)

def is_true(strval):
    return bool(strtobool(strval or "0".lower()))

class JKSProvider:
    _instance = None
    _lock = threading.Lock()  # Lock for thread-safe singleton

    def __new__(cls, config):
        if cls._instance is None:
            with cls._lock:  # Ensure only one thread can create the instance
                if cls._instance is None:  # Double-check
                    cls._instance = super(JKSProvider, cls).__new__(cls)
                    cls._instance.__init__(config)  # Initialize the instance
        return cls._instance

    def __init__(self, config):
        if hasattr(self, 'initialized'):  # Prevent re-initialization
            return

        self.jks_file_path = config.get("restfull_api_jks_file")
        self.ssm_key = config.get("restfull_api_jks_password")
        self.alias = config.get("restfull_api_jks_alias")
        self.cloud_provider_enabled = config.get("cloud_provider_enabled")
        self.cloud_provider_aws_enabled = config.get("cloud_provider_aws_enabled")
        self.cloud_provider_azure_enabled = config.get("cloud_provider_azure_enabled")
        self.restfull_api_jks_password = config.get("restfull_api_jks_password")
        self.password = None

        # Automatically initialize the provider
        self.initialized = True  # Mark as initialized

    def validate(self):
        """Load the JKS file from the specified EFS path."""
        if not os.path.exists(self.jks_file_path):
            raise FileNotFoundError(f"JKS file not found at {self.jks_file_path}")

        # Here you can implement logic to use the JKS file as needed
        # For example, you can load it using a library like `pyjks` or `javapackager`
        logging.info(f"Loaded JKS file from {self.jks_file_path} with alias {self.alias}.")
        return self.jks_file_path

    def get_password(self):
         if self.password:
           return self.password

         if is_true(self.cloud_provider_enabled):
           if is_true(self.cloud_provider_aws_enabled):
             self.password = self.fetch_aws_ssm_password()
           elif is_true(self.cloud_provider_azure_enabled):
             self.password = self.fetch_azure_key_vault_password()
         else:
           self.password = self.restfull_api_jks_password

         if not self.password:
           raise ValueError("JKS Password has not set properly.")

         return self.password

    def load_private_key_from_jks(self):
        """Load the private key from a JKS file."""
        with open(self.jks_file_path, "rb") as key_file:
            p12_data = key_file.read()
            private_key, certificate, additional_certificates = self._get_private_key(p12_data)
            # Serialize the private key to PEM format
            pem_private_key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
            return pem_private_key.decode('utf-8')  # Convert bytes to string

    def load_public_key_from_jks(self):
        with open(self.jks_file_path, "rb") as key_file:
            p12_data = key_file.read()
            private_key, certificate, additional_certificates = self._get_private_key(p12_data)
            return private_key.public_key()
        print('Public key loaded successfully.')
        return public_key

    def _get_private_key(self, p12_data):
        return pkcs12.load_key_and_certificates(
            p12_data,
            self.get_password().encode(),
            backend=default_backend()
        )

    def fetch_aws_ssm_password(self):
        return AwsSsmClient.fetch_parameter(self.restfull_api_jks_password)

    def fetch_azure_key_vault_password(self):
        return AzureKeyVaultClient.fetch_parameter(self.restfull_api_jks_password)
