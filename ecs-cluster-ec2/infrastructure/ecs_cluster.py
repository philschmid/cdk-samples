from aws_cdk import core as cdk

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_autoscaling as autoscaling
import aws_cdk.aws_iam as iam
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_ecs_patterns as ecs_patterns

# custom constructs
from infrastructure.ecs_service import WebService


class ClusterWithVpcAndAlbStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # creates dedicated VPC with 1 nat gateway
        vpc = ec2.Vpc(self, "VPC")

        # Create an ECS cluster
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        # # Add capacity to it without auscaling group
        # cluster.add_capacity(
        #     "DefaultAutoScalingGroupCapacity", instance_type=ec2.InstanceType("c5n.xlarge"), desired_capacity=3
        # )

        # add cluster autoscaling
        auto_scaling_group = autoscaling.AutoScalingGroup(
            self,
            "ASG",
            vpc=vpc,
            instance_type=ec2.InstanceType("c5n.xlarge"),
            # GPU
            # instance_type=ec2.InstanceType("g4dn.xlarge"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
            # GPU
            # machine_image=ecs.EcsOptimizedImage.amazon_linux2(ecs.AmiHardwareType.GPU),
            min_capacity=1,
            max_capacity=10,
        )
        EPHEMERAL_PORT_RANGE = ec2.Port.tcp_range(32768, 65535)
        auto_scaling_group.connections.allow_from_any_ipv4(EPHEMERAL_PORT_RANGE)

        capacity_provider = ecs.AsgCapacityProvider(
            self,
            "AsgCapacityProvider",
            auto_scaling_group=auto_scaling_group,
            machine_image_type=ecs.MachineImageType.AMAZON_LINUX_2,
        )
        cluster.add_asg_capacity_provider(capacity_provider)

        execution_role = iam.Role(
            self,
            "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        execution_role.add_to_policy(
            iam.PolicyStatement(
                resources=["*"],
                actions=[
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:GetAuthorizationToken",
                ],
            )
        )

        # # add Webservice
        web_service = WebService(
            self,
            "WebSerice1",
            ecs_cluster=cluster,
            ecs_task_execution_role=execution_role,
            # your registry container image
            container_image="123456789012.dkr.ecr.us-east-1.amazonaws.com/myregistry:latest",
            cpu=1024,
            memory_limit=2048,
            container_port=8080,
            auto_scaling_enabled=True,
            auto_scaling_max_capacity=5,
            scale_target_request_per_second=6,
        )
        # give load balancer permission to access autoscaling group
        auto_scaling_group.connections.allow_from(web_service.service.load_balancer, ec2.Port.tcp_range(32768, 65535))
