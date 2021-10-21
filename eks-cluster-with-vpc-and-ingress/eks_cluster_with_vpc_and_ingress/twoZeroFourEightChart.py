from constructs import Construct, Node
from cdk8s import App, Chart
import cdk8s_plus as k8s


class TwoZeroFourEightChart(Chart):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        label = {"app": Node.of(self).id}

        webservice_deployment = k8s.Deployment(
            self,
            "deployment",
            spec=k8s.DeploymentSpec(
                replicas=1,
                selector=k8s.LabelSelector(match_labels=label),
                template=k8s.PodTemplateSpec(
                    metadata=k8s.ObjectMeta(labels=label),
                    spec=k8s.PodSpec(
                        containers=[
                            k8s.Container(
                                name="2048",
                                image="alexwhen/docker-2048",
                                image_pull_policy=k8s.ImagePullPolicy.ALWAYS,
                                ports=[k8s.ContainerPort(container_port=80)],
                            )
                        ]
                    ),
                ),
            ),
        )
        webservice_service = webservice_deployment.expose(port=80, service_type=k8s.ServiceType.NODE_PORT)

        ingress = k8s.Ingress(
            self,
            "ingress",
        )
        ingress.addRule("/*", k8s.IngressBackend.fromService(webservice_service))
