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

        huggingface_model = self.node.try_get_context("model")
        model_data = self.node.try_get_context("model_data") or None
        huggingface_task = self.node.try_get_context("task") or "text-classification"
        execution_role = self.node.try_get_context("role")
        instance_type = self.node.try_get_context("instance_type") or "ml.m5.xlarge"

        ##############################
        #      Stack Variables      #
        ##############################

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
            model_data=model_data,
            huggingface_task=huggingface_task,
            execution_role_arn=execution_role_arn,
            instance_type=instance_type,
            **kwargs,
        )

        ##############################
        #         API Gateway        #
        ##############################

        # create IAM Role to invoke sagemaker endpoint

        credentials_role = iam.Role(self, "Role", assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"))

        credentials_role.attach_inline_policy(
            iam.Policy(
                self,
                "InvokeEndpoint",
                statements=[
                    iam.PolicyStatement(
                        actions=[
                            "sagemaker:InvokeEndpoint",
                        ],
                        resources=[
                            f"arn:aws:sagemaker:{self.region}:{self.account}:endpoint/{endpoint.endpoint_name.lower()}",
                        ],
                    )
                ],
            )
        )

        # create api gateway
        api = _apigw.RestApi(
            self,
            "api",
            rest_api_name=f"{endpoint.endpoint_name}-api",
            deploy_options=_apigw.StageOptions(
                stage_name="prod",
                caching_enabled=True,
                cache_ttl=cdk.Duration.minutes(60),
                cache_cluster_enabled=True,
                # cache_cluster_size="1.0",
            ),
        )

        # create /model_name route
        endpoint_gateway = api.root.add_resource(endpoint.model_name)

        # enable cors for POST
        endpoint_gateway.add_cors_preflight(allow_origins=["*"], allow_methods=["POST"])

        # add sagemaker integration
        endpoint_gateway.add_method(
            "POST",
            _apigw.AwsIntegration(
                service="runtime.sagemaker",
                path=f"endpoints/{endpoint.endpoint_name}/invocations",
                options=_apigw.IntegrationOptions(
                    # add mapped body to integration header
                    # https://www.serverless.com/plugins/serverless-api-gateway-caching
                    cache_key_parameters=["integration.request.header.bodyValue"],
                    request_parameters={"integration.request.header.bodyValue": "method.request.body"},
                    credentials_role=credentials_role,
                    integration_responses=[
                        _apigw.IntegrationResponse(
                            status_code="200",
                        )
                    ],
                ),
            ),
            method_responses=[_apigw.MethodResponse(status_code="200")],
        )

        # output url
        cdk.CfnOutput(self, "SageMakerEndpointUrl", value=api.url_for_path(endpoint_gateway.path))
