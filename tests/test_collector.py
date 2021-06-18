import boto3
import pytest
from botocore.stub import Stubber

from ecr_exporter.collector import ECRMetricsCollector


def test_collector_without_values():
    with pytest.raises(TypeError):
        ECRMetricsCollector()