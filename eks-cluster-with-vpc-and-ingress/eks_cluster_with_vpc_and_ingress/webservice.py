from typing import Mapping
from constructs import Construct, Node
from cdk8s import App, Chart
import cdk8s_plus as k8s


class WebService(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        image: str,
        replicas=1,
        port=80,
        containerPort=8080,
        ingress_path="/hello",
        node_selector: Mapping[str, str] = {},
        **kwargs
    ):
        super().__init__(scope, id)

        label = {"app": Node.of(self).id}

        webservice_deployment = k8s.Deployment(
            self,
            "deployment",
            spec=k8s.DeploymentSpec(
                replicas=replicas,
                selector=k8s.LabelSelector(match_labels=label),
                template=k8s.PodTemplateSpec(
                    metadata=k8s.ObjectMeta(labels=label),
                    spec=k8s.PodSpec(
                        containers=[
                            k8s.Container(
                                name="web", image=image, ports=[k8s.ContainerPort(container_port=containerPort)]
                            )
                        ],
                        node_selector=node_selector,
                    ),
                ),
            ),
        )
        # won't work since containerPort <> Port
        # webservice_service = webservice_deployment.expose(port=port, service_type=k8s.ServiceType.NODE_PORT)
        webservice_service = k8s.Service(
            self,
            "service",
            spec=k8s.ServiceSpec(
                type=k8s.ServiceType.NODE_PORT,
                ports=[k8s.ServicePort(port=port, target_port=k8s.IntOrString.from_number(containerPort))],
                selector=label,
            ),
        )

        ingress = k8s.Ingress(
            self,
            "ingress",
        )
        ingress.addRule(ingress_path, k8s.IngressBackend.fromService(webservice_service))
