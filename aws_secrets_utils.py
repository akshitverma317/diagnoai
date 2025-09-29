import boto3
import json

def get_secret(secret_name, region_name="ap-south-1"):
    """
    Retrieve a secret from AWS Secrets Manager.
    
    :param secret_name: Name of the secret in AWS Secrets Manager
    :param region_name: AWS region where the secret is stored
    :return: Dictionary of secret key-value pairs
    """
    try:
        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        # Retrieve the secret
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        
        # Depending on which type of secret, parse accordingly
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return json.loads(secret)
        else:
            # For binary secrets (less common)
            decoded_binary_secret = get_secret_value_response['SecretBinary'].decode('utf-8')
            return json.loads(decoded_binary_secret)
    
    except Exception as e:
        print(f"Error retrieving secret {secret_name}: {str(e)}")
        raise
