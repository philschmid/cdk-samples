import json
from os import path
from typing import Any

from aws_cdk import core as cdk
from aws_cdk.core import Duration, RemovalPolicy, Stack
import aws_cdk.aws_lambda as aws_lambda
import aws_cdk.aws_iam as iam
import aws_cdk.aws_eks as eks
import aws_cdk.aws_s3_assets as assets
import aws_cdk.aws_ec2 as ec2
from aws_cdk.lambda_layer_kubectl import KubectlLayer
from aws_cdk.lambda_layer_awscli import AwsCliLayer

from aws_cdk.custom_resources import Provider
import requests
import tempfile


class KubectlConstruct(cdk.Construct):
    """Kubectl Construct
    Creates an AWS Lambda function for a Customer Cloudformation Ressource,
    which uses kubectl to apply certain manifest to the cluster. Each KubectlContstruct
    creates 1 aws lambda function.
    Arguments:
        :param cluster - EKS Cluster
        :param manifest - Kubernetes yaml which should be applied
        :param label - used with kubectl apply -l label
    """

    def __init__(self, scope: cdk.Construct, id: str, cluster: eks.Cluster, manifest: str, label: str = None) -> None:
        super().__init__(scope, id)

        # official code
        # https://github.com/aws/aws-cdk/blob/master/packages/%40aws-cdk/aws-eks/lib/kubectl-provider.ts
        # https://github.com/aws/aws-cdk/tree/master/packages/%40aws-cdk/aws-eks/lib/kubectl-handler
        with open(path.join(path.dirname(__file__), "custom_resource_handler.py")) as f:
            code = f.read()

        event_handler = aws_lambda.SingletonFunction(
            scope=self,
            id=f"{id}EventHandler",
            uuid="Custom::AWSCDK-EKS-Kubectl",
            description="Kubectl Custom Resource Event Handler",
            runtime=aws_lambda.Runtime.PYTHON_3_7,
            code=aws_lambda.Code.from_inline(code),
            handler="index.on_event",
            timeout=Duration.minutes(15),
            environment=cluster.kubectl_environment,
            memory_size=1024,
            # # defined only when using private access
            vpc=cluster.vpc if cluster.kubectl_private_subnets else None,
            security_groups=[cluster.kubectl_security_group] if cluster.kubectl_security_group else None,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE if cluster.kubectl_private_subnets else None
            ),
            # layers
            layers=[KubectlLayer(self, "KubectlLayer"), AwsCliLayer(self, "AwsCliLayer")],
        )

        # upload remote manifest to S3 to be used in airgapped lambda
        if manifest.startswith("https://"):
            with tempfile.TemporaryDirectory() as tmpdirname:
                mainfest_response = requests.get(manifest)
                if mainfest_response.status_code != 200:
                    raise Exception(
                        f"Failed to download manifest from {manifest}. Status code: {mainfest_response.status_code}"
                    )
                manifest = path.join(tmpdirname, "manifest.yaml")
                with open(manifest, "w") as f:
                    f.writelines(mainfest_response.text)

                # upload s3 in the context of the temp manifest
                asset = assets.Asset(self, "manifestAsset", path=manifest)
                asset.grant_read(event_handler)
                manifest = asset.s3_object_url
        else:
            asset = assets.Asset(self, "manifestAsset", path=manifest)
            asset.grant_read(event_handler)
            manifest = asset.s3_object_url

        # add eks principal to event handler
        event_handler.role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=["eks:DescribeCluster"],
                resources=[cluster.cluster_arn],
            )
        )

        # allow this handler to assume the kubectl role
        cluster.kubectl_role.grant(event_handler.role, "sts:AssumeRole")

        provider = Provider(scope=self, id=f"{id}Provider", on_event_handler=event_handler)

        cdk.CustomResource(
            scope=self,
            id=f"{id}Kubectl",
            service_token=provider.service_token,
            resource_type="Custom::AWSCDK-EKS-Kubectl",
            properties={
                "cluster_name": cluster.cluster_name,
                "role_arn": cluster.kubectl_role.role_arn,
                "manifest": manifest,
                "label": label,
            },
        )
