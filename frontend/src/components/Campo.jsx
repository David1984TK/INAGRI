export default function Campo({ etiqueta, icono, unidad, ayuda, error, children }) {
  return (
    <label className="campo">
      <span className="campo-etiqueta">{etiqueta}</span>
      <span className={`campo-control ${error ? 'con-error' : ''}`}>
        {icono && <i className={`bi ${icono}`} aria-hidden="true" />}
        {children}
        {unidad && <span className="campo-unidad">{unidad}</span>}
      </span>
      {error ? <span className="campo-error">{error}</span> : ayuda && <span className="campo-ayuda">{ayuda}</span>}
    </label>
  )
}
