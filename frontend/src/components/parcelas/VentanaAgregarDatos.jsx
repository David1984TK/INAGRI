import { useState } from 'react'
import { useAvisos } from '../../hooks/useAvisos'
import { registrarLectura } from '../../services/parcelas'
import { horaActual, horaDeHoyAISO } from '../../utils/fechas'
import Campo from '../Campo'
import Ventana from '../Ventana'

const TOLERANCIA_MS = 5 * 60 * 1000

function horaEnFuturo(hora) {
  return new Date(horaDeHoyAISO(hora)).getTime() > Date.now() + TOLERANCIA_MS
}

function validar(f) {
  const errores = {}
  const humedad = Number(f.humedad)
  const temperatura = Number(f.temperatura)
  if (!f.idSensor) errores.idSensor = 'Elige un sensor.'
  if (f.humedad === '' || !(humedad >= 0 && humedad <= 100)) errores.humedad = 'Entre 0 y 100 %.'
  if (f.temperatura === '' || !(temperatura >= -40 && temperatura <= 85)) errores.temperatura = 'Entre -40 y 85 °C.'
  if (!f.horaHumedad) errores.horaHumedad = 'Elige la hora.'
  else if (horaEnFuturo(f.horaHumedad)) errores.horaHumedad = 'No puede ser futura.'
  if (!f.horaTemperatura) errores.horaTemperatura = 'Elige la hora.'
  else if (horaEnFuturo(f.horaTemperatura)) errores.horaTemperatura = 'No puede ser futura.'
  return errores
}

// `sensores` es null mientras se cargan.
export default function VentanaAgregarDatos({ sensores, idSensorInicial, alCerrar, alGuardar }) {
  const { mostrar } = useAvisos()
  const ahora = horaActual()
  const [formulario, setFormulario] = useState({
    idSensor: idSensorInicial ? String(idSensorInicial) : '',
    humedad: '',
    horaHumedad: ahora,
    temperatura: '',
    horaTemperatura: ahora,
  })
  const [errores, setErrores] = useState({})
  const [guardando, setGuardando] = useState(false)

  const lista = sensores ?? []
  const idSensor = formulario.idSensor || (lista[0] ? String(lista[0].id_sensor) : '')
  const sensor = lista.find((s) => String(s.id_sensor) === idSensor)
  const sinSensores = sensores !== null && lista.length === 0

  function cambiar(campo, valor) {
    setFormulario((f) => ({ ...f, [campo]: valor }))
    setErrores((e) => ({ ...e, [campo]: undefined }))
  }

  async function enviar(evento) {
    evento.preventDefault()
    const encontrados = validar({ ...formulario, idSensor })
    setErrores(encontrados)
    if (Object.keys(encontrados).length > 0) return

    setGuardando(true)
    try {
      await registrarLectura({
        id_sensor: sensor.id_sensor,
        id_parcela: sensor.id_parcela,
        humedad: Number(formulario.humedad),
        hora_humedad: horaDeHoyAISO(formulario.horaHumedad),
        temperatura: Number(formulario.temperatura),
        hora_temperatura: horaDeHoyAISO(formulario.horaTemperatura),
      })
      mostrar({ titulo: 'Registro guardado', mensaje: 'Se guardó correctamente.' })
      alGuardar()
    } catch (error) {
      console.error(error)
      mostrar({ tipo: 'error', titulo: 'No se pudo guardar', mensaje: 'Intenta de nuevo en un momento.' })
      setGuardando(false)
    }
  }

  const tonoPunto = sensor ? (sensor.estado === 'en_linea' ? 'punto-verde' : 'punto-naranja') : 'punto-gris'

  return (
    <Ventana titulo="Agregar datos" subtitulo="Registra una lectura manual de un sensor" icono="bi-pencil" alCerrar={alCerrar}>
      <form className="ventana-cuerpo" onSubmit={enviar} noValidate>
        <Campo
          etiqueta="Sensor"
          error={errores.idSensor}
          ayuda={sinSensores ? 'Aún no hay sensores asignados a tus parcelas.' : undefined}
        >
          <span className={`punto ${tonoPunto}`} aria-hidden="true" />
          <select
            data-autofocus
            value={idSensor}
            onChange={(e) => cambiar('idSensor', e.target.value)}
            disabled={lista.length === 0}
          >
            {sensores === null && <option value="">Cargando sensores…</option>}
            {sinSensores && <option value="">Sin sensores disponibles</option>}
            {lista.map((s) => (
              <option key={s.id_sensor} value={s.id_sensor}>
                {s.parcela} · {s.descripcion ?? `Sensor ${s.id_sensor}`}
              </option>
            ))}
          </select>
        </Campo>

        <fieldset className="ventana-caja">
          <legend className="ventana-caja-titulo">
            <i className="bi bi-droplet" aria-hidden="true" /> Humedad del suelo
          </legend>
          <div className="ventana-caja-campos">
            <Campo etiqueta="Valor" unidad="%" error={errores.humedad}>
              <input
                type="number"
                inputMode="decimal"
                min="0"
                max="100"
                step="0.1"
                value={formulario.humedad}
                onChange={(e) => cambiar('humedad', e.target.value)}
                placeholder="0"
              />
            </Campo>
            <Campo etiqueta="Hora" icono="bi-clock" error={errores.horaHumedad}>
              <input type="time" value={formulario.horaHumedad} onChange={(e) => cambiar('horaHumedad', e.target.value)} />
            </Campo>
          </div>
        </fieldset>

        <fieldset className="ventana-caja">
          <legend className="ventana-caja-titulo">
            <i className="bi bi-thermometer-half" aria-hidden="true" /> Temperatura
          </legend>
          <div className="ventana-caja-campos">
            <Campo etiqueta="Valor" unidad="°C" error={errores.temperatura}>
              <input
                type="number"
                inputMode="decimal"
                min="-40"
                max="85"
                step="0.1"
                value={formulario.temperatura}
                onChange={(e) => cambiar('temperatura', e.target.value)}
                placeholder="0"
              />
            </Campo>
            <Campo etiqueta="Hora" icono="bi-clock" error={errores.horaTemperatura}>
              <input
                type="time"
                value={formulario.horaTemperatura}
                onChange={(e) => cambiar('horaTemperatura', e.target.value)}
              />
            </Campo>
          </div>
        </fieldset>

        <div className="ventana-pie">
          <button type="button" className="boton boton-secundario" onClick={alCerrar}>
            Cancelar
          </button>
          <button type="submit" className="boton boton-primario" disabled={guardando || lista.length === 0}>
            <i className="bi bi-check-lg" aria-hidden="true" />
            {guardando ? 'Guardando…' : 'Guardar datos'}
          </button>
        </div>
      </form>
    </Ventana>
  )
}
