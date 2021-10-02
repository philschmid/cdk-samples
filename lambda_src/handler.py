import os
import boto3
import json

client = boto3.client("sagemaker-runtime")

ENDPOINT_NAME = os.environ.get("ENDPOINT_NAME", None)


def proxy(event, context):
    if ENDPOINT_NAME is None:
        return {"error": "Environment variable `ENDPOINT_NAME` not defined"}
    try:
        response = client.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType="application/json",
            Accept="application/json",
            Body=event["body"],
        )
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": response["Body"].read().decode(),
        }
    except Exception as e:
        print(repr(e))
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": json.dumps({"error": repr(e)}),
        }
    # return {
    #     'statusCode': 200,
    #     'body': json.loads(response['Body'].read())
    # }
