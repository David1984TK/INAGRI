import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import GraficaLecturas from '../components/GraficaLecturas'
import VentanaAgregarDatos from '../components/parcelas/VentanaAgregarDatos'
import SinDatos from '../components/SinDatos'
import { obtenerDetalleParcela, obtenerLecturasSensor } from '../services/parcelas'
import { diasEntre, fechaHoraLectura, fechaLarga, haceCuanto, hoyISO } from '../utils/fechas'
import { ESTADOS_PARCELA, alertaPrincipal, motivoAlerta, redondear, superficie } from '../utils/parcelas'
import './DetalleParcela.css'

const HORAS_GRAFICA = 24
const ETIQUETAS_EJE = ['Hace 24 h', 'Hace 18 h', 'Hace 12 h', 'Hace 6 h', 'Ahora']
const METRICAS = {
  humedad: { etiqueta: 'Humedad', descripcion: 'Humedad del suelo', unidad: '%', paso: 10 },
  temperatura: { etiqueta: 'Temperatura', descripcion: 'Temperatura', unidad: '°C', paso: 5 },
}

function ultimasHoras() {
  const hasta = new Date()
  return { desde: new Date(hasta.getTime() - HORAS_GRAFICA * 3600000), hasta }
}

function tiempoSinDatos(minutos) {
  if (minutos === null || minutos === undefined) return ''
  if (minutos < 60) return ` · ${minutos} min`
  if (minutos < 1440) return ` · ${Math.floor(minutos / 60)} h`
  return ` · ${Math.floor(minutos / 1440)} d`
}

function estadoSensor(sensor) {
  if (sensor.estado === 'en_linea') return haceCuanto(sensor.ultima_lectura?.fecha_hora) ?? 'en línea'
  if (sensor.estado === 'inactivo') return 'inactivo'
  return `sin señal${tiempoSinDatos(sensor.minutos_sin_datos)}`
}

function nombreSensor(sensor) {
  return sensor?.descripcion ?? (sensor ? `Sensor ${sensor.id_sensor}` : '—')
}

