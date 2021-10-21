from aws_cdk import core as cdk

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_iam as iam
import aws_cdk.aws_eks as eks
from cdk8s_aws_load_balancer_controller import AwsLoadBalancePolicy, VersionsLists
from cdk8s import App, Chart
from cdk8s_aws_load_balancer_controller import AwsLoadBalancerController
import constructs as constructs

import requests


class AwsAlbChart(Chart):
    def __init__(self, scope, name, *, cluster_name):
        super().__init__(scope, name)
        alb = AwsLoadBalancerController(self, "alb", cluster_name=cluster_name, create_service_account=False)
        self.deployment_name = alb.deployment_name
        self.deployment_name_space = alb.namespace


class EksClusterWithVpcAndIngressStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ####################
        #    Variables     #
        ####################
        authorized_iam_user_list = ["philippschmid"]

        # IAM role for our EC2 worker nodes
        workerRole = iam.Role(self, "EKSWorkerRole", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))

        # not good!
        clusterAdmin = iam.Role(self, "EKSAdminRole", assumed_by=iam.AccountRootPrincipal())

        # creates dedicated VPC with 1 nat gateway
        vpc = ec2.Vpc(self, "VPC", cidr="10.0.0.0/16", nat_gateways=1)

        # creates the EKS cluster
        cluster = eks.Cluster(
            self,
            "eksCluster",
            version=eks.KubernetesVersion.V1_21,
            default_capacity=0,
            vpc=vpc,
            vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE)],
            # mastersRole=clusterAdmin,
            output_cluster_name=True,
        )
        for user in authorized_iam_user_list:
            auth_user = iam.User.from_user_name(self, "MyImportedUserByName", user)
            cluster.aws_auth.add_user_mapping(auth_user, groups=["system:masters"])

        ################
        #    Ingress   #
        ################

        # Creates and Service account for our cluster to add a load Balancer
        alb_service_account = eks.ServiceAccount(
            self,
            "ALBServiceAccount",
            cluster=cluster,
            name="aws-load-balancer-controller",
            namespace="kube-system",
        )
        # adds the correct IAM Policies to the Role
        alb_version = "2.3.0"
        policy_document = requests.get(
            f"https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v{alb_version}/docs/install/iam_policy.json"
        )
        for statement in policy_document.json()["Statement"]:
            policy_statement = iam.PolicyStatement.from_json(statement)
            alb_service_account.add_to_principal_policy(policy_statement)
        # Deploys the HELM chart of the ALB Ingress controller to our cluster
        # https://github.com/aws-samples/nexus-oss-on-aws/blob/d3a092d72041b65ca1c09d174818b513594d3e11/src/lib/sonatype-nexus3-stack.ts#L207-L242
        add_alb_chart = cluster.add_helm_chart(
            "aws-load-balancer-controller-helm-chart",
            repository="https://aws.github.io/eks-charts",
            chart="eks/aws-load-balancer-controller",
            release="aws-load-balancer-controller",
            version="1.3.1",  # https://github.com/kubernetes-sigs/aws-load-balancer-controller/blob/main/helm/aws-load-balancer-controller/Chart.yaml
            namespace=alb_service_account.service_account_namespace,
            values={
                "clusterName": cluster.cluster_name,
                "serviceAccount": {
                    "create": False,
                    "name": alb_service_account.service_account_name,
                },
                "enableShield": False,
                "enableWaf": False,
                "enableWafv2": False,
            },
        )

        add_alb_chart.node.add_dependency(alb_service_account)

        #################
        #  Node Groups  #
        ################

        cluster.add_nodegroup_capacity(
            "custom-node-group",
            # node_role=workerRole,
            instance_types=[ec2.InstanceType("m5.large")],
            min_size=1,
            max_size=3,
            disk_size=100,
            ami_type=eks.NodegroupAmiType.AL2_X86_64,
            # ami_type=eks.NodegroupAmiType.AL2_X86_64_GPU,
        )

        # apply a kubernetes manifest to the cluster
        # cluster.add_manifest(
        #     "mypod",
        #     api_version="v1",
        #     kind="Pod",
        #     metadata={"name": "mypod"},
        #     spec={
        #         "containers": [
        #             {"name": "hello", "image": "paulbouwer/hello-kubernetes:1.5", "ports": [{"container_port": 8080}]}
        #         ]
        #     },
        # )
