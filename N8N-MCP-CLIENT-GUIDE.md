# Guía: Usar MCP Gmail Server desde N8N con HTTP Request

## Problema

El nodo **MCP Client** de n8n-nodes-mcp NO puede conectarse a servidores MCP remotos via HTTP/SSE. Solo ejecuta comandos locales (ej: `npx`, `node`).

## Solución

Usar nodos **HTTP Request** para hacer llamadas al protocolo MCP manualmente.

## Arquitectura

```
Workflow A: MCP Server Trigger
  └─> Expone: https://n8n.davidbuitrago.dev/mcp/gmail/sse
  └─> Autenticación: X-API-KEY header

Workflow B: HTTP Request nodes
  └─> Llama al MCP Server siguiendo el protocolo MCP
```

## Protocolo MCP: Flujo de Llamadas

### 1. Obtener Session ID (opcional con SSE)

**Nodo HTTP Request: "Get MCP Session"**

```yaml
Method: GET
URL: https://n8n.davidbuitrago.dev/mcp/gmail/sse
Headers:
  X-API-KEY: IVLhIYm8x9v11mKY5jZ23dxf230ICxSkZGKb4K8SLn4OzmELGtyp2lYNDUuaDYNQ
Timeout: 5000
Options:
  - Ignore SSL Issues: false
```

**Respuesta esperada (SSE):**
```
event: endpoint
data: /mcp/gmail/messages?sessionId=c7b1e758-e58b-4102-be84-e3dec7e42c29
```

Extraer el `sessionId` del data usando un nodo **Code** o **Set**.

---

### 2. Inicializar Sesión MCP

**Nodo HTTP Request: "Initialize MCP Session"**

```yaml
Method: POST
URL: https://n8n.davidbuitrago.dev/mcp/gmail/messages?sessionId={{ $json.sessionId }}
Headers:
  X-API-KEY: IVLhIYm8x9v11mKY5jZ23dxf230ICxSkZGKb4K8SLn4OzmELGtyp2lYNDUuaDYNQ
  Content-Type: application/json
  Accept: application/json, text/event-stream
Body (JSON):
  {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "n8n-workflow",
        "version": "1.0.0"
      }
    }
  }
```

**Respuesta esperada:**
```json
{
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "n8n-mcp-server",
      "version": "0.1.0"
    }
  },
  "jsonrpc": "2.0",
  "id": 1
}
```

**IMPORTANTE**: Guardar el header `Mcp-Session-Id` de la respuesta.

**Nodo Code (después de Initialize):**
```javascript
// Extraer Mcp-Session-Id del header de respuesta
const headers = $input.all()[0].json.headers || {};
const mcpSessionId = headers['mcp-session-id'];

return [{
  json: {
    sessionId: $input.all()[0].json.sessionId,
    mcpSessionId: mcpSessionId
  }
}];
```

---

### 3. Listar Herramientas Disponibles (Opcional)

**Nodo HTTP Request: "List MCP Tools"**

```yaml
Method: POST
URL: https://n8n.davidbuitrago.dev/mcp/gmail/messages?sessionId={{ $json.sessionId }}
Headers:
  X-API-KEY: IVLhIYm8x9v11mKY5jZ23dxf230ICxSkZGKb4K8SLn4OzmELGtyp2lYNDUuaDYNQ
  Content-Type: application/json
  Accept: application/json, text/event-stream
  Mcp-Session-Id: {{ $json.mcpSessionId }}
Body (JSON):
  {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }
```

**Herramientas disponibles:**
- `search` - Buscar mensajes (★ más útil)
- `get` - Obtener mensaje específico
- `reply` - Responder mensaje
- `delete` - Eliminar mensaje
- `markAsRead` / `markAsUnread`
- `addLabels` / `removeLabels`
- `getThread` / `getManyThreads`
- `replyThread`
- `addLabelThread` / `removeLabelThread`
- `getLabels` / `getLabel` / `createLabel` / `deleteLabel`
- `getManyDrafts` / `getDraft` / `createDraft` / `deleteDraft`

