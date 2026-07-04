# MPPX Weather Helper Spike

This is a local-only TypeScript spike. It does not replace the current Python app or the `tempo request` CLI fallback.

Goal: prove whether `mppx` + `accounts` provider + a Tempo Access Key can call OpenWeather MPP without browser/passkey approval for each paid request.

## Prerequisites

Install Node.js 20+ on the Mac mini:

```bash
brew install node
```

Install dependencies:

```bash
cd node_mppx
npm install
```

This creates `package-lock.json`. Commit it only after the spike installs successfully on the local machine.

## 1. Authorize a Small Access Key

Use a test Tempo Wallet only. Keep wallet balance small.

Default limit is `1` USDC/day for 7 days. You can lower it:

```bash
export MPPX_ACCESS_KEY_DAILY_LIMIT_USDC=0.25
export MPPX_ACCESS_KEY_EXPIRY_DAYS=1
npm run connect
```

The wallet/provider may open browser/passkey once. That is expected.

The script prints JSON like:

```json
{
  "ok": true,
  "mode": "mppx-access-key",
  "accountAddress": "0x...",
  "accessKeyAddress": "0x...",
  "accessKeyStatus": "pending",
  "dailyLimitUsdc": "0.25",
  "expiryDays": 1,
  "nextStep": "Run npm run weather:twice. The helper uses the access key saved by the accounts CLI provider."
}
```

The installed `accounts` package exposes the local Node provider through `accounts/cli`. It saves the generated Access Key state in the Tempo wallet CLI provider storage. The weather scripts reuse that saved state; they do not require `MPPX_ACCESS_KEY_ADDRESS`.

## 2. Test Weather Once

```bash
npm run weather:once
```

Expected behavior:

- browser/passkey approval may appear if the provider still needs connection,
- stdout is JSON,
- logs go to stderr,
- OpenWeather geocode and current-weather both return data.

## 3. Test Weather Twice

```bash
npm run weather:twice
```

Success condition:

- one process runs two OpenWeather weather flows,
- request 2 does not open browser/passkey approval,
- stdout ends with `"ok": true`.

If request 2 still opens browser/passkey approval, the new blocker is:

```text
Accounts SDK / wallet provider did authorize an Access Key, but mppx did not reuse it for unattended OpenWeather MPP payments in this local CLI runtime.
```

Capture stderr logs and compare whether `pinning access key for mppx payments` appears before payment events.

## Commands

```bash
npm run connect
npm run geocode
npm run current-weather
npm run weather:once
npm run weather:twice
npm run typecheck
```

## Environment

```bash
export WEATHER_CITY_QUERY=Hanoi,VN
export WEATHER_UNITS=metric
export WEATHER_LANG=vi
export MPPX_ACCESS_KEY_DAILY_LIMIT_USDC=0.25
export MPPX_ACCESS_KEY_EXPIRY_DAYS=1
```

Do not use a raw private key for this spike.

## Verified Local Result

On the local Mac environment, after `npm run connect` authorized an Access Key, both commands completed successfully through `mppx`:

```bash
npm run weather:once
npm run weather:twice
```

`weather:twice` made two complete OpenWeather flows in one process. Each flow called `/geocode` and `/current-weather`; all four paid requests received payment challenges, created credentials, retried, and returned HTTP 200 without another browser/passkey approval prompt in the command output.
