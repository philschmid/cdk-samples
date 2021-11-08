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


class KubectlConstruct(cdk.Construct):
    """Kubectl Construct
    Creates an AWS Lambda function for a Customer Cloudformation Ressource,
    which uses kubectl to apply certain manifest to the cluster. Each KubectlContstruct
    creates 1 aws lambda function.
    Arguments:
        :param cluster - EKS Cluster
        :param manifest - Kubernetes yaml which should be applied
    """

    def __init__(
        self,
        scope: cdk.Construct,
        id: str,
        cluster: eks.Cluster,
        manifest: str,
    ) -> None:
        super().__init__(scope, id)

        # official code
        # https://github.com/aws/aws-cdk/blob/master/packages/%40aws-cdk/aws-eks/lib/kubectl-provider.ts
        # https://github.com/aws/aws-cdk/tree/master/packages/%40aws-cdk/aws-eks/lib/kubectl-handler
        with open(path.join(path.dirname(__file__), "custom_resource_handler.py")) as file:
            code = file.read()

        event_handler = aws_lambda.SingletonFunction(
            scope=self,
            id=f"{id}EventHandler",
            uuid="Custom::AWSCDK-EKS-Kubectl",
            runtime=aws_lambda.Runtime.PYTHON_3_7,
            code=aws_lambda.Code.from_inline(code),
            handler="index.on_event",
            timeout=Duration.minutes(15),
            environment=cluster.kubectl_environment,
            # # defined only when using private access
            vpc=cluster.vpc if cluster.kubectl_private_subnets else None,
            security_groups=[cluster.kubectl_security_group] if cluster.kubectl_security_group else None,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE if cluster.kubectl_private_subnets else None
            ),
            # layers
            layers=[KubectlLayer(self, "KubectlLayer"), AwsCliLayer(self, "AwsCliLayer")],
        )

        # upload local kubernetes manifest to S3
        if not manifest.startswith("https://"):
            asset = assets.Asset(self, "ManifestAsset", path=manifest)
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
            },
        )


# export class MyCustomResource extends cdk.Construct {
#   public readonly response: string;

#   constructor(scope: cdk.Construct, id: string, props: MyCustomResourceProps) {
#     super(scope, id);

#     const resource = new cfn.CustomResource(this, 'Resource', {
#       provider: cfn.CustomResourceProvider.lambda(new lambda.SingletonFunction(this, 'Singleton', {
#         uuid: 'f7d4f730-4ee1-11e8-9c2d-fa7ae01bbebc',
#         code: new lambda.InlineCode(fs.readFileSync('custom-resource-handler.py', { encoding: 'utf-8' })),
#         handler: 'index.main',
#         timeout: cdk.Duration.seconds(300),
#         runtime: lambda.Runtime.PYTHON_3_6,
#       })),
#       properties: props
#     });

#     this.response = resource.getAtt('Response').toString();
#   }
# }