---

### 4. Llamar a una Herramienta

**Ejemplo: Obtener Correos No Leídos**

**Nodo HTTP Request: "Get Unread Emails"**

```yaml
Method: POST
URL: https://n8n.davidbuitrago.dev/mcp/gmail/messages?sessionId={{ $json.sessionId }}
Headers:
  X-API-KEY: IVLhIYm8x9v11mKY5jZ23dxf230ICxSkZGKb4K8SLn4OzmELGtyp2lYNDUuaDYNQ
  Content-Type: application/json
  Accept: application/json, text/event-stream
  Mcp-Session-Id: {{ $json.mcpSessionId }}
Body (JSON):
  {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {
        "Return_All": false,
        "Search": "is:unread",
        "Received_After": "",
        "Received_Before": "",
        "Sender": ""
      }
    }
  }
```

**Respuesta:**
```json
{
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"id\":\"...\",\"subject\":\"...\",\"from\":\"...\"}]"
      }
    ]
  },
  "jsonrpc": "2.0",
  "id": 3
}
```

---

## Workflow Completo de Ejemplo

### Flujo Simple: Obtener Correos No Leídos

```
1. [Trigger] (Manual o Schedule)
    ↓
2. [Set] - Definir configuración
    - sessionId: "new-session-{{ $now.format('x') }}"
    - apiKey: IVLhIYm8x9v11mKY5jZ23dxf230ICxSkZGKb4K8SLn4OzmELGtyp2lYNDUuaDYNQ
    ↓
3. [HTTP Request] - Initialize MCP Session
    - URL: https://n8n.davidbuitrago.dev/mcp/gmail/messages?sessionId={{ $json.sessionId }}
    - Method: POST
    - Headers: X-API-KEY, Content-Type, Accept
    - Body: initialize request
    ↓
4. [Code] - Extract Mcp-Session-Id from headers
    ↓
5. [HTTP Request] - Get Unread Emails
    - URL: https://n8n.davidbuitrago.dev/mcp/gmail/messages?sessionId={{ $json.sessionId }}
    - Method: POST
    - Headers: X-API-KEY, Content-Type, Accept, Mcp-Session-Id
    - Body: tools/call with "search" for "is:unread"
    ↓
6. [Code] - Parse emails from result.content[0].text
    ↓
7. [Split Out] - Separar cada email
    ↓
8. [Process each email] (tus acciones personalizadas)
```

---

## Ejemplos de Llamadas a Herramientas

### Buscar Correos de un Remitente

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "search",
    "arguments": {
      "Return_All": false,
      "Search": "",
      "Received_After": "",
      "Received_Before": "",
      "Sender": "example@gmail.com"
    }
  }
}
```

### Buscar Correos en un Rango de Fechas

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "search",
    "arguments": {
      "Return_All": false,
      "Search": "",
      "Received_After": "2025-11-01T00:00:00Z",
      "Received_Before": "2025-11-10T23:59:59Z",
      "Sender": ""
    }
  }
}
```

### Marcar Mensaje como Leído

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/call",
  "params": {
    "name": "markAsRead",
    "arguments": {
      "Message_ID": "19a6da4368f9f654"
    }
  }
}
```

### Responder a un Mensaje

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "reply",
    "arguments": {
      "Message_ID": "19a6da4368f9f654",
      "Message": "Gracias por tu mensaje. Te responderé pronto.",
      "Attachment_Field_Name": "",
      "BCC": "",
      "CC": ""
    }
  }
}
```

### Añadir Etiqueta a un Mensaje

```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "method": "tools/call",
  "params": {
    "name": "addLabels",
    "arguments": {
      "Message_ID": "19a6da4368f9f654",
      "Label_Names_or_IDs": "IMPORTANT,Label_123"
    }
  }
}
```

---

## Configuración de Credenciales en N8N

### Opción 1: Header Auth (Recomendado)

