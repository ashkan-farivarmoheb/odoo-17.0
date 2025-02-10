import boto3
import logging


class AwsSsmClient:
    """A reusable client for interacting with AWS SSM Parameter Store."""

    @staticmethod
    def fetch_parameter(parameter_name, region_name="ap-southeast-2", with_decryption=True):
        """
        Fetch a parameter from AWS SSM Parameter Store.

        :param parameter_name: The name of the SSM parameter.
        :param region_name: The AWS region for the SSM client.
        :param with_decryption: Whether to decrypt the parameter value.
        :return: The parameter value.
        :raises Exception: If fetching the parameter fails.
        """
        ssm_client = boto3.client('ssm', region_name=region_name)
        try:
            response = ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=with_decryption
            )
            logging.info(f"Successfully fetched parameter '{parameter_name}' from SSM.")
            return response['Parameter']['Value']
        except Exception as e:
            logging.error(f"Error fetching parameter '{parameter_name}' from SSM: {e}")
            raise
