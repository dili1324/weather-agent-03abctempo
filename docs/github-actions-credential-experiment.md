# GitHub Actions Credential Experiment

This is an experimental MVP path only. It is not documented as an official Tempo production deployment flow in the sources reviewed so far.

Use only a secondary/test Tempo wallet funded with a small amount, such as 1-5 USD. Assume any exported credential bundle could be exposed.

## What the Official Docs Confirm

The reviewed Tempo docs confirm:

- Install the CLI with `curl -fsSL https://tempo.xyz/install | bash`.
- Connect with `tempo wallet login`.
- Verify with `tempo wallet --format json whoami`.
- Use `tempo request` for MPP paid HTTP requests.
- Use `--max-spend` and small wallet balances to cap risk.

The docs reviewed do not specify an official GitHub Actions secret such as `TEMPO_ACCESS_KEY`, `TEMPO_SESSION`, or `AGENT_CREDENTIAL`.

## Experiment Goal

After local MVP works, test whether the Tempo CLI wallet state from a logged-in test wallet can be restored on a fresh GitHub Actions runner.

This experiment should answer:

- Where did the CLI store wallet/session/access-key state on macOS?
- Is that state portable to Linux GitHub Actions?
- Does `tempo wallet --format json whoami` return "ready": true after restore?
- Can `tempo request --dry-run` work before spending?

## Identify Local Tempo State

Before login, capture a baseline:

```bash
find "$HOME/.tempo" -maxdepth 4 -type f -print 2>/dev/null | sort > /tmp/tempo-files-before.txt
```

Login and verify:

```bash
"$HOME/.tempo/bin/tempo" wallet login
"$HOME/.tempo/bin/tempo" wallet --format json whoami
```

After login, capture changed files:

```bash
find "$HOME/.tempo" -maxdepth 4 -type f -print 2>/dev/null | sort > /tmp/tempo-files-after.txt
comm -13 /tmp/tempo-files-before.txt /tmp/tempo-files-after.txt
```

Also inspect timestamps:

```bash
find "$HOME/.tempo" -maxdepth 4 -type f -mtime -1 -print
```

If no credential-like files appear, macOS Keychain or another OS store may be involved. In that case, this GitHub Actions credential experiment is likely blocked for hosted runners.

## Experimental Secret Bundle

Only if the diff shows CLI state under `$HOME/.tempo` and you accept the MVP risk, create a base64 bundle:

```bash
tar -C "$HOME" -czf /tmp/tempo-home.tgz .tempo
base64 < /tmp/tempo-home.tgz > /tmp/tempo-home.tgz.b64
```

Create a GitHub Actions secret:

```text
TEMPO_HOME_TGZ_B64
```

Paste the content of `/tmp/tempo-home.tgz.b64`.

Do not do this with a main wallet. Do not store seed phrases or private keys. Keep the wallet balance small.

## Experimental Restore Step

An experimental workflow step would restore before running the agent:

```bash
printf '%s' "$TEMPO_HOME_TGZ_B64" | base64 --decode > /tmp/tempo-home.tgz
tar -C "$HOME" -xzf /tmp/tempo-home.tgz
chmod +x "$HOME/.tempo/bin/tempo" || true
"$HOME/.tempo/bin/tempo" wallet --format json whoami
```

Then use:

```bash
TEMPO_BIN="$HOME/.tempo/bin/tempo"
python -m weather_agent
```

## Safety Checks Before Spending

Run these in GitHub Actions first:

```bash
"$HOME/.tempo/bin/tempo" wallet --format json whoami
"$HOME/.tempo/bin/tempo" request -t --dry-run -X POST \
  --json '{"q":"Hanoi,VN","limit":1}' \
  https://openweather.mpp.paywithlocus.com/openweather/geocode
```

Only remove `--dry-run` after the wallet is ready and the maximum spend is low.

## GitHub Secrets for the Experiment

Required for the app:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Experimental:

- `TEMPO_HOME_TGZ_B64`

Optional GitHub Variables:

- `MPP_MAX_SPEND_USD`, for example `0.05`.
- `ENABLE_GPT_SUMMARY`, start with `false`.
- `GPT_MODEL`, default `gpt-4o`.

## When to Stop

Stop and do not spend if:

- `tempo wallet --format json whoami` does not return "ready": true.
- The restored CLI says an access key does not exist.
- The credential state appears to depend on macOS Keychain.
- `--dry-run` fails.
- The test wallet balance is higher than you are willing to lose.

## Production Note

This experiment is not an official Tempo CI/CD credential flow. For production, wait for official Tempo documentation describing non-interactive agent credentials, access-key export/import, or GitHub Actions deployment.
