# Azure Functions Terraform CDK example

This examples demonstrates how to deploy a Azure Functions app to Microsoft Azure using Terraform CDK and the Azure Functions CLI `func`. The examples contains two folders `infrastructure` and `testAppExample`, which contain the terraform cdk and function code. 

## Configure your local environment
Before you begin, you must have the following:

* An Azure account with an active subscription. [Create an account for free](https://azure.microsoft.com/free/?ref=microsoft.com&utm_source=microsoft.com&utm_medium=docs&utm_campaign=visualstudio).
* The [Azure Functions Core Tools version 4.x](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local#v2).
* One of the following tools for creating Azure resources:
  * Azure CLI version 2.4 or later.
  * The Azure Az PowerShell module version 5.9.0 or later.
* Python versions that are supported by Azure Functions

## Development

### Create new Azure Functions App

```bash
func init testAppExample --python
cd testAppExample
pip3 install -r requirements.txt
```

_P.S. You can add your python dependencies into the `requiremtents.txt`_

### Add Functions to your app

```bash
func new --name pingService --template "HTTP trigger" --authlevel "anonymous"
```

Get the list of templates by using the following command.

```bash
func templates list -l python
```

### Local Development 

You can test and develop locally with 

```bash
func start
```

### Deploy Functions to Azure

_**NOTE:** You must first deploy the `infrastucture` to deploy the functions_

```bash
func azure functionapp publish dev00ping00function
```

## Inrastucture

### Prerequisites

In order to use CDKTF, you need:
* The Terraform CLI (1.1+).
* Node.js and npm v16+.
* To follow the quickstart, you also need:
* Python v3.7 and pipenv v2021.5.29

To install the most recent stable release of CDKTF, use npm install with the @latest tag.
```bash
npm install --global cdktf-cli@latest
```

### Deploy the infrastructure

1. get the `azurerm` provider for terraform
```bash
cdktf get      
```
2. adjust the `config.py` with your preferred values
3. deploy the resources with
```bash
cdktf deploy
```

4. Now you can deploy the Azure functions app.
```bash
cd ../testAppExample
func azure functionapp publish dev00ping00function
```

## Clean Up

```bash
cd infrastructure
cdktf destory
```

## Resources

* [fastAPI example](https://docs.microsoft.com/en-us/samples/azure-samples/fastapi-on-azure-functions/azure-functions-python-create-fastapi-app/)
* [Quickstart: Create a Python function in Azure from the command line](https://docs.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-python?tabs=azure-cli%2Cbash%2Cbrowser)