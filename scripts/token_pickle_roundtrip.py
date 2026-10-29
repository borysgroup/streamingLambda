"""Upload the Google OAuth token.pickle from a base64 env secret to S3, then
verify the same download -> refresh -> re-upload cycle the Lambda performs.

Usage: python scripts/token_pickle_roundtrip.py
Needs: boto3, google-auth (pip install boto3 google-auth), AWS credentials,
and GOOGLE_OAUTH_PICKLE_TOKEN_B64 (base64 of token.pickle) in the environment.
Never prints token material.
"""

import base64
import os
import pickle
import sys

import boto3

S3_KEY = os.environ.get("YOUTUBE_TOKEN_S3_KEY", "token/token.pickle")
REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-2"


def client(service):
    return boto3.client(service, region_name=REGION)


def resolve_bucket():
    bucket = os.environ.get("YOUTUBE_TOKEN_S3_BUCKET")
    if bucket:
        return bucket
    fn = client("lambda").get_function_configuration(
        FunctionName="picam-lambda-function"
    )
    return fn["Environment"]["Variables"]["YOUTUBE_TOKEN_S3_BUCKET"]


def main():
    b64 = (
        os.environ.get("GOOGLE_OAUTH_PICKLE_TOKEN_B64")
        or os.environ.get("GOOGLE_OAUTH_TOKEN_PICKLE_B64")
        or ""
    ).strip()
    if not b64:
        sys.exit("Token secret env var is missing or empty; nothing to upload.")

    raw = base64.b64decode(b64)
    creds = pickle.loads(raw)
    if not hasattr(creds, "refresh_token"):
        sys.exit(f"Decoded object is {type(creds).__name__}, not Credentials.")
    print(f"Decoded token.pickle: {len(raw)} bytes, valid Credentials object, "
          f"has refresh_token: {bool(creds.refresh_token)}")

    bucket = resolve_bucket()
    s3 = client("s3")
    s3.put_object(Bucket=bucket, Key=S3_KEY, Body=raw)
    print("Uploaded to S3.")

    # Same cycle as chalicelib/ytb_api_utils.py get_authenticated_service()
    fetched = s3.get_object(Bucket=bucket, Key=S3_KEY)["Body"].read()
    assert fetched == raw, "Downloaded bytes differ from uploaded bytes"
    creds = pickle.loads(fetched)
    from google.auth.transport.requests import Request

    creds.refresh(Request())
    print(f"Refresh succeeded; token valid: {creds.valid}, expiry: {creds.expiry}")

    s3.put_object(Bucket=bucket, Key=S3_KEY, Body=pickle.dumps(creds))
    print("Re-uploaded refreshed token. Round-trip complete.")


if __name__ == "__main__":
    main()
