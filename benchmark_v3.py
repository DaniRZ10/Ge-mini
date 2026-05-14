import argparse
import time
import json
import httpx
import sys
import os

# PROMPTS INMUTABLES
PROMPTS = {
    "P1": "Implement a LRU Cache class in Python with fixed capacity. Operations get(key) and put(key, value) MUST run in O(1). You MUST implement a doubly linked list manually. Do NOT use OrderedDict, deque, or any collections module. Use only a plain dict and your own DLL node class. Show the full implementation and explain your approach.",
    "P2": "Implement two functions in Python: serialize(root) and deserialize(data). serialize must convert a binary tree to a single string. deserialize must reconstruct the exact same tree from that string. The tree must survive a full round-trip: deserialize(serialize(root)) must produce a tree identical to the original, including None children. Do not use any external libraries. Define your own TreeNode class.",
    "P3": "Implement a function has_cycle(graph) in Python that detects if a directed graph contains a cycle. The graph is given as an adjacency list (dict of lists). You MUST use a three-color DFS approach: WHITE (unvisited), GRAY (in current path), BLACK (fully processed). A node marked GRAY when revisited during DFS indicates a cycle. Do not use any external libraries.",
    "P4": "Implement a function edit_distance(s1, s2) in Python that computes the minimum edit distance (Levenshtein) between two strings AND reconstructs the exact sequence of operations to transform s1 into s2. Return a tuple: (distance, operations) where operations is a list of strings describing each step (e.g. \"Insert 'a' at position 2\", \"Delete 'x' at position 1\", \"Replace 'b' with 'c' at position 3\"). Do not use any external libraries."
}

DEFAULT_MODELS = ["qwen2.5-coder:1.5b", "qwen2.5-coder:3b", "gemma2:2b", "deepseek-r1:1.5b", "phi3:mini"]

def call_ollama(model, prompt):
    """Llama a la API de Ollama con streaming y mide métricas."""
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True
    }
    
    full_response = ""
    start_time = time.time()
    ttft = None
    token_count = 0
    
    try:
        with httpx.stream("POST", url, json=payload, timeout=None) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    text = chunk.get("response", "")
                    if text and ttft is None:
                        ttft = time.time() - start_time
                    
                    full_response += text
                    print(text, end="", flush=True)
                    
                    if chunk.get("done"):
                        total_latency = time.time() - start_time
                        eval_count = chunk.get("eval_count", 0)
                        if eval_count == 0:
                            token_count = len(full_response.split())
                        else:
                            token_count = eval_count
                            
                        tps = token_count / (total_latency - (ttft or 0)) if total_latency > (ttft or 0) else 0
                        return {
                            "response": full_response,
                            "ttft": ttft or 0,
                            "total_latency": total_latency,
                            "tps": tps,
                            "tokens": token_count
                        }
    except Exception as e:
        print(f"\nError llamando a Ollama: {e}")
        return None

def generate_report(results):
    """Genera el archivo benchmark_results_v3.md con los resultados."""
    with open("benchmark_results_v3.md", "w", encoding="utf-8") as f:
        f.write("# Benchmark Cognitivo v3 - Results\n\n")
        f.write("| Modelo | Problema | Estado | TTFT (s) | Latencia (s) | Tokens/s | Notas |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
        
        for r in results:
            f.write(f"| {r['model']} | {r['p_id']} | {r['status']} | {r['ttft']:.2f} | {r['total_latency']:.2f} | {r['tps']:.1f} | {r['notes']} |\n")
        
        f.write("\n## Comparativa v1/v2/v3\n")
        f.write("- v1: Base\n- v2: Razonamiento\n- v3: Algoritmos Estrictos (Actual)\n\n")
        f.write("## Conclusiones\n\n")
        f.write("*(Espacio para rellenar manualmente)*\n")

def main():
    parser = argparse.ArgumentParser(description="Benchmark Cognitivo v3")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS, help="Lista de modelos a testear")
    args = parser.parse_args()

    results = []

    print("="*50)
    print(" INICIANDO BENCHMARK COGNITIVO V3 ")
    print("="*50)

    for model in args.models:
        print(f"\n>>> MODELO: {model}")
        for p_id, prompt in PROMPTS.items():
            print(f"\n--- Problema {p_id} ---")
            print(f"Prompt: {prompt[:100]}...")
            print("Generando respuesta...\n")
            
            metrics = call_ollama(model, prompt)
            
            if not metrics:
                print(f"Saltando {p_id} debido a error.")
                continue
            
            print("\n" + "-"*30)
            print(f"Métricas: TTFT={metrics['ttft']:.2f}s, Latencia={metrics['total_latency']:.2f}s, TPS={metrics['tps']:.1f}")
            print("-"*30)
            
            status = "N/A"
            valid = False
            while not valid:
                choice = input("\nResultado (V/P/I - Válido/Parcial/Inválido): ").upper()
                if choice in ["V", "P", "I"]:
                    status = {"V": "VÁLIDO", "P": "PARCIAL", "I": "INVÁLIDO"}[choice]
                    valid = True
                else:
                    print("Opción no válida. Usa V, P o I.")
            
            notes = input("Notas adicionales (opcional): ")
            
            results.append({
                "model": model,
                "p_id": p_id,
                "status": status,
                "ttft": metrics["ttft"],
                "total_latency": metrics["total_latency"],
                "tps": metrics["tps"],
                "notes": notes
            })

    print("\n" + "="*50)
    print(" BENCHMARK FINALIZADO ")
    print("="*50)
    
    generate_report(results)
    print(f"Reporte generado en: benchmark_results_v3.md")

if __name__ == "__main__":
    main()
