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

## Notas

- No guardar credenciales en el código ni en el repositorio. Las de RDS van en Secrets Manager.
- Versión de Python de las Lambdas: por confirmar contra los runtimes que ofrece AWS.
