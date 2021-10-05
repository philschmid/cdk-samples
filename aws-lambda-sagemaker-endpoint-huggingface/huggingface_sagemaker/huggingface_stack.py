# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import (
    aws_iam as iam,
    aws_sagemaker as sagemaker,
    aws_lambda as lambda_,
    aws_apigateway as _apigw,
)
from .sagemaker_endpoint import SageMakerEndpointConstruct
from aws_cdk import core as cdk
import os
from huggingface_sagemaker.config import LATEST_PYTORCH_VERSION, LATEST_TRANSFORMERS_VERSION, region_dict

# policies based on https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-roles.html#sagemaker-roles-createmodel-perms
iam_sagemaker_actions = [
    "sagemaker:*",
    "ecr:GetDownloadUrlForLayer",
    "ecr:BatchGetImage",
    "ecr:BatchCheckLayerAvailability",
    "ecr:GetAuthorizationToken",
    "cloudwatch:PutMetricData",
    "cloudwatch:GetMetricData",
    "cloudwatch:GetMetricStatistics",
    "cloudwatch:ListMetrics",
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:DescribeLogStreams",
    "logs:PutLogEvents",
    "logs:GetLogEvents",
    "s3:CreateBucket",
    "s3:ListBucket",
    "s3:GetBucketLocation",
    "s3:GetObject",
    "s3:PutObject",
]


class HuggingfaceSagemaker(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ##############################
        #      Context Parameter     #
        ##############################

        huggingface_model = self.node.try_get_context("model") or "distilbert-base-uncased-finetuned-sst-2-english"
        huggingface_task = self.node.try_get_context("task") or "text-classification"
        instance_type = self.node.try_get_context("instance_type") or "ml.m5.xlarge"
        execution_role = self.node.try_get_context("role")

        ##############################
        #      Stack Variables      #
        ##############################

        lambda_handler_path = os.path.join(os.getcwd(), "lambda_src")

        # creates new iam role for sagemaker using `iam_sagemaker_actions` as permissions or uses provided arn
        if execution_role is None:
            execution_role = iam.Role(
                self, "hf_sagemaker_execution_role", assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com")
            )
            execution_role.add_to_policy(iam.PolicyStatement(resources=["*"], actions=iam_sagemaker_actions))
            execution_role_arn = execution_role.role_arn
        else:
            execution_role_arn = execution_role

        ##############################
        #     SageMaker Endpoint     #
        ##############################

        endpoint = SageMakerEndpointConstruct(
            self,
            "SagemakerEndpoint",
            huggingface_model=huggingface_model,
            huggingface_task=huggingface_task,
            execution_role_arn=execution_role_arn,
            instance_type=instance_type,
            **kwargs,
        )

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
            environment={"ENDPOINT_NAME": endpoint.endpoint_name},
        )

        # add policy for invoking
        lambda_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "sagemaker:InvokeEndpoint",
                ],
                resources=[
                    f"arn:aws:sagemaker:{self.region}:{self.account}:endpoint/{endpoint.endpoint_name}",
                ],
            )
        )

        api = _apigw.LambdaRestApi(self, "hf_api_gw", proxy=True, handler=lambda_fn)
