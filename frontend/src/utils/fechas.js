const MS_DIA = 24 * 60 * 60 * 1000

function aFechaLocal(iso) {
  const [anio, mes, dia] = iso.slice(0, 10).split('-').map(Number)
  return new Date(anio, mes - 1, dia)
}

function aISO(fecha) {
  const anio = fecha.getFullYear()
  const mes = String(fecha.getMonth() + 1).padStart(2, '0')
  const dia = String(fecha.getDate()).padStart(2, '0')
  return `${anio}-${mes}-${dia}`
}

export function hoyISO() {
  return aISO(new Date())
}

export function sumarDias(iso, dias) {
  const fecha = aFechaLocal(iso)
  fecha.setDate(fecha.getDate() + dias)
  return aISO(fecha)
}

export function diasEntre(desdeISO, hastaISO) {
  return Math.round((aFechaLocal(hastaISO) - aFechaLocal(desdeISO)) / MS_DIA)
}

export function fechaCorta(iso) {
  if (!iso) return '—'
  return aFechaLocal(iso).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' }).replace('.', '')
}

export function fechaLarga(iso) {
  if (!iso) return '—'
  return aFechaLocal(iso)
    .toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })
    .replace('.', '')
}

export function horaActual() {
  const ahora = new Date()
  return `${String(ahora.getHours()).padStart(2, '0')}:${String(ahora.getMinutes()).padStart(2, '0')}`
}

// "HH:MM" de hoy en hora local → ISO 8601 en UTC, como lo espera el back.
export function horaDeHoyAISO(hora) {
  const [horas, minutos] = hora.split(':').map(Number)
  const fecha = new Date()
  fecha.setHours(horas, minutos, 0, 0)
  return fecha.toISOString().replace(/\.\d{3}Z$/, 'Z')
}

export function haceCuanto(fechaHora) {
  if (!fechaHora) return null
  const minutos = Math.max(0, Math.floor((Date.now() - new Date(fechaHora)) / 60000))
  if (minutos < 1) return 'hace un momento'
  if (minutos < 60) return `hace ${minutos} min`
  const horas = Math.floor(minutos / 60)
  if (horas < 24) return `hace ${horas} h`
  const dias = Math.floor(horas / 24)
  return dias === 1 ? 'hace 1 día' : `hace ${dias} días`
}

export function fechaHoraLectura(fechaHora) {
  const fecha = new Date(fechaHora)
  const hora = fecha.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit', hour12: true })
  const dia = aISO(fecha)
  const hoy = hoyISO()
  if (dia === hoy) return `Hoy · ${hora}`
  if (dia === sumarDias(hoy, -1)) return `Ayer · ${hora}`
  return `${fechaCorta(dia)} · ${hora}`
}
