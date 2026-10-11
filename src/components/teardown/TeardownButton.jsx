import React, { useEffect, useRef, useState } from 'react'
import './Teardown.css'

export const CameraIcon = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
    <circle cx="12" cy="13" r="4" />
  </svg>
)

/**
 * The prominent "What's it really cost?" pill + the small sheet that collects
 * a photo, the price paid and an optional hint.
 */
export default function TeardownButton({ busy, onSubmit, open, setOpen }) {
  const [file, setFile] = useState(null)
  const [thumb, setThumb] = useState(null)
  const [price, setPrice] = useState('')
  const [hint, setHint] = useState('')
  const inputRef = useRef(null)
  const wrapRef = useRef(null)

  useEffect(() => () => { if (thumb) URL.revokeObjectURL(thumb) }, [thumb])

  // Close on outside click / Escape
  useEffect(() => {
    if (!open) return
    const onDown = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false) }
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('pointerdown', onDown)
    document.addEventListener('keydown', onKey)
    return () => { document.removeEventListener('pointerdown', onDown); document.removeEventListener('keydown', onKey) }
  }, [open, setOpen])

  const pick = (f) => {
    if (!f || !f.type.startsWith('image/')) return
    setFile(f)
    setThumb(URL.createObjectURL(f))
  }

  const submit = (e) => {
    e.preventDefault()
    if (!file || busy) return
    onSubmit(file, { pricePaid: price.replace(/[^\d.]/g, ''), hint })
    setOpen(false)
  }

  // Once a teardown has started, clear the form for the next one
  const clear = () => { setFile(null); setThumb(null); setPrice(''); setHint('') }
  useEffect(() => { if (busy) clear() }, [busy])

  return (
    <div className={`td-anchor ${open ? 'is-open' : ''}`} ref={wrapRef}>
      {open && <div className="td-sheet-scrim" onClick={() => setOpen(false)} />}
      {open && (
        <form className="td-sheet" onSubmit={submit} aria-label="Tear down an object">
          <div className="td-sheet-head">
            <div>
              <div className="td-sheet-title">What does it really cost?</div>
              <div className="td-sheet-sub">Snap it — I'll work out the factory cost.</div>
            </div>
            <button type="button" className="td-icon-btn" onClick={() => setOpen(false)} aria-label="Close">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><path d="M18 6 6 18M6 6l12 12" /></svg>
            </button>
          </div>

          <input
            ref={inputRef}
            className="td-file"
            type="file"
            accept="image/*"
            capture="environment"
            onChange={(e) => { pick(e.target.files?.[0]); e.target.value = '' }}
          />
          <button
            type="button"
            className={`td-drop ${thumb ? 'has-photo' : ''}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files?.[0]) }}
          >
            {thumb ? (
              <>
                <img src={thumb} alt="Selected item" />
                <span className="td-drop-change">Change photo</span>
              </>
            ) : (
              <>
                <span className="td-drop-icon"><CameraIcon size={22} /></span>
                <span className="td-drop-main">Take or choose a photo</span>
                <span className="td-drop-sub">Whole object, good light · JPG/PNG up to 8 MB</span>
              </>
            )}
          </button>

          <label className="td-field">
            <span>Price you paid <em>optional</em></span>
            <div className="td-input-wrap">
              <span className="td-rupee">₹</span>
              <input
                inputMode="decimal"
                placeholder="1,499"
                value={price}
                onChange={(e) => setPrice(e.target.value.replace(/[^\d.,]/g, ''))}
              />
            </div>
          </label>
          <label className="td-field">
            <span>What is it? <em>optional</em></span>
            <input
              className="td-input"
              placeholder="e.g. Milton 1 L steel bottle"
              maxLength={120}
              value={hint}
              onChange={(e) => setHint(e.target.value)}
            />
          </label>

          <button className="td-go" type="submit" disabled={!file || busy}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
            </svg>
            Tear it down
          </button>
        </form>
      )}

      <button
        type="button"
        className="td-pill"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-label="What does it really cost? Tear down a photo"
      >
        <span className="td-pill-icon"><CameraIcon /></span>
        <span className="td-pill-text">
          <strong>What's it really cost?</strong>
          <small>Snap anything · see the markup</small>
        </span>
      </button>
    </div>
  )
}
