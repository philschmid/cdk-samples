# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import (
    aws_lambda as lambda_,
    aws_apigateway as _apigw,
    aws_iam as iam,
)
from aws_cdk import core as cdk
import os


class AwsLambda(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, sagemaker, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        ##############################
        #      Stack Variables      #
        ##############################

        endpoint = sagemaker.endpoint.endpoint_name
        print(endpoint)
        lambda_handler_path = os.path.join(os.getcwd(), "lambda_src")

        ##############################
        #       Lambda Function      #
        ##############################

        # create function
        lambda_fn = lambda_.Function(
            self,
            "sm_invoke",
            code=lambda_.Code.from_asset(lambda_handler_path),
            handler="handler.proxy",
            timeout=cdk.Duration.seconds(60),
            runtime=lambda_.Runtime.PYTHON_3_8,
            environment={"ENDPOINT_NAME": endpoint},
        )

        # add policy for invoking
        lambda_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "sagemaker:InvokeEndpoint",
                ],
                resources=[
                    f"arn:aws:sagemaker:{self.region}:{self.account}:endpoint/{endpoint}",
                ],
            )
        )

        api = _apigw.LambdaRestApi(self, "hf_api_gw", proxy=True, handler=lambda_fn)
