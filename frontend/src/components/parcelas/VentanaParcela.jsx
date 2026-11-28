import { useEffect, useState } from 'react'
import { useAvisos } from '../../hooks/useAvisos'
import { actualizarParcela, crearParcela, obtenerCultivos } from '../../services/parcelas'
import { hoyISO, sumarDias } from '../../utils/fechas'
import { ESTADOS_CICLO } from '../../utils/parcelas'
import Campo from '../Campo'
import Ventana from '../Ventana'

function validar(f) {
  const errores = {}
  if (!f.nombre.trim()) errores.nombre = 'Escribe el nombre de la parcela.'
  else if (f.nombre.trim().length > 100) errores.nombre = 'Máximo 100 caracteres.'
  if (!(Number(f.superficie) > 0)) errores.superficie = 'Mayor a 0.'
  if (f.ubicacion.trim().length > 150) errores.ubicacion = 'Máximo 150 caracteres.'
  if (f.idCultivo) {
    if (!f.siembra) errores.siembra = 'Elige la fecha.'
    if (f.cosecha && f.siembra && f.cosecha <= f.siembra) errores.cosecha = 'Debe ser después de la siembra.'
  }
  return errores
}

// Sin `parcela` es "Nueva parcela" (02j); con `parcela` es "Editar parcela" (02h).
export default function VentanaParcela({ parcela, idProductor, nombreProductor, alCerrar, alGuardar }) {
  const editando = Boolean(parcela)
  const { mostrar } = useAvisos()
  const [cultivos, setCultivos] = useState([])
  const [formulario, setFormulario] = useState({
    nombre: parcela?.nombre ?? '',
    superficie: parcela ? Number(parcela.superficie_ha).toFixed(1) : '',
    ubicacion: parcela?.ubicacion ?? '',
    idCultivo: '',
    siembra: parcela?.ciclo?.fecha_siembra ?? '',
    cosecha: parcela?.ciclo?.fecha_cosecha_estimada ?? '',
    estado: parcela?.ciclo?.estado ?? (editando && parcela.ciclo ? 'en_curso' : 'planeado'),
  })
  const [cosechaManual, setCosechaManual] = useState(Boolean(parcela?.ciclo?.fecha_cosecha_estimada))
  const [errores, setErrores] = useState({})
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    let vigente = true
    obtenerCultivos().then((lista) => {
      if (!vigente) return
      setCultivos(lista)
      const actual = lista.find((c) => c.nombre === parcela?.ciclo?.cultivo)
      if (actual) setFormulario((f) => ({ ...f, idCultivo: String(actual.id_cultivo) }))
    })
    return () => {
      vigente = false
    }
  }, [parcela])

  const cultivo = cultivos.find((c) => String(c.id_cultivo) === formulario.idCultivo)

  function cambiar(campo, valor) {
    setFormulario((f) => {
      const siguiente = { ...f, [campo]: valor }
      if ((campo === 'idCultivo' || campo === 'siembra') && !cosechaManual) {
        const elegido = cultivos.find((c) => String(c.id_cultivo) === siguiente.idCultivo)
        const siembra = siguiente.siembra || (elegido ? hoyISO() : '')
        siguiente.siembra = siembra
        siguiente.cosecha = elegido?.duracion_dias && siembra ? sumarDias(siembra, elegido.duracion_dias) : ''
      }
      return siguiente
    })
    setErrores((e) => ({ ...e, [campo]: undefined }))
  }

  async function enviar(evento) {
    evento.preventDefault()
    const encontrados = validar(formulario)
    setErrores(encontrados)
    if (Object.keys(encontrados).length > 0) return

    const datos = {
      id_productor: idProductor,
      nombre: formulario.nombre.trim(),
      ubicacion: formulario.ubicacion.trim() || null,
      superficie_ha: Number(formulario.superficie),
      ciclo: formulario.idCultivo
        ? {
            id_cultivo: Number(formulario.idCultivo),
            fecha_siembra: formulario.siembra,
            fecha_cosecha_estimada: formulario.cosecha || null,
            estado: formulario.estado,
          }
        : null,
    }

    setGuardando(true)
    try {
      if (editando) await actualizarParcela(parcela.id_parcela, datos)
      else await crearParcela(datos)
      mostrar(
        editando
          ? { titulo: 'Cambios guardados', mensaje: 'La parcela se actualizó.' }
          : { titulo: 'Parcela creada', mensaje: 'Se agregó a tus parcelas.' },
      )
      alGuardar()
    } catch (error) {
      console.error(error)
      mostrar({
        tipo: 'error',
        titulo: editando ? 'No se pudieron guardar los cambios' : 'No se pudo crear la parcela',
        mensaje: 'Intenta de nuevo en un momento.',
      })
      setGuardando(false)
    }
  }

  const subtitulo = editando
    ? [parcela.nombre, parcela.ciclo?.cultivo].filter(Boolean).join(' · ')
    : 'Registra una parcela y su ciclo de siembra'
  const ayudaCultivo = cultivo
    ? `${cultivo.tipo} · ciclo aproximado de ${cultivo.duracion_dias} días`
    : 'Al elegir un cultivo se calcula la fecha estimada de cosecha.'

  return (
    <Ventana
      titulo={editando ? 'Editar parcela' : 'Nueva parcela'}
      subtitulo={subtitulo}
      icono={editando ? 'bi-pencil' : 'bi-plus-lg'}
      alCerrar={alCerrar}
    >
      <form className="ventana-cuerpo" onSubmit={enviar} noValidate>
        <div className="ventana-fila">
          <Campo etiqueta="Nombre de la parcela" error={errores.nombre}>
            <input
              data-autofocus
              value={formulario.nombre}
              onChange={(e) => cambiar('nombre', e.target.value)}
              placeholder="Ej. Parcela Norte"
              maxLength={100}
            />
          </Campo>
          <Campo etiqueta="Superficie" unidad="ha" error={errores.superficie}>
            <input
              type="number"
              inputMode="decimal"
              min="0"
              step="0.1"
              value={formulario.superficie}
              onChange={(e) => cambiar('superficie', e.target.value)}
              placeholder="0.0"
            />
          </Campo>
        </div>

        <Campo etiqueta="Ubicación" icono="bi-geo-alt" error={errores.ubicacion}>
          <input
            value={formulario.ubicacion}
            onChange={(e) => cambiar('ubicacion', e.target.value)}
            placeholder="Ej. Sector norte"
            maxLength={150}
          />
        </Campo>

        <Campo etiqueta="Cultivo" ayuda={ayudaCultivo}>
          <select
            value={formulario.idCultivo}
            onChange={(e) => cambiar('idCultivo', e.target.value)}
            className={formulario.idCultivo ? '' : 'sin-valor'}
          >
            <option value="">{parcela?.ciclo?.cultivo ?? 'Selecciona un cultivo'}</option>
            {cultivos.map((c) => (
              <option key={c.id_cultivo} value={c.id_cultivo}>
                {c.nombre}
              </option>
            ))}
          </select>
        </Campo>

        <fieldset className="ventana-caja" disabled={!formulario.idCultivo} style={{ '--columnas': 3 }}>
          <legend className="ventana-caja-titulo">
            <i className="bi bi-calendar3" aria-hidden="true" /> Ciclo de siembra
          </legend>
          <div className="ventana-caja-campos">
            <Campo etiqueta="Fecha de siembra" error={errores.siembra}>
              <input type="date" value={formulario.siembra} onChange={(e) => cambiar('siembra', e.target.value)} />
            </Campo>
            <Campo etiqueta="Cosecha estimada" error={errores.cosecha}>
              <input
                type="date"
                value={formulario.cosecha}
                onChange={(e) => {
                  setCosechaManual(Boolean(e.target.value))
                  cambiar('cosecha', e.target.value)
                }}
              />
            </Campo>
            <Campo etiqueta="Estado">
              <select value={formulario.estado} onChange={(e) => cambiar('estado', e.target.value)}>
                {Object.entries(ESTADOS_CICLO).map(([valor, etiqueta]) => (
                  <option key={valor} value={valor}>
                    {etiqueta}
                  </option>
                ))}
              </select>
            </Campo>
          </div>
        </fieldset>

        <div className="ventana-pie">
          {!editando && nombreProductor && (
            <span className="ventana-pie-nota">
              <i className="bi bi-person" aria-hidden="true" /> Productor: {nombreProductor}
            </span>
          )}
          <button type="button" className="boton boton-secundario" onClick={alCerrar}>
            Cancelar
          </button>
          <button type="submit" className="boton boton-primario" disabled={guardando}>
            <i className={`bi ${editando ? 'bi-check-lg' : 'bi-plus-lg'}`} aria-hidden="true" />
            {guardando ? 'Guardando…' : editando ? 'Guardar cambios' : 'Crear parcela'}
          </button>
        </div>
      </form>
    </Ventana>
  )
}
