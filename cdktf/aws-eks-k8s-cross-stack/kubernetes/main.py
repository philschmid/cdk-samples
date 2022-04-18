# for CDK
from ctypes import Union

from cdktf import App, Fn, TerraformOutput, TerraformStack, Token
from constructs import Construct

# for terraform provider
from imports.aws.eks import DataAwsEksCluster, DataAwsEksClusterAuth
from imports.kubernetes import KubernetesProvider, Namespace, Deployment, Service
from utils import DeploymentEnvironment

# for terraform module


class KubernetesStack(TerraformStack):
    def __init__(
        self,
        scope: Construct,
        ns: str,
        env: DeploymentEnvironment,
        # cluster: Union[DataAwsEksCluster, "AzureDataSource"],
        cluster: DataAwsEksCluster,
        # clutser_auth: Union[DataAwsEksClusterAuth, "AzureDataAuth"],
        cluster_auth: DataAwsEksClusterAuth,
    ):
        super().__init__(scope, ns)

        # define resources here
        k8s_provider = KubernetesProvider(
            self,
            "k8s",
            host=cluster.endpoint,
            cluster_ca_certificate=Fn.base64decode(cluster.certificate_authority.get(0).data),
            token=cluster_auth.token,
        )

        my_namespace = Namespace(
            self,
            "tf-cdk-example",
            metadata={
                "name": "tf-cdk-example",
            },
        )

        app = "nginx-example"
        nginx = Deployment(
            self,
            "nginx-deployment",
            metadata={
                "name": app,
                "namespace": my_namespace.metadata.name,
                "labels": {
                    "app": app,
                },
            },
            spec={
                "replicas": "1",
                "selector": {
                    "match_labels": {
                        "app": app,
                    },
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": app,
                        },
                    },
                    "spec": {
                        "container": [
                            {
                                "image": "nginx:1.7.8",
                                "name": "example",
                                "port": [
                                    {
                                        "containerPort": 80,
                                    },
                                ],
                            },
                        ],
                    },
                },
            },
        )

        Service(
            self,
            "nginx-service",
            metadata={
                "namespace": nginx.metadata.namespace,
                "name": "nginx-service",
            },
            spec={
                "selector": {
                    "app": app,
                },
                "port": [
                    {
                        "port": 80,
                        "targetPort": "80",
                    },
                ],
                "type": "NodePort",
            },
        )
