class AzureKeyVaultClient:
    """A reusable client for interacting with Azure Key Valut."""
    @staticmethod
    def fetch_parameter(parameter_name, region_name="australiasoutheast", with_decryption=True):
        return None