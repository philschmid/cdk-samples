# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import (
    aws_sagemaker as sagemaker,
)
from aws_cdk import core as cdk
from huggingface_sagemaker.config import LATEST_PYTORCH_VERSION, LATEST_TRANSFORMERS_VERSION, region_dict


def get_image_uri(
    region=None,
    transformmers_version=LATEST_TRANSFORMERS_VERSION,
    pytorch_version=LATEST_PYTORCH_VERSION,
    use_gpu=False,
):
    repository = f"{region_dict[region]}.dkr.ecr.{region}.amazonaws.com/huggingface-pytorch-inference"
    tag = f"{pytorch_version}-transformers{transformmers_version}-{'gpu-py38-cu111' if use_gpu == True else 'cpu-py38'}-ubuntu20.04"
    return f"{repository}:{tag}"


def is_gpu_instance(instance_type):
    return True if instance_type.split(".")[1][0].lower() in ["p", "g"] else False


# https://docs.aws.amazon.com/cdk/latest/guide/constructs.html#constructs_author
class SageMakerEndpointConstruct(cdk.Construct):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        *,
        env: cdk.Environment,
        huggingface_model: str,
        model_data: str,
        huggingface_task: str,
        execution_role_arn: str,
    ) -> None:
        super().__init__(scope, construct_id)

        ##############################
        #     Construct Variables    #
        ##############################

        if huggingface_model is None:
            parsed_model_name = "huggingface-transformers"
        else:
            parsed_model_name = huggingface_model.replace("_", "-")
            if "/" in parsed_model_name:
                parsed_model_name = parsed_model_name.split("/")[-1]

        model_name = f"model-{parsed_model_name}"
        endpoint_config_name = f"config-{parsed_model_name}"
        endpoint_name = f"endpoint-{parsed_model_name}"

        # creates the image_uir based on the instance type and region
        image_uri = get_image_uri(region=env.region, use_gpu=False)

        # defines and creates container configuration for deployment
        container_environment = {}
        container_environment["HF_TASK"] = huggingface_task
        # FIXME: Added TEMP "MMS_DEFAULT_WORKERS_PER_MODEL=1" to be able to load models >512MB
        container_environment["MMS_DEFAULT_WORKERS_PER_MODEL"] = str(1)
        if huggingface_model:
            container_environment["HF_MODEL_ID"] = huggingface_model

        container = sagemaker.CfnModel.ContainerDefinitionProperty(
            environment=container_environment, image=image_uri, model_data_url=model_data
        )

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
                    initial_variant_weight=1.0,
                    variant_name=model.model_name,
                    model_name=model.model_name,
                    serverless_config=sagemaker.CfnEndpointConfig.ServerlessConfigProperty(
                        max_concurrency=8, memory_size_in_mb=6144
                    ),
                )
            ],
        )

        # Creates Real-Time Endpoint
        endpoint = sagemaker.CfnEndpoint(
            self,
            "hf_endpoint",
            endpoint_name=endpoint_name,
            endpoint_config_name=endpoint_configuration.endpoint_config_name,
        )

        # adds depends on for different resources
        endpoint_configuration.node.add_dependency(model)
        endpoint.node.add_dependency(endpoint_configuration)

        # construct export values
        self.endpoint_name = endpoint.endpoint_name
        self.model_name = parsed_model_name
