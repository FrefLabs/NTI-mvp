# NTI MVP — Informe de avance (Fase 3)

**Fecha:** 2026-07-02.
**Alcance de esta fase:** MVP del Resultado R2 de la MML (análisis de
activos con sugerencia automática), reescrito desde cero — sin reutilizar
código ni arquitectura de los repositorios NTI anteriores.

## Funcionalidades implementadas vs. acciones R2 de la MML

| Acción MML | Estado | Implementación |
| --- | --- | --- |
| **A2.1** Integración con el proveedor de datos financieros externos | ✅ Completa | Capa `backend/app/market.py` sobre yfinance (Yahoo Finance): cotización, histórico OHLCV y fundamentals en vivo, con caché SQLite (TTL 5 min) y errores limpios ante fallos del proveedor (RNF-14). |
| **A2.2** Módulo de consulta y visualización de activos | ✅ Completa (acotada) | Selección fija entre **KO** y **NVDA** (sin búsqueda libre, por diseño del MVP); gráfico histórico interactivo con 5 rangos temporales. |
| **A2.3** Panel de visualización de datos relevantes del mercado | ✅ Completa | Precio actual en tipografía mono de gran tamaño, variación diaria, máximo/mínimo del día, volumen, cierre anterior; endpoint de fundamentals (RF-20). |
| **A2.4** Módulo de redes neuronales con visualización automática al consultar un activo | ⚠️ Completa con ajuste deliberado | La sugerencia comprar/mantener/vender + nivel de confianza se muestra automáticamente al consultar cada activo. El motor es un **modelo placeholder** (heurística SMA+RSI), no una red neuronal entrenada — ver ajuste n°2. |
| **A2.5** Sistema de términos y condiciones previo al uso | ⚠️ Parcial | El descargo del ERS §6.1 es permanente y visible en la UI. El flujo de aceptación previa requiere registro/sesión, que está fuera del alcance del MVP. |

Requerimientos del ERS cubiertos: RF-04, RF-06, RF-08, RF-15, RF-20,
RF-21, RF-22, RF-24. Verificación en `docs/test-log.md`.

## Los tres ajustes deliberados de alcance

Son **decisiones documentadas**, no carencias:

1. **SQLite en lugar de MariaDB.** El ERS especifica MariaDB; para la
   viabilidad del MVP se usa SQLite (caché de respuestas en
   `backend/app/database.py`). La migración a MariaDB es tarea de una fase
   futura.
2. **Modelo de IA placeholder, no una red TensorFlow/Keras entrenada.**
   Una heurística real y explicable (cruce SMA 20/50 + RSI 14) recorre el
   flujo completo de predicción de punta a punta. Vive aislada en
   `backend/app/prediction/` detrás de una interfaz estable
   (`predict(ticker) -> Prediction`), con el aislamiento verificado por
   test, para poder reemplazarla por un modelo TF/Keras sin tocar el resto
   del sistema.
3. **Sin autenticación.** Demo abierta, sesión única implícita, sin tabla
   de usuarios.

## Diferido a fases futuras (explícitamente fuera de este MVP)

- **R1** — módulo educativo, gamificación, rachas y niveles.
- **R3** — alertas de precio configurables.
- **Registro/login y gestión de usuarios** (incluye el flujo completo de
  términos y condiciones de A2.5).
- **MariaDB** como base de datos definitiva.
- **Modelo real TensorFlow/Keras** entrenado, en reemplazo del placeholder.
- **Arquitectura distribuida** (gateway, nodos de cómputo, cola de
  entrenamiento): este MVP corre en un único proceso de backend.
- Redes neuronales creadas por usuarios y exploración comunitaria.
- Búsqueda libre de tickers (el MVP fija KO y NVDA).
- Aplicación móvil (React Native).
