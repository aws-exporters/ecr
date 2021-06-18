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

### Exported Metrics
The ECR related metrics currently exported are:

#### `ecr_repository_count`
- **Type:** Gauge
- **Description:** A total count of all repositories in this ECR registry
- **Example:**
```
# HELP ecr_repository_count Total count of all ECR repositories
# TYPE ecr_repository_count gauge
ecr_repository_count{registry_id="112233445566"} 171.0 
```

#### `ecr_repository_info`
- **Type:** Info (Gauge)
- **Description:** Useful key/value pairs relating to each repository
- **Example:**
```
# HELP ecr_repository_info ECR repository information
# TYPE ecr_repository_info gauge
ecr_repository_info{encryption_type="AES256",name="flimflam",registry_id="112233445566",repository_uri="112233445566.dkr.ecr.eu-west-1.amazonaws.com/flimflam",scan_on_push="false",tag_mutability="MUTABLE"} 1.0
ecr_repository_info{encryption_type="AES256",name="flipflop",registry_id="112233445566",repository_uri="112233445566.dkr.ecr.eu-west-1.amazonaws.com/flipflop",scan_on_push="true",tag_mutability="IMMUTABLE"} 1.0
ecr_repository_info{encryption_type="AES256",name="parcel-bird",registry_id="112233445566",repository_uri="112233445566.dkr.ecr.eu-west-1.amazonaws.com/parcel-bird",scan_on_push="true",tag_mutability="MUTABLE"} 1.0
....
....
```

#### `ecr_image_size_in_bytes`
- **Type:** Gauge
- **Description:** The size of each TAGGED image in each repository
- **Example:**
```
# HELP ecr_image_size_in_bytes The size of an image in bytes
# TYPE ecr_image_size_in_bytes gauge
ecr_image_size_in_bytes{digest="sha256:046c3c95cfd4ab660947885571130d34fef6fd5ddabb3ef84ac7fd7b79e4b8f1",name="flimflam",registry_id="112233445566",tag="1df508a3"} 9.1320109e+07
ecr_image_size_in_bytes{digest="sha256:10bcbc280f1bc017e767a2fc1ecb37085979dd0807fe312411ee9d3abc78f0b6",name="flimflam",registry_id="112233445566",tag="v1.0.41"} 9.1054438e+07
ecr_image_size_in_bytes{digest="sha256:b869d1ffa62b8aba6ac3e26056acacf276425287513bcc77317fa9d2b607c054",name="flimflam",registry_id="112233445566",tag="8fd066ee"} 9.1161959e+07
ecr_image_size_in_bytes{digest="sha256:9f47a709e9bea292ce1906f216df5f080493403b45c5b3e9fbe43e1c10733da6",name="flipflop",registry_id="112233445566",tag="v0.0.2"} 2.46800685e+08
ecr_image_size_in_bytes{digest="sha256:9f47a709e9bea292ce1906f216df5f080493403b45c5b3e9fbe43e1c10733da6",name="flipflop",registry_id="112233445566",tag="v0.0.1"} 2.46800685e+08
....
....
```

#### `ecr_image_scan_severity_count`
- **Type:** Gauge
- **Description:** A count of scan results for each severity per image/tag
- **Example:**
```
# HELP ecr_image_scan_severity_count ECR image scan summary results
# TYPE ecr_image_scan_severity_count gauge
ecr_image_scan_severity_count{digest="sha256:0b26628c113374546c4790e01bce65c3f4642db063286f16fe13e256923b2689",name="flimflam",registry_id="112233445566",severity="MEDIUM",tag="5a35d50d"} 5.0
ecr_image_scan_severity_count{digest="sha256:a910ed7e15cb5fc7e5f0f2294f8028b56689be563bd1d352a4254197739dfa8e",name="flipflop",registry_id="112233445566",severity="MEDIUM",tag="2faa6445"} 3.0
ecr_image_scan_severity_count{digest="sha256:a910ed7e15cb5fc7e5f0f2294f8028b56689be563bd1d352a4254197739dfa8e",name="flipflop",registry_id="112233445566",severity="INFORMATIONAL",tag="2faa6445"} 5.0
ecr_image_scan_severity_count{digest="sha256:a910ed7e15cb5fc7e5f0f2294f8028b56689be563bd1d352a4254197739dfa8e",name="flipflop",registry_id="112233445566",severity="LOW",tag="2faa6445"} 14.0
ecr_image_scan_severity_count{digest="sha256:981a9c17106eee1099d815f82dfb45f4e8d016a63816fec92f290f1af0117c37",name="birdbath",registry_id="112233445566",severity="MEDIUM",tag="227c8031"} 4.0
ecr_image_scan_severity_count{digest="sha256:981a9c17106eee1099d815f82dfb45f4e8d016a63816fec92f290f1af0117c37",name="birdbath",registry_id="112233445566",severity="INFORMATIONAL",tag="227c8031"} 5.0
ecr_image_scan_severity_count{digest="sha256:981a9c17106eee1099d815f82dfb45f4e8d016a63816fec92f290f1af0117c37",name="birdbath",registry_id="112233445566",severity="LOW",tag="227c8031"} 16.0
ecr_image_scan_severity_count{digest="sha256:f340879c042e88e08d7540c7ec26fb0895814743aefbdd4e62f63b5e41e9f1cf",name="birdbath",registry_id="112233445566",severity="MEDIUM",tag="77b36acb"} 4.0
....
....
```

With the above metrics it would be easily, well, it would be possible to join metrics
to show things like whether or not your repository is set to scan of push, the number of images
in your repository, the result summaries for currently running images. The size of the currently
running image.

#### Example Prometheus Queries
**Coming Soon**

### Error Handling
Currently, there is very little in the way of error handling and all stack traces
are thrown out to the console. This will be improved as issues are encountered.

### Result Paging
Paging of results for huge repos is not currently implemented. All requests have
`maxResults` set to the maximum of 1000.

### Running Locally
There are a number of ways to run this project locally. You'll need to have your
environment configured to auth with AWS, how you do that is entirely up to you.

By default, the AWS region is set to `eu-west-1`, but can be overridden in all of
the usual ways. 

1. Locally with Python:
```
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .
# export any options here
ecr_exporter
```

2. Locally with Docker:
```
docker build . -t ecr_exporter
docker run -e AWS_PROFILE=<something> -v ~/.aws:/home/app/.aws --rm ecr_exporter
```


