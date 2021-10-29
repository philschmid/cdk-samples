from aws_cdk import core as cdk

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
import aws_cdk.aws_iam as iam
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecs_patterns as ecs_patterns


class WebService(cdk.Construct):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        ecs_cluster: ecs.Cluster,
        ecs_task_execution_role: iam.Role,
        container_image: str,
        container_port: int = 8080,
        health_check_path: str = "/health",
        desired_count: int = 1,
        cpu: int = 1024,
        memory_limit: int = 1024,
        auto_scaling_enabled: bool = True,
        auto_scaling_max_capacity: int = 5,
        scale_target_request_per_second: int = 100,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.service = ecs_patterns.ApplicationLoadBalancedEc2Service(
            self,
            "Service",
            cluster=ecs_cluster,
            desired_count=desired_count,
            cpu=cpu,
            memory_limit_mib=memory_limit,
            # target_protocol="HTTPS",
            task_image_options={
                "image": ecs.ContainerImage.from_registry(container_image),
                "container_port": container_port,
                "execution_role": ecs_task_execution_role,
            },
        )
        # health check route
        self.service.target_group.configure_health_check(path=health_check_path)

        # add task autoscaling based on requests
        if auto_scaling_enabled:
            scalable_target = self.service.service.auto_scale_task_count(
                min_capacity=1, max_capacity=auto_scaling_max_capacity
            )

            scalable_target.scale_on_request_count(
                "ScalePerRequest",
                requests_per_target=(scale_target_request_per_second * 60),  # request per minute to target,
                target_group=self.service.target_group,
            )
            # # allow correct load balancing
