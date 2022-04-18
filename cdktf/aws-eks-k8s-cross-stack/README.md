# Terraform CDK - Mutli-cloud Kuberenetes setup with AWS EKS Azure AKS

## Getting started

The project is an example on how to create a multi-cloud setup using Terraform CDK, AWS, Azure and kuberentes.

### Infrastructure

The Repository currently create a EKS + VPC to AWS and deploys an nginx demo app. _Azure coming soon._

**Requirements**

Install Terraform CDK. 
```Bash
npm install --global cdktf-cli@latest
```
verify installation
```bash
cdktf --version
```
get modules and provider
```bash
cdktf get
```

#### AWS

_Note: Before you are able to run this project you need to adjust the `aws_auth_roles` & `aws_auth_users` in [aws/main.py](./aws/main.py)_

Deploy HF endpoint infrastucture with
```bash
AWS_PROFILE=hf-sm cdktf deploy 'aws-*'
```
This will deploy the `aws-strack` and the `aws-kubernetes` to AWS.

#### Azure

_coming soon_

# Resources

* [CDKTF Documentation](https://www.terraform.io/cdktf)
* [CDKTF Getting started](https://learn.hashicorp.com/tutorials/terraform/cdktf?in=terraform/cdktf)
* [CDKTF Examples](https://github.com/hashicorp/terraform-cdk/tree/main/examples)
* [CDKTF v0.10.0 blog](https://www.hashicorp.com/blog/cdk-for-terraform-0-10-adds-multi-stack-deployments-and-more)
* [CDKTF aws-eks module example](https://github.com/hashicorp/terraform-cdk/blob/main/examples/typescript/aws-kubernetes/main.ts)
* [AWS EKS module](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest)
* [IAM Role for Service Accounts in EKS (autoscaling, external dns..)](https://github.com/terraform-aws-modules/terraform-aws-iam/tree/master/modules/iam-role-for-service-accounts-eks)
