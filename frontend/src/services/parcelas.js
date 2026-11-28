// Pendiente de conectar con la API (lo hará quien integre el back).
// Cada función dice qué endpoint le toca y qué forma de datos espera la pantalla.
// Mientras tanto, las consultas regresan vacío y las escrituras fallan con un aviso.

const PENDIENTE = 'Pendiente de conectar con el back.'

function pendiente(endpoint) {
  return Promise.reject(new Error(`${PENDIENTE} (${endpoint})`))
}

// GET /productores/{idProductor}/parcelas
// Regresa { productor, resumen, total, parcelas }. Cada parcela trae lo que arma
// common/monitoreo.py del back: id_parcela, nombre, ubicacion, superficie_ha, ciclo, sensores,
// ultima_lectura, estado ('optima' | 'requiere_atencion' | 'sin_datos') y alertas.
// Para las minigráficas, agregar a cada parcela `tendencia: { humedad: [], temperatura: [] }`
// con las lecturas de 24 h (GET /sensores/{id}/lecturas?horas=24) de sus sensores.
export async function obtenerMisParcelas() {
  return { productor: null, resumen: null, total: 0, parcelas: [] }
}

// GET /parcelas/{idParcela}/sensores
// Regresa { parcela, sensores } (pantalla Detalle de parcela). null = sin datos.
export async function obtenerDetalleParcela() {
  return null
}

// GET /sensores/{idSensor}/lecturas?horas=24
// Regresa { lecturas: [{ fecha_hora, humedad, temperatura }] }, la más reciente primero.
export async function obtenerLecturasSensor() {
  return { lecturas: [] }
}

// Sensores activos del productor, cada uno con { id_sensor, descripcion, estado, id_parcela, parcela }.
// Se puede armar con GET /parcelas/{id}/sensores de cada parcela.
export async function obtenerSensoresProductor() {
  return []
}

// Catálogo de cultivos: { id_cultivo, nombre, tipo, duracion_dias }. El back aún no tiene endpoint.
export async function obtenerCultivos() {
  return []
}

// POST /parcelas
// Recibe { id_productor, nombre, ubicacion, superficie_ha, ciclo }. Ojo: el back solo acepta
// id_productor, nombre, ubicacion y superficie_ha; `ciclo` ({ id_cultivo, fecha_siembra,
// fecha_cosecha_estimada, estado }) necesita su propio endpoint, que aún no existe.
export function crearParcela() {
  return pendiente('POST /parcelas')
}

// PUT /parcelas/{idParcela}  — mismos campos que crearParcela.
export function actualizarParcela() {
  return pendiente('PUT /parcelas/{id}')
}

// DELETE /parcelas/{idParcela}  — el back responde 409 si la parcela tiene sensores o ciclos.
export function eliminarParcela() {
  return pendiente('DELETE /parcelas/{id}')
}

// POST /lecturas
// Recibe { id_sensor, id_parcela, humedad, hora_humedad, temperatura, hora_temperatura }
// (horas en ISO 8601). Ojo: el back guarda una sola fecha_hora por lectura con humedad y
// temperatura juntas, y espera origen: 'manual'.
export function registrarLectura() {
  return pendiente('POST /lecturas')
}
