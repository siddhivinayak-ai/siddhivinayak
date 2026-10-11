import React, { useEffect, useRef, useState } from 'react'
import { rupees, formatMultiple, formatMass, verdictTone, verdictFor } from './format'
import './Teardown.css'

const LOADING_LINES = [
  'Identifying parts…',
  'Weighing materials…',
  'Matching manufacturing processes…',
  'Pricing the factory floor…',
  'Adding up the markup…',
]

const COST_PARTS = [
  ['materials', 'Materials'],
  ['processing', 'Processing'],
  ['assembly', 'Assembly'],
  ['packaging', 'Packaging'],
  ['overhead', 'Overhead'],
]

// html-to-image needs fonts inlined into the SVG. Its default scan walks every
// stylesheet (KaTeX ships dozens of fonts), so we inline only the Google fonts
// the card uses (latin + latin-ext for ₹), once, as data URLs.
let fontCSSPromise = null
function cardFontCSS() {
  if (!fontCSSPromise) {
    fontCSSPromise = (async () => {
      const link = document.querySelector('link[href*="fonts.googleapis.com/css"]')
      if (!link) return undefined
      const css = await (await fetch(link.href)).text()
      const blocks = css.split(/(?=\/\*\s*[\w-]+\s*\*\/)/).filter((b) => /^\/\*\s*(latin|latin-ext)\s*\*\//.test(b))
      const toData = async (url) => {
        const blob = await (await fetch(url)).blob()
        return new Promise((res) => { const r = new FileReader(); r.onload = () => res(r.result); r.readAsDataURL(blob) })
      }
      const out = await Promise.all(blocks.map(async (b) => {
        const m = b.match(/url\((https:[^)]+)\)/)
        return m ? b.replace(m[1], await toData(m[1])) : b
      }))
      return out.join('\n') || undefined
    })().catch(() => { fontCSSPromise = null; return undefined })
  }
  return fontCSSPromise
}

/** Animated count-up from 0 → value (ease-out), restarted when value changes. */
function useCountUp(value, duration = 1200, delay = 0) {
  const [v, setV] = useState(0)
  useEffect(() => {
    if (value == null) return undefined
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) { setV(value); return undefined }
    let raf
    let start
    const tick = (t) => {
      if (start == null) start = t + delay
      const p = Math.min(1, Math.max(0, (t - start) / duration))
      setV(value * (1 - Math.pow(1 - p, 3)))
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [value, duration, delay])
  return v
}

const CloseIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12" /></svg>
)

function Watermark({ date }) {
  return (
    <div className="td-watermark">
      <span className="td-wm-brand"><i className="td-wm-dot" />Siddhivinayak · engineer twin</span>
      <span className="td-wm-est">Engineering estimate</span>
      {date && <span className="td-wm-date">{date}</span>}
    </div>
  )
}

function LoadingBody({ previewUrl, onCancel }) {
  const [i, setI] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setI((n) => (n + 1) % LOADING_LINES.length), 1400)
    return () => clearInterval(id)
  }, [])
  return (
    <div className="td-loading">
      <div className="td-scan">
        {previewUrl && <img src={previewUrl} alt="Your photo" />}
        <div className="td-scan-grid" />
        <div className="td-scan-line" />
        <span className="td-corner tl" /><span className="td-corner tr" /><span className="td-corner bl" /><span className="td-corner br" />
      </div>
      <div className="td-loading-text" aria-live="polite">
        <span className="td-spinner" />
        <span key={i} className="td-loading-line">{LOADING_LINES[i]}</span>
      </div>
      <div className="td-loading-sub">Your engineer twin is tearing it down</div>
      <div className="td-loading-steps">
        {LOADING_LINES.slice(0, 4).map((l, n) => <span key={l} className={n <= i ? 'on' : ''} />)}
      </div>
      <button className="td-btn ghost" onClick={onCancel}>Cancel</button>
    </div>
  )
}

function ErrorBody({ previewUrl, error, onRetry, onBack }) {
  return (
    <div className="td-error">
      {previewUrl && <img className="td-error-img" src={previewUrl} alt="Your photo" />}
      <div className="td-error-title">Couldn't tear that one down</div>
      <p>{error}</p>
      <div className="td-actions">
        <button className="td-btn primary" onClick={onRetry}>Try again</button>
        <button className="td-btn ghost" onClick={onBack}>Pick another photo</button>
      </div>
    </div>
  )
}

