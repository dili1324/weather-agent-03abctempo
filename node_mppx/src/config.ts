import { isHex, type Hex } from 'viem'

export const OPENWEATHER_MPP_BASE_URL =
  process.env.OPENWEATHER_MPP_BASE_URL ?? 'https://openweather.mpp.paywithlocus.com/openweather'

export const DEFAULT_CITY_QUERY = process.env.WEATHER_CITY_QUERY ?? 'Hanoi,VN'
export const DEFAULT_UNITS = process.env.WEATHER_UNITS ?? 'metric'
export const DEFAULT_LANG = process.env.WEATHER_LANG ?? 'vi'

function requireHex(value: string, name: string): Hex {
  if (!isHex(value)) {
    throw new Error(`${name} must be a 0x-prefixed hex string`)
  }
  return value
}

export const TEMPO_USDC_TOKEN = requireHex(
  process.env.TEMPO_USDC_TOKEN ?? '0x20C000000000000000000000b9537d11c60E8b50',
  'TEMPO_USDC_TOKEN',
)

export const ACCESS_KEY_DAILY_LIMIT_USDC = process.env.MPPX_ACCESS_KEY_DAILY_LIMIT_USDC ?? '1'
export const ACCESS_KEY_EXPIRY_DAYS = Number(process.env.MPPX_ACCESS_KEY_EXPIRY_DAYS ?? '7')
export const ACCESS_KEY_PERIOD_SECONDS = Number(process.env.MPPX_ACCESS_KEY_PERIOD_SECONDS ?? '86400')

export function endpoint(path: string): string {
  return `${OPENWEATHER_MPP_BASE_URL}${path}`
}
