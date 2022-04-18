#!/usr/bin/env python
from cdktf import App, TerraformStack
from constructs import Construct


class AzureStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        # define resources here
