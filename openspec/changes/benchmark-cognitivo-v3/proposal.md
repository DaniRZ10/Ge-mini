# Proposal: Benchmark Cognitivo v3

## Objetivo
Evaluar la capacidad de razonamiento algorítmico y codificación de modelos de lenguaje locales mediante la resolución de problemas clásicos de ciencias de la computación con restricciones estrictas.

## Alcance
- **Script CLI**: `benchmark_v3.py` para automatizar la ejecución y recolección de métricas.
- **Modelos**: Evaluación de modelos locales vía Ollama (Qwen, Gemma, DeepSeek, Phi).
- **Problemas**: 4 desafíos técnicos (LRU Cache, Serialización de Árboles, Ciclos en Grafos, Distancia de Edición).
- **Métricas**: TTFT (Time to First Token), Latencia Total, Tokens por Segundo.
- **Validación**: Humano-en-el-bucle para calificación cualitativa (VÁLIDO / PARCIAL / INVÁLIDO).

## Criterios de Éxito
1. Ejecución fluida de los 4 problemas para cada modelo seleccionado.
2. Generación automática de `benchmark_results_v3.md`.
3. Persistencia de métricas precisas de rendimiento de Ollama.