export default function DetalleParcela() {
  const idParcela = Number(useParams().id)
  const [detalle, setDetalle] = useState(null)
  const [recarga, setRecarga] = useState(0)
  const [idSensorElegido, setIdSensorElegido] = useState(null)
  const [metrica, setMetrica] = useState('humedad')
  const [consulta, setConsulta] = useState(() => ({ lecturas: [], ventana: ultimasHoras() }))
  const [agregando, setAgregando] = useState(false)

  useEffect(() => {
    let vigente = true
    obtenerDetalleParcela(idParcela)
      .then((respuesta) => vigente && setDetalle(respuesta))
      .catch((error) => console.error(error))
    return () => {
      vigente = false
    }
  }, [idParcela, recarga])

  const parcela = detalle?.parcela ?? null
  const sensores = detalle?.sensores ?? []
  const sensor = sensores.find((s) => s.id_sensor === idSensorElegido) ?? sensores[0] ?? null
  const idSensor = sensor?.id_sensor ?? null

  useEffect(() => {
    if (idSensor === null) return
    let vigente = true
    const ventana = ultimasHoras()
    obtenerLecturasSensor(idSensor, { horas: HORAS_GRAFICA })
      .then((respuesta) => vigente && setConsulta({ lecturas: respuesta.lecturas, ventana }))
      .catch((error) => console.error(error))
    return () => {
      vigente = false
    }
  }, [idSensor, recarga])

  const lecturas = idSensor === null ? [] : consulta.lecturas
  const infoMetrica = METRICAS[metrica]
  const valores = lecturas.map((l) => l[metrica])
  const conAlerta = sensor?.alertas?.some((a) => a.tipo === metrica)
  const estadistica = (calcular) => (valores.length > 0 ? `${redondear(calcular(valores))} ${infoMetrica.unidad}` : '—')

  const infoEstado = ESTADOS_PARCELA[parcela?.estado] ?? ESTADOS_PARCELA.sin_datos
  const alerta = alertaPrincipal(parcela?.alertas)
  const textoEstado =
    parcela?.estado === 'requiere_atencion' && alerta ? `${infoEstado.etiqueta} · ${motivoAlerta(alerta)}` : infoEstado.etiqueta

  const ciclo = parcela?.ciclo
  const progreso = ciclo?.dias_totales ? Math.min(100, (ciclo.dia_actual / ciclo.dias_totales) * 100) : 0
  const diasCosecha = ciclo?.fecha_cosecha_estimada ? diasEntre(hoyISO(), ciclo.fecha_cosecha_estimada) : null
  const sensoresEnLinea = parcela?.sensores?.en_linea ?? 0
  const sensoresTotal = parcela?.sensores?.total ?? 0

  return (
    <>
      <nav className="migas" aria-label="Ruta">
        <Link to="/parcelas">Mis parcelas</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{parcela?.nombre ?? 'Detalle de parcela'}</span>
      </nav>

      <div className="pagina-encabezado">
        <div className="detalle-titulo">
          <Link to="/parcelas" className="detalle-regresar" aria-label="Regresar a Mis parcelas">
            <i className="bi bi-arrow-left" />
          </Link>
          <h1>{parcela?.nombre ?? 'Detalle de parcela'}</h1>
          <span className={`insignia insignia-${infoEstado.tono}`}>{textoEstado}</span>
        </div>
        <button type="button" className="boton boton-primario" onClick={() => setAgregando(true)}>
          <i className="bi bi-plus-lg" aria-hidden="true" />
          Agregar datos
        </button>
      </div>

      <section className="detalle-datos" aria-label="Datos de la parcela">
        <div className="dato panel">
          <span className="dato-icono" aria-hidden="true">
            <i className="bi bi-flower1" />
          </span>
          <div>
            <strong>{ciclo?.cultivo ?? '—'}</strong>
            <span>{ciclo?.dias_totales ? `Ciclo de ${ciclo.dias_totales} días` : 'Sin cultivo en curso'}</span>
          </div>
        </div>
        <div className="dato panel">
          <span className="dato-icono" aria-hidden="true">
            <i className="bi bi-calendar3" />
          </span>
          <div className="dato-con-barra">
            <strong>{ciclo ? (ciclo.dias_totales ? `Día ${ciclo.dia_actual} de ${ciclo.dias_totales}` : `Día ${ciclo.dia_actual}`) : '—'}</strong>
            <span>Ciclo en curso</span>
            <div className="barra-progreso">
              <span style={{ width: `${progreso}%` }} />
            </div>
          </div>
        </div>
        <div className="dato panel">
          <span className="dato-icono" aria-hidden="true">
            <i className="bi bi-calendar-check" />
          </span>
          <div>
            <strong>{fechaLarga(ciclo?.fecha_cosecha_estimada)}</strong>
            <span>
              {diasCosecha === null ? 'Cosecha estimada' : diasCosecha >= 0 ? `Cosecha en ${diasCosecha} días` : 'Cosecha vencida'}
            </span>
          </div>
        </div>
        <div className="dato panel">
          <span className="dato-icono" aria-hidden="true">
            <i className="bi bi-arrows-angle-expand" />
          </span>
          <div>
            <strong>{parcela ? superficie(parcela.superficie_ha) : '—'}</strong>
            <span>{[parcela?.ubicacion, parcela?.productor].filter(Boolean).join(' · ') || 'Superficie'}</span>
          </div>
        </div>
      </section>

      <div className="detalle-cuerpo">
        <section className="panel detalle-lecturas" aria-labelledby="titulo-lecturas">
          <header className="panel-encabezado">
            <div>
              <h2 id="titulo-lecturas">Lecturas</h2>
              <p>
                {sensor ? `Sensor ${nombreSensor(sensor)}` : 'Sin sensor'} · {infoMetrica.descripcion}
              </p>
            </div>
            <div className="detalle-controles">
              <label className="selector-sensor">
                <span className="sr-only">Sensor</span>
                <span className={`punto ${sensor?.estado === 'en_linea' ? 'punto-verde' : sensor ? 'punto-naranja' : 'punto-gris'}`} />
                <select value={idSensor ?? ''} onChange={(e) => setIdSensorElegido(Number(e.target.value))} disabled={sensores.length === 0}>
                  {sensores.length === 0 && <option value="">—</option>}
                  {sensores.map((s) => (
                    <option key={s.id_sensor} value={s.id_sensor}>
                      {nombreSensor(s)}
                    </option>
                  ))}
                </select>
              </label>
              <div className="segmentos" role="group" aria-label="Variable">
                {Object.entries(METRICAS).map(([clave, info]) => (
                  <button
                    key={clave}
                    type="button"
                    className={`segmento ${metrica === clave ? 'activo' : ''}`}
                    aria-pressed={metrica === clave}
                    onClick={() => setMetrica(clave)}
                  >
                    {info.etiqueta}
                  </button>
                ))}
              </div>
            </div>
          </header>

          {valores.length > 0 ? (
            <GraficaLecturas
              puntos={lecturas.map((l) => ({ t: new Date(l.fecha_hora).getTime(), valor: l[metrica] }))}
              desde={consulta.ventana.desde.getTime()}
              hasta={consulta.ventana.hasta.getTime()}
              etiquetasX={ETIQUETAS_EJE}
              unidad={infoMetrica.unidad}
              paso={infoMetrica.paso}
              tono={conAlerta ? 'naranja' : 'verde'}
            />
          ) : (
            <SinDatos
              className="detalle-grafica-vacia"
              texto={sensor ? 'No hay lecturas de este sensor en las últimas 24 horas.' : 'Esta parcela aún no tiene lecturas.'}
            />
          )}

          <dl className="estadisticas">
            <div>
              <dt>Actual</dt>
              <dd className={conAlerta ? 'texto-alerta' : ''}>{valores.length > 0 ? `${redondear(valores[0])} ${infoMetrica.unidad}` : '—'}</dd>
            </div>
            <div>
              <dt>Mínimo</dt>
              <dd>{estadistica((v) => Math.min(...v))}</dd>
            </div>
            <div>
              <dt>Máximo</dt>
              <dd>{estadistica((v) => Math.max(...v))}</dd>
            </div>
            <div>
              <dt>Promedio</dt>
              <dd>{estadistica((v) => v.reduce((suma, n) => suma + n, 0) / v.length)}</dd>
            </div>
          </dl>
        </section>

        <section className="panel detalle-sensores" aria-labelledby="titulo-sensores">
          <header className="panel-encabezado">
            <h2 id="titulo-sensores">Sensores</h2>
            {sensoresTotal > 0 && (
              <span className={sensoresEnLinea < sensoresTotal ? 'texto-alerta' : 'texto-ok'}>
                {sensoresEnLinea} de {sensoresTotal} en línea
              </span>
            )}
          </header>

          {sensores.length > 0 ? (
            <ul className="lista-sensores">
              {sensores.map((s) => {
                const lectura = s.ultima_lectura
                return (
                  <li key={s.id_sensor}>
                    <button
                      type="button"
                      className={`sensor ${s.id_sensor === idSensor ? 'activo' : ''}`}
                      aria-pressed={s.id_sensor === idSensor}
                      onClick={() => setIdSensorElegido(s.id_sensor)}
                    >
                      <span className={`punto ${s.estado === 'en_linea' ? 'punto-verde' : s.estado === 'inactivo' ? 'punto-gris' : 'punto-naranja'}`} />
                      <strong>{nombreSensor(s)}</strong>
                      <span className="sensor-valores">
                        {lectura && s.estado === 'en_linea'
                          ? `${redondear(lectura.humedad)} % · ${redondear(lectura.temperatura)} °C`
                          : '— · —'}
                      </span>
                      <span className="sensor-estado">{estadoSensor(s)}</span>
                    </button>
                  </li>
                )
              })}
            </ul>
          ) : (
            <SinDatos className="detalle-sensores-vacio" icono="bi-broadcast" texto="Esta parcela no tiene sensores asignados." />
          )}

          <p className="detalle-nota">
            <i className="bi bi-clock" aria-hidden="true" /> Cada sensor envía 1 lectura por hora
          </p>
        </section>
      </div>

      <section className="panel detalle-recientes" aria-labelledby="titulo-recientes">
        <header className="panel-encabezado">
          <h2 id="titulo-recientes">Lecturas recientes</h2>
          <div className="detalle-recientes-acciones">
            {sensor && <span>Sensor {nombreSensor(sensor)} · solo lectura</span>}
            <Link to="/lecturas" className="enlace">
              Ver todas <i className="bi bi-arrow-right" aria-hidden="true" />
            </Link>
          </div>
        </header>
        <div className="tabla-envoltura">
          <table className="tabla">
            <thead>
              <tr>
                <th scope="col">Fecha y hora</th>
                <th scope="col">Sensor</th>
                <th scope="col">Humedad</th>
                <th scope="col">Temperatura</th>
              </tr>
            </thead>
            <tbody>
              {lecturas.length > 0 ? (
                lecturas.slice(0, 3).map((l) => (
                  <tr key={l.fecha_hora}>
                    <td>
                      <strong>{fechaHoraLectura(l.fecha_hora)}</strong>
                    </td>
                    <td>{nombreSensor(sensor)}</td>
                    <td>{redondear(l.humedad)} %</td>
                    <td>{redondear(l.temperatura)} °C</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="tabla-vacia">
                    Sin datos que mostrar
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {agregando && (
        <VentanaAgregarDatos
          sensores={sensores
            .filter((s) => s.estatus !== 'inactivo')
            .map((s) => ({ ...s, id_parcela: parcela.id_parcela, parcela: parcela.nombre }))}
          idSensorInicial={idSensor}
          alCerrar={() => setAgregando(false)}
          alGuardar={() => {
            setAgregando(false)
            setRecarga((n) => n + 1)
          }}
        />
      )}
    </>
  )
}
