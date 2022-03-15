from aws_cdk import core as cdk

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_autoscaling as autoscaling
import aws_cdk.aws_iam as iam
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_elasticloadbalancingv2 as elbv2
import aws_cdk.aws_ecs_patterns as ecs_patterns
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_certificatemanager as acm
from aws_cdk.aws_elasticloadbalancingv2 import SslPolicy


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
        domain="example.com"
        self.my_hosted_zone = route53.HostedZone.from_lookup(self, "HostedZone", domain_name=domain)
  
        # if you want to create certificate 
        self.acm = acm.Certificate(
            self,
            "Certificate",
            domain_name=domain, # e.g. randomvalue.example.com
            subject_alternative_names=[f"*.{domain}"], # optional
            validation=acm.CertificateValidation.from_dns(self.my_hosted_zone),
        )
        # if you already created a wildcard certificate
        acm_arn = "arn:aws:acm:us-east-1:123456:certificate/abcdefg"
        self.acm = acm.Certificate.from_certificate_arn(self, "Cert", acm_arn)

        
        load_balanced_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "Service",
        cluster=cluster,
        memory_limit_mib=1024,
        cpu=512,
        certificate=self.acm,
        ssl_policy=SslPolicy.RECOMMENDED,
        domain_name="api.example.com",
        domain_zone=self.my_hosted_zone,
        protocol=elbv2.ApplicationProtocol.HTTPS,
        redirect_http=True,
        task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample")
        )
    )