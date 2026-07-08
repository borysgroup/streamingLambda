# AWS infrastructure (account 6030…, region `us-east-2`)

Set up 2026-07-08 (issue No. 3) by the `stream-manager` IAM user — see
[`aws-iam-stream-manager.md`](./aws-iam-stream-manager.md). Mirrors the pipeline from the prior
vertical-cloud-lab setup (PR 2 there; archived in [`pr2-comment-archive.md`](./pr2-comment-archive.md)).

Deliberately **not** written down here: the token bucket name and the function URL. Both are
retrievable with the `stream-manager` credentials (commands below) or in the AWS console; keeping
them out of the public repo follows the practice established in PR 2.

## Lambda

- **Function:** `picam-lambda-function` — runtime `python3.12`, handler `lambda_function.lambda_handler`,
  timeout 60 s, memory 512 MB.
- **Code:** `deployment.zip` built by [`build-deployment-zip.sh`](../build-deployment-zip.sh)
  (pinned `manylinux2014_x86_64` wheels — verified the shipped `cryptography` `_rust.abi3.so` is
  x86-64, avoiding the ARM-build 502 from PR 2).
- **Env vars:** `YOUTUBE_TOKEN_S3_BUCKET`, `YOUTUBE_TOKEN_S3_KEY` = `token/token.pickle`
  (read by `chalicelib/ytb_api_utils.py`).
- **Function URL:** auth type `NONE` + resource policy `FunctionURLAllowPublicAccess`
  (`lambda:InvokeFunctionUrl`, principal `*`, condition `lambda:FunctionUrlAuthType = NONE`) —
  same shape as the prior working setup. Retrieve it with:

  ```bash
  aws lambda get-function-url-config --function-name picam-lambda-function \
    --query FunctionUrl --output text
  ```

## Execution role

- **Role:** `picam-lambda-execution-role` (trusts `lambda.amazonaws.com`), carrying exactly:
  - managed `AWSLambdaBasicExecutionRole` (CloudWatch Logs), and
  - inline `pickle-token-bucket`: `s3:GetObject`/`s3:PutObject` on `token/*` in the token bucket
    plus `s3:ListBucket` on the bucket (so a missing token reads as 404, not a masked 403).

  This is the complete least-privilege set identified at the end of PR 2: read the YouTube token,
  write the refreshed token back, emit logs. Nothing else.

## S3 token bucket

- Region `us-east-2`, all four public-access blocks on, default SSE-S3 (AES256) encryption.
- Currently **empty** — the pipeline is blocked on the `token.pickle` upload (see below).
- Find the name with `aws s3 ls`, or read the function's `YOUTUBE_TOKEN_S3_BUCKET` env var.

## Verified state (2026-07-08)

- Invalid-action probe → clean `400` (imports fine on `python3.12`, handler healthy).
- `create` probe → `500` with S3 **404** `HeadObject … Not Found` on the token object — exactly
  the expected failure while the pickle doesn't exist yet; the S3 wiring and role permissions are
  correct (a permissions problem would surface as 403, as it did in PR 2).

## Remaining steps (blocked on inputs)

1. **`token.pickle`** — upload to `s3://<TOKEN_BUCKET>/token/token.pickle`, or add it (base64) as
   a repo secret so the agent can upload and run the download/refresh/re-upload tests
   (PR 2, comment No. 46).
2. **`LAMBDA_FUNCTION_URL` secret** — set from the `get-function-url-config` output above, for the
   Pi's `my_secrets.py` and the agent env.
3. **Region env var** — `AWS_REGION` reaches the agent env but is currently **empty**; set it (or
   `AWS_DEFAULT_REGION`) to `us-east-2`.
4. **Camera** — Pi-side setup (`device.py`, `device.service`, crontab 8-hour chunk reboots,
   watchdog/heartbeat) once SSH access is granted; the playbook is in
   [`ac-training-lab-picam-suggestions.md`](./ac-training-lab-picam-suggestions.md) and the PR 2 archive.
