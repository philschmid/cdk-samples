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


def get_image_uri(
    region=None,
    transformmers_version=LATEST_TRANSFORMERS_VERSION,
    pytorch_version=LATEST_PYTORCH_VERSION,
    use_gpu=False,
):
    repository = f"{region_dict[region]}.dkr.ecr.{region}.amazonaws.com/huggingface-pytorch-inference"
    tag = f"{pytorch_version}-transformers{transformmers_version}-{'gpu-py36-cu111' if use_gpu == True else 'cpu-py36'}-ubuntu18.04"
    return f"{repository}:{tag}"


def is_gpu_instance(instance_type):
    return True if instance_type.split(".")[1][0].lower() in ["p", "g"] else False


class HuggingfaceSagemaker(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ##############################
        #      Context Parameter     #
        ##############################

        huggingface_model = self.node.try_get_context("model")
        huggingface_task = self.node.try_get_context("task")
        instance_type = self.node.try_get_context("instance_type") or "ml.m5.xlarge"
        execution_role = self.node.try_get_context("role")

        if huggingface_model is None and huggingface_task is None:
            raise ValueError(
                "You need to define `model` and `task` in your context, "
                'e.g. `-c model="distilbert-base-uncased-finetuned-sst-2-english"  -c task="text-classification"`',
            )

        ##############################
        #      Stack Variables      #
        ##############################

        lambda_handler_path = os.path.join(os.getcwd(), "lambda_src")
        model_name = f'model-{huggingface_model.replace("_","-").replace("/","--")}'
        endpoint_config_name = f'config-{huggingface_model.replace("_","-").replace("/","--")}'
        endpoint_name = f'endpoint-{huggingface_model.replace("_","-").replace("/","--")}'

        # creates the image_uir based on the instance type and region
        use_gpu = is_gpu_instance(instance_type)
        image_uri = get_image_uri(region=self.region, use_gpu=use_gpu)

        # creates new iam role for sagemaker using `iam_sagemaker_actions` as permissions or uses provided arn
        if execution_role is None:
            execution_role = iam.Role(
                self, "hf_sagemaker_execution_role", assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com")
            )
            execution_role.add_to_policy(iam.PolicyStatement(resources=["*"], actions=iam_sagemaker_actions))
            execution_role_arn = execution_role.role_arn
        else:
            execution_role_arn = execution_role

        # defines and creates container configuration for deployment
        container_environment = {"HF_MODEL_ID": huggingface_model, "HF_TASK": huggingface_task}
        container = sagemaker.CfnModel.ContainerDefinitionProperty(environment=container_environment, image=image_uri)

        # creates SageMaker Model Instance
        model = sagemaker.CfnModel(
            self,
            "hf_model",
            execution_role_arn=execution_role_arn,
            primary_container=container,
            model_name=model_name,
        )

        # Creates SageMaker Endpoint configurations
        endpoint_configuration = sagemaker.CfnEndpointConfig(
            self,
            "hf_endpoint_config",
            endpoint_config_name=endpoint_config_name,
            production_variants=[
                sagemaker.CfnEndpointConfig.ProductionVariantProperty(
                    initial_instance_count=1,
                    instance_type=instance_type,
                    model_name=model.model_name,
                    initial_variant_weight=1.0,
                    variant_name=model.model_name,
                )
            ],
        )
        # Creates Real-Time Endpoint
        self.endpoint = sagemaker.CfnEndpoint(
            self,
            "hf_endpoint",
            endpoint_name=endpoint_name,
            endpoint_config_name=endpoint_configuration.endpoint_config_name,
        )

        # adds depends on for different resources
        endpoint_configuration.node.add_dependency(model)
        self.endpoint.node.add_dependency(endpoint_configuration)
