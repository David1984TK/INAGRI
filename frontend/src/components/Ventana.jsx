import { useEffect, useId, useRef } from 'react'
import { createPortal } from 'react-dom'
import './Ventana.css'

// Ventana modal de vidrio. `apilada` pone el ícono arriba del título (confirmaciones).
export default function Ventana({ titulo, subtitulo, icono, tono = 'verde', apilada = false, ancho = 560, alCerrar, children }) {
  const idTitulo = useId()
  const ref = useRef(null)
  const alCerrarRef = useRef(alCerrar)

  useEffect(() => {
    alCerrarRef.current = alCerrar
  })

  useEffect(() => {
    const anterior = document.activeElement
    const primero = ref.current.querySelector('[data-autofocus]') ?? ref.current.querySelector('input, select, button')
    primero?.focus()

    function alTeclear(evento) {
      if (evento.key === 'Escape') alCerrarRef.current()
    }
    document.addEventListener('keydown', alTeclear)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', alTeclear)
      document.body.style.overflow = ''
      anterior?.focus?.()
    }
  }, [])

  return createPortal(
    <div className="ventana-fondo" onMouseDown={(e) => e.target === e.currentTarget && alCerrar()}>
      <div
        ref={ref}
        className={`ventana vidrio ${apilada ? 'ventana-apilada' : ''}`}
        style={{ maxWidth: ancho }}
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
      >
        <header className="ventana-encabezado">
          <span className={`ventana-icono ventana-icono-${tono}`} aria-hidden="true">
            <i className={`bi ${icono}`} />
          </span>
          <div className="ventana-titulos">
            <h2 id={idTitulo}>{titulo}</h2>
            {subtitulo && <p>{subtitulo}</p>}
          </div>
          {!apilada && (
            <button type="button" className="boton-icono ventana-cerrar" aria-label="Cerrar" onClick={alCerrar}>
              <i className="bi bi-x-lg" />
            </button>
          )}
        </header>
        {children}
      </div>
    </div>,
    document.body,
  )
}
