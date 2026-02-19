# Sistema de Recupero de Subsidios (Streamlit)

Este proyecto usa **Streamlit** como interfaz (`app.py`) y mantiene la lógica de negocio en módulos (`src/*`) para facilitar mantenimiento y evolución.

## Estructura

- `app.py`: UI de gestión, filtros, tabla principal, detalle opcional y descarga Excel.
- `src/io_excel.py`: lectura de Excel, validación de columnas mínimas y preparación de campos internos.
- `src/casos.py`: motor de casos, clasificación y consecutividad.
- `src/alertas.py`: reglas de alertas Nivel 1 (vencimiento) y Nivel 2 (estancamiento).
- `src/kpis.py`: cálculo de KPIs del tablero.

## Requisitos

```bash
pip install -r requirements.txt
```

## Cómo correr

```bash
streamlit run app.py
```

## Formato del Excel

La aplicación trabaja con cabeceras en español (respetando tildes, espacios y paréntesis), por ejemplo:

- `APELLIDOS Y NOMBRES`
- `STATUS PLATAFORMA VIVA`
- `DETALLE DE RPTA ESSALUD OBSERVACIÓN`
- `FECHA DE COBRO (CONTABILIDAD)`

### Columnas mínimas requeridas (core)

Para poder analizar, el archivo debe incluir al menos:

- `DNI`
- `APELLIDOS Y NOMBRES`
- `FECHA DE INICIO`
- `FECHA FIN`
- `VENCIMIENTO DE EXPEDIENTE`
- `STATUS PLATAFORMA VIVA`

Si faltan otras columnas de gestión no-core, la app **no bloquea** la carga: muestra un aviso de columnas opcionales faltantes.

## Descarga de reporte

El botón **Descargar reporte Excel (.xlsx)** genera un archivo con 2 hojas:

1. `GESTION`: columnas visibles en la tabla principal y con filtros aplicados.
2. `DETALLE`: todas las columnas originales del Excel para los registros filtrados.
