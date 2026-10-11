import React, { useCallback, useRef, useState } from 'react'
import useTeardown from '../../hooks/useTeardown'
import TeardownButton from './TeardownButton'
import TeardownCard from './TeardownCard'

/**
 * "What does it really cost?" feature: button + sheet + result modal.
 * onResult(result) fires once per successful teardown (scene + narration hooks).
 */
export default function Teardown({ onResult, onStart }) {
  const td = useTeardown()
  const [sheetOpen, setSheetOpen] = useState(false)
  const [cardOpen, setCardOpen] = useState(false)
  const lastRef = useRef(null)

  const start = useCallback(async (file, opts) => {
    lastRef.current = { file, opts }
    setCardOpen(true)
    onStart?.()
    const result = await td.run(file, opts)
    if (result) onResult?.(result)
  }, [td, onResult, onStart])

  const retry = () => { if (lastRef.current) start(lastRef.current.file, lastRef.current.opts) }
  const close = () => setCardOpen(false)
  const cancel = () => { td.cancel(); setCardOpen(false) }
  const again = () => { setCardOpen(false); setSheetOpen(true) }

  return (
    <>
      <TeardownButton
        busy={td.status === 'uploading'}
        onSubmit={start}
        open={sheetOpen}
        setOpen={setSheetOpen}
      />
      {cardOpen && td.status !== 'idle' && (
        <TeardownCard
          status={td.status}
          result={td.result}
          error={td.error}
          previewUrl={td.previewUrl}
          onClose={close}
          onCancel={cancel}
          onRetry={retry}
          onAgain={again}
        />
      )}
    </>
  )
}
