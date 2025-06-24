import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("TABLE_NAME")
WS_ENDPOINT = os.environ.get("WS_ENDPOINT")

dynamo_db = boto3.client('dynamodb')
api_gateway_mngmt = boto3.client('apigatewaymanagementapi', endpoint_url=WS_ENDPOINT)

def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    try:
        json_body = event.get("body")
        if not json_body:
            logger.warning("Empty body.")
            return {
                'statusCode': 400, 'body': 'Empty request body'
            }

        body = json.loads(json_body)
        sessions = body.get("sessions", [])

        if not sessions:
            logger.warning("No sessions provided.")
            return {
                'statusCode': 400, 'body': 'Missing sessions'
            }

        logger.info("Querying DB for sessions: %s", sessions)

        session_keys = [{"session_id": {"S": session}} for session in sessions]
        logger.info("Session key list: %s", session_keys)

        response = dynamo_db.batch_get_item(
            RequestItems={
                TABLE_NAME: {
                    'Keys': session_keys
                }
            }
        )

        items = response.get("Responses", {}).get(TABLE_NAME, [])
        logger.info("DB response - connections found: %d", len(items))

        # Remove "sessions" antes de enviar a mensagem
        body.pop("sessions", None)

        for item in items:
            connection_id = item["connection_id"]["S"]

            try:
                logger.info("Sending message to connection_id: %s", connection_id)

                api_gateway_mngmt.post_to_connection(
                    Data=json.dumps(body).encode("utf-8"),
                    ConnectionId=connection_id
                )

                logger.info("Message sent to %s", connection_id)

            except api_gateway_mngmt.exceptions.GoneException:
                logger.warning("Stale connection %s, removing from table", connection_id)
                dynamo_db.delete_item(
                    TableName=TABLE_NAME,
                    Key={"connection_id": {"S": connection_id}}
                )
            except Exception as e:
                logger.exception("Error sending message to %s: %s", connection_id, str(e))

        logger.info("Message broadcast complete")
        return {
            'statusCode': 200
        }

    except Exception as e:
        logger.exception("Unhandled error during message broadcast")
        return {
            'statusCode': 500, 'body': str(e)
        }
