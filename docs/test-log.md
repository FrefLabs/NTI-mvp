# NTI MVP — Registro de pruebas manuales

**Fecha de ejecución:** 2026-07-02.
**Entorno:** Linux, backend FastAPI en `localhost:8000` (uvicorn), frontend
Vite en `localhost:5173`, navegador Chromium headless (viewport 1280×900)
instrumentado con Playwright. Datos reales de Yahoo Finance vía yfinance.
**Flujo bajo prueba:** seleccionar ticker → ver datos → obtener predicción.

## Corrida 1 — Ticker KO

| Paso | Resultado observado | Estado |
| --- | --- | --- |
| Abrir la app (KO seleccionado por defecto) | Pantalla principal renderiza con identidad aprobada; indicador "Live" verde y reloj ART corriendo. | ✅ |
| Ver precio actual | `$84.14`, badge `↗ +3.57%` en verde, cierre anterior `$81.24`. Coincide con `GET /api/tickers/KO/quote`. | ✅ |
| Ver gráfico histórico (6M por defecto) | Curva SVG con datos reales (ene–jul 2026), gradiente verde, eje temporal correcto. | ✅ |
| Hover sobre el gráfico | Crosshair + tooltip `17-mar · $77.08` (valor real de la serie). | ✅ |
| Ver predicción | Badge **MANTENER** en ámbar, confianza **74%** con 15/20 bloques llenos, indicadores SMA 20/50 "Cruce alcista" y RSI 60.0 — neutral. Coincide con `GET /api/tickers/KO/prediction`. | ✅ |
| Descargo ERS §6.1 visible | "NTI no ejecuta operaciones ni brinda asesoramiento financiero profesional…" visible al pie sin scroll. | ✅ |

**Resultado corrida 1: PASA.**

## Corrida 2 — Ticker NVDA

| Paso | Resultado observado | Estado |
| --- | --- | --- |
| Click en toggle NVDA | Card cambia a "Precio actual — NVDA"; durante la carga se muestran placeholders (sin datos del ticker anterior — ver bug corregido abajo). | ✅ |
| Ver precio actual | `$194.83`, badge `↘ -1.12%` en rojo, cierre anterior `$197.04`. | ✅ |
| Ver gráfico histórico | Serie real 6M renderizada; cambio a rango 1Y re-renderiza ejes (`03 jul 25 → 02 jul 26`). | ✅ |
| Ver predicción | Badge **VENDER** en ámbar, confianza **25%** (5/20 bloques), SMA 20/50 "Cruce bajista", RSI 40.4 — neutral. | ✅ |
| Descargo ERS §6.1 visible | Permanece visible tras el cambio de ticker. | ✅ |

**Resultado corrida 2: PASA.**

## Pruebas adicionales (robustez)

| Prueba | Resultado observado | Estado |
| --- | --- | --- |
| Alternar KO↔NVDA rápidamente (6 clicks) | El estado final es consistente (NVDA con su precio correcto); sin datos mezclados. | ✅ |
| Backend detenido + recarga | Indicador pasa a "Offline" en rojo; panel de predicción muestra error limpio; sin crash de la UI. | ✅ |
| Ticker no permitido vía API (`GET /api/tickers/MSFT/quote`) | `404 {"detail":"Unknown ticker 'MSFT'. Available tickers: KO, NVDA"}`. | ✅ |
| Rango inválido (`?range=99y`) | `422` con mensaje de rangos válidos. | ✅ |
| Fallo simulado de yfinance (suite pytest) | `502` JSON limpio, sin traceback (RNF-14). 17/17 tests pasan. | ✅ |

## Bugs encontrados y estado

| Bug | Estado |
| --- | --- |
| Al cambiar de ticker se mostraba momentáneamente el precio del ticker anterior bajo la etiqueta del nuevo (dato viejo durante la carga). | **Corregido** durante esta verificación: `useApiData` ahora limpia `data` al recargar. Re-verificado en corrida 2. |

## Pendientes / observaciones (no bloqueantes)

- Máximo/mínimo del día y volumen muestran "—" cuando `fast_info` de
  yfinance devuelve nulos; el resto del panel no se ve afectado.
- Con el backend caído, el mensaje de error visible es "HTTP 500" (lo
  devuelve el proxy de Vite): limpio pero poco descriptivo.
- 404 de favicon en consola del navegador (no hay favicon definido).
