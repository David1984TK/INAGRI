# INAGRI: backend

Lambdas en Python para la API de INAGRI.

## Estructura

```
backend/
├── lambdas/
│   ├── lecturas/     # Lambdas de DynamoDB (lecturas de sensores)
│   └── catalogo/     # Lambdas de RDS (productores, parcelas, cultivos, ciclos)
├── common/           # código compartido entre Lambdas
├── sql/              # scripts SQL de RDS (tablas, llaves, usuario limitado)
├── scripts/          # carga de datos inventados
└── tests/
```

## Preparar el entorno

Desde la carpeta `backend/`:

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements-dev.txt
```

```bash
cp .env.example .env
```

Después llena los valores de `.env`. Para salir del entorno virtual: `deactivate`.

## Pruebas

```bash
pytest
```

## Correr todo en local (sin gastar en AWS)

Hace falta Docker Desktop. En `.env` pon una contraseña en `DB_PASSWORD`, otra en `DB_ADMIN_PASSWORD` y una llave de al menos 32 caracteres en `TOKEN_SECRET`.

1. Levantar Postgres (en lugar de RDS) y DynamoDB Local. La primera vez se crean las tablas, el usuario limitado y los datos de demostración (`sql/`).

   ```bash
   docker compose up -d
   ```

2. Crear la tabla de lecturas en DynamoDB Local y cargarle las lecturas inventadas. DynamoDB Local guarda todo en memoria: repetir este paso cada vez que se reinicie el contenedor.

   ```bash
   python scripts/crearTablaLocal.py
   python scripts/cargarLecturas.py --cargar
   ```

3. Levantar la API local, que llama a las Lambdas igual que API Gateway:

   ```bash
   python scripts/servidorLocal.py
   ```

   Queda en `http://localhost:3001`. Ejemplos: `GET /productores/1/parcelas`, `GET /sensores/3/lecturas?horas=24`.

4. En otra terminal (también con `.venv` activo), encender el simulador de sensores. Manda una lectura por sensor cada 5 minutos a `POST /lecturas`, como lo harían los sensores reales. Sin él, todos los sensores salen "sin señal", porque `cargarLecturas.py` solo deja lecturas de cada hora.

   ```bash
   python scripts/simularSensores.py
   ```

   El sensor 4 no manda lecturas a propósito, para que la Parcela Sur muestre un sensor sin señal como en los bocetos. Con `--todos` se incluye.

Para apagar las bases: `docker compose down`. Para borrar los datos de Postgres y volver a correr los scripts SQL: `docker compose down -v`.

Importante: mientras `DYNAMODB_ENDPOINT_URL` tenga valor, los scripts usan DynamoDB Local. Para cargar datos en la tabla real de AWS, deja esa variable vacía.

## Endpoints

| Método | Ruta | Lambda | Base |
|---|---|---|---|
| POST | `/auth/login` | `auth/iniciarSesion` | RDS |
| PUT | `/auth/contrasena` | `auth/cambiarContrasena` | RDS |
| POST | `/lecturas` | `lecturas/crearLectura` | DynamoDB |
| GET | `/sensores/{id}/lecturas?horas=24` | `lecturas/obtenerLecturas` | DynamoDB |
| PUT | `/sensores/{id}/lecturas/{fechaHora}` | `lecturas/actualizarLectura` | DynamoDB |
| DELETE | `/sensores/{id}/lecturas/{fechaHora}` | `lecturas/eliminarLectura` | DynamoDB |
| GET | `/productores` y `/productores/{id}` | `catalogo/obtenerProductores` | RDS |
| POST | `/productores` (también crea su cuenta) | `catalogo/crearProductor` | RDS |
| PUT | `/productores/{id}` | `catalogo/actualizarProductor` | RDS |
| DELETE | `/productores/{id}` | `catalogo/eliminarProductor` | RDS |
| GET | `/productores/{id}/parcelas` (Mis parcelas) | `catalogo/obtenerParcelasProductor` | RDS + DynamoDB |
| GET | `/parcelas` y `/parcelas/{id}` | `catalogo/obtenerParcelas` | RDS |
| GET | `/parcelas/{id}/sensores` (Detalle de parcela) | `catalogo/obtenerSensoresParcela` | RDS + DynamoDB |
| POST | `/parcelas` | `catalogo/crearParcela` | RDS |
| PUT | `/parcelas/{id}` | `catalogo/actualizarParcela` | RDS |
| DELETE | `/parcelas/{id}` | `catalogo/eliminarParcela` | RDS |

