# CDK for Terraform

Cloud Development Kit for Terraform (CDKTF) allows you to use familiar programming languages to define and provision infrastructure. This gives you access to the entire Terraform ecosystem without learning HashiCorp Configuration Language (HCL) and lets you leverage the power of your existing toolchain for testing, dependency management, etc.


## Examples
This repo contains examples the following examples. 

| Language | Description |
|----------|-------------------------|
| [AWS-EKS](https://github.com/hashicorp/terraform-cdk/tree/main/examples/python/aws-eks) | Creates an EKS Cluster with an VPC using Terraform modules. |

## Learning Resources
While this is an excellent learning resource for the CDK, there are other resources that can be referenced to assist with your learning/development process.

- [Developer Guide](https://www.terraform.io/docs/cdktf/index.html)
- [Get Started](https://learn.hashicorp.com/tutorials/terraform/cdktf-install?in=terraform/cdktf)
- [Examples](https://www.terraform.io/docs/cdktf/examples.html)
- [Provider & Modules](https://www.terraform.io/docs/cdktf/create-and-deploy/configuration-file.html)


## Installation & Getting Started

more [here](https://learn.hashicorp.com/tutorials/terraform/cdktf-install?in=terraform/cdktf)

Installation using `yarn` or `npm`.

```bash
npm install --global cdktf-cli
```


```bash
yarn global add cdktf-cli
```

Initalizing a project

```bash
mkdir aws-eks-with-module && cd aws-eks-with-module && \
cdktf init --template=python-pip --project-name aws-eks-with-module
```

## Create CDK Project based of existing Terraform project with `.tf` files

Create a new Typescript project from an existing Terraform codebase. Currently, you can only use the `--from-terraform-project`.

```bash
cdktf init --template=python --project-name my-new-cdk-project --from-terraform-project /Path/to/Project
```


## Commands

```bash
$ cdktf help
cdktf

Commands:
  cdktf convert [OPTIONS]          Converts a single file of HCL configuration to CDK for Terraform. Takes the file to be
                                   converted on stdin.
  cdktf deploy [stack] [OPTIONS]   Deploy the given stack                                                     [aliases: apply]
  cdktf destroy [stack] [OPTIONS]  Destroy the given stack
  cdktf diff [stack] [OPTIONS]     Perform a diff (terraform plan) for the given stack                         [aliases: plan]
  cdktf get [OPTIONS]              Generate CDK Constructs for Terraform providers and modules.
  cdktf init [OPTIONS]             Create a new cdktf project from a template.
  cdktf list [OPTIONS]             List stacks in app.
  cdktf login                      Retrieves an API token to connect to Terraform Cloud.
  cdktf synth [stack] [OPTIONS]    Synthesizes Terraform code for the given app in a directory.          [aliases: synthesize]
  cdktf watch [stack] [OPTIONS]    [experimental] Watch for file changes and automatically trigger a deploy

Options:
  --version                   Show version number                                                                    [boolean]
  --disable-logging           Dont write log files. Supported using the env CDKTF_DISABLE_LOGGING.   [boolean] [default: true]
  --disable-plugin-cache-env  Dont set TF_PLUGIN_CACHE_DIR automatically. This is useful when the plugin cache is configured
                              differently. Supported using the env CDKTF_DISABLE_PLUGIN_CACHE_ENV.  [boolean] [default: false]
  --log-level                 Which log level should be written. Only supported via setting the env CDKTF_LOG_LEVEL   [string]
  -h, --help                  Show help                                                                              [boolean]

Options can be specified via environment variables with the "CDKTF_" prefix (e.g. "CDKTF_OUTPUT")
```


# License 

This library is licensed under the Apache 2.0 License.