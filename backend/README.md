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

Hace falta Docker Desktop. En `.env` pon una contraseña en `DB_PASSWORD` y otra en `DB_ADMIN_PASSWORD`.

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

Para apagar las bases: `docker compose down`. Para borrar los datos de Postgres y volver a correr los scripts SQL: `docker compose down -v`.

Importante: mientras `DYNAMODB_ENDPOINT_URL` tenga valor, los scripts usan DynamoDB Local. Para cargar datos en la tabla real de AWS, deja esa variable vacía.

## Endpoints

| Método | Ruta | Lambda | Base |
|---|---|---|---|
| POST | `/lecturas` | `lecturas/crearLectura` | DynamoDB |
| GET | `/sensores/{id}/lecturas?horas=24` | `lecturas/obtenerLecturas` | DynamoDB |
| PUT | `/sensores/{id}/lecturas/{fechaHora}` | `lecturas/actualizarLectura` | DynamoDB |
| DELETE | `/sensores/{id}/lecturas/{fechaHora}` | `lecturas/eliminarLectura` | DynamoDB |
| GET | `/productores` y `/productores/{id}` | `catalogo/obtenerProductores` | RDS |
| POST | `/productores` | `catalogo/crearProductor` | RDS |
| PUT | `/productores/{id}` | `catalogo/actualizarProductor` | RDS |
| DELETE | `/productores/{id}` | `catalogo/eliminarProductor` | RDS |
| GET | `/productores/{id}/parcelas` | `catalogo/obtenerParcelasProductor` | RDS |
| GET | `/parcelas` y `/parcelas/{id}` | `catalogo/obtenerParcelas` | RDS |
| POST | `/parcelas` | `catalogo/crearParcela` | RDS |
| PUT | `/parcelas/{id}` | `catalogo/actualizarParcela` | RDS |
| DELETE | `/parcelas/{id}` | `catalogo/eliminarParcela` | RDS |

## Base relacional (RDS)

- `sql/01_tablas.sql`: productores, parcelas, sensores, cultivos, ciclos_siembra y usuarios, con llaves foráneas.
- `sql/02_usuario.sql`: usuario `inagri_app`, que solo puede SELECT, INSERT, UPDATE y DELETE. La contraseña se pasa con `-v clave_app='...'`.
- `sql/03_datos_demo.sql`: 5 productores, 10 parcelas, 10 sensores (los mismos id que usa `cargarLecturas.py`), cultivos y ciclos.

En RDS se corren igual, con el usuario administrador:

```bash
psql -h <endpoint-rds> -U <admin> -d inagri -f sql/01_tablas.sql
psql -h <endpoint-rds> -U <admin> -d inagri -v clave_app='<contraseña>' -f sql/02_usuario.sql
psql -h <endpoint-rds> -U <admin> -d inagri -f sql/03_datos_demo.sql
```

## Notas

- No guardar credenciales en el código ni en el repositorio. Las de RDS van en Secrets Manager.
- Versión de Python de las Lambdas: por confirmar contra los runtimes que ofrece AWS.
