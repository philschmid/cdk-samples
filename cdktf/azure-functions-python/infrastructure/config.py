from dataclasses import dataclass, field
from enum import Enum, EnumMeta
from typing import Dict, Optional, Union


class EnumDirectValueMeta(EnumMeta):
    def __getattribute__(cls, name):
        value = super().__getattribute__(name)
        if isinstance(value, cls):
            value = value.value
        return value


class CdktfEnum(Enum, metaclass=EnumDirectValueMeta):
    def __str__(self):
        return str(self.value)


class DeploymentStage(CdktfEnum):
    DEV = "dev"
    PROD = "prod"


class AzureRegion(CdktfEnum):
    EAST_US = "East Us"
    CENTRAL_US = "Central Us"
    WEST_EUROPE = "West Europe"


@dataclass
class StackVariables:
    name: str = ""
    location: AzureRegion = AzureRegion.EAST_US
    stage: DeploymentStage = DeploymentStage.DEV
    tags: Dict[str, str] = field(default_factory=lambda: {})

    def __post_init__(self):
        self.rg_name = f"{self.stage}-{self.name}"
        self.storage_name = f"{self.stage}00{self.name}00storage"
        self.sc_name = f"{self.stage}00{self.name}00container"
        self.ap_name = f"{self.stage}00{self.name}00insights"
        self.sp_name = f"{self.stage}00{self.name}00service-plan"
        self.function_name = f"{self.stage}00{self.name}00function"
        # tags
        self.tags = {
            **{
                "ENV": self.stage,
            },
            **self.tags,
        }
