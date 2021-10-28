# Work in Progress
# CDK MLOps Sample: Automatic Batch Transform Jobs on S3 Upload

Best Practice: https://aws.amazon.com/de/blogs/developer/recommended-aws-cdk-project-structure-for-python-applications/
https://github.com/aws-samples/aws-cdk-project-structure-python/blob/main/tests/test_api_infrastructure.py

https://constructs.dev/packages/cdk8s-aws-load-balancer-controller/v/2.3.6?lang=python#before-usage-need-to-install-helm
https://github.com/neilkuan/cdk8s-cdk-example/blob/main/src/main.ts
https://pypi.org/project/cdk8s-aws-load-balancer-controller/
https://github.com/superluminar-io/super-eks
https://stackoverflow.com/questions/67762104/how-to-install-aws-load-balancer-controller-in-a-cdk-project

autoscaler: https://hackernoon.com/how-to-adjust-size-of-a-kubernetes-cluster-using-cluster-autoscaler-qy1j3t66
https://gist.github.com/esys/bb7bbeb44565f85f48b3112a8d73a092


# Todos

- [ ] nginx ingress/istio as alternative -> url rewrites/proxies
- [ ] clean project, create deployment.py and cluster.py etc
- [ ] HPO or autoscaling in generall
- [ ] install CRDs like kubeflow or knative
    - use CRDs with cdk8s https://github.com/cdk8s-team/cdk8s/blob/master/examples/python/crd/main.py
         https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_eks/README.html#adding-resources-from-a-url
    https://knative.dev/docs/admin/install/serving/install-serving-with-yaml/
    ```python
    def install_knative(version="0.26.0",cluster):
      serving_crds = f"https://github.com/knative/serving/releases/download/v{version}/serving-crds.yaml"
      serving_core = f"https://github.com/knative/serving/releases/download/v{version}/serving-core.yaml"
      serving_crds_yaml = yaml.safe_load_all(requests.get(serving_crds).content.decode())
      serving_core_yaml = yaml.safe_load_all(requests.get(serving_core).content.decode())
      cluster.add_manifest("serving_crds",serving_crds_yaml)
      cluster.add_manifest("serving_core",serving_core_yaml)

      # Install a networking layer
      kourier = f"https://github.com/knative/net-kourier/releases/download/v{version}/kourier.yaml"
      kourier_yaml = yaml.safe_load_all(requests.get(kourier).content.decode())
      cluster.add_manifest("kourier_yaml",kourier_yaml)
      KubernetesPatch(self, "hello-kub-deployment-label",
        cluster=cluster,
        resource_name="configmap/config-network",
        apply_patch={"data":{"ingress.class":"kourier.ingress.networking.knative.dev"}},
      )
      ```
## cdk8s

* https://github.com/cdk8s-team/cdk8s/tree/master/examples
* https://cdk8s.io/docs/latest/
## Idea 

1x Stack für IaC
  kubectl describe ingress/2048-ingress -n 2048-game
1x Stack für K8s deployment


# Installation get L1 K9s constructs
yarn global add cdk8s-cli

cdk8s import k8s --language python