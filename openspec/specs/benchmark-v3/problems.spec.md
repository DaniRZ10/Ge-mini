# Problems Specification - Benchmark v3

## P1 — LRU Cache O(1) estricto
**Prompt**: Implement a LRU Cache class in Python with fixed capacity. Operations get(key) and put(key, value) MUST run in O(1). You MUST implement a doubly linked list manually. Do NOT use OrderedDict, deque, or any collections module. Use only a plain dict and your own DLL node class. Show the full implementation and explain your approach.

**Criterios de Validación**:
- **VÁLIDO**: DLL manual + dict, O(1) real, evicción correcta.
- **PARCIAL**: Lógica correcta pero usa OrderedDict o falla casos límite.
- **INVÁLIDO**: No implementa DLL o código no ejecutable.
- **Solución Ideal**: Clase `Node` con `prev`/`next` + `dict`. `get` mueve al frente. `put` inserta al frente y elimina `tail` si se excede la capacidad.

## P2 — Serialización/Deserialización de árbol binario
**Prompt**: Implement two functions in Python: serialize(root) and deserialize(data). serialize must convert a binary tree to a single string. deserialize must reconstruct the exact same tree from that string. The tree must survive a full round-trip: deserialize(serialize(root)) must produce a tree identical to the original, including None children. Do not use any external libraries. Define your own TreeNode class.

**Criterios de Validación**:
- **VÁLIDO**: Round-trip perfecto, nulos manejados, sin librerías externas.
- **PARCIAL**: Serializa bien pero falla en árboles no completos.
- **INVÁLIDO**: No reconstituye correctamente o código no ejecutable.
- **Solución Ideal**: BFS con marcador de nulos ('null'). `serialize` produce string delimitado por comas. `deserialize` reconstruye nivel a nivel con una cola.

## P3 — Detección de ciclos en grafo dirigido con coloración DFS
**Prompt**: Implement a function has_cycle(graph) in Python that detects if a directed graph contains a cycle. The graph is given as an adjacency list (dict of lists). You MUST use a three-color DFS approach: WHITE (unvisited), GRAY (in current path), BLACK (fully processed). A node marked GRAY when revisited during DFS indicates a cycle. Do not use any external libraries.

**Criterios de Validación**:
- **VÁLIDO**: Tres estados correctos, detecta ciclos en grafos desconectados.
- **PARCIAL**: Solo maneja grafos conectados o usa solo dos estados.
- **INVÁLIDO**: Algoritmo incorrecto o falsos positivos sistemáticos.
- **Solución Ideal**: Diccionario de colores, DFS recursivo, retorna `True` en cuanto encuentra un nodo `GRAY`. Maneja grafos desconectados iterando todos los nodos.

## P4 — Levenshtein con reconstrucción del camino
**Prompt**: Implement a function edit_distance(s1, s2) in Python that computes the minimum edit distance (Levenshtein) between two strings AND reconstructs the exact sequence of operations to transform s1 into s2. Return a tuple: (distance, operations) where operations is a list of strings describing each step (e.g. "Insert 'a' at position 2", "Delete 'x' at position 1", "Replace 'b' with 'c' at position 3"). Do not use any external libraries.

**Criterios de Validación**:
- **VÁLIDO**: Distancia correcta + operaciones con posiciones exactas.
- **PARCIAL**: Distancia correcta pero operaciones incorrectas o sin posiciones.
- **INVÁLIDO**: Distancia incorrecta o sin reconstrucción.
- **Solución Ideal**: Tabla DP 2D completa, backtracking desde `dp[m][n]` para reconstruir operaciones con posiciones y tipos correctos.