## Mis parcelas y Detalle de parcela

Estas dos Lambdas juntan las dos bases: de RDS sacan las parcelas, el ciclo en curso, el rango ideal del cultivo y los sensores, y de DynamoDB la última lectura de cada sensor (una consulta con `Limit=1` por sensor). La lógica está en `common/monitoreo.py`:

- Un sensor está `en_linea` si mandó una lectura en los últimos 15 minutos (`MINUTOS_SIN_SENAL`), `sin_senal` si no, e `inactivo` si se dio de baja.
- La parcela usa el promedio de la última lectura de sus sensores en línea.
- La parcela queda en `requiere_atencion` si la humedad o la temperatura salen del rango ideal del cultivo, o si tiene sensores sin señal. Si no hay ningún sensor en línea queda en `sin_datos`, y si todo está bien en `optima`.
- En AWS, el rol de estas dos Lambdas necesita permiso `dynamodb:Query` sobre la tabla de lecturas, además de leer el secreto de RDS.

## Inicio de sesión

- `POST /auth/login` con `{"correo", "contrasena"}` regresa `token` y `usuario` (con `rol`, `id_productor` y `debe_cambiar_contrasena`).
- El frontend guarda el token y lo manda en cada petición: `Authorization: Bearer <token>`. Dura 8 horas.
- Si `debe_cambiar_contrasena` es `true`, el frontend debe pedir la contraseña nueva con `PUT /auth/contrasena`.
- Las contraseñas se guardan cifradas con scrypt (`common/seguridad.py`). La llave de los tokens va en `TOKEN_SECRET` (local) o en Secrets Manager (`TOKEN_SECRET_NAME`, en AWS).
- Al dar de alta un productor (`POST /productores`) se crea su cuenta con una contraseña temporal, que se regresa una sola vez en `acceso.contrasena_temporal`.

## Base relacional (RDS)

- `sql/01_tablas.sql`: productores, parcelas, sensores, cultivos, ciclos_siembra y usuarios, con llaves foráneas.
- `sql/02_usuario.sql`: usuario `inagri_app`, que solo puede SELECT, INSERT, UPDATE y DELETE. La contraseña se pasa con `-v clave_app='...'`.
- `sql/03_datos_demo.sql`: 5 productores, 10 parcelas, 10 sensores (los mismos id que usa `cargarLecturas.py`), cultivos con su rango ideal, ciclos y cuentas de acceso.

Cuentas de demostración (contraseña de todas: `Inagri2026`):

| Correo | Rol | Nota |
|---|---|---|
| `admin@inagri.com` | administrador | |
| `juan.perez@ejemplo.com` | productor | Parcela Sur y Parcela Río |
| `maria.lopez@ejemplo.com` | productor | Parcela Norte |
| `rosa.hernandez@ejemplo.com` | productor | debe cambiar su contraseña al entrar |
| `luis.garcia@ejemplo.com` | productor | dado de baja, no puede entrar |

En RDS se corren igual, con el usuario administrador:

```bash
psql -h <endpoint-rds> -U <admin> -d inagri -f sql/01_tablas.sql
psql -h <endpoint-rds> -U <admin> -d inagri -v clave_app='<contraseña>' -f sql/02_usuario.sql
psql -h <endpoint-rds> -U <admin> -d inagri -f sql/03_datos_demo.sql
```

## Notas

- No guardar credenciales en el código ni en el repositorio. Las de RDS van en Secrets Manager.
- Versión de Python de las Lambdas: por confirmar contra los runtimes que ofrece AWS.
