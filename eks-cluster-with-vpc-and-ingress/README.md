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


## Idea 

1x Stack für IaC
  kubectl describe ingress/2048-ingress -n 2048-game
1x Stack für K8s deployment