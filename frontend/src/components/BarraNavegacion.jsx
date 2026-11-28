import { useCallback, useRef, useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import logo from '../assets/logo-inagri.svg'
import { useCerrarAlSalir } from '../hooks/useCerrarAlSalir'
import { cerrarSesion, iniciales, obtenerUsuario } from '../services/sesion'
import './BarraNavegacion.css'

const ROLES = { productor: 'Productor', administrador: 'Administrador' }

export default function BarraNavegacion() {
  const usuario = obtenerUsuario()
  const nombre = usuario?.nombre ?? 'Usuario'
  const [menuAbierto, setMenuAbierto] = useState(false)
  const refMenu = useRef(null)
  const cerrarMenu = useCallback(() => setMenuAbierto(false), [])
  useCerrarAlSalir(refMenu, menuAbierto, cerrarMenu)

  return (
    <header className="barra">
      <nav className="barra-pildora vidrio" aria-label="Principal">
        <Link to="/parcelas" className="barra-logo">
          <img src={logo} alt="INAGRI Monitoreo agrícola" />
        </Link>

        <div className="barra-pestanas">
          <NavLink to="/parcelas" className="barra-pestana">
            <i className="bi bi-grid" aria-hidden="true" />
            Mis parcelas
          </NavLink>
          <NavLink to="/lecturas" className="barra-pestana">
            <i className="bi bi-activity" aria-hidden="true" />
            Lecturas
          </NavLink>
        </div>

        <div className="barra-usuario" ref={refMenu}>
          <button
            type="button"
            className="barra-chip"
            aria-haspopup="menu"
            aria-expanded={menuAbierto}
            onClick={() => setMenuAbierto((abierto) => !abierto)}
          >
            <span className="barra-avatar" aria-hidden="true">
              {iniciales(usuario?.nombre)}
            </span>
            <span className="barra-nombre">{nombre}</span>
            <i className={`bi ${menuAbierto ? 'bi-chevron-up' : 'bi-chevron-down'}`} aria-hidden="true" />
          </button>

          {menuAbierto && (
            <div className="menu vidrio barra-menu" role="menu">
              <div className="barra-menu-cabecera">
                <strong>{nombre}</strong>
                <span>{ROLES[usuario?.rol] ?? 'Sin sesión'}</span>
              </div>
              <hr className="menu-separador" />
              <Link to="/perfil" className="menu-opcion" role="menuitem" onClick={cerrarMenu}>
                <i className="bi bi-person" aria-hidden="true" />
                Mi perfil
              </Link>
              <button
                type="button"
                className="menu-opcion"
                role="menuitem"
                onClick={() => {
                  cerrarSesion()
                  cerrarMenu()
                }}
              >
                <i className="bi bi-box-arrow-right" aria-hidden="true" />
                Cerrar sesión
              </button>
            </div>
          )}
        </div>
      </nav>
    </header>
  )
}
