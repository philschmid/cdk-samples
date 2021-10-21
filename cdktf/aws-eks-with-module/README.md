# AWS EKS with Terraform modules


The `cdktf.json` contains the provider and the terraform modules, which we use in this example.

```json
{
  "language": "python",
  "app": "python3 ./main.py",
  "projectId": "ae86c9aa-33a9-491e-a8a8-926f1fb7c31d",
  "terraformProviders": [
    {
      "name": "aws",
      "source": "hashicorp/aws",
      "version": "~> 3.22"
    }
  ],
  "terraformModules": [
    {
      "name": "vpc",
      "source": "terraform-aws-modules/vpc/aws",
      "version": "2.77.0"
    },
    {
      "name": "eks",
      "source": "terraform-aws-modules/eks/aws",
      "version": "~> 14.0"
    }
  ],
  "codeMakerOutput": "imports",
  "context": {
    "excludeStackIdFromLogicalIds": "true",
    "allowSepCharsInLogicalIds": "true"
  }
}

```