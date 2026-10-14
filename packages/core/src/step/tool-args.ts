import type { ToolDef } from '@agnes/extension-api'
import { validateAgainst } from '@agnes/protocol'

/**
 * Unwrap parameters packaged under an `input` envelope if the schema does not define `input`.
 * Handles models or provider adapters that serialize tool calls as { input: "..." } or { input: { ... } }.
 */
export function unwrapToolArgs(schema: ToolDef['parameters'] | undefined, args: unknown): unknown {
  if (typeof args !== 'object' || args === null) return args
  const props = (schema as { properties?: Record<string, unknown> } | undefined)?.properties
  if (props && 'input' in props) return args
  if ('input' in args) {
    const raw = (args as { input: unknown }).input
    if (typeof raw === 'string') {
      try {
        const parsed = JSON.parse(raw)
        if (typeof parsed === 'object' && parsed !== null) return parsed
      } catch {}
    } else if (typeof raw === 'object' && raw !== null) {
      return raw
    }
  }
  return args
}

/** Explain schema refusals without echoing argument values or relaxing validation. */
export function toolArgumentError(schema: ToolDef['parameters'], args: unknown): string | undefined {
  const prefix = 'tool arguments do not match the registered schema'
  try {
    const unwrapped = unwrapToolArgs(schema, args)
    const checked = validateAgainst(schema, unwrapped)
    if (checked.ok) return undefined
    const hints = checked.errors
      .filter((error) => error.code === 'MISSING')
      .slice(0, 5)
      .map((error) => `${`${error.path}/${error.key ?? '?'}`.slice(0, 160)}: missing required parameter`)
    return `${prefix}: ${hints.join('; ') || 'invalid parameter type or value'}. Retry with complete arguments matching the tool schema.`
  } catch {
    // A malformed schema must still refuse the call before policy or execution.
    return prefix
  }
}
