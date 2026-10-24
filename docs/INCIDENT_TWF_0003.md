# TWF-0003 — Copilot secret presence preflight failed (NO CHARGE)

Date: 2026-10-24.
Evidence: https://github.com/kk051780/toy-wars-factory/actions/runs/40049282533

- The secure GitHub Actions job evaluated `secrets.COPILOT_GITHUB_TOKEN != ''` as **false** on branch `setup/agentic-runtime-probe`.
- The GitHub connection, Actions runner, gh-aw compiler and agent candidate integrity checks are working; **model inference was not invoked**.
- The failure indicates the workflow could not access a nonempty secret with exactly that name. It does not reveal token contents or verify any Copilot license.
- Next action: owner checks GitHub repository settings > Secrets and variables > Actions > **Repository secrets**, the exact name `COPILOT_GITHUB_TOKEN`, and if necessary re-adds the fine-grained personal PAT. **Never share token in chat, PR or source code.**
- After owner confirms, rerun the same presence-only workflow. Then perform an independently approved one-off AI-inference trial; do not enable the 20-minute recurring schedule until a real, QA-passing AI-generated PR has been observed.
- Cost policy: 1 AI Credit (AIC) is $0.01 USD in gh-aw's modeled cost accounting, but Copilot plan allocation and GitHub Actions usage are billed separately. The 25 AIC/run guard is not a total-spend cap and threat-detection/evaluation phases may incur separate AI credits. User financial approval required first.
- Prevention: secret-presence check before inference, never log the token, require actual action-run evidence and stop on missing credentials.
