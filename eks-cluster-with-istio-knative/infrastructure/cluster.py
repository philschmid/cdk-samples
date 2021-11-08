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
# from eks_cluster_with_vpc_and_ingress.webservice import WebService
# from eks_cluster_with_vpc_and_ingress.twoZeroFourEightChart import TwoZeroFourEightChart
def load_k8s_manifest(url):
    response = requests.get(url)
    return list(yaml.safe_load_all(response.text))


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
            kubectl_memory=cdk.Size.gibibytes(4),  # 4 GiB https://github.com/aws/aws-cdk/issues/11787
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

        # Received response status [FAILED] from custom resource. Message returned: Error: b'error: error validating "/tmp/manifest.yaml": error validating data: [apiVersion not
        # set, kind not set]; if you choose to ignore these errors, turn validation off with --validate=false\n'

        # add serving crds
        serving_crd = load_k8s_manifest(
            f"https://github.com/knative/serving/releases/download/knative-v{knative_version}/serving-crds.yaml"
        )

        eks.KubernetesManifest(
            self,
            "serving-crd",
            cluster=cluster,
            manifest=serving_crd,
            skip_validation=True,
        )

        # )
        # cluster.add_manifest("serving-crd", serving_crd)

        # # add serving core
        # serving_core = load_k8s_manifest(
        #     f"https://github.com/knative/serving/releases/download/knative-v{knative_version}/serving-core.yaml"
        # )
        # cluster.add_manifest("serving-core", serving_core)

        # # add serving
        # istio_install = load_k8s_manifest(
        #     f"https://github.com/knative/net-istio/releases/download/knative-v{knative_version}/istio.yaml"
        # )
        # cluster.add_manifest("istio-install", istio_install)

        # # add istio knative controller
        # istio_knative = load_k8s_manifest(
        #     f"https://github.com/knative/net-istio/releases/download/knative-v{knative_version}/net-istio.yaml"
        # )
        # cluster.add_manifest("istio-knative", istio_knative)

        ###################################
        #   Deployment of K8s Ressource   #
        ###################################

        # _2048 = TwoZeroFourEightChart(App(), "2048")
        # # add the cdk8s chart to the cluster
        # cluster.add_cdk8s_chart("2048", _2048)

        # # create a cdk8s chart and use `cdk8s.App` as the scope.
        # echo_service = WebService(
        #     App(),
        #     "Webservice",
        #     image="paulbouwer/hello-kubernetes:1.7",
        #     replicas=2,
        #     port=8080,
        #     ingress_path="/*",
        #     node_selector={"accelerator": "cpu"},
        # )

        # # add the cdk8s chart to the cluster
        # cluster.add_cdk8s_chart("echo-service", echo_service)
