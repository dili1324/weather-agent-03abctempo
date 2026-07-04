# MVP Local Run on macOS

This guide is for a proof of concept on a Mac mini or any macOS machine. It prioritizes proving the Weather Agent works end-to-end before production-hardening GitHub Actions.

Use a Tempo test wallet or secondary wallet only. Fund it with a small amount, such as 1-5 USD.

## 1. Prepare Python

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pip install --no-build-isolation -e .
```

If you want `python3 scripts/debug_checks.py ...` to work, activate the virtualenv:

```bash
source .venv/bin/activate
```

Run tests:

```bash
.venv/bin/python -m pytest -q
```

## 2. Configure Telegram

Create a local `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Fill:

```bash
TELEGRAM_BOT_TOKEN=your_test_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Load it in the current shell:

```bash
set -a
source .env
set +a
```

If Telegram does not receive messages:

- Make sure you have opened a chat with `@weatheagent_bot`.
- Send `/start` to the bot if this is a direct chat.
- Confirm `TELEGRAM_CHAT_ID` points to the destination chat.
- For a group, add the bot to the group and use the group chat id.
- Run the Telegram-only check below and read the HTTP error in the log.

## 3. Install Tempo CLI

Install using the official command from Tempo docs:

```bash
curl -fsSL https://tempo.xyz/install | bash
```

Use the installed binary directly if your shell has not picked up the path yet:

```bash
"$HOME/.tempo/bin/tempo" --version
```

For this project, either make `tempo` available in `PATH` or set:

```bash
export TEMPO_BIN="$HOME/.tempo/bin/tempo"
```

## 4. Connect Tempo Wallet

Run:

```bash
"$HOME/.tempo/bin/tempo" wallet login
```

Complete the browser/passkey flow. Then verify:

```bash
"$HOME/.tempo/bin/tempo" wallet --format json whoami
```

You need the output to indicate the wallet is ready. If it is not ready:

- Run `"$HOME/.tempo/bin/tempo" wallet login` again and complete the browser/passkey flow.
- If the CLI reports a stale or missing access key, run `"$HOME/.tempo/bin/tempo" wallet logout --yes`, then login again.
- Confirm you are using the same `TEMPO_BIN` that was installed and logged in.

## 5. Fund the Test Wallet

If the balance is empty, add a small amount:

```bash
"$HOME/.tempo/bin/tempo" wallet fund
```

For MVP testing, use only a secondary/test wallet and keep the balance small, for example 1-5 USD.

Optional credits check:

```bash
"$HOME/.tempo/bin/tempo" wallet --format json whoami --credits
```

## 5.1. Authorize Local Access Key for mppx MVP v2

The recommended local MVP v2 path uses the Node helper in `node_mppx/` instead of `tempo request` for OpenWeather. This keeps Python as the orchestrator and Telegram sender, while `mppx` handles paid OpenWeather requests.

Install Node dependencies:

```bash
cd node_mppx
npm install
```

Authorize a small local Access Key once:

```bash
export MPPX_ACCESS_KEY_DAILY_LIMIT_USDC=0.25
export MPPX_ACCESS_KEY_EXPIRY_DAYS=1
npm run connect
```

The browser/passkey flow may open once here. That is expected.

Verify the helper can pay OpenWeather MPP without approving every payment:

```bash
npm run weather:once
npm run weather:twice
cd ..
```

Success means `weather:twice` returns `"ok": true` and the second weather flow does not open another browser/passkey payment approval.

The older Tempo CLI fallback notes remain in [docs/access-key-local-run.md](access-key-local-run.md).

## 6. Run Component Checks

Tempo readiness:

```bash
.venv/bin/python scripts/debug_checks.py tempo
```

If the virtualenv is activated, you can also run:

```bash
python3 scripts/debug_checks.py tempo
```

Telegram:

```bash
.venv/bin/python scripts/debug_checks.py telegram
```

Activated virtualenv equivalent:

```bash
python3 scripts/debug_checks.py telegram
```

OpenWeather MPP:

```bash
.venv/bin/python scripts/debug_checks.py weather
```

Activated virtualenv equivalent:

```bash
python3 scripts/debug_checks.py weather
```

GPT MPP, only if you want to spend on the optional summary path:

```bash
.venv/bin/python scripts/debug_checks.py gpt
```

Activated virtualenv equivalent:

```bash
python3 scripts/debug_checks.py gpt
```

All checks:

```bash
.venv/bin/python scripts/debug_checks.py all
```

Activated virtualenv equivalent:

```bash
python3 scripts/debug_checks.py all
```

## 7. Run the Weather Agent

For local MVP v2, use mppx mode and keep GPT disabled:

```bash
export WEATHER_PAYMENT_MODE=mppx
export ENABLE_GPT_SUMMARY=false
.venv/bin/python -m weather_agent
```

Expected result:

- The command logs the Node mppx OpenWeather helper and Telegram send.
- Telegram receives a Hanoi weather message.

Fallback CLI mode remains available:

```bash
export WEATHER_PAYMENT_MODE=cli
export ENABLE_GPT_SUMMARY=false
export MPP_MAX_SPEND_USD=0.05
.venv/bin/python -m weather_agent
```

After this works, enable GPT summary if desired:

```bash
export ENABLE_GPT_SUMMARY=true
.venv/bin/python -m weather_agent
```

## MVP Done Checklist

- `tempo wallet --format json whoami` shows "ready": true.
- Test wallet has a small balance.
- `scripts/debug_checks.py telegram` sends a message.
- `npm run weather:twice` succeeds from `node_mppx/` without another payment approval prompt.
- `python -m weather_agent` sends the final Telegram weather report.
