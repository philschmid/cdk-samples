# for CDK
from cdktf import Fn, TerraformOutput, TerraformStack, Token
from constructs import Construct

# for terraform provider
from imports.aws import AwsProvider, eks
from imports.aws.datasources import DataAwsAvailabilityZones
from imports.eks import Eks
from imports.kubernetes import KubernetesProvider

# for terraform module
from imports.vpc import Vpc
from utils import DeploymentEnvironment


class AwsStack(TerraformStack):
    def __init__(
        self,
        scope: Construct,
        ns: str,
        env: DeploymentEnvironment,
    ):
        super().__init__(scope, ns)
        # setup provider with authentication
        aws_provider = AwsProvider(
            self,
            "aws",
            region=env.region,
        )

        all_azs = DataAwsAvailabilityZones(
            self,
            "all-availability-zones",
        ).names

        self.vpc = Vpc(
            self,
            "Vpc",
            name=f"{env.prefix}-vpc",
            cidr="10.0.0.0/16",
            azs=all_azs,
            public_subnets=["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"],
            private_subnets=["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"],
            single_nat_gateway=True,
            enable_nat_gateway=True,
        )

        cluster = Eks(
            self,
            "Eks",
            cluster_name=f"{env.prefix}-cluster",
            cluster_version="1.21",
            cluster_endpoint_private_access=True,
            cluster_endpoint_public_access=True,
            cluster_addons={
                "coredns": {"resolve_conflicts": "OVERWRITE"},
                "kube-proxy": {},
                "vpc-cni": {"resolve_conflicts": "OVERWRITE"},
            },
            subnet_ids=Token().as_list(self.vpc.private_subnets_output),
            vpc_id=Token().as_string(self.vpc.vpc_id_output),
            eks_managed_node_group_defaults={
                "disk_size": 50,
                "instance_types": ["c6i.xlarge", "g4dn.xlarge"],
            },
            eks_managed_node_groups={
                "cpu": {
                    "min_size": 1,
                    "max_size": 10,
                    "desired_size": 1,
                    "instance_types": ["c6i.xlarge"],
                    "ami_type": "AL2_x86_64",
                },
            },
            manage_aws_auth_configmap=True,
            aws_auth_roles=[
                {
                    "rolearn": "arn:aws:iam::xx:role/xx",
                    "username": "console",
                    "groups": ["system:masters"],
                }
            ],
            aws_auth_users=[
                {
                    "userarn": "arn:aws:iam::xx:user/xx",
                    "username": "cli",
                    "groups": ["system:masters"],
                }
            ],
        )

        # We create the Eks cluster within the module, this is so we can access the cluster resource afterwards
        self.eks = eks.DataAwsEksCluster(self, "eks-cluster", name=cluster.cluster_id_output)

        #  We need to fetch the authentication data from the EKS cluster as well
        self.eks_auth = eks.DataAwsEksClusterAuth(
            self,
            "eks-auth",
            name=cluster.cluster_name,
        )

        # needed to run some configuration
        KubernetesProvider(
            self,
            "k8s",
            host=cluster.cluster_endpoint_output,
            # INFO Terraform methods not available
            # https://discuss.hashicorp.com/t/leveraging-built-in-terraform-functions-in-cdktf/17118/3
            cluster_ca_certificate=Fn.base64decode(cluster.cluster_certificate_authority_data_output),
            token=self.eks_auth.token,
        )

        TerraformOutput(
            self,
            "KubelctlCommand",
            value=f"aws eks update-kubeconfig --name {cluster.cluster_name} --region {env.region}",
        )

        TerraformOutput(self, "cluster_endpoint", value=cluster.cluster_endpoint_output)
        TerraformOutput(self, "cluster_name", value=cluster.cluster_name)
        TerraformOutput(self, "cluster_id", value=cluster.cluster_id_output)
