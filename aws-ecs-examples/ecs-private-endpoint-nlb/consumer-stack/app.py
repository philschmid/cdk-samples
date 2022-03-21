#!/usr/bin/env python3
import os
from aws_cdk import core as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_iam as iam
import aws_cdk.aws_ecs_patterns as ecs_patterns


class Ec2WithVpc(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc_endpoint_svc_name = self.node.try_get_context("vpc-endpoint-service-name")

        # creates dedicated VPC with 1 nat gateway
        vpc = ec2.Vpc(
            self,
            "VPC",
            max_azs=2,
        )
        # create Interface Endpoint
        interface_endpoint = ec2.InterfaceVpcEndpoint(
            self,
            "VPCEndpoint",
            vpc=vpc,
            service=ec2.InterfaceVpcEndpointService(vpc_endpoint_svc_name, 80),
            # add the az from the instance to the vpc endpoint
            subnets=ec2.SubnetSelection(availability_zones=["us-east-1b"]),
        )
        # for idx, dns_entry in enumerate(interface_endpoint.vpc_endpoint_dns_entries):
        cdk.CfnOutput(
            self, f"InferfaceEndpointDns", value=cdk.Fn.select(0, interface_endpoint.vpc_endpoint_dns_entries)
        )

        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE,
        )

        role = iam.Role(self, "InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        instance = ec2.Instance(
            self,
            "Instance",
            instance_type=ec2.InstanceType("t3.nano"),
            machine_image=amzn_linux,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(availability_zones=["us-east-1b"], subnet_type=ec2.SubnetType.PUBLIC),
            role=role,
        )


# Environment
# CDK_DEFAULT_ACCOUNT and CDK_DEFAULT_REGION are set based on the
# AWS profile specified using the --profile option.
my_environment = cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"])


app = cdk.App()
Ec2WithVpc(app, "Ec2WithVpc", env=my_environment)

app.synth()
