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
- [ ] create custom Resource for kubectl apply install CRDs like kubeflow or knative
## cdk8s

* https://github.com/cdk8s-team/cdk8s/tree/master/examples
* https://cdk8s.io/docs/latest/
## Todos 

- [ ] improve custom resource
  - [ ] split lambda code
  - [ ] check cloudformation outputs
- [ ] create proper cdk construct out of it
- [ ] clean logger
https://www.matthewbonig.com/2020/01/11/creating-constructs/
https://dev.to/aws-builders/a-beginner-s-guide-to-create-aws-cdk-construct-library-with-projen-5eh4
https://www.sebastianhesse.de/2021/03/01/migrating-a-cdk-construct-to-projen-and-jsii/
https://github.com/hayao-k/cdk-ecr-image-scan-notify/blob/main/developAWSCDKConstructslib.md

# Installation get L1 K9s constructs
yarn global add cdk8s-cli

cdk8s import k8s --language python



## access cluster

```
aws eks get-token --cluster-name EksClusterWithVpcAndIstio-cluster --region us-east-1 --profile hf-inf --role-arn arn:aws:iam::379486364332:role/EksClusterWithVpcAndIstio-eksClusterMastersRole632-1MVZCIODDYLSL
```


aws eks update-kubeconfig --name EksClusterWithVpcAndIstio-cluster --region us-east-1 --profile hf-inf --role-arn arn:aws:iam::379486364332:role/EksClusterWithVpcAndIstio-eksClusterMastersRole632-1MVZCIODDYLSL
aws eks get-token --cluster-name EksClusterWithVpcAndIstio-cluster --region us-east-1 --role-arn arn:aws:iam::379486364332:role/EksClusterWithVpcAndIstio-eksClusterMastersRole632-1MVZCIODDYLSL