1. Ir a **Credentials** en N8N
2. Crear nueva credencial tipo **Header Auth**
3. Configurar:
   - Name: `Gmail MCP API Key`
   - Header Name: `X-API-KEY`
   - Header Value: `IVLhIYm8x9v11mKY5jZ23dxf230ICxSkZGKb4K8SLn4OzmELGtyp2lYNDUuaDYNQ`

4. En cada nodo HTTP Request:
   - Authentication: Header Auth
   - Credential: `Gmail MCP API Key`

### Opción 2: Variables de Entorno

En tu `.env` del servidor:
```bash
GMAIL_MCP_API_KEY=IVLhIYm8x9v11mKY5jZ23dxf230ICxSkZGKb4K8SLn4OzmELGtyp2lYNDUuaDYNQ
GMAIL_MCP_URL=https://n8n.davidbuitrago.dev/mcp/gmail
```

En el workflow, usar: `{{ $env.GMAIL_MCP_API_KEY }}`

---

## Parsear Respuestas

### Extraer Emails del Resultado

**Nodo Code: "Parse Emails"**

```javascript
const response = $input.all()[0].json;
const content = response.result.content[0].text;
const emails = JSON.parse(content);

return emails.map(email => ({
  json: {
    id: email.id,
    threadId: email.threadId,
    subject: email.Subject || 'No subject',
    from: email.From,
    to: email.To,
    snippet: email.snippet,
    labels: email.labels.map(l => l.name),
    internalDate: new Date(parseInt(email.internalDate)),
    isUnread: email.labels.some(l => l.name === 'UNREAD')
  }
}));
```

---

## Troubleshooting

### Error: "Not Acceptable: Client must accept both application/json and text/event-stream"

**Solución**: Agregar header `Accept: application/json, text/event-stream`

### Error: "Bad Request: Server not initialized"

**Solución**: Debes llamar primero al método `initialize` antes de usar otras funciones.

### Error: "Bad Request: Mcp-Session-Id header is required"

**Solución**: Después de `initialize`, debes incluir el header `Mcp-Session-Id` en todas las llamadas siguientes. Extraerlo de la respuesta del `initialize`.

### Error 401: Unauthorized

**Solución**: Verificar que el header `X-API-KEY` esté correcto.

### Los emails no se parsean correctamente

**Solución**: El resultado viene como string JSON dentro de `result.content[0].text`. Debes hacer `JSON.parse()` primero.

---

## Optimización

### Reutilizar Sesión

Las sesiones MCP pueden persistir. Guarda el `mcpSessionId` en una variable de workflow o en un database para reutilizarlo:

```javascript
// Guardar sesión
$execution.customData.set('mcpSessionId', mcpSessionId);

// Recuperar sesión
const savedSessionId = $execution.customData.get('mcpSessionId');
```

### Conexión Interna (más rápida)

Si ambos workflows están en el mismo N8N, usa la URL interna:

```
http://localhost:5678/mcp/gmail/sse
```

Esto evita pasar por nginx-proxy y es más rápido.

---

## Ejemplo de Workflow JSON

Puedes importar este workflow de ejemplo en N8N:

