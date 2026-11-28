import { useState } from 'react'
import logo from '../assets/logo-inagri.png'

const IconoCorreo = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="5" width="18" height="14" rx="3" />
    <path d="m4 8 8 6 8-6" />
  </svg>
)

const IconoFlecha = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
)

const IconoVolver = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 12H5M11 18l-6-6 6-6" />
  </svg>
)

const IconoCheck = () => (
  <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
    <path d="m5 12.5 4.5 4.5L19 7.5" />
  </svg>
)

function RecuperarPassword({ onVolver }) {
  const [correo, setCorreo] = useState('')
  const [enviado, setEnviado] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    // Aquí conectarás con tu backend, por ejemplo:
    // fetch('http://localhost:8000/recuperar-password', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ correo }),
    // })
    console.log('Recuperar contraseña para:', correo)
    setEnviado(true)
  }

  return (
    <form className="login-card" onSubmit={handleSubmit}>
      <img src={logo} alt="INAGRI Monitoreo Agrícola" className="login-logo" />

      {!enviado ? (
        <>
          <h1>¿Olvidaste tu contraseña?</h1>
          <p className="subtitulo">
            Escribe tu correo y te enviaremos un enlace para crear una nueva.
          </p>

          <label htmlFor="correo-recuperar">Correo</label>
          <div className="campo">
            <span className="campo-icono"><IconoCorreo /></span>
            <input
              id="correo-recuperar"
              type="email"
              placeholder="correo@ejemplo.com"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-login">
            Enviar enlace <IconoFlecha />
          </button>
        </>
      ) : (
        <div className="exito">
          <span className="exito-icono"><IconoCheck /></span>
          <h1>Revisa tu correo</h1>
          <p className="subtitulo">
            Si <strong>{correo}</strong> está registrado, recibirás un enlace
            para restablecer tu contraseña en unos minutos.
          </p>
          <button
            type="button"
            className="reenviar"
            onClick={() => setEnviado(false)}
          >
            ¿No te llegó? Intentar de nuevo
          </button>
        </div>
      )}

      <button type="button" className="volver" onClick={onVolver}>
        <IconoVolver /> Volver a iniciar sesión
      </button>
    </form>
  )
}

export default RecuperarPassword