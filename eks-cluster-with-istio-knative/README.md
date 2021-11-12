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

https://aws.amazon.com/es/blogs/opensource/network-load-balancer-nginx-ingress-controller-eks/


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

# Installation get L1 K8s constructs
yarn global add cdk8s-cli

cdk8s import k8s --language python

## access cluster

```
aws eks update-kubeconfig --name EksClusterWithVpcAndIstio-cluster --region us-east-1 --role-arn arn:aws:iam::379486364332:role/EksClusterWithVpcAndIstio-eksClusterMastersRole632-9PHLWJQRKTJ9 --profile hf-inf
```
# Help full commands

get service
```Bash
kn service list
```

get ingress 
```Bash
kubectl --namespace istio-system get service istio-ingressgateway
```


edit ingress config-map
```bash
kubectl edit cm config-domain --namespace knative-serving
```

# istio

### Install istio manually

### -> **Is integrated into CDK!**


https://maytan.work/aws-alb-with-istio/
https://istio.io/latest/blog/2018/aws-nlb/


create `istio-operator.yaml`
```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  values:
    global:
      proxy:
        autoInject: disabled
      useMCP: false
      # The third-party-jwt is not enabled on all k8s.
      # See: https://istio.io/docs/ops/best-practices/security/#configure-third-party-service-account-tokens
      jwtPolicy: first-party-jwt
    gateways:
      istio-ingressgateway:
        serviceAnnotations:
          service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
          
  addonComponents:
    pilot:
      enabled: true

  components:
    ingressGateways:
      - name: istio-ingressgateway
        enabled: true
```

create `istio-peer-authencation.yaml`

```bash
apiVersion: "security.istio.io/v1beta1"
kind: "PeerAuthentication"
metadata:
  name: "default"
  namespace: "knative-serving"
spec:
  mtls:
    mode: PERMISSIVE
```


1. `curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.11.4 TARGET_ARCH=x86_64 sh -`
2. `chmod +x istio-1.11.4/bin/istioctl`
3. `istio-1.11.4/bin/istioctl  install -f infrastructure/istio/istio-operator.yaml --set profile=default`
4. `kubectl label namespace knative-serving istio-injection=enabled`
5. `kubectl apply -f infrastructure/istio/istio-peer-authentication.yaml`
6. check if it works `kubectl get pods --namespace istio-system`
7. `kubectl --namespace istio-system get service istio-ingressgateway`
8. `kubectl apply -f https://github.com/knative/net-istio/releases/download/knative-v1.0.0/net-istio.yaml`

_alternative:_
`kubectl apply -f infrastructure/istio/istio-v1.0.0-operator.yaml`
`kubectl apply -f infrastructure/istio/istio-v1.0.0-operator.yaml`
`kubectl label namespace knative-serving istio-injection=enabled`
`kubectl apply -f https://github.com/knative/net-istio/releases/download/knative-v1.0.0/net-istio.yaml`

_using knative istio yaml:_
`kubectl apply -l knative.dev/crd-install=true -f infrastructure/istio/knative-istio.yaml`
`kubectl apply -f infrastructure/istio/knative-istio.yaml`
`kubectl apply -f https://github.com/knative/net-istio/releases/download/knative-v1.0.0/net-istio.yaml`
`kubectl --namespace istio-system get service istio-ingressgateway`

**dns**
a. dns `kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.0.0/serving-default-domain.yaml`
b. adjust dns `kubectl edit cm config-domain --namespace knative-serving`
```bash
kubectl patch configmap/config-domain \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"infinity.huggingface.co":""}}'
```



**uninstall**
`istioctl x uninstall --purge`
`kubectl delete -f https://github.com/knative/net-istio/releases/download/knative-v1.0.0/net-istio.yaml`

_alternative:_
`kubectl delete -f https://github.com/knative/net-istio/releases/download/knative-v1.0.0/net-istio.yaml -f infrastructure/istio/istio-v1.0.0-operator.yaml`


**generate manifest for kubectl apply**
https://discuss.istio.io/t/setting-gateways-istio-ingressgateway-serviceannotations/5711/5
`istioctl manifest generate --set 'values.gateways.istio-ingressgateway.serviceAnnotations.service\.beta\.kubernetes\.io/aws-load-balancer-type=nlb' > generated.yaml`

### Upgrade knative Istio

get knative istio yaml -> add annotations for load balancer

```Bash
apiVersion: v1
kind: Service
metadata:
  name: istio-ingressgateway
  namespace: istio-system
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
```

This will create a NLB for the ingress gateway instead of a CLB.


# Deploy Knative Serving

```bash
kubectl apply -f hello_world.yaml
kubectl get ksvc
```

curl -H "Host: hello.default.example.com" http://a5adf19bc63b242b6b4999a1685ec3aa-2856ae13be6c2ef9.elb.us-east-1.amazonaws.com