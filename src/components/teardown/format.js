// Shared helpers for the teardown UI.

const inr0 = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 })

/** ₹1,499 — rupees rounded for display (JSON keeps 1 decimal place). */
export function rupees(n) {
  if (n == null || Number.isNaN(Number(n))) return '₹—'
  return `₹${inr0.format(Math.round(Number(n)))}`
}

/** Same buckets as the server (contract §3). */
export function verdictFor(multiple) {
  if (multiple < 2) return 'Fair deal'
  if (multiple < 4) return 'Normal retail'
  if (multiple < 8) return 'Brand premium'
  if (multiple < 20) return 'Premium brand'
  return 'Mostly marketing'
}

/** Colour tone for the verdict chip. */
export function verdictTone(multiple) {
  if (multiple < 2) return 'fair'
  if (multiple < 4) return 'normal'
  if (multiple < 8) return 'brand'
  if (multiple < 20) return 'premium'
  return 'marketing'
}

export function formatMultiple(m) {
  if (m == null) return '—'
  return m >= 10 ? m.toFixed(1).replace(/\.0$/, '') : m.toFixed(1)
}

export function formatMass(g) {
  if (g == null) return '—'
  if (g >= 1000) return `${(g / 1000).toFixed(g >= 10000 ? 0 : 2).replace(/\.?0+$/, '')} kg`
  return `${g >= 10 ? Math.round(g) : Number(g.toFixed(1))} g`
}
