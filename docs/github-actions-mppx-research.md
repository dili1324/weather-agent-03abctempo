# GitHub Actions mppx Research

This document researches and documents the manual GitHub Actions mppx experiment after local MVP v2.

## Scope

Goal: determine whether GitHub Actions hosted runners can run:

```bash
WEATHER_PAYMENT_MODE=mppx python -m weather_agent
```

after a Tempo Access Key has been authorized locally through `node_mppx` and the `accounts/cli` provider.

Out of scope for this step:

- raw private keys,
- main wallet usage,
- GPT MPP,
- scheduled GitHub Actions,
- production security guarantees.

## Current Local Baseline

Local MVP v2 is working:

- `node_mppx` uses `mppx` + `accounts/cli`.
- `npm run connect` authorizes a limited Access Key once.
- `npm run weather:once` and `npm run weather:twice` can call OpenWeather MPP without another per-payment browser/passkey approval.
- Python can call the Node helper via `WEATHER_PAYMENT_MODE=mppx`.
- Telegram send works from the Python app.

## What the SDK Stores Locally

The installed package versions are pinned in `node_mppx/package-lock.json`:

- `accounts@0.14.11`
- `mppx@0.8.5`
- `viem@2.54.2`

The local Node helper imports:

```ts
import { Provider } from 'accounts/cli'
```

The `accounts/cli` storage source defines the default path:

```text
~/.tempo/wallet/store.json
```

The source also sets secure local permissions:

- directory mode: `0700`
- file mode: `0600`

Local metadata inspection, with values redacted, shows:

```text
top_level_keys: tempo-cli.store
state_keys: accessKeys, accounts, activeAccount, chainId
accounts: 1
accessKeys: 24
accessKey item keys: access, address, chainId, expiry, handle, keyType, limits, publicKey
chainId: 4217
```

Important security interpretation:

- `handle` is not harmless metadata.
- `accounts/src/core/Keystore.ts` says a keystore handle is persisted verbatim and later turns the stored record back into a signing account.
- `accounts/src/cli/adapter.ts` explicitly uses an extractable p256 WebCrypto key because CLI filesystem storage must survive process restart.
- Therefore `~/.tempo/wallet/store.json` must be treated as a spend-capable credential, bounded only by the Access Key's expiry, limits, scopes, wallet balance, and revocation status.

## Can GitHub Hosted Runner Reuse the Local Access Key?

Technical conclusion: **likely yes, but experimental**.

Reasoning:

1. The CLI provider storage is a JSON file under `~/.tempo/wallet/store.json`.
2. The stored access-key record includes the account, public key, signed key authorization, limits, expiry, and a keystore handle.
3. The CLI keystore is designed to persist through filesystem storage.
4. The Python mppx mode does not call `wallet_connect`; it calls `npm run weather:once`, and `weather.ts` starts by reading existing provider state through:

```ts
const accounts = await provider.request({ method: 'eth_accounts' })
```

5. If restored state is valid, the helper can build `mppx` credentials without opening browser/passkey.
6. A GitHub hosted runner is ephemeral, so the state must be restored on every run before calling the Python app.

What is not yet official:

- I did not find official Tempo/Mpp docs saying to export `~/.tempo/wallet/store.json` to GitHub Secrets.
- This should be treated as an MVP experiment with a test wallet, not production guidance.

## Proposed GitHub Secrets and Variables

Secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TEMPO_ACCOUNTS_CLI_STORE_B64`

Variables:

- `WEATHER_PAYMENT_MODE=mppx`
- `WEATHER_CITY_QUERY=Hanoi,VN`
- `WEATHER_UNITS=metric`
- `WEATHER_LANG=vi`
- `ENABLE_GPT_SUMMARY=false`
- `MPPX_COMMAND_TIMEOUT_SECONDS=120`

The initial manual experiment workflow sets these variables directly inside the workflow. You can move them to repository Variables later after the experiment is stable.

Do not add:

- private key,
- seed phrase,
- main wallet credential,
- `node_modules`,
- `.env`.

## How to Create the Experimental Store Secret

After local `npm run connect` succeeds, encode the local store:

```bash
base64 < "$HOME/.tempo/wallet/store.json"
```

Put the resulting text into GitHub Secret:

```text
TEMPO_ACCOUNTS_CLI_STORE_B64
```

Do not commit this file or the base64 output. Base64 is transport encoding, not encryption.

Recommended local Access Key policy before exporting:

```bash
cd node_mppx
export MPPX_ACCESS_KEY_DAILY_LIMIT_USDC=0.25
export MPPX_ACCESS_KEY_EXPIRY_DAYS=1
npm run connect
npm run weather:twice
```

Then export the store immediately after confirming it works.

## How the Runner Would Restore State

Experimental restore step:

```bash
mkdir -p "$HOME/.tempo/wallet"
chmod 700 "$HOME/.tempo" "$HOME/.tempo/wallet"
printf '%s' "$TEMPO_ACCOUNTS_CLI_STORE_B64" | base64 --decode > "$HOME/.tempo/wallet/store.json"
chmod 600 "$HOME/.tempo/wallet/store.json"
```

After that, the runner should install dependencies and run:

```bash
cd node_mppx
npm ci
npm run typecheck
npm run weather:once
cd ..
WEATHER_PAYMENT_MODE=mppx ENABLE_GPT_SUMMARY=false python -m weather_agent
```

`npm run weather:once` is a useful canary before sending Telegram. For the first experiment, `npm run weather:twice` is better because it proves repeated paid calls work on the hosted runner without prompt.

## Manual Experiment Workflow

The manual-only experiment workflow is:

```text
.github/workflows/weather-agent-mppx-experiment.yml
```

It has only:

```yaml
on:
  workflow_dispatch:
