import { useCallback, useMemo, useRef, useState } from 'react'
import { AvisosContext } from '../context/avisos'
import './Avisos.css'

const DURACION_MS = 4500

export default function ProveedorAvisos({ children }) {
  const [avisos, setAvisos] = useState([])
  const siguienteId = useRef(1)

  const quitar = useCallback((id) => {
    setAvisos((actuales) => actuales.filter((a) => a.id !== id))
  }, [])

  const mostrar = useCallback(
    ({ tipo = 'exito', titulo, mensaje }) => {
      const id = siguienteId.current++
      setAvisos((actuales) => [...actuales, { id, tipo, titulo, mensaje }])
      setTimeout(() => quitar(id), DURACION_MS)
    },
    [quitar],
  )

  const valor = useMemo(() => ({ mostrar }), [mostrar])

  return (
    <AvisosContext.Provider value={valor}>
      {children}
      <div className="avisos" role="status" aria-live="polite">
        {avisos.map((aviso) => (
          <div key={aviso.id} className={`aviso aviso-${aviso.tipo} vidrio`}>
            <span className="aviso-icono" aria-hidden="true">
              <i className={aviso.tipo === 'exito' ? 'bi bi-check-lg' : 'bi bi-exclamation-lg'} />
            </span>
            <div className="aviso-texto">
              <strong>{aviso.titulo}</strong>
              {aviso.mensaje && <span>{aviso.mensaje}</span>}
            </div>
            <button type="button" className="aviso-cerrar" aria-label="Cerrar aviso" onClick={() => quitar(aviso.id)}>
              <i className="bi bi-x-lg" />
            </button>
            <span className="aviso-progreso" style={{ animationDuration: `${DURACION_MS}ms` }} />
          </div>
        ))}
      </div>
    </AvisosContext.Provider>
  )
}
