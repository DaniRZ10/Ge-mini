# Informe de Inferencia Local: Ge-mini 💠
## El Reto de los 8GB: Código de Calidad a Velocidad de Producción

---

## 🎯 El Desafío Técnico
*   **Hardware Limitado**: Ejecución sobre 8GB de RAM y CPU (Intel i5-10210U).
*   **Objetivo**: Encontrar un modelo local que genere código de calidad profesional sin latencias prohibitivas.
*   **Restricción**: Sin uso de APIs externas (Privacidad y Vibe Coding Offline).

---

## 🧪 Modelos Seleccionados (Bajo Consumo)
Hemos priorizado modelos altamente optimizados y cuantizados para maximizar el uso de la RAM disponible:
1.  **Qwen 2.5 Coder (1.5B)**: El más equilibrado en parámetros/rendimiento.
2.  **DeepSeek Coder (1.3B)**: Conocido por su alta velocidad de inferencia.
3.  **Qwen 2.5 Coder (3B)**: Testeado como límite superior de calidad en 8GB.

---

## 📊 Benchmarking: Tiempos y Latencias
| Modelo | Time to First Token | Velocidad Total | Calidad (MCM Java) |
| :--- | :--- | :--- | :--- |
| **Qwen 2.5 1.5B** | ~2.5s | ~7 tokens/s | **Alta** (Lógica correcta) |
| **DeepSeek 1.3B** | ~1.8s | ~12 tokens/s | Media (Necesita guia) |
| **Qwen 2.5 3B** | ~6.5s | ~2 tokens/s | Muy Alta (Lento) |

---

## ⚡ Solución a la Latencia: Streaming
Para solventar el cuello de botella de la CPU, se ha implementado un sistema de **Streaming de Texto**:
*   Permite al desarrollador empezar a leer el código en **2-3 segundos**.
*   Elimina la espera de bloqueo (45-60s) propia de la inferencia en CPU.
*   Hace viable el uso de modelos locales en el flujo diario de trabajo.

---

## 🏆 Veredicto: El Modelo Ganador
Tras las pruebas, el **Qwen 2.5 Coder 1.5B** se establece como la versión ideal:
*   **Calidad**: Capaz de resolver problemas de recursividad complejos.
*   **Eficiencia**: No colapsa los 8GB de RAM del equipo.
*   **Conclusión**: Es posible programar en local con calidad profesional usando modelos ultra-cuantizados.
