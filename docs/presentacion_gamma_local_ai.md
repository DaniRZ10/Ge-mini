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

---

## ⚖️ Ventajas y Desventajas de la IA Local
### Modelos Pequeños (1B-3B) en Hardware de Consumo

| Ventajas (Pros) | Desventajas (Contras) |
| :--- | :--- |
| **Privacidad Total**: El código nunca sale de la red local. | **Razonamiento Limitado**: Menor capacidad lógica en tareas abstractas. |
| **Coste Cero**: Sin suscripciones ni pagos por token. | **Amnesia**: Ventanas de contexto más cortas que modelos Cloud. |
| **Latencia Baja**: Respuestas inmediatas sin depender del servidor. | **Calor/Recursos**: Alto uso de CPU y calentamiento del equipo. |
| **Acceso Offline**: Programación asistida sin necesidad de internet. | **Alucinaciones**: Mayor tendencia a inventar sintaxis en modelos <3B. |

---

## 🔄 Alternativas e Hibridación
*   **Alternativa Local Superior**: Ampliación a 16GB/32GB RAM para usar modelos de **7B o 14B**.
*   **Estrategia Híbrida**: 
    *   **Local**: Tareas repetitivas, snippets y lógica simple.
    *   **Cloud**: Refactorización compleja y diseño de arquitectura.

---

## 🏆 Veredicto: El Modelo Ganador
Tras las pruebas, el **Qwen 2.5 Coder 1.5B** se establece como la versión ideal:
*   **Calidad**: Capaz de resolver problemas de recursividad complejos.
*   **Eficiencia**: No colapsa los 8GB de RAM del equipo.
*   **Conclusión**: Es posible programar en local con calidad profesional usando modelos ultra-cuantizados.
