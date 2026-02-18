# Sistema de Recupero de Subsidios (Streamlit)

Este proyecto mantiene **Streamlit** como capa de interfaz (`app.py`) y separa la lógica de negocio en módulos reutilizables para facilitar una futura migración a FastAPI.

## Estructura

- `app.py`: UI (carga de archivo, filtros, render de tabla y detalle).
- `src/io_excel.py`: carga de Excel y validación de columnas requeridas.
- `src/casos.py`: motor de casos, clasificación y consecutividad.
- `src/alertas.py`: reglas de alertas Nivel 1 (vencimiento) y Nivel 2 (estancamiento).
- `src/kpis.py`: cálculo de KPIs del tablero.

## Reglas funcionales incluidas

- Casos con estado de cierre (`cerrado`, `finalizado`, `pagado`) se clasifican como `Cierre`.
- Nivel 2 - Estancamiento: caso abierto con `dias_sin_mov >= 15`.
- Nivel 1 - Vencimiento: caso abierto con `dias_sin_mov >= 30`.
- El Nivel 1 tiene prioridad visual sobre Nivel 2 cuando ambas condiciones se cumplen.

## Requisitos

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run app.py
```

## Formato esperado del Excel

Columnas requeridas (se normalizan en minúscula y con `_`):

- `id`
- `fecha_registro`
- `fecha_ultimo_mov`
- `estado`
- `subestado`
- `agente`
- `monto`
