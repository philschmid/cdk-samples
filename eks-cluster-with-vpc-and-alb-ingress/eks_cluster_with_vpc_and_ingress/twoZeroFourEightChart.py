from constructs import Construct, Node
from cdk8s import App, Chart
import cdk8s_plus
import cdk8s


class TwoZeroFourEightChart(Chart):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        label = {"app": Node.of(self).id}

        webservice_deployment = cdk8s_plus.Deployment(
            self,
            "deployment",
            replicas=1,
            metadata=cdk8s.ApiObjectMetadata(labels=label),
            containers=[
                cdk8s_plus.Container(
                    name="2048",
                    image="alexwhen/docker-2048",
                    image_pull_policy=cdk8s_plus.ImagePullPolicy.ALWAYS,
                    port=80,
                )
            ],
        )
        webservice_service = webservice_deployment.expose(port=80, service_type=cdk8s_plus.ServiceType.NODE_PORT)

        ingress = cdk8s_plus.Ingress(
            self,
            "ingress",
        )
        ingress.addRule("/*", cdk8s_plus.IngressBackend.fromService(webservice_service))
