# Gestor de insumos y descartables médicos: quiebres de stock en Farmacia Central

Pipeline en Python que reconstruye día por día el stock de cada descartable médico de una clínica a partir de las exportaciones del sistema de gestión Geclisa, y detecta qué insumos se quedaron sin stock, cuánto tiempo y cuántas veces.

## El problema de negocio

Farmacia Central abastece a todos los servicios de la clínica con más de 400 descartables distintos. Cuando un insumo se agota, Geclisa no registra el faltante: el stock simplemente queda en cero y no se puede descargar. Por eso nadie sabe con datos qué insumos fallan más ni con qué frecuencia, y la reposición se decide por urgencia.

> Como jefa de Farmacia, quiero saber qué descartables médicos concentraron los quiebres de stock durante el último año, para decidir qué insumos reponer antes y dónde fijar un stock mínimo.

## Stack tecnológico

- **Python 3** con **pandas** para extraer, limpiar y reconstruir el stock diario.
- **matplotlib** para el gráfico de resultados.
- **Excel**: base de trabajo construida a partir de exportaciones de Geclisa (SQL Server), anonimizada y simplificada para el alcance del curso.
- **Git y GitHub** para versionar el código.

## Metodología

El proyecto sigue **CRISP-DM** en sprints cortos. Cada sprint recorre todo el ciclo sobre una porción más grande del problema (rebanadas delgadas), en lugar de dedicar un sprint a cada fase.

| Fase CRISP-DM | Qué se hizo en la Rebanada #1 |
|---|---|
| Comprensión del negocio | Pregunta orientada a la decisión de la jefa de Farmacia: días sin stock por descartable. |
| Comprensión de los datos | Análisis de 447.686 movimientos (oct 2025 – sep 2026) y del saldo al 01/10/2025. Se identificó qué combinación de depósitos indica un ingreso o un egreso de Farmacia Central. |
| Preparación | Se leen solo las columnas necesarias. Se filtran los descartables activos (con consumo en al menos 6 de los 12 meses). |
| Modelado | Saldo inicial más movimientos netos diarios da el stock al cierre de cada día. Se cuentan los días en cero y los episodios (cada vez que el stock llega a cero). |
| Evaluación | Validaciones automáticas: sin fechas nulas, sin cantidades ≤ 0, todos los insumos con saldo inicial y ningún saldo negativo (Geclisa no permite descargar sin stock). |
| Despliegue | Script reproducible que genera un CSV y un gráfico en `output/`. |

**Sprint 1 (esta rebanada):** top 10 de descartables con más días sin stock.
**Sprint 2:** stock mínimo sugerido para los insumos de alta rotación.
**Sprint 3:** reporte mensual automatizado.

## Hallazgos clave

- **179 de 251 descartables activos (71%)** estuvieron al menos un día con stock en cero en el último año.
- Los insumos que **más tiempo** pasan en cero son mayormente de **baja rotación**: 8 del top 10 se consumen menos de 18 unidades por mes. Por ejemplo, el gel de ultrasonido de 1 kg estuvo 226 días en cero.
- En los insumos de **alta rotación** el problema es la **frecuencia**: 11 se agotaron 5 veces o más. La aguja hipodérmica 25/8 (3.283 u/mes) llegó a cero 8 veces, y el guante de vinilo M (5.067 u/mes), 7 veces.

**Recomendación:** fijar un stock mínimo con punto de pedido para los 11 insumos de alta rotación con quiebres recurrentes, y revisar con Farmacia si los 8 de baja rotación con meses en cero siguen en uso.

## Cómo ejecutar el proyecto

1. Clonar el repositorio e instalar las dependencias:
   ```
   git clone https://github.com/Msasiuk/gestor-insumos-medicos.git
   cd gestor-insumos-medicos
   pip install -r requirements.txt
   ```
2. Guardar la base de trabajo en `data/raw/` (esta carpeta está en `.gitignore`: los datos de la institución no se publican):
   - `MEDICACION_Y_DESCARTABLE.xlsx`: movimientos de stock de 12 meses.
   - `stock_al_01102025.xlsx`: saldo por insumo al inicio del período. Si Geclisa lo exporta como `.xls`, abrirlo en Excel y guardarlo como `.xlsx`.
3. Ejecutar:
   ```
   python src/rebanada1_dias_sin_stock.py
   ```
4. Revisar los resultados en `output/`: `dias_sin_stock_descartables.csv` y `top10_dias_sin_stock.png`.

## Estructura

```
gestor-insumos-medicos/
├── data/raw/            # exportaciones de Geclisa (no versionadas)
├── output/              # resultados generados
├── src/rebanada1_dias_sin_stock.py
├── requirements.txt
└── README.md
```

## Autora

**Gabriela Maza Sasiuk**: Data Engineer Jr con foco en el sector salud.
[LinkedIn](https://www.linkedin.com/in/gabriela-maza-sasiuk) · [GitHub](https://github.com/Msasiuk)
