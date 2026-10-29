# AWS IAM: `stream-manager` intermediate user

Created 2026-07-08 (issue No. 3) so the root credentials can be retired from the agent environment.

## What exists

- **IAM user:** `stream-manager` (tags: `purpose=streaming-lambda-setup`, `created-by=claude-issue-3`)
- **Customer-managed policy:** `stream-manager-policy`, attached to the user. Source of truth: [`stream-manager-policy.json`](./stream-manager-policy.json)

What it can do: everything needed for the streaming pipeline setup — full Lambda (create/update/deploy, env vars, function URLs), full S3 (token bucket etc.), CloudWatch Logs, API Gateway (for Chalice deploys later), and create/manage Lambda **execution roles**.

What it deliberately cannot do: manage IAM users/groups or credentials (no `iam:CreateUser`, `iam:CreateAccessKey`, `iam:AttachUserPolicy`, …), and `iam:PassRole` only works when the role is passed to `lambda.amazonaws.com`. So it cannot escalate its own permissions or mint new identities.

What was intentionally **not** created: access keys and a console login profile. No secret material exists for this user yet.

> **Status 2026-07-08:** handoff complete. An access key for `stream-manager` now reaches the
> agent environment, `aws sts get-caller-identity` returns the `stream-manager` ARN, and the
> root-level access key was deleted. The infrastructure this user was created to build is
> documented in [`aws-infrastructure.md`](./aws-infrastructure.md).

## Handoff (root user does this)

1. **Access key:** AWS console → IAM → Users → `stream-manager` → Security credentials → Create access key → "Application running outside AWS".
2. **Store as secrets** using the naming scheme from the prior PR — `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` = `us-east-2` — in the same places the current AWS secrets live (the agent workflow env and/or the Copilot agent environment), replacing the root values.
3. **Console password (optional):** only needed if you want to log in *as* `stream-manager`. Yes — you can do this entirely yourself with the root login: IAM → Users → `stream-manager` → Security credentials → Enable console access, and set/rotate the password there. No password ever needs to pass through the agent or email.
4. **Retire root:** once `aws sts get-caller-identity` under the new keys returns the `stream-manager` ARN, remove the root credentials from all agent environments.
