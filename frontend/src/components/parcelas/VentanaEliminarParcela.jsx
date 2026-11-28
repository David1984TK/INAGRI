import { useState } from 'react'
import { useAvisos } from '../../hooks/useAvisos'
import { eliminarParcela } from '../../services/parcelas'
import Ventana from '../Ventana'

export default function VentanaEliminarParcela({ parcela, alCerrar, alEliminar }) {
  const { mostrar } = useAvisos()
  const [eliminando, setEliminando] = useState(false)
  const totalSensores = parcela.sensores?.total ?? 0

  async function confirmar() {
    setEliminando(true)
    try {
      await eliminarParcela(parcela.id_parcela)
      mostrar({ titulo: 'Parcela eliminada', mensaje: `Se eliminó ${parcela.nombre}.` })
      alEliminar()
    } catch (error) {
      console.error(error)
      mostrar({ tipo: 'error', titulo: 'No se pudo eliminar la parcela', mensaje: 'Intenta de nuevo en un momento.' })
      setEliminando(false)
    }
  }

  return (
    <Ventana titulo={`¿Eliminar ${parcela.nombre}?`} icono="bi-trash3" tono="naranja" apilada ancho={440} alCerrar={alCerrar}>
      <div className="ventana-cuerpo">
        <p className="ventana-texto">
          {parcela.ciclo
            ? 'Se eliminará la parcela junto con su ciclo de siembra. Esta acción no se puede deshacer.'
            : 'Se eliminará la parcela. Esta acción no se puede deshacer.'}
        </p>

        {totalSensores > 0 && (
          <p className="ventana-nota">
            <i className="bi bi-info-circle" aria-hidden="true" />
            <span>
              {totalSensores === 1 ? 'Su sensor quedará' : `Sus ${totalSensores} sensores quedarán`} sin parcela asignada. Las
              lecturas ya guardadas se conservan.
            </span>
          </p>
        )}

        <div className="ventana-pie">
          <button type="button" className="boton boton-secundario" onClick={alCerrar} data-autofocus>
            Cancelar
          </button>
          <button type="button" className="boton boton-peligro" onClick={confirmar} disabled={eliminando}>
            <i className="bi bi-trash3" aria-hidden="true" />
            {eliminando ? 'Eliminando…' : 'Eliminar parcela'}
          </button>
        </div>
      </div>
    </Ventana>
  )
}
