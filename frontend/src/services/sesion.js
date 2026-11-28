// Pendiente: la pantalla de inicio de sesión guardará aquí la respuesta de POST /auth/login
// ({ token, usuario: { id_usuario, nombre, rol, id_productor, ... } }).

export function obtenerUsuario() {
  return null
}

export function cerrarSesion() {}

export function iniciales(nombre) {
  if (!nombre) return '?'
  return nombre
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((parte) => parte[0].toUpperCase())
    .join('')
}
