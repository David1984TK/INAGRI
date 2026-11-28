const ANCHO = 700
const ALTO = 100

function escala(valores, paso) {
  let bajo = Math.floor(Math.min(...valores) / paso) * paso
  let alto = Math.ceil(Math.max(...valores) / paso) * paso
  if (bajo === alto) {
    bajo -= paso
    alto += paso
  }
  if ((alto - bajo) % (paso * 2) !== 0) alto += paso
  return [bajo, (bajo + alto) / 2, alto]
}

// puntos: [{ t: milisegundos, valor }]. desde/hasta en milisegundos.
export default function GraficaLecturas({ puntos, desde, hasta, etiquetasX, unidad, paso = 10, tono = 'verde' }) {
  const ordenados = [...puntos].sort((a, b) => a.t - b.t)
  const marcas = escala(
    ordenados.map((p) => p.valor),
    paso,
  )
  const [minimo, , maximo] = marcas
  const x = (t) => ((t - desde) / (hasta - desde)) * ANCHO
  const y = (valor) => ALTO - ((valor - minimo) / (maximo - minimo)) * ALTO

  const linea = ordenados.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(p.t).toFixed(1)},${y(p.valor).toFixed(1)}`).join(' ')
  const primero = ordenados[0]
  const ultimo = ordenados.at(-1)
  const area = `${linea} L${x(ultimo.t).toFixed(1)},${ALTO} L${x(primero.t).toFixed(1)},${ALTO} Z`

  return (
    <div className={`grafica-lecturas grafica-${tono}`}>
      <div className="grafica-eje-y" aria-hidden="true">
        {[...marcas].reverse().map((marca) => (
          <span key={marca}>
            {marca} {unidad}
          </span>
        ))}
      </div>
      <div className="grafica-lienzo">
        <svg viewBox={`0 0 ${ANCHO} ${ALTO}`} preserveAspectRatio="none" role="img" aria-label="Gráfica de lecturas">
          {marcas.map((marca) => (
            <line key={marca} x1="0" x2={ANCHO} y1={y(marca)} y2={y(marca)} className="grafica-guia" vectorEffect="non-scaling-stroke" />
          ))}
          <path d={area} className="grafica-area" />
          <path d={linea} className="grafica-linea" vectorEffect="non-scaling-stroke" />
        </svg>
        <span
          className="grafica-punto"
          style={{ left: `${(x(ultimo.t) / ANCHO) * 100}%`, top: `${(y(ultimo.valor) / ALTO) * 100}%` }}
        />
      </div>
      <div className="grafica-eje-x" aria-hidden="true">
        {etiquetasX.map((etiqueta, i) => (
          <span key={i}>{etiqueta}</span>
        ))}
      </div>
    </div>
  )
}