```json
{
  "name": "MCP Gmail - Get Unread Emails",
  "nodes": [
    {
      "parameters": {},
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "position": [250, 300],
      "typeVersion": 1
    },
    {
      "parameters": {
        "values": {
          "string": [
            {
              "name": "sessionId",
              "value": "=session-{{ $now.format('x') }}"
            },
            {
              "name": "baseUrl",
              "value": "https://n8n.davidbuitrago.dev/mcp/gmail"
            }
          ]
        }
      },
      "name": "Set Config",
      "type": "n8n-nodes-base.set",
      "position": [450, 300],
      "typeVersion": 1
    },
    {
      "parameters": {
        "url": "={{ $json.baseUrl }}/messages?sessionId={{ $json.sessionId }}",
        "method": "POST",
        "headerParameters": {
          "parameters": [
            {
              "name": "X-API-KEY",
              "value": "IVLhIYm8x9v11mKY5jZ23dxf230ICxSkZGKb4K8SLn4OzmELGtyp2lYNDUuaDYNQ"
            },
            {
              "name": "Content-Type",
              "value": "application/json"
            },
            {
              "name": "Accept",
              "value": "application/json, text/event-stream"
            }
          ]
        },
        "body": {
          "jsonrpc": "2.0",
          "id": 1,
          "method": "initialize",
          "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
              "name": "n8n-workflow",
              "version": "1.0.0"
            }
          }
        },
        "options": {
          "response": {
            "response": {
              "fullResponse": true
            }
          }
        }
      },
      "name": "Initialize MCP",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300],
      "typeVersion": 1
    },
    {
      "parameters": {
        "jsCode": "// Extract MCP Session ID from response headers\nconst mcpSessionId = $input.first().json.headers['mcp-session-id'];\nconst sessionId = $input.first().json.body.sessionId;\n\nreturn [{\n  json: {\n    sessionId: sessionId,\n    mcpSessionId: mcpSessionId,\n    baseUrl: $('Set Config').item.json.baseUrl\n  }\n}];"
      },
      "name": "Extract Session ID",
      "type": "n8n-nodes-base.code",
      "position": [850, 300],
      "typeVersion": 1
    },
    {
      "parameters": {
        "url": "={{ $json.baseUrl }}/messages?sessionId={{ $json.sessionId }}",
        "method": "POST",
        "headerParameters": {
          "parameters": [
            {
              "name": "X-API-KEY",
              "value": "IVLhIYm8x9v11mKY5jZ23dxf230ICxSkZGKb4K8SLn4OzmELGtyp2lYNDUuaDYNQ"
            },
            {
              "name": "Content-Type",
              "value": "application/json"
            },
            {
              "name": "Accept",
              "value": "application/json, text/event-stream"
            },
            {
              "name": "Mcp-Session-Id",
              "value": "={{ $json.mcpSessionId }}"
            }
          ]
        },
        "body": {
          "jsonrpc": "2.0",
          "id": 2,
          "method": "tools/call",
          "params": {
            "name": "search",
            "arguments": {
              "Return_All": false,
              "Search": "is:unread",
              "Received_After": "",
              "Received_Before": "",
              "Sender": ""
            }
          }
        }
      },
      "name": "Get Unread Emails",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1050, 300],
      "typeVersion": 1
    },
    {
      "parameters": {
        "jsCode": "const response = $input.first().json;\nconst content = response.result.content[0].text;\nconst emails = JSON.parse(content);\n\nreturn emails.map(email => ({\n  json: {\n    id: email.id,\n    subject: email.Subject || 'No subject',\n    from: email.From,\n    snippet: email.snippet,\n    labels: email.labels.map(l => l.name)\n  }\n}));"
      },
      "name": "Parse Emails",
      "type": "n8n-nodes-base.code",
      "position": [1250, 300],
      "typeVersion": 1
    }
  ],
  "connections": {
    "Manual Trigger": {
      "main": [[{ "node": "Set Config", "type": "main", "index": 0 }]]
    },
    "Set Config": {
      "main": [[{ "node": "Initialize MCP", "type": "main", "index": 0 }]]
    },
    "Initialize MCP": {
      "main": [[{ "node": "Extract Session ID", "type": "main", "index": 0 }]]
    },
    "Extract Session ID": {
      "main": [[{ "node": "Get Unread Emails", "type": "main", "index": 0 }]]
    },
    "Get Unread Emails": {
      "main": [[{ "node": "Parse Emails", "type": "main", "index": 0 }]]
    }
  }
}
```

---

## Resumen

✅ **Funciona desde fuera**: Tu MCP server es accesible públicamente con autenticación
✅ **Protocolo correcto**: Implementa MCP correctamente
❌ **Nodo MCP Client**: NO funciona para conexiones remotas
✅ **HTTP Request**: Solución correcta para llamar a tu MCP server desde N8N

**Próximos pasos**:
1. Crear workflow en N8N con nodos HTTP Request
2. Seguir el flujo: Initialize → List Tools (opcional) → Call Tool
3. Parsear respuestas con nodos Code
4. Procesar emails según tus necesidades
