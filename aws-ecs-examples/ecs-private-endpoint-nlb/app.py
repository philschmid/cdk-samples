#!/usr/bin/env python3
import os
from aws_cdk import core as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_iam as iam
import aws_cdk.aws_ecs_patterns as ecs_patterns


class ClusterWithVpcAndNlbStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        allowed_aws_accounts = ["379486364332"]

        # creates dedicated VPC with 1 nat gateway
        vpc = ec2.Vpc(
            self,
            "VPC",
            max_azs=3,
            nat_gateways=1,
        )

        # Create an ECS cluster
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        # # Add capacity to it without auscaling group
        cluster.add_capacity(
            "DefaultAutoScalingGroupCapacity", instance_type=ec2.InstanceType("c5n.xlarge"), desired_capacity=1
        )

        ecs_service = ecs_patterns.NetworkLoadBalancedEc2Service(
            self,
            "Service",
            cluster=cluster,
            memory_limit_mib=1024,
            desired_count=1,
            # important for private VPC
            public_load_balancer=False,
            task_image_options=ecs_patterns.NetworkLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry("nginxdemos/hello"),
                enable_logging=True,
                environment={
                    "TEST_ENVIRONMENT_VARIABLE1": "test environment variable 1 value",
                    "TEST_ENVIRONMENT_VARIABLE2": "test environment variable 2 value",
                },
            ),
        )
        # ADD inbound secruity group to the NLB
        # related issue https://github.com/aws/aws-cdk/issues/1490
        EPHEMERAL_PORT_RANGE = ec2.Port.tcp_range(32768, 65535)
        ecs_service.service.connections.allow_from_any_ipv4(EPHEMERAL_PORT_RANGE)

        # CREATE VPC Endpoint
        vpc_endpoint = ec2.VpcEndpointService(
            self,
            "vpc-endpoint-service",
            vpc_endpoint_service_load_balancers=[ecs_service.load_balancer],
            acceptance_required=False,
            whitelisted_principals=[
                iam.ArnPrincipal(f"arn:aws:iam::{account_id}:root") for account_id in allowed_aws_accounts
            ],
        )
        cdk.CfnOutput(self, "VpcEndpointServiceName", value=vpc_endpoint.vpc_endpoint_service_name)
        cdk.CfnOutput(self, "VpcEndpointServiceId", value=vpc_endpoint.vpc_endpoint_service_id)


# Environment
# CDK_DEFAULT_ACCOUNT and CDK_DEFAULT_REGION are set based on the
# AWS profile specified using the --profile option.
my_environment = cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"])


app = cdk.App()
ClusterWithVpcAndNlbStack(app, "ClusterWithVpcAndNlbStack", env=my_environment)

app.synth()
