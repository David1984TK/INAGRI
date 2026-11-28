const ANCHO = 100
const ALTO = 40
const MARGEN = 4

export default function MiniGrafica({ valores = [], tono = 'verde' }) {
  if (valores.length < 2) {
    return <div className="mini-grafica mini-grafica-vacia" aria-hidden="true" />
  }

  const minimo = Math.min(...valores)
  const maximo = Math.max(...valores)
  const rango = maximo - minimo || 1
  const puntos = valores.map((valor, i) => [
    (i / (valores.length - 1)) * ANCHO,
    MARGEN + (1 - (valor - minimo) / rango) * (ALTO - MARGEN * 2),
  ])
  const linea = puntos.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ')
  const area = `${linea} L${ANCHO},${ALTO} L0,${ALTO} Z`
  const [, yFinal] = puntos.at(-1)

  return (
    <div className={`mini-grafica mini-grafica-${tono}`} aria-hidden="true">
      <svg viewBox={`0 0 ${ANCHO} ${ALTO}`} preserveAspectRatio="none">
        <path d={area} className="mini-grafica-area" />
        <path d={linea} className="mini-grafica-linea" vectorEffect="non-scaling-stroke" />
      </svg>
      <span className="mini-grafica-punto" style={{ top: `${(yFinal / ALTO) * 100}%` }} />
    </div>
  )
}
