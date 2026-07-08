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
- **Function URL:** auth type `NONE`, **publicly reachable and working** (verified 2026-07-08,
  second session). The initial `FunctionURLAllowPublicAccess` statement (`lambda:InvokeFunctionUrl`,
  principal `*`, condition `lambda:FunctionUrlAuthType = NONE`) alone produced
  `403 AccessDeniedException` on this account; the console's own hint held the fix — this account
  also requires `lambda:InvokeFunction` for principal `*`. That statement
  (`FunctionURLAllowInvokeAction`, condition `lambda:InvokedViaFunctionUrl = true`) was added
  manually via the console and anonymous invokes now succeed. Retrieve the URL with:

  ```bash
  aws lambda get-function-url-config --function-name picam-lambda-function \
    --query FunctionUrl --output text
  ```

## API Gateway HTTP API (alternate public endpoint)

While the function URL was 403ing, a **HTTP API** (`picam-http-api`, API Gateway v2
quick-create: `$default` stage, auto-deploy, `$default` route → Lambda proxy) was stood up to
front the function; it also works. The Lambda resource policy grants `lambda:InvokeFunction` to
`apigateway.amazonaws.com` scoped to this API's `execute-api` ARN. The request/response contract
is identical through either endpoint. Now that the bare function URL works, **either** can be
`LAMBDA_FUNCTION_URL`; the HTTP API can be deleted if you prefer the function URL. Retrieve it with:

```bash
aws apigatewayv2 get-apis --query 'Items[?Name==`picam-http-api`].ApiEndpoint' --output text
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
- Holds a **dummy placeholder** at `token/token.pickle` (a 104-byte pickled dict tagged
  `DUMMY PLACEHOLDER`, uploaded 2026-07-08) so the S3 path is exercised end-to-end; it must be
  overwritten with the real Google OAuth `token.pickle` before streams can be created.
- Find the name with `aws s3 ls`, or read the function's `YOUTUBE_TOKEN_S3_BUCKET` env var.

## Verified state (2026-07-08, second session)

- Anonymous invalid-action probe **via the bare function URL** → clean `400` (public access works).
- `create` probe → `500` `'dict' object has no attribute 'expired'` — the Lambda successfully
  downloaded and unpickled the placeholder from S3 and failed only where real Google credentials
  are needed. Every layer (URL → Lambda → role → S3) is verified; only the real token is missing.

## Remaining steps (blocked on inputs)

1. **`token.pickle`** — overwrite the placeholder at `s3://<TOKEN_BUCKET>/token/token.pickle`
   with the real one, or add it (base64: `base64 -w 0 token.pickle` on Linux,
   `base64 -i token.pickle` on macOS) as a repo secret so the agent can upload and run the
   download/refresh/re-upload tests (PR 2, comment No. 46).
2. **`LAMBDA_FUNCTION_URL` secret** — set to either the function URL or the HTTP API endpoint
   (both work now), for the Pi's `my_secrets.py` and the agent env.
3. **Region env var** — the resources are in **`us-east-2`** (us-east-1 holds nothing).
   `claude.yml` doesn't currently pass `AWS_REGION` through to the agent env, so add
   `AWS_REGION: us-east-2` (a literal value is fine — the region isn't secret) to the `env:`
   block of the `Run Claude Code` step; the agent cannot edit workflow files itself.
4. **Camera** — Pi-side setup (`device.py`, `device.service`, crontab 8-hour chunk reboots,
   watchdog/heartbeat) once SSH access is granted; the playbook is in
   [`ac-training-lab-picam-suggestions.md`](./ac-training-lab-picam-suggestions.md) and the PR 2 archive.
