# INAGRI: Monitoreo agrícola con sensores (Proyecto Integrador, AWS)

Este archivo resume el contexto del proyecto para trabajar en conjunto con Claude Code.
Marcas usadas: **[CONFIRMADO]** viene de los lineamientos de la materia; **[PROPUESTA]** es una decisión sugerida que el equipo aún debe confirmar; **[PENDIENTE]** es algo que no sabemos.

## 1. Qué es

- Materia: Bases de datos en la nube, 7.º cuatrimestre, UTEZ. Proyecto Integrador "Sistema Cloud Híbrido en AWS". [CONFIRMADO]
- Tema asignado: **5. Monitoreo agrícola con sensores**. Contexto: una cooperativa mide humedad y temperatura en sus parcelas. [CONFIRMADO]
- Nombre del proyecto: **INAGRI**. [CONFIRMADO por el usuario]
- Equipo: 5 a 6 integrantes. [CONFIRMADO]
- Integrantes y nombre del equipo: [PENDIENTE]

## 2. Lineamientos generales (aplican a los 11 proyectos) [CONFIRMADO]

- Arquitectura: frontend que consume servicios mediante **API Gateway + AWS Lambda**.
- Bases de datos: **dos bases de datos en AWS**. Hay que identificar y justificar si cada una es relacional o no relacional y qué servicio AWS usa (RDS, Aurora, DynamoDB, etc.).
- Operaciones mínimas: crear, leer, actualizar y eliminar en ambas bases.
- Seguridad mínima: credenciales en **Secrets Manager**, **roles IAM de mínimo privilegio** para cada Lambda y **usuario de BD con privilegios limitados**.
- Entregables finales: diagrama de arquitectura, justificación escrita de la elección de cada base, demostración funcional (GET y POST) y reporte digital.

## 3. Datos del tema 5 [CONFIRMADO]

- **Dato A:** productores, parcelas, cultivos, ciclos de siembra y usuarios del sistema.
- **Dato B:** lecturas de sensores, con miles de registros por día y consultas casi siempre por sensor y rango de fechas.
- Operaciones mínimas del tema: registrar una lectura, consultar las últimas 24 horas de un sensor, listar las parcelas de un productor.
- Los datos de la demostración serán **inventados** (simulados). [CONFIRMADO por el usuario]

## 4. Primera entrega: planteamiento (Classroom, "Integradoras") [CONFIRMADO]

Se entrega un documento, una página de Notion o una presentación, **uno por equipo**, con:

1. Nombre del proyecto e integrantes
2. Problema que resuelve y tipos de usuario
3. Datos que manejará el sistema, divididos en dos grupos
4. Base de datos de cada grupo: servicio AWS, si es relacional o no relacional, y justificación
5. Campos principales de cada base (tablas o colecciones, con llaves)
6. Diagrama de arquitectura: frontend, API Gateway, Lambda, las dos bases y dónde se guardan las credenciales
7. Al menos 4 endpoints de la API (método, ruta y base que consulta)
8. Boceto del prototipo: mínimo 3 pantallas
9. Riesgos principales y siguientes pasos

El texto de la sección de datos ya está redactado en dos grupos: administrativo y monitoreo con sensores.

## 5. Decisiones técnicas propuestas [PROPUESTA]

Estas decisiones las propuso Claude y no vienen de los lineamientos. Confirmarlas con el equipo y el profesor antes de construir.

| Grupo de datos | Tipo | Servicio AWS | Por qué |
|---|---|---|---|
| Dato A (administrativos) | Relacional | Amazon RDS for PostgreSQL (o Aurora) | Relaciones claras (productor → parcelas → ciclos → cultivo), llaves foráneas, JOINs |
| Dato B (lecturas) | No relacional | Amazon DynamoDB | Alto volumen de escrituras; consulta casi siempre por sensor y rango de fechas; sin JOINs |

**DynamoDB, tabla de lecturas:** llave de partición `sensor_id`, llave de ordenamiento `timestamp`. Atributos: `humedad` (%), `temperatura` (°C). "Últimas 24 horas de un sensor" es un solo Query por rango sobre la llave de ordenamiento. TTL opcional para borrar lecturas viejas. Modo on-demand.

