from infrastructure.custom_resource_handler import kubectl
import pytest


def test_istio_knative_cluster_creation():
    kubectl("apply", "infrastructure/istio/knative-istio.yaml")

    kubectl("delete", "infrastructure/istio/knative-istio.yaml")
