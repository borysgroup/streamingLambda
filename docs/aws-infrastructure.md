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
- Holds the **real Google OAuth token** at `token/token.pickle` (uploaded 2026-07-08, fourth
  session, from the `GOOGLE_OAUTH_TOKEN_PICKLE_B64` secret via
  [`scripts/token_pickle_roundtrip.py`](../scripts/token_pickle_roundtrip.py)). Note: this token
  is slated to be replaced with one from a different Google account; re-run the same script after
  the secret is swapped.
- Find the name with `aws s3 ls`, or read the function's `YOUTUBE_TOKEN_S3_BUCKET` env var.

## Verified state (2026-07-08, fourth session) — pipeline fully working

- Token round-trip: secret decoded → valid `Credentials` with a refresh token → uploaded to S3 →
  downloaded → `creds.refresh()` **succeeded against Google** → refreshed token re-uploaded.
- Via the `LAMBDA_FUNCTION_URL` secret: invalid-action probe → `400`; **`create` probe → `200`**
  with a real private broadcast (broadcast/stream/RTMP URL all returned), and `end` → `200`.
  The test broadcast and its stream were then deleted via the YouTube API so no test artifacts
  remain on the channel. Livestreaming is enabled on the token's account.
- One transient wart in the `create` response: `playlist_add_status` failed with a YouTube
  `409 SERVICE_UNAVAILABLE` on `playlistItems.insert` — the broadcast itself was fine; worth
  watching whether it recurs.
- ⚠️ The `create` response **includes the RTMP stream key in plain text** — anyone holding the
  unauthenticated endpoint URL gets valid stream keys by design. Keep the URL secret, and treat
  any key that leaks into logs as burned (the test one from this session was invalidated by
  deleting its stream).

## Remaining steps

1. **Token swap** — replace the `GOOGLE_OAUTH_TOKEN_PICKLE_B64` secret with the new account's
   token once its 24-hour livestreaming enablement completes, then re-run
   [`scripts/token_pickle_roundtrip.py`](../scripts/token_pickle_roundtrip.py).
2. **`picam-http-api`** — redundant now that the bare function URL works; delete if unwanted.
3. **Camera** — Pi-side setup (`device.py`, `device.service`, crontab 8-hour chunk reboots,
   watchdog/heartbeat) once SSH access is granted; the playbook is in
   [`ac-training-lab-picam-suggestions.md`](./ac-training-lab-picam-suggestions.md) and the PR 2 archive.
