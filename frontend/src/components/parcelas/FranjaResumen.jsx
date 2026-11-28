import { diasEntre, hoyISO } from '../../utils/fechas'

function diasProximaCosecha(parcelas) {
  const hoy = hoyISO()
  const dias = parcelas
    .map((p) => p.ciclo?.fecha_cosecha_estimada)
    .filter(Boolean)
    .map((fecha) => diasEntre(hoy, fecha))
    .filter((d) => d >= 0)
  return dias.length > 0 ? Math.min(...dias) : null
}

export default function FranjaResumen({ resumen, parcelas, alAgregarDatos }) {
  const conAlerta = resumen?.parcelas_con_alerta ?? null
  const dias = diasProximaCosecha(parcelas)

  return (
    <section className="franja" aria-label="Resumen">
      <button type="button" className="franja-celda franja-agregar" onClick={alAgregarDatos}>
        <span className="franja-icono franja-icono-solido" aria-hidden="true">
          <i className="bi bi-pencil" />
        </span>
        <span className="franja-texto">
          <strong>Agregar datos</strong>
          <span>Registrar una lectura manual</span>
        </span>
        <i className="bi bi-chevron-right franja-flecha" aria-hidden="true" />
      </button>

      <div className={`franja-celda ${conAlerta > 0 ? 'franja-alerta' : ''}`}>
        <span className="franja-icono franja-icono-naranja" aria-hidden="true">
          <i className="bi bi-exclamation-triangle" />
        </span>
        <span className="franja-texto">
          <strong>{conAlerta ?? '—'}</strong>
          <span>Requieren atención</span>
        </span>
      </div>

      <div className="franja-celda">
        <span className="franja-icono" aria-hidden="true">
          <i className="bi bi-wifi" />
        </span>
        <span className="franja-texto">
          <strong>{resumen ? `${resumen.sensores_en_linea} de ${resumen.sensores_total}` : '—'}</strong>
          <span>Sensores en línea</span>
        </span>
      </div>

      <div className="franja-celda">
        <span className="franja-icono" aria-hidden="true">
          <i className="bi bi-calendar3" />
        </span>
        <span className="franja-texto">
          <strong>{dias === null ? '—' : dias === 1 ? '1 día' : `${dias} días`}</strong>
          <span>Próxima cosecha</span>
        </span>
      </div>
    </section>
  )
}