function ResultBody({ result, previewUrl, shareRef }) {
  const [showAssumptions, setShowAssumptions] = useState(false)
  const { object, price, cost, markup, components = [], processes = [], assumptions = [] } = result
  const paid = price?.paid
  const priceUsed = markup?.price_used ?? paid ?? price?.estimated_retail
  const multiple = markup?.multiple ?? (priceUsed && cost.total ? priceUsed / cost.total : null)
  const verdict = markup?.verdict || (multiple != null ? verdictFor(multiple) : '')
  const tone = multiple != null ? verdictTone(multiple) : 'normal'

  const makeV = useCountUp(cost.total, 1100, 150)
  const priceV = useCountUp(priceUsed, 1300, 350)
  const multV = useCountUp(multiple, 1300, 650)

  const makePct = priceUsed ? Math.min(100, (cost.total / priceUsed) * 100) : 100
  const [grow, setGrow] = useState(false)
  useEffect(() => { const t = setTimeout(() => setGrow(true), 500); return () => clearTimeout(t) }, [])

  const restLabel = markup?.where_the_money_goes?.[1]?.label || 'Shipping, retail, brand, profit, tax'
  const restAmount = markup?.where_the_money_goes?.[1]?.amount ?? Math.max(0, priceUsed - cost.total)
  const date = result.created_at
    ? new Date(result.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
    : null
  const partsTotal = COST_PARTS.reduce((s, [k]) => s + (cost[k] || 0), 0) || cost.total
  const procs = processes.length
    ? processes
    : [...new Set(components.flatMap((c) => c.process_labels || []))].map((label) => ({ id: label, label }))

  return (
    <div className="td-share" ref={shareRef}>
      <div className="td-hero">
        {previewUrl ? <img src={previewUrl} alt={object?.name} /> : <div className="td-hero-blank" />}
        <div className="td-hero-shade" />
        <span className="td-hero-tag">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" /></svg>
          Teardown
        </span>
        <div className="td-hero-text">
          {object?.category && <span className="td-hero-cat">{object.category}</span>}
          <h2 className="td-title">{object?.name || 'Mystery object'}</h2>
        </div>
      </div>

      <div className="td-body">
        <div className="td-numbers">
          <div className="td-num make">
            <span className="td-num-label">Costs to make</span>
            <span className="td-num-value">{rupees(makeV)}</span>
          </div>
          <span className="td-vs">vs</span>
          <div className="td-num paid">
            <span className="td-num-label">{paid != null ? 'You paid' : 'Sells for ~'}</span>
            <span className="td-num-value">{rupees(priceV)}</span>
          </div>
        </div>

        {multiple != null && (
          <div className={`td-markup tone-${tone}`}>
            <div className="td-markup-num">
              <span className="td-markup-x">{formatMultiple(multV)}×</span>
              <span className="td-markup-word">markup</span>
            </div>
            <span className="td-verdict">{verdict}</span>
          </div>
        )}

        <section className="td-section">
          <h3>Where your money goes</h3>
          <div className="td-stack" role="img" aria-label={`Making it ${Math.round(makePct)}%, everything else ${Math.round(100 - makePct)}%`}>
            <div className="td-stack-make" style={{ width: grow ? `${Math.max(makePct, 2.5)}%` : '0%' }} />
            <div className="td-stack-rest" />
          </div>
          <div className="td-legend">
            <div><i className="sw make" /><span>Making it</span><b>{rupees(cost.total)}</b><em>{Math.round(makePct)}%</em></div>
            <div><i className="sw rest" /><span>{restLabel}</span><b>{rupees(restAmount)}</b><em>{Math.round(100 - makePct)}%</em></div>
          </div>
        </section>

        <section className="td-section td-noshare">
          <h3>The {rupees(cost.total)} factory cost</h3>
          <div className="td-mini">
            {COST_PARTS.map(([k], n) => (cost[k] ? <span key={k} className={`m${n}`} style={{ flexGrow: cost[k] / partsTotal }} /> : null))}
          </div>
          <div className="td-mini-legend">
            {COST_PARTS.map(([k, label], n) => (cost[k] ? (
              <span key={k}><i className={`m${n}`} />{label} <b>{rupees(cost[k])}</b></span>
            ) : null))}
          </div>
        </section>

        {components.length > 0 && (
          <section className="td-section">
            <h3>What's inside</h3>
            <ul className="td-parts">
              {components.map((c, n) => (
                <li key={`${c.name}-${n}`}>
                  <div className="td-part-main">
                    <span className="td-part-name">{c.qty > 1 && <em>{c.qty}× </em>}{c.name}</span>
                    <span className="td-part-meta">{c.material_label || c.material_id} · {formatMass(c.mass_g)}</span>
                  </div>
                  <span className="td-part-cost">{rupees(c.cost)}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {procs.length > 0 && (
          <section className="td-section td-noshare">
            <h3>How it's made</h3>
            <div className="td-chips">
              {procs.map((p) => <span key={p.id} className="td-chip">{p.label}</span>)}
            </div>
          </section>
        )}

        {result.fun_fact && (
          <div className="td-fact">
            <span className="td-fact-icon" aria-hidden="true">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2z" /></svg>
            </span>
            <p><b>Engineer's note · </b>{result.fun_fact}</p>
          </div>
        )}

        <button
          type="button"
          className={`td-disclaimer td-noshare ${showAssumptions ? 'open' : ''}`}
          onClick={() => setShowAssumptions((s) => !s)}
          aria-expanded={showAssumptions}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></svg>
          Estimate — tap to see assumptions
          <svg className="td-chev" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6" /></svg>
        </button>
        {showAssumptions && (
          <div className="td-assumptions td-noshare">
            <ul>
              {assumptions.map((a) => <li key={a}>{a}</li>)}
              {object?.confidence != null && <li>Identification confidence: {Math.round(object.confidence * 100)}%</li>}
              {(cost.warnings || []).map((w) => <li key={w} className="warn">{w}</li>)}
            </ul>
            {result.model && <div className="td-model">Physical estimate by {result.model}; costs computed from material &amp; process tables.</div>}
          </div>
        )}

        <Watermark date={date} />
      </div>
    </div>
  )
}

/**
 * Modal overlay showing the loading scan, an error, or the shareable result card.
 */
export default function TeardownCard({ status, result, error, previewUrl, onClose, onCancel, onRetry, onAgain }) {
  const shareRef = useRef(null)
  const [sharing, setSharing] = useState(false)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') (status === 'uploading' ? onCancel : onClose)() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [status, onClose, onCancel])

  useEffect(() => {
    if (!toast) return undefined
    const t = setTimeout(() => setToast(null), 2600)
    return () => clearTimeout(t)
  }, [toast])

  const share = async () => {
    if (!shareRef.current || sharing) return
    setSharing(true)
    let stage = null
    try {
      const [{ toBlob }, fontEmbedCSS] = await Promise.all([import('html-to-image'), cardFontCSS()])
      // Capture an off-screen copy in "poster" mode: the punchline only, compact enough to share
      const src = shareRef.current
      stage = document.createElement('div')
      stage.className = 'td-capture-stage'
      const node = src.cloneNode(true)
      node.classList.add('is-capturing')
      stage.appendChild(node)
      document.body.appendChild(stage)
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))
      const blob = await toBlob(node, {
        ...(fontEmbedCSS ? { fontEmbedCSS } : {}),
        pixelRatio: 2,
        backgroundColor: '#F4F7FC',
        width: node.offsetWidth,
        height: node.offsetHeight,
      })
      if (!blob) throw new Error('empty image')
      const slug = (result?.object?.name || 'teardown').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40)
      const file = new File([blob], `teardown-${slug}.png`, { type: 'image/png' })
      const text = result
        ? `${result.object?.name}: costs ${rupees(result.cost.total)} to make, sells for ${rupees(result.markup?.price_used)} (${formatMultiple(result.markup?.multiple)}× markup). Torn down by my engineer twin.`
        : ''
      if (navigator.canShare?.({ files: [file] })) {
        try {
          await navigator.share({ files: [file], title: 'What does it really cost?', text })
          return
        } catch (e) {
          if (e.name === 'AbortError') return
        }
      }
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = file.name
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => URL.revokeObjectURL(url), 4000)
      setToast('Image saved — share it anywhere')
    } catch (e) {
      console.error('Share image failed:', e?.message || e?.type || String(e))
      setToast('Could not make the image — try a screenshot')
    } finally {
      stage?.remove()
      setSharing(false)
    }
  }

  return (
    <div className="td-modal" role="dialog" aria-modal="true" aria-label="Teardown result" onClick={(e) => { if (e.target === e.currentTarget && status !== 'uploading') onClose() }}>
      <div className={`td-card state-${status}`}>
        <button className="td-close" onClick={status === 'uploading' ? onCancel : onClose} aria-label="Close">
          <CloseIcon />
        </button>

        <div className="td-scroll">
          {status === 'uploading' && <LoadingBody previewUrl={previewUrl} onCancel={onCancel} />}
          {status === 'error' && <ErrorBody previewUrl={previewUrl} error={error} onRetry={onRetry} onBack={onAgain} />}
          {status === 'done' && result && <ResultBody result={result} previewUrl={previewUrl} shareRef={shareRef} />}
        </div>

        {status === 'done' && result && (
          <div className="td-footer-actions">
            <button className="td-btn primary" onClick={share} disabled={sharing}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" /><polyline points="16 6 12 2 8 6" /><line x1="12" y1="2" x2="12" y2="15" /></svg>
              {sharing ? 'Making image…' : 'Share image'}
            </button>
            <button className="td-btn ghost" onClick={onAgain}>Tear down another</button>
          </div>
        )}
        {toast && <div className="td-toast">{toast}</div>}
      </div>
    </div>
  )
}
