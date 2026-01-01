# https://dev.to/aws-heroes/hands-on-with-aws-lambda-durable-functions-callback-lets-build-series-4agd
# boto3==1.42.13
# botocore==1.42.13
#
import boto3
import json
from botocore.exceptions import ClientError
print(boto3.__version__)

client = boto3.client('lambda')

approval_ok ="Approved"
approval_ng ="Rejected"

def lambda_handler(event, context):
    callback_id = event["callback_id"]
    #callback_id = "Ab9hZXiMYXJuOmF3czpsYW1iZGE6dXMtZWFzdC0yOjMzMDE3NDM4MTkyOTpmdW5jdGlvbjpkZW1vLWR1cmFibGUtZnVuY3Rpb246JExBVEVTVC9kdXJhYmxlLWV4ZWN1dGlvbi90ZXN0MTU1Mi84ZmZkYjY0Ny0wNjkyLTNkOGUtYjg2Mi1jNWNlZDY1OTY3YWVhaXgkZGFlMmY3MDUtZjQwNy00NmQwLTk4YjYtODZjMjMxYzQxNjFk/w"

    try:
        client.send_durable_execution_callback_success(
            CallbackId=callback_id,
            Result=approval_ok
        )
    except ClientError as e:
        # Notify failure
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }
    return {
        "statusCode": 200,
        "message": "Callback Sent"
    }