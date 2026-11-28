export const ESTADOS_PARCELA = {
  optima: { etiqueta: 'Óptima', tono: 'verde' },
  requiere_atencion: { etiqueta: 'Atención', tono: 'naranja' },
  sin_datos: { etiqueta: 'Sin datos', tono: 'gris' },
}

export const ESTADOS_CICLO = {
  planeado: 'Planeado',
  en_curso: 'En curso',
  cosechado: 'Cosechado',
  cancelado: 'Cancelado',
}

const MENSAJES_CORTOS = {
  'humedad-bajo': ['Humedad baja: conviene regar', 'humedad baja'],
  'humedad-alto': ['Humedad alta: revisar riego', 'humedad alta'],
  'temperatura-bajo': ['Temperatura baja: revisar', 'temperatura baja'],
  'temperatura-alto': ['Temperatura alta: revisar', 'temperatura alta'],
}

export function alertaPrincipal(alertas = []) {
  return alertas.find((a) => a.tipo !== 'sensor') ?? alertas[0] ?? null
}

export function mensajeAlerta(alerta) {
  const corto = MENSAJES_CORTOS[`${alerta.tipo}-${alerta.nivel}`]
  return corto ? corto[0] : alerta.mensaje.replace(/\.$/, '')
}

export function motivoAlerta(alerta) {
  const corto = MENSAJES_CORTOS[`${alerta.tipo}-${alerta.nivel}`]
  return corto ? corto[1] : alerta.mensaje.replace(/\.$/, '').toLowerCase()
}

export function tieneAlerta(alertas = [], tipo) {
  return alertas.some((a) => a.tipo === tipo)
}

export function superficie(valor) {
  return `${Number(valor).toFixed(1)} ha`
}

export function redondear(valor) {
  return valor === null || valor === undefined ? '—' : Math.round(Number(valor))
}
