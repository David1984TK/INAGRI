import { Link } from 'react-router-dom'
import { fechaCorta, haceCuanto } from '../../utils/fechas'
import { ESTADOS_CICLO, ESTADOS_PARCELA, alertaPrincipal, mensajeAlerta, redondear, superficie, tieneAlerta } from '../../utils/parcelas'
import MiniGrafica from '../MiniGrafica'
import SinDatos from '../SinDatos'
import MenuParcela from './MenuParcela'

function Metrica({ icono, etiqueta, valor, unidad, valores, alerta }) {
  return (
    <div className={`metrica ${alerta ? 'metrica-alerta' : ''}`}>
      <span className="metrica-etiqueta">
        <i className={`bi ${icono}`} aria-hidden="true" />
        {etiqueta}
      </span>
      <span className="metrica-valor">
        {redondear(valor)}
        <small>{unidad}</small>
      </span>
      <MiniGrafica valores={valores} tono={alerta ? 'naranja' : 'verde'} />
    </div>
  )
}

export default function TarjetaParcela({ parcela, alEditar, alEliminar }) {
  const { ciclo, sensores, ultima_lectura: lectura, alertas, estado } = parcela
  const infoEstado = ESTADOS_PARCELA[estado] ?? ESTADOS_PARCELA.sin_datos
  const alerta = alertaPrincipal(alertas)
  const conLectura = estado !== 'sin_datos' && lectura
  const progreso = ciclo?.dias_totales ? Math.min(100, (ciclo.dia_actual / ciclo.dias_totales) * 100) : 0
  const detalleCultivo = [ciclo?.cultivo, superficie(parcela.superficie_ha)].filter(Boolean).join(' · ')
  const hace = haceCuanto(lectura?.fecha_hora)

  return (
    <article className={`tarjeta tarjeta-${infoEstado.tono}`}>
      <header className="tarjeta-encabezado">
        <div className="tarjeta-titulos">
          <h2>{parcela.nombre}</h2>
          <p>{detalleCultivo}</p>
          {parcela.ubicacion && (
            <p>
              <i className="bi bi-geo-alt" aria-hidden="true" /> {parcela.ubicacion}
            </p>
          )}
        </div>
        <span className={`insignia insignia-${infoEstado.tono}`}>{infoEstado.etiqueta}</span>
        <MenuParcela parcela={parcela} alEditar={alEditar} alEliminar={alEliminar} />
      </header>

      {conLectura ? (
        <>
          {alerta ? (
            <p className="tarjeta-mensaje tarjeta-mensaje-alerta">
              <i className="bi bi-exclamation-triangle" aria-hidden="true" /> {mensajeAlerta(alerta)}
            </p>
          ) : (
            <p className="tarjeta-mensaje">
              <i className="bi bi-check-circle" aria-hidden="true" /> Humedad y temperatura en rango
            </p>
          )}

          <div className="tarjeta-metricas">
            <Metrica
              icono="bi-droplet"
              etiqueta="Humedad"
              valor={lectura.humedad}
              unidad="%"
              valores={parcela.tendencia?.humedad}
              alerta={tieneAlerta(alertas, 'humedad')}
            />
            <Metrica
              icono="bi-thermometer-half"
              etiqueta="Temperatura"
              valor={lectura.temperatura}
              unidad="°C"
              valores={parcela.tendencia?.temperatura}
              alerta={tieneAlerta(alertas, 'temperatura')}
            />
          </div>
        </>
      ) : (
        <SinDatos className="tarjeta-sin-datos" texto="Aún no hay lecturas de los sensores de esta parcela." />
      )}

      {ciclo && (
        <div className="tarjeta-ciclo">
          <div className="tarjeta-ciclo-encabezado">
            <span>
              <i className="bi bi-calendar3" aria-hidden="true" /> Ciclo de siembra
            </span>
            <span className="insignia insignia-verde insignia-chica">{ESTADOS_CICLO[ciclo.estado] ?? 'En curso'}</span>
          </div>
          <div className="barra-progreso" role="progressbar" aria-valuenow={Math.round(progreso)} aria-valuemin={0} aria-valuemax={100}>
            <span style={{ width: `${progreso}%` }} />
          </div>
          <div className="tarjeta-ciclo-pie">
            <strong>{ciclo.dias_totales ? `Día ${ciclo.dia_actual} de ${ciclo.dias_totales}` : `Día ${ciclo.dia_actual}`}</strong>
            <span>Cosecha estimada · {fechaCorta(ciclo.fecha_cosecha_estimada)}</span>
          </div>
        </div>
      )}

      <footer className="tarjeta-pie">
        <span className={`punto ${sensores?.sin_senal > 0 ? 'punto-naranja' : sensores?.en_linea > 0 ? 'punto-verde' : 'punto-gris'}`} />
        <span>
          {sensores?.total > 0 ? `${sensores.en_linea} de ${sensores.total} sensores` : 'Sin sensores'}
          {hace && ` · ${hace}`}
        </span>
        <Link to={`/parcelas/${parcela.id_parcela}`} className="tarjeta-ir" aria-label={`Ver detalle de ${parcela.nombre}`}>
          <i className="bi bi-chevron-right" />
        </Link>
      </footer>
    </article>
  )
}

export function TarjetaVacia() {
  return (
    <article className="tarjeta tarjeta-gris tarjeta-vacia">
      <SinDatos className="tarjeta-sin-datos" texto="Cuando haya parcelas registradas aparecerán aquí." />
    </article>
  )
}
