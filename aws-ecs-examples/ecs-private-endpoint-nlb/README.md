# CDK Sample: Private cross-account APIs with Amazon API Gateway and AWS PrivateLink

This example creates an ECS Cluster with a private a VPC Endpoint for a secure, protected API. This example based on [apigateway-vpcendpoints](https://github.com/aws-samples/apigateway-vpcendpoints). Additional example [cross-account VPC access in AWS]( https://tomgregory.com/cross-account-vpc-access-in-aws/)

![image.jpeg](./image.png)

## Get started 

clone the repository 
```bash
git clone https://github.com/philschmid/cdk-samples.git
cd aws-ecs-examples/ecs-private-endpoint-nlb
```

Install the cdk required dependencies. Make your you have the [cdk](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html#getting_started_install) installed.
```bash
pip3 install -r requirements.txt
```

[Bootstrap](https://docs.aws.amazon.com/cdk/latest/guide/bootstrapping.html) your application in the cloud.

```bash
cdk bootstrap
```

Create Cluster with private VPC endpoint.

```bash
AWS_PROFILE=hf-sm cdk deploy 
```


# Todo

2. stack der vpc, sg, vpc endpoint und ec2 erstellt zum testen