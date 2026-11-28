export default function SinDatos({ texto, icono = 'bi-bar-chart-line', className = '' }) {
  return (
    <div className={`sin-datos ${className}`}>
      <i className={`bi ${icono}`} aria-hidden="true" />
      <strong>Sin datos que mostrar</strong>
      {texto && <span>{texto}</span>}
    </div>
  )
}
