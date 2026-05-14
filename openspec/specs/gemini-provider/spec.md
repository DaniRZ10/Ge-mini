# gemini-provider Specification

## Purpose
TBD - created by archiving change migrate-to-google-genai-sdk. Update Purpose after archive.
## Requirements
### Requirement: Identidad del proveedor

El adaptador SHALL exponerse como proveedor de IA con nombre `gemini` a través de la propiedad `name` definida en el puerto `AiProvider`.

#### Scenario: Lectura del nombre

- **WHEN** se accede a `GeminiAdapter.name`
- **THEN** el valor devuelto MUST ser exactamente `"gemini"`

### Requirement: Inicialización con clave de API

El adaptador SHALL aceptar una `api_key` y un `system_prompt` (este último puede ser cadena vacía) en su constructor, y MUST instanciar un cliente del SDK `google-genai` enlazado a esa clave para reutilizarlo en todas sus operaciones.

#### Scenario: Construcción válida

- **WHEN** se instancia `GeminiAdapter(api_key="k", system_prompt="...")`
- **THEN** el adaptador MUST quedar listo para invocar `list_models`, `send_message` y `send_message_stream` sin volver a configurar globalmente el SDK

#### Scenario: System prompt vacío

- **WHEN** se instancia `GeminiAdapter(api_key="k", system_prompt="")`
- **THEN** las llamadas posteriores a `send_message` y `send_message_stream` MUST omitir cualquier `system_instruction` en la petición al modelo

### Requirement: Listado de modelos disponibles

El método `list_models` SHALL devolver de forma asíncrona la lista de modelos accesibles bajo la API key, filtrada a aquellos que soporten la acción de generación de contenido, en el formato `[{"id": str, "name": str}]` donde `id` es el último segmento de la ruta del modelo y `name` es su `display_name`.

#### Scenario: Listado correcto con modelos compatibles

- **WHEN** la API devuelve modelos cuyas acciones soportadas incluyen `generateContent`
- **THEN** el método MUST devolver un elemento por cada uno con `id` igual al sufijo de `name` (`models/<id>` → `<id>`) y `name` igual al `display_name` del modelo

#### Scenario: Filtrado de modelos no compatibles

- **WHEN** un modelo devuelto por la API no incluye `generateContent` entre sus acciones soportadas (o no expone esa información)
- **THEN** ese modelo MUST ser omitido del resultado

#### Scenario: Fallo al listar

- **WHEN** la llamada al SDK lanza una excepción
- **THEN** el método MUST registrar el error y devolver `[]` en lugar de propagar la excepción

### Requirement: Envío de mensaje con respuesta completa

El método `send_message(message, history, model_id)` SHALL enviar de forma asíncrona el `message` al modelo `model_id` con el `history` previo como contexto y el `system_prompt` (si existe) como instrucción de sistema, y devolver el texto completo generado por el modelo.

#### Scenario: Respuesta correcta

- **WHEN** el modelo responde con éxito
- **THEN** el método MUST devolver el `text` íntegro de la respuesta como `str`

#### Scenario: Historial respetado

- **WHEN** `history` contiene mensajes con roles `user` y `assistant`
- **THEN** la petición al modelo MUST conservar el orden y mapear los roles a `user` y `model` respectivamente, anteponiéndolos al turno de usuario actual

#### Scenario: Cuota agotada

- **WHEN** el SDK reporta un error con código HTTP `429`
- **THEN** el método MUST devolver exactamente `"Error: Has agotado tu cuota de Gemini (Rate Limit). Por favor, espera un minuto o prueba con otro modelo."` sin propagar la excepción

#### Scenario: Otro fallo del SDK

- **WHEN** el SDK lanza cualquier otra excepción al generar contenido
- **THEN** el método MUST devolver una cadena con prefijo `"Error en Gemini SDK: "` seguida del mensaje de la excepción, sin propagarla

### Requirement: Envío de mensaje en streaming

El método `send_message_stream(message, history, model_id)` SHALL devolver un `AsyncIterator[str]` que emita los fragmentos de texto del modelo en el orden en que el SDK los produce, usando el mismo `system_prompt` e historial que `send_message`.

#### Scenario: Streaming exitoso

- **WHEN** el modelo emite varios chunks con texto no vacío
- **THEN** el iterador MUST yieldar el `text` de cada chunk a medida que llega y terminar limpiamente cuando el SDK cierra el stream

#### Scenario: Chunks sin texto

- **WHEN** un chunk del SDK no contiene texto
- **THEN** el iterador MUST omitir ese chunk sin yieldar cadena vacía

#### Scenario: Cuota agotada durante el stream

- **WHEN** el SDK reporta un error con código HTTP `429` antes o durante la emisión
- **THEN** el iterador MUST yieldar exactamente `"Error: Cuota agotada (Rate Limit). Reintenta en un minuto."` y finalizar

#### Scenario: Otro fallo durante el stream

- **WHEN** el SDK lanza cualquier otra excepción
- **THEN** el iterador MUST yieldar una cadena con prefijo `"Error en streaming Gemini: "` seguida del mensaje de la excepción y finalizar

