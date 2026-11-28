import { useState } from 'react'
import logo from '../assets/logo-inagri.png'
import './IniciarSesion.css'
import RecuperarPassword from './RecuperarPassword'

/* ---------- Iconos ---------- */
const IconoCorreo = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="5" width="18" height="14" rx="3" />
    <path d="m4 8 8 6 8-6" />
  </svg>
)

const IconoCandado = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="11" width="16" height="10" rx="3" />
    <path d="M8 11V8a4 4 0 0 1 8 0v3" />
  </svg>
)

const IconoOjo = ({ oculto }) => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
    <circle cx="12" cy="12" r="3" />
    {oculto && <path d="m3 3 18 18" />}
  </svg>
)

const IconoFlecha = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
)

const IconoGota = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11Z" />
  </svg>
)

const IconoTermometro = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 14.5V5a2 2 0 0 0-4 0v9.5a4 4 0 1 0 4 0Z" />
  </svg>
)

const IconoCheck = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 12a8 8 0 1 1-4.5-7.2" />
    <path d="m8.5 12 2.5 2.5L20 6" />
  </svg>
)

/* ---------- Mini gráfica ---------- */
const Grafica = ({ puntos }) => {
  const linea = `M${puntos.join(' L')}`
  const area = `${linea} L${puntos[puntos.length - 1].split(',')[0]},50 L0,50 Z`
  const [ux, uy] = puntos[puntos.length - 1].split(',')
  return (
    <svg className="grafica" viewBox="0 0 190 50" preserveAspectRatio="none">
      <path d={area} fill="rgba(22,128,60,0.15)" />
      <path d={linea} fill="none" stroke="#16803c" strokeWidth="2" strokeLinejoin="round" />
      <circle cx={ux} cy={uy} r="3.5" fill="#16803c" />
    </svg>
  )
}

/* ---------- Componente principal ---------- */
function IniciarSesion() {
  const [correo, setCorreo] = useState('')
  const [password, setPassword] = useState('')
  const [verPassword, setVerPassword] = useState(false)
  const [vista, setVista] = useState('login')

  const handleSubmit = (e) => {
    e.preventDefault()
    // Aquí conectarás con tu backend (Python), por ejemplo:
    // fetch('http://localhost:8000/login', { method: 'POST', ... })
    console.log({ correo, password })
  }

  return (
    <main className="login-page">
      {/* Tarjetas decorativas */}
      <div className="widget widget-humedad">
        <div className="widget-cabecera">
          <span className="widget-icono"><IconoGota /></span>
          <span>Humedad</span>
        </div>
        <p className="widget-valor">42<small>%</small></p>
        <Grafica puntos={['0,40','20,28','45,26','70,27','90,32','110,18','140,16','165,17','188,22']} />
      </div>

      <div className="widget widget-temperatura">
        <div className="widget-cabecera">
          <span className="widget-icono"><IconoTermometro /></span>
          <span>Temperatura</span>
        </div>
        <p className="widget-valor">27<small> °C</small></p>
        <Grafica puntos={['0,36','20,30','50,32','80,30','100,22','130,22','160,24','188,18']} />
      </div>

      <div className="widget widget-sensores">
        <div className="sensores-fila">
          <span>Sensores en línea</span>
          <strong>9 de 10</strong>
        </div>
        <div className="barras">
          {Array.from({ length: 10 }).map((_, i) => (
            <span key={i} className={i < 9 ? 'activa' : ''} />
          ))}
        </div>
      </div>

      <div className="widget widget-parcela">
        <span className="parcela-check"><IconoCheck /></span>
        <div>
          <strong>Parcela Norte</strong>
          <p>Óptima · hace 2 min</p>
        </div>
      </div>

      {vista === 'recuperar' ? (
        <RecuperarPassword onVolver={() => setVista('login')} />
      ) : (
      <form className="login-card" onSubmit={handleSubmit}>
        <img src={logo} alt="INAGRI Monitoreo Agrícola" className="login-logo" />

        <h1>Bienvenido</h1>
        <p className="subtitulo">Entra a tu cuenta de INAGRI.</p>

        <label htmlFor="correo">Correo</label>
        <div className="campo">
          <span className="campo-icono"><IconoCorreo /></span>
          <input
            id="correo"
            type="email"
            placeholder="correo@ejemplo.com"
            value={correo}
            onChange={(e) => setCorreo(e.target.value)}
            required
          />
        </div>

        <label htmlFor="password">Contraseña</label>
        <div className="campo">
          <span className="campo-icono"><IconoCandado /></span>
          <input
            id="password"
            type={verPassword ? 'text' : 'password'}
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button
            type="button"
            className="ojo"
            onClick={() => setVerPassword(!verPassword)}
            aria-label={verPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
          >
            <IconoOjo oculto={!verPassword} />
          </button>
        </div>

        <button type="button" className="olvido" onClick={() => setVista('recuperar')}>
          ¿Olvidaste tu contraseña?
        </button>

        <button type="submit" className="btn-login">
          Iniciar sesión <IconoFlecha />
        </button>
      </form>
      )}
    </main>
  )
}

export default IniciarSesion