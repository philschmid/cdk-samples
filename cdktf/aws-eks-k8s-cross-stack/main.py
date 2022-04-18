from cdktf import App
from aws.main import AwsStack
from azure.main import AzureStack
from utils import AwsRegion, CloudProvider, DeploymentEnvironment, DeploymentStage
from kubernetes.main import KubernetesStack
import os

environment = os.environ.get("ENVIRONMENT", "prod")

app = App()

# creates AWS Terraform state
# cdktf deploy 'aws-*'
aws_environment = DeploymentEnvironment(CloudProvider.AWS, DeploymentStage.DEV, AwsRegion.US_EAST_1)
aws_stack = AwsStack(app, "aws-infrastructure", env=aws_environment)
KubernetesStack(app, "aws-kubernetes", env=aws_environment, cluster=aws_stack.eks, cluster_auth=aws_stack.eks_auth)

# creates AWS Terraform state
# cdktf deploy 'azure-*'
# aws_environment = DeploymentEnvironment(CloudProvider.AZURE, DeploymentStage.DEV)
# AzureStack(app, "azure-infrastructure", environment={"provider": "azure"})
# KubernetesStack(app, "azure-kubernetes", environment={"provider": "azure"})


app.synth()
