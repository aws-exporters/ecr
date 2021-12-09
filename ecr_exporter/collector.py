import boto3
import botocore
import logging

from prometheus_client.core import InfoMetricFamily, GaugeMetricFamily
from cachetools import TTLCache
from datetime import timezone


def _ecr_client():
    boto_config = botocore.client.Config(
        connect_timeout=2, read_timeout=10, retries={"max_attempts": 2}
    )
    session = boto3.session.Session()
    return session.client("ecr", config=boto_config)


class ECRMetricsCollector:
    def __init__(self, registry_id):
        self.logger = logging.getLogger()
        self.registry_id = (
            registry_id or _ecr_client().describe_registry()["registryId"]
        )
        self.repocache = TTLCache(1, 86400)
        self.imagecache = TTLCache(1000, 86400)

    def collect(self):
        repositories = self.repocache.get("cache")

        if repositories is None:
            self.refresh_repository_cache()
            repositories = self.repocache.get("cache")
        else:
            self.logger.debug("fetched repositories from cache")

        repository_count_metric = GaugeMetricFamily(
            "aws_ecr_repository_count",
            "Total count of all ECR repositories",
            labels=["registry_id"],
        )

        repository_count_metric.add_metric([self.registry_id], len(repositories))

        repository_info_metrics = InfoMetricFamily(
            "aws_ecr_repository", "ECR repository information"
        )

        for repo in repositories:
            repository_info_metrics.add_metric(
                [],
                {
                    "name": repo["repositoryName"],
                    "registry_id": repo["registryId"],
                    "repository_uri": repo["repositoryUri"],
                    "tag_mutability": repo["imageTagMutability"],
                    "scan_on_push": str(
                        repo["imageScanningConfiguration"]["scanOnPush"]
                    ).lower(),
                    "encryption_type": repo["encryptionConfiguration"][
                        "encryptionType"
                    ],
                },
            )

        image_common_label_keys = ["name", "tag", "digest", "registry_id", "image"]

        image_size_metrics = GaugeMetricFamily(
            "aws_ecr_image_size_in_bytes",
            "The size of an image in bytes",
            labels=image_common_label_keys,
        )

        image_push_timestamp_metrics = GaugeMetricFamily(
            "aws_ecr_image_pushed_at_timestamp_seconds",
            "The unix timestamp that this image was pushed at",
            labels=image_common_label_keys,
        )

        image_scan_metrics = GaugeMetricFamily(
            "aws_ecr_image_scan_severity_count",
            "ECR image scan summary results",
            labels=image_common_label_keys + ["severity"],
        )

        image_scan_timestamp_metrics = GaugeMetricFamily(
            "aws_ecr_image_scan_completed_at_timestamp_seconds",
            "The unix timestamp when the scan was completed",
            labels=image_common_label_keys,
        )

        for repo in repositories:
            images = self.imagecache.get(repo["repositoryName"])

            if images is None:
                self.refresh_image_cache(repositories)
                images = self.imagecache.get(repo["repositoryName"])
            else:
                self.logger.debug(f"fetched {repo['repositoryName']} images from cache")

            for image in images:
                tags = image.get("imageTags")
                if tags:
                    for tag in tags:
                        image_common_label_values = [
                            repo["repositoryName"],
                            tag,
                            image["imageDigest"],
                            self.registry_id,
                            f'{repo["repositoryUri"]}:{tag}',
                        ]

                        image_size_metrics.add_metric(
                            image_common_label_values,
                            int(image["imageSizeInBytes"]),
                        )
                        image_push_timestamp_metrics.add_metric(
                            image_common_label_values,
                            int(
                                image["imagePushedAt"]
                                .replace(tzinfo=timezone.utc)
                                .timestamp()
                            ),
                        )

                    scan_summary = image.get("imageScanFindingsSummary")
                    if scan_summary and scan_summary.get("findingSeverityCounts"):
                        severity_counts = scan_summary.get("findingSeverityCounts")
                        for severity in severity_counts:
                            image_scan_metrics.add_metric(
                                image_common_label_values + [severity],
                                int(severity_counts[severity]),
                            )
                        image_scan_timestamp_metrics.add_metric(
                            image_common_label_values,
                            int(
                                scan_summary["imageScanCompletedAt"]
                                .replace(tzinfo=timezone.utc)
                                .timestamp()
                            ),
                        )

        return [
            repository_count_metric,
            repository_info_metrics,
            image_size_metrics,
            image_push_timestamp_metrics,
            image_scan_metrics,
            image_scan_timestamp_metrics,
        ]

    def refresh_repository_cache(self):
        ecr_client = _ecr_client()
        self.logger.info("refreshing repositories cache")
        paginator = ecr_client.get_paginator("describe_repositories")
        repository_iterator = paginator.paginate(
            registryId=self.registry_id, PaginationConfig={"pageSize": 1000}
        )
        repositories = [
            repo for x in list(repository_iterator) for repo in x["repositories"]
        ]
        self.logger.debug(f"caching {len(repositories)} repositories")
        self.repocache["cache"] = repositories

    def refresh_image_cache(self, repositories, repository_name=""):
        ecr_client = _ecr_client()
        self.logger.info("refreshing image cache")
        paginator = ecr_client.get_paginator("describe_images")
        for repo in repositories:
            image_iterator = paginator.paginate(
                registryId=self.registry_id,
                repositoryName=repo["repositoryName"],
                filter={"tagStatus": "TAGGED"},
                PaginationConfig={"pageSize": 1000},
            )
            images = [
                image for x in list(image_iterator) for image in x["imageDetails"]
            ]

            self.imagecache[repo["repositoryName"]] = images
            self.logger.debug(
                f"refreshed cache with {len(images)} images for {repo['repositoryName']}"
            )

    def refresh_caches(self):
        self.refresh_repository_cache()
        repositories = self.repocache.get("cache")
        self.refresh_image_cache(repositories)
