# Tempo Access Key Local MVP

This document focuses on local Mac execution only. Do not put Tempo credentials in GitHub Secrets for this step.

Use a secondary/test Tempo Wallet only. Keep the balance small.

## What the Official Docs Confirm

Tempo Wallet CLI supports:

- `tempo wallet login`: browser/passkey wallet connection.
- `tempo wallet refresh`: refresh the current access key without logging out.
- `tempo wallet keys`: list access keys and spending limits.
- `tempo wallet revoke <access-key>`: revoke an access key.
- `tempo request --max-spend <amount>`: cap paid MPP request spend.

Tempo protocol/SDK docs confirm that Access Keys can have:

- expiry timestamps,
- per-token spending limits,
- recurring periods,
- call scopes,
- revoke/update operations.

Important gap for this MVP:

- The installed Tempo Wallet CLI `0.6.2` does not expose a documented command to create a new access key with a custom smaller spending limit or custom expiry.
- The documented CLI path creates/refreshes the current wallet-managed access key through browser/passkey authorization.
- `tempo request` does not expose a documented `--yes`, `--assume-yes`, `--auto-approve`, `--trusted-service`, or approval-policy flag.
- `tempo request --max-spend` caps spend, but it is not documented as a pre-approval mechanism that suppresses browser/passkey payment approval.
- MPP docs describe pre-authorized agent spend through Access Keys plus wallet provider / `mppx` SDK, not through a `tempo request` auto-approve flag.

## Local Goal

Separate two states clearly:

1. The wallet/access key is ready.
2. A paid `tempo request` may still require browser/passkey approval for each payment.

Current conclusion: with Tempo Wallet CLI `0.6.2`, local unattended `tempo request` is not confirmed as supported. The blocker is per-request payment approval, not wallet login.

## 1. Confirm Tempo CLI Version

```bash
tempo --version
tempo wallet --help
```

The CLI should show wallet commands including `login`, `refresh`, `keys`, `revoke`, and `whoami`.

## 2. Login or Refresh the Access Key

If this is a fresh machine:

```bash
tempo wallet login
```

Complete the browser/passkey flow once.

If you are already logged in, refresh the current access key:

```bash
tempo wallet refresh
```

This may open an Auth URL and require browser/passkey approval once. That is expected for key authorization.

This does not prove payment approval is pre-approved. It only refreshes the wallet-managed access key.

## 3. Inspect Current Wallet and Key

```bash
tempo wallet --format json whoami
```

Check:

- `"ready": true`
- `key.address` exists
- `key.spending_limit.limit` exists
- `key.expires_at` exists

List all keys:

```bash
tempo wallet --format json keys
```

The current CLI-managed key may show a default spending limit, such as `100.000000` USDC.e. Because the CLI does not document custom limit creation, keep the wallet balance small and use `MPP_MAX_SPEND_USD` as the per-run cap.

## 4. Risk Controls for MVP

Use all of these:

```bash
export MPP_MAX_SPEND_USD=0.05
export ENABLE_GPT_SUMMARY=false
```

Keep only a small balance in the test wallet, for example 1-5 USD or less.

## 5. Dry Run an MPP Request

```bash
tempo request --dry-run --max-spend 0.05 -X POST \
  --json '{"q":"Hanoi,VN","limit":1}' \
  https://openweather.mpp.paywithlocus.com/openweather/geocode
```

Dry-run should preview the challenge without payment. It does not prove unattended paid execution.

## 6. Test Whether CLI Requires Per-Request Approval

Run the weather check twice:

```bash
python3 scripts/debug_checks.py weather
python3 scripts/debug_checks.py weather
```

Success criteria:

- both commands complete,
- no browser/passkey prompt appears on the second run,
- logs show geocode/current-weather completed.

Observed blocker:

- If every paid `tempo request` still opens browser/passkey approval, then `tempo request` is not operating unattended even though `tempo wallet --format json whoami` reports `"ready": true`.
- In that case, do not treat this as a wallet-login problem. Treat it as a per-payment approval policy problem.

Then run all non-GPT checks:

```bash
export ENABLE_GPT_SUMMARY=false
python3 scripts/debug_checks.py all
```

This should check wallet readiness, call OpenWeather MPP, skip GPT, and send Telegram.

## 7. Revoke Stale Keys

Inspect keys first:

```bash
tempo wallet --format json keys
```

Preview revoke:

```bash
tempo wallet revoke <ACCESS_KEY_ADDRESS> --dry-run --format json
```

Revoke only stale or unusable keys you no longer need:

```bash
tempo wallet revoke <ACCESS_KEY_ADDRESS> --format json
```

Do not revoke the current `whoami.key.address` unless you are ready to run `tempo wallet refresh` or `tempo wallet login` again.

## If It Still Prompts Every Request

Stop and inspect:

```bash
tempo wallet --format json whoami
tempo wallet --format json keys
```

You can try one refresh:

```bash
tempo wallet refresh
```

If refresh still does not produce a key that can pay without per-request browser/passkey approval, the remaining missing piece is an official Tempo CLI command or documented wallet UI flow for pre-approving payment spend for `tempo request`.

## Official SDK Direction, Not Yet Implemented

MPP's managing-agent-spend docs describe a different path:

- ask the wallet provider to authorize an Access Key using `wallet_connect` capabilities or `wallet_authorizeAccessKey`,
- include expiry, spending limits, and scopes in that Access Key,
- use `mppx` with the wallet provider and optionally pin the access key for that runtime.

That is the documented route for background agent spend with budgets. This project currently uses Python plus `tempo request`, so switching to `mppx` would be an architecture change and is not implemented in the local MVP.

## Local Conclusion

With the current CLI:

- Access key ready: supported and checkable via `tempo wallet --format json whoami`.
- Spending limit/expiry visibility: supported via `whoami` and `keys`.
- Revoke: supported via `tempo wallet revoke`.
- Per-run spend cap: supported via `tempo request --max-spend`.
- Unattended `tempo request` without per-payment browser/passkey approval: not documented or confirmed.

Therefore the current blocker is per-request payment approval, not wallet login or access-key readiness.
