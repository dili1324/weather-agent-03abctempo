export function log(message: string, fields: Record<string, unknown> = {}): void {
  const payload = Object.keys(fields).length === 0 ? '' : ` ${JSON.stringify(fields)}`
  process.stderr.write(`[mppx-helper] ${message}${payload}\n`)
}

export function printJson(value: unknown): void {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`)
}
