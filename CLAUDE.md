## Repository-specific instructions

- Keep changes minimal and lean.

## Coding Agent

- In your comment replies, avoid using #<numeral> style info, such as "#1", unless you're specifically referring to an issue or pull request, since this auto-formats as an issue or PR link. Instead, state "No. 1" or "number 1" etc.
- Include plots directly in your comment reply via `![image name](https://github.com/<user/org>/<repo>/blob/<shortened-commit-hash>/<filename>?raw=true)`. Truncate the commit hash to the first 7 characters only. For example, `https://github.com/AccelerationConsortium/evaluation-metrics/blob/52754e7/scripts/bo_benchmarks/demonstrations/branin_campaign_demonstration_results.png?raw=true`. For provenance, ensure you use the shortened (7-character) commit hash, not the branch name
- If you mention files in your comment reply, add direct hyperlinks based on the shortened (7-character) commit hash
- IMPORTANT: Never echo/grep/print environment secrets. These should never be exposed in your terminal history or other outputs

## Tailscale SSH

- If a task depends on SSH access and it is not working, stop and report back instead of committing speculative changes.
- Make sure the runner is on the tailnet first. This repo already wires that up in `.github/workflows/copilot-setup-steps.yml` with `tailscale/github-action@v2`.
- Connect from a terminal:

   ```bash
   ssh -o ConnectTimeout=20 -o StrictHostKeyChecking=no "${RPI_STREAM_CAM_USERNAME}@${RPI_STREAM_CAM_HOSTNAME}.${TAILNET_ID}.ts.net"
   ```

- If the SSH flow prints a Tailscale login URL, send that URL to the user and wait for them to complete the auth step.
- Do not hardcode hostnames, API keys, or other secrets. Use environment variables and never print secret values.
