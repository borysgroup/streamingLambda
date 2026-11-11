# YouTube Streaming Lambda Function

This repository holds the AWS Lambda function (`picam-lambda-function`) that creates and ends YouTube livestreams for the [monitoring devices](https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html). The handler is `lambda_function.lambda_handler`. Pushes to `main` that touch the function code are built with `build-deployment-zip.sh` and deployed by `.github/workflows/deploy.yaml`.
