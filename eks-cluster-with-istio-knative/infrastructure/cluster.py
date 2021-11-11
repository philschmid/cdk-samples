from aws_cdk import core as cdk

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_iam as iam
import aws_cdk.aws_eks as eks
from cdk8s import App

import requests
import yaml

##### chart
from infrastructure.kubectl_cdk import KubectlConstruct


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
            cluster_name=f"{construct_id}-cluster",
            output_cluster_name=True,
            kubectl_memory=cdk.Size.gibibytes(2),  # 4 GiB https://github.com/aws/aws-cdk/issues/11787
        )
        # add permissions to iam user so see the cluster
        for user in authorized_iam_user_list:
            auth_user = iam.User.from_user_name(self, "MyImportedUserByName", user)
            cluster.aws_auth.add_user_mapping(auth_user, groups=["system:masters"])

        #################
        #  Node Groups  #
        #################

        # CPU Node Group

        cluster.add_nodegroup_capacity(
            "cpu-node-group",
            # node_role=workerRole,
            instance_types=[ec2.InstanceType("m6i.large")],
            min_size=1,
            max_size=3,
            disk_size=100,
            ami_type=eks.NodegroupAmiType.AL2_X86_64,
            labels={"accelerator": "cpu", "hardware": "intel"},
        )

        # GPU Node Group

        # cluster.add_nodegroup_capacity(
        #     "gpu-node-group",
        #     # node_role=workerRole,
        #     instance_types=[ec2.InstanceType("g4dn.xlarge")],
        #     min_size=1,
        #     max_size=3,
        #     disk_size=100,
        #     ami_type=eks.NodegroupAmiType.AL2_X86_64_GPU,
        #     labels={"accelerator": "gpu", "hardware": "nvidia"},
        # )

        ################
        #    knative   #
        ################

        # adds the correct IAM Policies to the Role
        knative_version = "1.0.0"

        # add serving crds
        serving_crd = KubectlConstruct(
            self,
            "ServingCRD",
            cluster=cluster,
            manifest=f"https://github.com/knative/serving/releases/download/knative-v{knative_version}/serving-crds.yaml",
        )
        serving_core = KubectlConstruct(
            self,
            "ServingCore",
            cluster=cluster,
            manifest=f"https://github.com/knative/serving/releases/download/knative-v{knative_version}/serving-core.yaml",
        )
        serving_core.node.add_dependency(serving_crd)

        istio_install = KubectlConstruct(
            self,
            "IstioInstall",
            cluster=cluster,
            manifest=f"eks-cluster-with-istio-knative/infrastructure/istio/istio-v{knative_version}-operator.yaml",
            label="knative.dev/crd-install=true",
        )
        istio_install.node.add_dependency(serving_core)

        istio_knative = KubectlConstruct(
            self,
            "IstioKnative",
            cluster=cluster,
            manifest=f"https://github.com/knative/net-istio/releases/download/knative-v{knative_version}/net-istio.yaml",
        )
        istio_knative.node.add_dependency(istio_install)

        # # configure dns
        # # TODO: real DNS :
        # # * get ELB CNAME from the cluster
        # # * set up CNAME in Route53 for the ELB: ELB.cname -> my-domain.com
        # # * upate istio config
        # # Magic DNS (sslip.io) https://knative.dev/docs/install/serving/install-serving-with-yaml/#configure-dns
        # magic_dns = KubectlConstruct(
        #     self,
        #     "DNS",
        #     cluster=cluster,
        #     manifest=f"https://github.com/knative/serving/releases/download/knative-v{knative_version}/serving-default-domain.yaml",
        # )
        # magic_dns.node.add_dependency(istio_knative)
