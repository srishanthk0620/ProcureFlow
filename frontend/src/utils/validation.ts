/** ASCII digits only; use to normalize controlled input, not to validate submission. */
export function digitsOnly(value: string): string {
  return value.replace(/[^0-9]/g, '')
}
/** Normalize and cap a controlled input before storing its value. */
export function maxDigits(value: string, max: number): string {
  if (!Number.isSafeInteger(max) || max < 0) throw new RangeError('max must be a non-negative integer')
  return digitsOnly(value).slice(0, max)
}
export function validateIndianMobile(value: string): boolean {
  return /^[6-9][0-9]{9}$/.test(value)
}
export function validateOtp(value: string, length: number): boolean {
  return Number.isSafeInteger(length) && length > 0 && value.length === length && /^[0-9]+$/.test(value)
}
export function validateRequired(value: string | null | undefined): boolean {
  return typeof value === 'string' && value.trim().length > 0
}
// Controlled inputs should use these before setting state; validators reject malformed submissions.
export const mobileInputValue = (value: string): string => maxDigits(value, 10)
export const otpInputValue = (value: string, length: number): string => maxDigits(value, length)
