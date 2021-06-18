import pytest

from ecr_exporter.collector import ECRMetricsCollector


def test_collector_without_values():
    with pytest.raises(TypeError):
        ECRMetricsCollector()
