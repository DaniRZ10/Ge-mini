# Implementación de IA Local: Ge-mini 💠
## Optimizando Latencia y Calidad con Modelos de Bajo Consumo

---

## 🎯 Objetivo del Proyecto
*   **Independencia**: Ejecución 100% local sin dependencia de APIs externas.
*   **Vibe Coding**: Mantener la fluidez de programación incluso sin conexión.
*   **Eficiencia**: Correr modelos de alta calidad en hardware con 8GB de RAM.

---

## 🛠️ Stack Tecnológico Local
*   **Motor**: Ollama (Inferencia optimizada).
*   **Modelos Testeados**: 
    *   Qwen 2.5 Coder (1.5B / 3B).
    *   DeepSeek Coder (1.3B).
*   **Hardware**: Intel i5-10210U | 8GB RAM.

---

## ⚡ Innovación: Real-Time Streaming
*   **Problema**: Latencias de 40-80s para respuestas completas en CPU.
*   **Solución**: Implementación de `StreamingResponse` (FastAPI).
*   **Resultado**: Time-to-First-Token (TTFT) reducido a < 3 segundos.
*   **UX**: "Smart Scroll" implementado para lectura fluida durante la generación.

---

## 📊 Benchmarking de Modelos
| Modelo | Latencia Total | Calidad de Código | Estabilidad |
| :--- | :--- | :--- | :--- |
| **Qwen 2.5 1.5B** | 35-45s | Alta (Lógica MCM) | Excelente |
| **DeepSeek 1.3B** | 10-25s | Media | Muy Rápida |
| **Qwen 2.5 3B** | 80s+ | Muy Alta | Lenta en 8GB |

---

## 🧠 Optimización de "Amnesia" y Precisión
*   **Memoria**: Persistencia de ID de conversación en el flujo de streaming.
*   **Prompt Engineering**: Refinado de "Silent Expert" para eliminar preámbulos innecesarios.
*   **Limpieza**: Filtros automáticos para eliminar artefactos LaTeX (`\times`) en modelos pequeños.

---

## 🚀 Conclusiones y Siguientes Pasos
1.  El modelo **Qwen 2.5 Coder 1.5B** es el equilibrio perfecto para este equipo.
2.  El **Streaming** ha transformado una espera frustrante en una experiencia usable.
3.  Próximo hito: Cuantización avanzada para probar modelos de 7B.
