import { useCallback, useEffect, useRef, useState } from 'react'
import { BRAIN_API } from './useBrain'
import fixture from '../components/teardown/fixture.json'
import fixtureNoPrice from '../components/teardown/fixture-no-price.json'
import { verdictFor } from '../components/teardown/format'

const MOCK_DELAY_MS = 1500

// ?mock=teardown → fixture data, ?mock=teardown-429 / teardown-502 / teardown-offline → error paths
function mockMode() {
  const m = new URLSearchParams(window.location.search).get('mock') || ''
  return m.startsWith('teardown') ? m : null
}

const wait = (ms, signal) => new Promise((resolve, reject) => {
  const t = setTimeout(resolve, ms)
  signal?.addEventListener('abort', () => { clearTimeout(t); reject(new DOMException('Aborted', 'AbortError')) })
})

class TeardownError extends Error {}

function mockResult(pricePaid) {
  if (pricePaid == null) return structuredClone(fixtureNoPrice)
  // Re-derive the markup from the price the user typed so the mock reacts to input
  const r = structuredClone(fixture)
  const total = r.cost.total
  const multiple = Math.round((pricePaid / total) * 10) / 10
  r.price.paid = pricePaid
  r.markup.price_used = pricePaid
  r.markup.multiple = multiple
  r.markup.verdict = verdictFor(multiple)
  r.markup.where_the_money_goes[1].amount = Math.max(0, Math.round((pricePaid - total) * 10) / 10)
  return r
}

async function mockRequest(mode, pricePaid, signal) {
  await wait(MOCK_DELAY_MS, signal)
  if (mode === 'teardown-429') throw new TeardownError('Busy — try again in 12s.')
  if (mode === 'teardown-502') throw new TeardownError("My eyes glitched on that photo. Try again, or a clearer shot of the whole object.")
  if (mode === 'teardown-offline') throw new TeardownError("Can't reach my brain server. Is it running?")
  return mockResult(pricePaid)
}

async function apiRequest(file, { pricePaid, hint }, signal) {
  const form = new FormData()
  form.append('image', file, file.name || 'photo.jpg')
  if (pricePaid != null) form.append('price_paid', String(pricePaid))
  form.append('currency', 'INR')
  if (hint) form.append('hint', hint)

  let r
  try {
    r = await fetch(`${BRAIN_API}/teardown`, { method: 'POST', body: form, signal })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new TeardownError("Can't reach my brain server. Is it running?")
  }
  const data = await r.json().catch(() => ({}))
  if (r.ok && data?.cost && data?.object) return data

  if (r.status === 429) {
    const s = Math.max(1, Math.ceil(Number(data.retry_after_s) || Number(r.headers.get('Retry-After')) || 10))
    throw new TeardownError(`Busy — try again in ${s}s.`)
  }
  if (r.status === 502) {
    throw new TeardownError(data.error
      ? `My eyes glitched on that photo: ${data.error}`
      : 'My eyes glitched on that photo. Try again, or a clearer shot of the whole object.')
  }
  if (r.status === 413) throw new TeardownError('That photo is too big — keep it under 8 MB.')
  if (r.status === 400) throw new TeardownError(data.error || "That photo didn't work. Try a JPG or PNG.")
  if (r.status === 404 || r.status === 503 || r.status === 504) {
    throw new TeardownError('The teardown service is not running on my brain server yet.')
  }
  throw new TeardownError(data.error || `Something went wrong (HTTP ${r.status}).`)
}

/**
 * "What does it really cost?" — uploads a photo to /api/teardown and keeps the result.
 * status: idle | uploading | done | error
 */
export default function useTeardown() {
  const [state, setState] = useState({ status: 'idle', result: null, error: null, previewUrl: null })
  const abortRef = useRef(null)
  const urlRef = useRef(null)

  const setPreview = (url) => {
    if (urlRef.current && urlRef.current !== url) URL.revokeObjectURL(urlRef.current)
    urlRef.current = url
  }

  useEffect(() => () => {
    abortRef.current?.abort()
    if (urlRef.current) URL.revokeObjectURL(urlRef.current)
  }, [])

  const run = useCallback(async (file, { pricePaid, hint } = {}) => {
    if (!file) return null
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    const price = pricePaid === '' || pricePaid == null ? null : Number(pricePaid)
    const opts = { pricePaid: Number.isFinite(price) && price > 0 ? price : null, hint: hint?.trim() || null }

    const previewUrl = URL.createObjectURL(file)
    setPreview(previewUrl)
    setState((s) => ({ ...s, status: 'uploading', error: null, previewUrl }))

    try {
      const mode = mockMode()
      const result = mode ? await mockRequest(mode, opts.pricePaid, ctrl.signal) : await apiRequest(file, opts, ctrl.signal)
      if (ctrl.signal.aborted) return null
      setState({ status: 'done', result, error: null, previewUrl })
      return result
    } catch (e) {
      if (e.name === 'AbortError') return null
      setState((s) => ({ ...s, status: 'error', error: e instanceof TeardownError ? e.message : 'Something went wrong. Try again.' }))
      return null
    }
  }, [])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setState((s) => ({ ...s, status: 'idle', error: null }))
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setPreview(null)
    setState({ status: 'idle', result: null, error: null, previewUrl: null })
  }, [])

  return { ...state, run, cancel, reset }
}
