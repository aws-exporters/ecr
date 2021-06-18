[![CodeQL](https://github.com/aws-exporters/ecr/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/aws-exporters/ecr/actions/workflows/codeql-analysis.yml)
[![Test and Lint](https://github.com/aws-exporters/ecr/actions/workflows/test-and-lint.yaml/badge.svg)](https://github.com/aws-exporters/ecr/actions/workflows/test-and-lint.yaml)

# ecr_exporter
A Prometheus exporter for AWS ECR.

## Motivation
ECR repositories and images have a lot of useful information, image sizes, repository
configuration, scan results... I'm sure there will be more.

Information that might be useful to display in some way on team based dashboards
alongside things like Kubernetes workload availability and Istio traffic metrics.

## Technical Design
This exporter makes use of `boto3` to query ECR for repositories and images, in
an attempt to be kind to the AWS APIs, results are cached and refreshed every
10 minutes (by default).

This is built as, and designed to run as a Docker container in Kubernetes using
the underlying instance IAM role or an IRSA role.

It uses the HTTP server provided by the `prom_client` library which exposes metrics
on a given port and doesn't care about paths.

### Configuration
Configuration is purely through environment variables:

| Variable | Description | Default | Example |
| -------- | ----------- | ------- | ------- |
| `APP_PORT` | The port to expose the exporter on | `9000` | `8080` |
| `APP_HOST` | The host to bind the application to | `0.0.0.0` | `localhost` |
| `CACHE_REFRESH_INTERVAL` | How many seconds to wait before refreshing caches in the background | `600` | `3600` |
| `ECR_REGISTRY_ID` | The ID of the registry to export metrics for | `current AWS account` | `112233445566` |
| `LOG_LEVEL` | How much or little logging do you want | `INFO` | `DEBUG` |

### Error Handling
Currently, there is very little in the way of error handling and all stack traces
are thrown out to the console. This will be improved as issues are encountered.