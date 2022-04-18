from dataclasses import dataclass
from enum import Enum, EnumMeta
from typing import Optional, Union


class EnumDirectValueMeta(EnumMeta):
    def __getattribute__(cls, name):
        value = super().__getattribute__(name)
        if isinstance(value, cls):
            value = value.value
        return value


class CdktfEnum(Enum, metaclass=EnumDirectValueMeta):
    def __str__(self):
        return str(self.value)


class CloudProvider(CdktfEnum):
    AWS = "aws"
    AZURE = "azure"


class DeploymentStage(CdktfEnum):
    DEV = "dev"
    PROD = "prod"


class AwsRegion(CdktfEnum):
    US_EAST_1 = "us-east-1"
    EU_CENTRAL_1 = "eu-central-1"
    EU_WEST_1 = "eu-west-1"


class AzureRegion(CdktfEnum):
    US_EAST_1 = "us-east-1"
    EU_CENTRAL_1 = "eu-central-1"
    EU_WEST_1 = "eu-west-1"


@dataclass
class DeploymentEnvironment:
    provider: CloudProvider
    stage: DeploymentStage
    region: Union[AwsRegion, AzureRegion]
    name: str = "example"
    prefix: Optional[str] = None

    def __post_init__(self):
        self.prefix = f"{self.stage}-{self.name}"
