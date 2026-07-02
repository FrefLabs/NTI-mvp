# NTI MVP — Evaluación de cumplimiento contra la MML (R2)

**Fecha:** 2026-07-02.
**Referencia:** Matriz de Marco Lógico NTI v2, fila Resultados, R2.

## El indicador (IVO) de R2

> "El 60% de los usuarios consulta información de al menos 2 activos
> distintos por semana durante los primeros 3 meses, visualizando en cada
> caso la sugerencia de red neuronal asociada."
>
> Fuentes de verificación: "Historial de consultas de activos en la
> plataforma. Registros de visualización del módulo de sugerencias."

## Qué cumple este MVP

| Aspecto del IVO / supuestos R2 | Estado | Detalle |
| --- | --- | --- |
| El usuario puede consultar **al menos 2 activos distintos** | ✅ | Exactamente dos: KO y NVDA, con datos reales y actualizados de Yahoo Finance. |
| Cada consulta muestra **la sugerencia asociada automáticamente** | ✅ | Al seleccionar un ticker, el panel de IA carga la señal comprar/mantener/vender sin acción adicional del usuario. |
| Sugerencias "coherentes y comprensibles" (supuesto R2) | ✅ | Señal en lenguaje claro (Comprar/Mantener/Vender), nivel de confianza visible (RF-24) y los indicadores que la explican (SMA, RSI). |
| Aclaración de que no constituye asesoramiento profesional (supuesto R2) | ✅ | Descargo ERS §6.1 permanente en la interfaz. |
| Información "confiable y actualizada" | ✅ | Datos en vivo del proveedor externo, con caché de 5 minutos y manejo de fallos. |

## Qué NO cumple (y por qué)

| Aspecto del IVO | Estado | Motivo |
| --- | --- | --- |
| Medición del **60% de usuarios** con la frecuencia indicada | ❌ No medible | El IVO es un indicador de *adopción en operación* a 3 meses, con usuarios registrados. Este MVP no tiene registro ni usuarios (ajuste deliberado n°3), por lo que no existe la población sobre la cual medir el porcentaje. |
| Fuente de verificación: **historial de consultas por usuario** | ❌ No implementada | Requiere identidad de usuario y logging de actividad; diferido junto con la autenticación. |
| Fuente de verificación: **registros de visualización del módulo de sugerencias** | ❌ No implementada | Mismo motivo: sin sesión de usuario no hay registro atribuible. |
| Sugerencia generada por **red neuronal** | ⚠️ Parcial | La sugerencia existe y se visualiza según lo previsto, pero la genera un modelo placeholder (heurística SMA+RSI), no una red neuronal entrenada (ajuste deliberado n°2). La interfaz del módulo ya está preparada para el reemplazo. |

## Lectura general

El MVP deja **verificable la capacidad funcional** que el IVO de R2
presupone (consultar activos y visualizar la sugerencia asociada, probado
en `docs/test-log.md`), pero **no puede evidenciar el indicador
cuantitativo** porque éste mide comportamiento de usuarios registrados en
operación sostenida. Para que R2 sea medible en una fase futura se
necesita: registro/login, logging de consultas y visualizaciones por
usuario, y el reemplazo del placeholder por la red neuronal real.
