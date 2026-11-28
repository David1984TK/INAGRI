import { useCallback, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useCerrarAlSalir } from '../../hooks/useCerrarAlSalir'

export default function MenuParcela({ parcela, alEditar, alEliminar }) {
  const [abierto, setAbierto] = useState(false)
  const ref = useRef(null)
  const cerrar = useCallback(() => setAbierto(false), [])
  useCerrarAlSalir(ref, abierto, cerrar)

  return (
    <div className="tarjeta-menu" ref={ref}>
      <button
        type="button"
        className="boton-icono"
        aria-label={`Opciones de ${parcela.nombre}`}
        aria-haspopup="menu"
        aria-expanded={abierto}
        onClick={() => setAbierto((valor) => !valor)}
      >
        <i className="bi bi-three-dots-vertical" />
      </button>

      {abierto && (
        <div className="menu vidrio tarjeta-menu-lista" role="menu">
          <Link to={`/parcelas/${parcela.id_parcela}`} className="menu-opcion" role="menuitem">
            <i className="bi bi-arrow-up-right" aria-hidden="true" />
            Ver detalle
          </Link>
          <button
            type="button"
            className="menu-opcion"
            role="menuitem"
            onClick={() => {
              cerrar()
              alEditar(parcela)
            }}
          >
            <i className="bi bi-pencil" aria-hidden="true" />
            Editar parcela
          </button>
          <hr className="menu-separador" />
          <button
            type="button"
            className="menu-opcion menu-opcion-peligro"
            role="menuitem"
            onClick={() => {
              cerrar()
              alEliminar(parcela)
            }}
          >
            <i className="bi bi-trash3" aria-hidden="true" />
            Eliminar parcela
          </button>
        </div>
      )}
    </div>
  )
}
