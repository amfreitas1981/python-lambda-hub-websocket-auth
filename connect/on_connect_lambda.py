import json
import boto3
import os
import logging
import hmac
import hashlib
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.client('dynamodb')
secrets_client = boto3.client('secretsmanager')
table_name = os.environ.get("TABLE_NAME")
secret_name = os.environ.get("SIGNING_SECRET_NAME")
region = os.environ.get("AWS_REGION")
# region = os.environ.get("AWS_REGION", "us-east-1")

MAX_SKEW_MINUTES = 5  # tolerância de tempo


def get_secret():
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return response["SecretString"]
    except Exception as e:
        logger.error(f"Failed to retrieve secret from Secrets Manager: {e}")
        raise


def is_valid_datetime(timestamp_str):
    try:
        request_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = abs((now - request_time).total_seconds()) / 60
        return delta <= MAX_SKEW_MINUTES
    except Exception as e:
        logger.warning(f"Invalid timestamp format: {e}")
        return False


def lambda_handler(event, context):
    logger.info(f"Connection event received: {json.dumps(event)}")

    try:
        headers = event.get("headers", {})
        session_id = headers.get("X-Session")
        date_time = headers.get("X-Date-Time")
        signature = headers.get("X-Signature")

        if not session_id or not date_time or not signature:
            logger.warning("Missing one or more required signature headers")
            return {
                'statusCode': 400, 'body': 'Missing required headers'
            }

        if not is_valid_datetime(date_time):
            logger.warning("Timestamp outside acceptable range")
            return {
                'statusCode': 403, 'body': 'Invalid or expired timestamp'
            }

        secret_key = get_secret()

        data_to_sign = f"{session_id}:{date_time}".encode("utf-8")
        expected_signature = hmac.new(
            secret_key.encode("utf-8"),
            data_to_sign,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("Invalid signature provided")
            return {
                'statusCode': 403, 'body': 'Unauthorized'
            }

        connection_id = event["requestContext"]["connectionId"]

        dynamodb.put_item(
            TableName=table_name,
            Item={
                'session_id': {'S': session_id},
                'connection_id': {'S': connection_id}
            }
        )

        logger.info(f"Session {session_id} authorized and connection {connection_id} stored")
        return {
            'statusCode': 200, 'body': 'Connection accepted'
        }

    except Exception as e:
        logger.error(f"Unexpected error in connect handler: {e}")
        return {
            'statusCode': 500, 'body': 'Internal server error'
        }