```

It intentionally has no `schedule`.

Workflow steps:

1. `actions/checkout`
2. `actions/setup-python` with Python `3.12`
3. `actions/setup-node` with Node `24`
4. Install Python dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
python -m pip install --no-build-isolation -e .
```

5. Install Node dependencies with `npm ci`:

```bash
cd node_mppx
npm ci
npm run typecheck
cd ..
```

6. Restore `~/.tempo/wallet/store.json` from `TEMPO_ACCOUNTS_CLI_STORE_B64`.
7. Run `npm run typecheck`.
8. Run a paid mppx canary:

```bash
cd node_mppx
npm run weather:twice
cd ..
```

9. Run the Python app:

```bash
WEATHER_PAYMENT_MODE=mppx ENABLE_GPT_SUMMARY=false python -m weather_agent
```

Cache:

- Node: `actions/setup-node` supports npm cache and `cache-dependency-path`.
- Python: pip cache is optional.
- Do **not** cache `~/.tempo`, `node_modules`, `.env`, or any wallet state.
- The workflow may cache npm package downloads only; it must not cache wallet state.

## Can It Run Without Browser/Passkey?

Expected answer: **yes if restored state is valid**.

The hosted runner cannot complete browser/passkey approval unattended. The only viable hosted-runner path is:

1. authorize Access Key locally,
2. export the resulting filesystem state,
3. restore it on the runner,
4. run only code paths that do not call `wallet_connect`.

The current mppx weather path fits that model because it loads `eth_accounts` from local state and does not call `npm run connect`.

If the state is missing or invalid, the helper should fail with an error like:

```text
No local wallet account available. Run npm run connect first.
```

or fail to create a payment credential. It should not be expected to open a useful browser/passkey flow on GitHub hosted runners.

## Risks

`TEMPO_ACCOUNTS_CLI_STORE_B64` is effectively a scoped spending credential.

Risks:

- Anyone with access to the secret may be able to spend from the test wallet within the Access Key limits.
- A misconfigured workflow could print or upload the restored store.
- Forked PRs and debug steps must not receive this secret.
- A broad Access Key limit or long expiry increases blast radius.
- GitHub hosted runners are disposable, so restore must happen every run.
- If the SDK storage format changes, the restored file may stop working after dependency upgrades.

Risk controls:

- Use only a secondary/test Tempo Wallet.
- Keep wallet balance small.
- Use short expiry, such as 1 day for experiments.
- Use a very small daily limit, such as 0.25 USDC or less if supported.
- Keep `ENABLE_GPT_SUMMARY=false` for the hosted-runner experiment.
- Pin Node dependencies with `package-lock.json`.
- Never cache `~/.tempo`.
- Rotate the Access Key by running `npm run connect` again and replacing the GitHub Secret.
- Revoke stale/unwanted Access Keys from Tempo Wallet tooling where supported.
- Run only on `workflow_dispatch` first, not schedule.

## If State Restore Fails

If restored `store.json` cannot sign on the hosted runner:

1. Confirm `~/.tempo/wallet/store.json` exists and is mode `0600`.
2. Confirm `TEMPO_ACCOUNTS_CLI_STORE_B64` decodes without extra shell quoting.
3. Confirm `node_mppx/package-lock.json` versions match local.
4. Run `npm run weather:once` before Python to isolate Node helper failure.
5. Re-authorize locally with a fresh Access Key and update the secret.

If it still fails, the likely next option is a self-hosted runner on a machine where the provider state already exists and can remain on disk. That could be a Mac mini or another always-on machine, but it conflicts with the original "no machine needs to stay on" preference.

## Conclusion

Technical conclusion: **GitHub hosted runner support is likely feasible but experimental**.

The strongest path is to restore the `accounts/cli` filesystem state from an encrypted GitHub Secret and run `WEATHER_PAYMENT_MODE=mppx`.

This is not an official production credential bootstrap documented by Tempo/Mpp. It is an MVP experiment with controlled risk. Proceed only with:

- test wallet,
- small balance,
- short expiry,
- low daily limit,
- manual `workflow_dispatch` first,
- no GPT,
- no schedule until the hosted-runner canary succeeds.

## Proposed Next Phase

Phase 2A: manual GitHub Actions mppx canary.

1. Add secret `TEMPO_ACCOUNTS_CLI_STORE_B64`.
2. Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` if not already present.
3. Open GitHub Actions.
4. Select `Weather Agent mppx Experiment`.
5. Run the workflow manually with `workflow_dispatch`.
6. Confirm `npm run weather:twice` passes.
7. Confirm the Python app sends Telegram.
8. Only after this works, consider a separate scheduled mppx workflow or updating the existing scheduled workflow.

## Sources

- MPP managing agent spend: https://mpp.dev/guides/managing-agent-spend
- MPP client quickstart: https://mpp.dev/quickstart/client
- GitHub `actions/setup-node`: https://github.com/actions/setup-node
- GitHub `actions/setup-python`: https://github.com/actions/setup-python
- Installed SDK source inspected locally:
  - `node_mppx/node_modules/accounts/src/cli/storage.ts`
  - `node_mppx/node_modules/accounts/src/cli/adapter.ts`
  - `node_mppx/node_modules/accounts/src/core/Provider.ts`
  - `node_mppx/node_modules/accounts/src/core/Keystore.ts`
