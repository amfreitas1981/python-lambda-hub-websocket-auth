import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamo_db = boto3.client('dynamodb')
TABLE_NAME = os.environ.get("TABLE_NAME")

def lambda_handler(event, context):
    logger.info("Disconnect event: %s", json.dumps(event))

    try:
        connection_id = event["requestContext"]["connectionId"]

        logger.info("Querying database to get the line to delete")
        query_result = dynamo_db.query(
            TableName='TABLE_NAME',
            IndexName='connection_id-index',
            ExpressionAttributeValues={
                ':connection_id': {
                    'S': connection_id,
                },
            },
            KeyConditionExpression=f'connection_id = :connection_id'
        )

        # Remove pelo session_id
        logger.info("Query returned the following: %s", json.dumps(query_result))
        session_id = query_result["Items"][0]["session_id"]["S"]
        logger.info("Session id is %s, DELETING", session_id)
        dynamo_db.delete_item(
            TableName=TABLE_NAME,
            Key={'session_id': {'S': session_id}}
        )

        logger.info("Deleted session_id %s", session_id)
        return {
            'statusCode': 200
        }

    except Exception as e:
        logger.exception("Error during disconnect event")
        return {
            'statusCode': 500, 'body': str(e)
        }