**RDS, tablas (campos propuestos):**
- `productores`: id, nombre, contacto, estatus
- `parcelas`: id, ubicación, superficie, productor_id (FK)
- `cultivos`: id, nombre, tipo, duración aproximada del ciclo
- `ciclos_siembra`: id, parcela_id (FK), cultivo_id (FK), fecha_siembra, fecha_cosecha_estimada, estado
- `usuarios`: id, nombre_usuario, rol, hash de contraseña, fecha_alta
- La relación entre sensores y parcelas (`sensor_id` ↔ `parcela_id`) puede vivir en una tabla `sensores` en RDS. Decidirlo con el equipo.

**Arquitectura:** Frontend (web) → API Gateway → Lambda → RDS y DynamoDB. Secrets Manager guarda las credenciales de RDS. Un rol IAM por cada Lambda, con permisos mínimos (la Lambda de lecturas solo accede a la tabla de DynamoDB; la de parcelas y productores solo a RDS). Usuario de BD en RDS sin permisos de administrador (solo SELECT, INSERT, UPDATE, DELETE).

**Endpoints propuestos:**
- `POST /lecturas` → registra una lectura (DynamoDB)
- `GET /sensores/{id}/lecturas?horas=24` → últimas 24 horas (DynamoDB)
- `GET /productores/{id}/parcelas` → parcelas de un productor (RDS)
- `PUT /lecturas/...` y `DELETE /lecturas/...` → actualizar y eliminar lecturas (DynamoDB)
- CRUD de productores y parcelas (RDS), por ejemplo `POST /productores`, `PUT /productores/{id}`, `DELETE /productores/{id}`

**Punto de cuidado:** si RDS va dentro de una VPC, la Lambda que lo usa debe estar en la misma VPC, y entonces necesita VPC endpoints o un NAT Gateway (con costo) para llegar a Secrets Manager y a DynamoDB. Apagar o eliminar RDS y el NAT al terminar la demostración. Costos y capa gratuita: verificar las condiciones vigentes en la página de AWS. [PENDIENTE confirmar presupuesto y límites de la cuenta]

## 6. Qué se desarrolla

1. Script SQL con las tablas y llaves foráneas, y usuario de BD con privilegios limitados.
2. Tabla de DynamoDB (con TTL opcional).
3. Lambdas para RDS (CRUD de productores y parcelas) y para DynamoDB (registrar lectura, consultar últimas 24 horas, actualizar y eliminar).
4. API Gateway con los endpoints.
5. Frontend sencillo (HTML y JavaScript): formulario para registrar lecturas, tabla de las últimas 24 horas y lista de parcelas por productor.
6. Script de datos inventados para cargar ambas bases (por ejemplo, unos 5 productores, 10 parcelas, algunos cultivos y ciclos, y unos miles de lecturas con fechas recientes para que la consulta de 24 horas devuelva resultados en la demostración).
7. Diagrama de arquitectura, justificación escrita de cada base y reporte.

## 7. Reparto sugerido (5 a 6 integrantes) [PROPUESTA]

1. Base relacional (RDS, tablas, usuario limitado)
2. DynamoDB y sus Lambdas
3. Lambdas de RDS, Secrets Manager e IAM
4. API Gateway y pruebas de endpoints
5. Frontend
6. Diagrama, justificación escrita y reporte (si son seis)

## 8. Identidad visual de INAGRI

- Logo: hexágono con un brote y una señal de sensor. Nombre en mayúsculas con la leyenda "MONITOREO AGRÍCOLA".
- Paleta: verde bosque `#14532D`, verde campo `#16803C`, verde brote `#3FAA5E`, verde claro `#9BE3B4`, verde noche `#0F3D22`, verde niebla `#F3FAF4`.
- Tipografía: Manrope (ExtraBold 800 para títulos, Medium 500 para texto).
- Usar estos colores y esta tipografía en el frontend y en las pantallas del boceto.

## 9. Pendientes

- Confirmar con el profesor: lenguaje de las Lambdas, si exige un frontend específico, formato del reporte y límites del presupuesto de AWS.
- Confirmar con el equipo: RDS PostgreSQL vs. Aurora, nombres de los campos y si habrá tabla `sensores`.
- Definir integrantes, nombre del equipo y región de AWS.
- No hay código ni infraestructura creados todavía.

## 10. Cómo trabajar

- Idioma de la comunicación y de los comentarios: español de México.
- No inventar datos, URLs ni referencias; si algo no se sabe, decirlo.
- No guardar credenciales ni claves en el código ni en el repositorio: usar Secrets Manager.
- Todo el código que se entregue debe ser archivos listos para usar.
