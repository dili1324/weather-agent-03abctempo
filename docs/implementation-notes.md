# Implementation Notes

## Phase 1

- Created repository structure.
- Added Python 3.12 CI workflow.
- Added daily GitHub Actions workflow scheduled for 07:00 Asia/Ho_Chi_Minh.
- Added `.env.example` and `.gitignore`.

## Phase 2

- Added OpenWeather MPP client flow.
- Added Telegram client.
- Added message formatter.
- Added logging and structured configuration.

## Phase 3

- Added Tempo CLI wrapper for MPP payments.
- Added optional GPT summary through OpenAI MPP.
- Kept GPT disabled by default to avoid dynamic spend unless explicitly enabled.

## Phase 4

- Added unit tests for non-payment code paths.
- Documented the Tempo Wallet GitHub Actions credential blocker.
- Added security checklist to README.
- Added `requirements-lock.txt` and switched GitHub Actions to install from it.
- Added step-level logging and duration metrics for Tempo Wallet checks, OpenWeather MPP calls, optional GPT calls, Telegram sending, and total runtime.

## Documentation Gap

The official Tempo docs found during implementation describe browser-based login, remote-host login URL, access keys, `tempo request`, `--dry-run`, and `--max-spend`. They do not describe a complete non-interactive GitHub Actions credential bootstrap mechanism. This repository therefore cannot honestly claim the scheduled paid workflow will succeed until you provide an officially supported way to make `tempo wallet whoami` return `ready=true` inside GitHub Actions.

## MVP / Proof of Concept Pivot

- Local macOS run is now the recommended first milestone.
- Added `docs/mvp-local-run.md` with step-by-step Mac mini instructions.
- Added `scripts/debug_checks.py` to test Tempo readiness, Telegram, OpenWeather MPP, and optional GPT MPP independently.
- Added `docs/github-actions-credential-experiment.md` for a test-wallet-only credential portability experiment.
- The GitHub Actions credential experiment is not official production guidance; it exists only to help validate whether a low-balance test wallet can run on hosted CI after local success.
- Added `pyproject.toml` so the `src/` layout is installed as an editable package instead of relying on `PYTHONPATH`.

## Local Access Key MVP

- Added `docs/access-key-local-run.md`.
- Tempo Wallet CLI `0.6.2` exposes `login`, `refresh`, `keys`, and `revoke`, but not a documented command to create a new access key with custom spending limit/expiry.
- Protocol and SDK docs confirm access keys support expiry, spending limits, recurring periods, call scopes, and revoke/update operations.
- `tempo request --help`, `--schema`, and `--llms-full` expose `--dry-run`, `--max-spend`, and `--private-key`, but no documented auto-approve / assume-yes / non-interactive / trusted-service / approval-policy flag.
- MPP managing-agent-spend docs describe unattended agent spend through wallet-provider Access Key authorization plus `mppx`, not through a `tempo request` pre-approval flag.
- Updated conclusion: local CLI wallet/access-key readiness is separate from payment approval. The current blocker is per-request browser/passkey payment approval by `tempo request`.

## Local MPPX SDK Research

- Added `docs/local-mppx-sdk-research.md`.
- Official Python MPP client exists and handles HTTP `402` automatically, but the documented Tempo example uses `TempoAccount.from_key("0x...")`; the docs reviewed do not show a Python passkey-wallet / Accounts SDK provider equivalent.
- Official TypeScript `mppx/client` supports `accounts` provider integration and can create a payment-aware `fetch` client with Tempo charge/session support.
- Official MPP spend-management docs show wallet-provider Access Key authorization with expiry, limits, scopes, and optional Access Key pinning through `provider.getMppxParameters({ accessKey })`.
- Current recommendation for local MVP v2 is a small Node/TypeScript helper for paid MPP requests, while Python remains the orchestrator and Telegram sender.

## Local MPPX SDK Spike

- Added `node_mppx/` as an isolated TypeScript helper.
- The helper does not replace the Python app and does not remove `tempo request` CLI fallback.
- Added `npm run connect` to authorize a small Tempo Access Key through the `accounts` provider.
- Added `npm run weather:once`, `npm run weather:twice`, `npm run geocode`, and `npm run current-weather`.
- The helper uses `mppx.fetch` for OpenWeather MPP `/geocode` and `/current-weather`.
- GPT and GitHub Actions remain out of scope for this spike.
- The installed SDK package exposes the local Node provider via `accounts/cli`; the helper now uses that typed API instead of the browser-style root `accounts` provider.
- `npm run typecheck` passes.
- `npm run connect` authorized an Access Key and saved local provider state.
- `npm run weather:once` and `npm run weather:twice` both completed through `mppx`.
- `weather:twice` made two complete OpenWeather flows in one process; all four paid requests created credentials and returned HTTP 200 without another browser/passkey approval prompt in the command output.

## Python mppx Weather Integration

- Added `WEATHER_PAYMENT_MODE=cli|mppx`.
- CLI mode remains the default and still uses `TempoRequestClient`.
- mppx mode calls the Node helper from Python through `MppxWeatherClient`.
- The Python app now skips the Tempo CLI wallet check when `WEATHER_PAYMENT_MODE=mppx` and GPT is disabled.
- Verified `WEATHER_PAYMENT_MODE=mppx ENABLE_GPT_SUMMARY=false python -m weather_agent` fetched OpenWeather through `mppx`, formatted the Telegram message, and sent Telegram successfully.
