# Guía Completa: Implementación del MCP de Calendario en AION

## Índice
1. [Prerequisitos](#prerequisitos)
2. [Configuración en N8N](#configuración-en-n8n)
3. [Backend - Implementación del Tool](#backend)
4. [Configuración de Variables de Entorno](#variables-de-entorno)
5. [Frontend (No requiere cambios)](#frontend)
6. [Pruebas](#pruebas)
7. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisitos

Antes de comenzar, asegúrate de tener:
- ✅ N8N MCP Server de Gmail funcionando (ya lo tienes)
- ✅ Acceso a configurar un nuevo MCP Server en N8N para calendario
- ✅ Credenciales de OAuth para Google Calendar (o Microsoft si usas ese)

---

## 2. Configuración en N8N

### Paso 2.1: Crear el workflow MCP para Calendar en N8N

1. **Duplica el workflow de Gmail MCP Server** que ya tienes
2. **Renombra** el workflow a "Calendar MCP Server"
3. **Configura el nodo MCP Server Trigger:**
   - Cambia el path a `/mcp/calendar`
   - Mantén la misma autenticación (X-API-KEY)

4. **Reemplaza el nodo de Gmail** con un nodo de **Google Calendar** (o Microsoft Calendar)
5. **Configura las operaciones** que quieres exponer:
   - `list_events` - Listar eventos
   - `create_event` - Crear evento
   - `update_event` - Actualizar evento
   - `delete_event` - Eliminar evento
   - `search_events` - Buscar eventos

6. **Activa el workflow** y anota la URL del endpoint SSE

**URL esperada:** `https://n8n.davidbuitrago.dev/mcp/calendar/sse`

---

## 3. Backend - Implementación del Tool

### Paso 3.1: Crear el Calendar MCP Tool

Crea el archivo: `src/infrastructure/tools/calendar_mcp_tool.py`

```python
"""
Calendar MCP tool for accessing Google Calendar through N8N MCP server.
"""

from typing import Any

from src.config.settings import get_settings
from src.domain.entities.tool import BaseTool, ToolParameter
from src.infrastructure.mcp import MCPN8NClient
from src.shared.logging import LoggerMixin


class CalendarMCPTool(BaseTool, LoggerMixin):
    """
    Calendar tool using MCP (Model Context Protocol) via N8N.

    Communicates with N8N MCP server for all Calendar operations,
    eliminating the need for OAuth handling in AION.
    """

    def __init__(self, mcp_client: MCPN8NClient | None = None):
        """
        Initialize Calendar MCP tool.

        Args:
            mcp_client: MCP N8N client instance (optional, will create if not provided)
        """
        self.settings = get_settings()

        # Use provided client or create new one
        if mcp_client:
            self.mcp_client = mcp_client
        else:
            if not self.settings.mcp.is_calendar_configured:
                raise ValueError(
                    "Calendar MCP not configured. Set N8N_MCP_CALENDAR_BASE_URL and "
                    "N8N_MCP_HEADER_VALUE environment variables."
                )

            # Remove /sse suffix if present for N8N client
            base_url = self.settings.mcp.n8n_mcp_calendar_base_url.replace("/sse", "")

            self.mcp_client = MCPN8NClient(
                base_url=base_url,
                auth_header_name=self.settings.mcp.n8n_mcp_header_name,
                auth_header_value=self.settings.mcp.n8n_mcp_header_value,
            )

        self.logger.info("calendar_mcp_tool_initialized")

    @property
    def name(self) -> str:
        return "get_calendar_events"

    @property
    def description(self) -> str:
        return """Get calendar events from Google Calendar.
Use this tool when the user asks about:
- Their calendar or schedule
- Upcoming meetings or events
- What they have planned
- Free time or availability
- Specific events by date or time

Returns a list of calendar events with titles, times, locations, and attendees."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="calendar_id",
                type="string",
                description="Calendar ID to get events from (e.g., 'primary' for main calendar or email address)",
                required=True,
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of events to return (default: 10, max: 50)",
                required=False,
            ),
            ToolParameter(
                name="time_min",
                type="string",
                description="Lower bound (inclusive) for event's start time (ISO 8601 format, e.g., '2025-11-10T00:00:00Z')",
                required=False,
            ),
            ToolParameter(
                name="time_max",
                type="string",
                description="Upper bound (exclusive) for event's end time (ISO 8601 format)",
                required=False,
            ),
            ToolParameter(
                name="query",
                type="string",
                description="Free text search query to filter events",
                required=False,
            ),
        ]

    async def execute(self, **kwargs: Any) -> Any:
        """
        Get calendar events via MCP.

        Args:
            calendar_id: Calendar ID (default: 'primary')
            max_results: Maximum events to return (default 10)
            time_min: Start time filter (ISO 8601)
            time_max: End time filter (ISO 8601)
            query: Search query (optional)

        Returns:
            Dictionary with calendar events or error message

        Raises:
            ValueError: If required parameters are missing
            Exception: If MCP call fails
        """
        calendar_id = kwargs.get("calendar_id", "primary")
        max_results = int(kwargs.get("max_results", 10))
        time_min = kwargs.get("time_min")
        time_max = kwargs.get("time_max")
        query = kwargs.get("query")

        # Validate max_results
        max_results = min(max(max_results, 1), 50)

        self.logger.info(
            "calendar_mcp_getting_events",
            calendar_id=calendar_id,
            max_results=max_results,
            has_time_min=bool(time_min),
            has_time_max=bool(time_max),
            has_query=bool(query),
        )

        try:
            # Prepare arguments for MCP call
            # IMPORTANTE: Ajusta estos nombres según los parámetros que definas en N8N
            arguments = {
                "calendar_id": calendar_id,
                "max_results": max_results,
            }

            if time_min:
                arguments["time_min"] = time_min
            if time_max:
                arguments["time_max"] = time_max
            if query:
                arguments["query"] = query

            # Connect to MCP server and call tool
            async with self.mcp_client as client:
                result = await client.call_tool(
                    tool_name="list_events",  # Ajusta según el nombre en N8N
                    arguments=arguments,
                )

            # Process MCP response
            content = result.get("content", [])
            is_error = result.get("isError", False)

            if is_error:
                error_text = ""
                for item in content:
                    if item.get("type") == "text":
                        error_text += item.get("text", "")

                return {
                    "status": "error",
                    "error": error_text or "Unknown error from MCP server",
                    "events": [],
                }

            # Extract events from content
            events = []
            for item in content:
                if item.get("type") == "text":
                    text_content = item.get("text", "")
                    # Try to parse as JSON
                    try:
                        import json
                        parsed = json.loads(text_content)
                        if isinstance(parsed, dict) and "events" in parsed:
                            events = parsed["events"]
                        elif isinstance(parsed, list):
                            events = parsed
                    except (json.JSONDecodeError, ValueError):
                        # If not JSON, treat as plain text response
                        pass

            self.logger.info(
                "calendar_mcp_events_retrieved",
                calendar_id=calendar_id,
                num_events=len(events),
            )

            return {
                "status": "success",
                "events": events,
                "calendar_id": calendar_id,
            }

        except Exception as e:
            error_msg = f"Failed to get Calendar events via MCP: {str(e)}"
            self.logger.error(
                "calendar_mcp_get_events_error",
                calendar_id=calendar_id,
                error=str(e),
            )

            return {
                "status": "error",
                "error": error_msg,
                "events": [],
            }

    async def create_event(
        self,
        calendar_id: str,
        summary: str,
        start_time: str,
        end_time: str,
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create a calendar event via MCP.

        Args:
            calendar_id: Calendar ID
            summary: Event title
            start_time: Start time (ISO 8601)
            end_time: End time (ISO 8601)
            description: Event description (optional)
            location: Event location (optional)
            attendees: List of attendee emails (optional)

        Returns:
            Dictionary with creation result
        """
        self.logger.info(
            "calendar_mcp_creating_event",
            calendar_id=calendar_id,
            summary=summary[:50],
        )

        try:
            arguments = {
                "calendar_id": calendar_id,
                "summary": summary,
                "start_time": start_time,
                "end_time": end_time,
            }

            if description:
                arguments["description"] = description
            if location:
                arguments["location"] = location
            if attendees:
                arguments["attendees"] = attendees

            # Connect to MCP server and call tool
            async with self.mcp_client as client:
                result = await client.call_tool(
                    tool_name="create_event",
                    arguments=arguments,
                )

            self.logger.info(
                "calendar_mcp_event_created",
                calendar_id=calendar_id,
                summary=summary,
            )

            return result

        except Exception as e:
            error_msg = f"Failed to create calendar event via MCP: {str(e)}"
            self.logger.error(
                "calendar_mcp_create_event_error",
                calendar_id=calendar_id,
                error=str(e),
            )

            return {
                "status": "error",
                "error": error_msg,
            }

    async def health_check(self) -> bool:
        """
        Check if Calendar MCP server is healthy.

        Returns:
            True if healthy, False otherwise
        """
        return await self.mcp_client.health_check()
```

### Paso 3.2: Actualizar Settings para Calendar

Edita: `src/config/settings.py`

Busca la sección de MCP settings y agrega:

```python
class MCPSettings(BaseSettings):
    """MCP-related settings."""

    # ... código existente para Gmail ...

    # Calendar MCP Server settings
    n8n_mcp_calendar_base_url: str = Field(
        default="",
        validation_alias=AliasChoices("N8N_MCP_CALENDAR_BASE_URL"),
    )

    @property
    def is_calendar_configured(self) -> bool:
        """Check if Calendar MCP is configured."""
        return bool(self.n8n_mcp_calendar_base_url and self.n8n_mcp_header_value)
```

### Paso 3.3: Registrar el Tool en el Sistema

Edita: `src/infrastructure/tools/__init__.py`

```python
from src.infrastructure.tools.calendar_mcp_tool import CalendarMCPTool
from src.infrastructure.tools.gmail_mcp_tool import GmailMCPTool
# ... otros imports ...

__all__ = [
    # ... otros tools ...
    "GmailMCPTool",
    "CalendarMCPTool",  # Agregar esta línea
]
```

### Paso 3.4: Registrar el Tool en las Dependencias de la API

Edita: `src/presentation/api/dependencies.py`

Busca la función que registra los tools y agrega:

```python
from src.infrastructure.tools import (
    # ... otros imports ...
    CalendarMCPTool,
    GmailMCPTool,
)

# En la función de registro de tools (probablemente get_tools o similar)
async def get_tools() -> list[BaseTool]:
    """Get all available tools."""
    tools = []

    # ... código existente ...

    # Calendar MCP Tool
    try:
        calendar_tool = CalendarMCPTool()
        tools.append(calendar_tool)
        logger.info("calendar_mcp_tool_registered")
    except Exception as e:
        logger.warning(
            "calendar_mcp_tool_not_configured",
            error=str(e),
        )

    return tools
```

---

## 4. Variables de Entorno

### Paso 4.1: Actualizar el archivo `.env`

Agrega las siguientes variables:

```bash
# Calendar MCP Configuration
N8N_MCP_CALENDAR_BASE_URL=https://n8n.davidbuitrago.dev/mcp/calendar/sse
N8N_MCP_HEADER_VALUE=tu_api_key_aqui  # La misma que usas para Gmail
```

### Paso 4.2: Actualizar docker-compose.yml (si usas Docker)

En la sección de `environment` del servicio `api`, agrega:

```yaml
services:
  api:
    environment:
      # ... variables existentes ...
      - N8N_MCP_CALENDAR_BASE_URL=${N8N_MCP_CALENDAR_BASE_URL}
```

---

## 5. Frontend

**¡Buenas noticias!** No necesitas hacer cambios en el frontend. El sistema de tools es completamente genérico y automáticamente:
- Detectará el nuevo tool `get_calendar_events`
- Lo usará cuando el usuario pregunte sobre calendario
- Mostrará los resultados en el chat

El LLM decidirá cuándo usar el tool basado en la descripción que le diste.

---

## 6. Pruebas

### Paso 6.1: Crear un script de prueba

Crea: `test_calendar_mcp.py` en la raíz del proyecto

```python
"""Test Calendar MCP integration."""
import asyncio
from src.infrastructure.tools.calendar_mcp_tool import CalendarMCPTool
from src.config.settings import get_settings


async def test():
    print("=" * 70)
    print("Calendar MCP Integration Test")
    print("=" * 70)

    settings = get_settings()

    print("\n1. Configuration:")
    print(f"   Base URL: {settings.mcp.n8n_mcp_calendar_base_url}")
    print(f"   Has Auth: {bool(settings.mcp.n8n_mcp_header_value)}")

    # Create Calendar MCP tool
    print("\n2. Creating Calendar MCP tool...")
    try:
        tool = CalendarMCPTool()
        print("   ✓ Tool created")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    # Test getting events
    print("\n3. Testing get_calendar_events...")
    try:
        result = await tool.execute(
            calendar_id="primary",
            max_results=10,
        )

        print(f"   Status: {result.get('status')}")
        events = result.get('events', [])
        print(f"   Found {len(events)} events")

        if events:
            print(f"\n   Sample event:")
            event = events[0]
            print(f"     Summary: {event.get('summary', 'N/A')}")
            print(f"     Start: {event.get('start', 'N/A')}")
            print(f"     End: {event.get('end', 'N/A')}")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test())
```

### Paso 6.2: Ejecutar las pruebas

```bash
# Rebuild el contenedor con los cambios
docker-compose build api

# Restart el servicio
docker-compose up -d api

# Espera a que el servicio esté listo
sleep 3

# Copia el script de prueba al contenedor
docker cp test_calendar_mcp.py aion_api:/app/

# Ejecuta la prueba
docker-compose exec -T api python /app/test_calendar_mcp.py
```

### Paso 6.3: Probar desde la UI

1. Abre http://localhost:5173
2. Haz una pregunta sobre tu calendario:
   - "¿Qué eventos tengo hoy?"
   - "Muéstrame mi calendario de esta semana"
   - "¿Tengo alguna reunión mañana?"

El sistema debería:
- Detectar que necesita el tool `get_calendar_events`
- Llamar al MCP server de N8N
- Mostrar los eventos en el chat

---

## 7. Troubleshooting

### Error: "Calendar MCP not configured"
**Solución:** Verifica que las variables de entorno estén correctamente configuradas:
```bash
docker-compose exec api printenv | grep CALENDAR
```

### Error: "Server not initialized"
**Solución:** Asegúrate de que:
- El workflow de Calendar MCP en N8N está activo
- La URL en `.env` es correcta (sin `/sse` al final en la variable)
- El cliente MCPN8NClient se está usando correctamente

### Error: "Failed to call tool 'list_events'"
**Solución:**
- Verifica que el nombre del tool en N8N coincida con el que usas en `call_tool()`
- Revisa los logs de N8N para ver qué está recibiendo
- Asegúrate de que los parámetros coincidan con lo que espera N8N

### Los eventos no se muestran correctamente
**Solución:**
- Revisa el formato de respuesta de N8N
- Ajusta el parsing en el método `execute()` según el formato real
- Usa `self.logger.info()` para debug

---

## Checklist Final

Antes de probar en producción, verifica:

- [ ] Workflow de Calendar MCP creado y activo en N8N
- [ ] URL del endpoint anotada
- [ ] Variables de entorno configuradas en `.env`
- [ ] Archivo `calendar_mcp_tool.py` creado
- [ ] Settings actualizado con configuración de calendar
- [ ] Tool registrado en `__init__.py`
- [ ] Tool registrado en `dependencies.py`
- [ ] Docker container rebuildeado
- [ ] Script de prueba ejecutado exitosamente
- [ ] Prueba manual desde la UI realizada

---

## Notas Importantes

1. **Nombres de herramientas en N8N:** Los nombres de las herramientas que uses en `call_tool()` deben coincidir EXACTAMENTE con los nombres definidos en tu workflow de N8N.

2. **Parámetros:** Ajusta los parámetros en el método `execute()` según lo que definas en N8N. Los nombres de los parámetros deben coincidir.

3. **Formato de respuesta:** El parsing de la respuesta depende de cómo N8N estructure los datos. Puede que necesites ajustar el código de parsing.

4. **Reutilización del cliente MCP:** El `MCPN8NClient` ya está implementado y maneja toda la comunicación con N8N, incluyendo:
   - Gestión de sesiones
   - Parsing de SSE
   - Manejo de errores

5. **Testing iterativo:** Usa los logs para ir ajustando el código según las respuestas reales de N8N.

---

## Lecciones Aprendidas del MCP de Gmail

Durante la implementación del MCP de Gmail, descubrimos estos puntos críticos que debes aplicar al Calendar MCP:

### 1. Gestión de Sesiones
- **Usar SOLO `Mcp-Session-Id` header** después de la inicialización
- NO incluir `sessionId` como parámetro de URL en requests posteriores al `initialize`
- El formato correcto es: `POST /messages` (sin `?sessionId=...`)

### 2. Protocolo de Inicialización
```
1. GET /sse → obtener sessionId
2. POST /messages?sessionId=X con "initialize" → obtener Mcp-Session-Id
3. POST /messages con Mcp-Session-Id header → llamadas a tools
```

### 3. Parsing de Respuestas SSE
Todas las respuestas de N8N vienen en formato SSE:
```
event: message
data: {"result": {...}}
```

Debes parsear con:
```python
if "data: " in response_text:
    data_line = [line for line in response_text.split("\n") if line.startswith("data: ")][0]
    json_str = data_line.replace("data: ", "")
    result = json.loads(json_str)
```

### 4. NO Enviar `notifications/initialized`
N8N no espera la notificación `notifications/initialized` del protocolo MCP estándar.

---

## Arquitectura de la Solución

```
┌─────────────────┐
│   Frontend UI   │
│  (React + TS)   │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│   AION API      │
│  (FastAPI)      │
└────────┬────────┘
         │ LLM decide usar tool
         ▼
┌─────────────────┐
│ CalendarMCPTool │
│  (Python)       │
└────────┬────────┘
         │ HTTP + MCP Protocol
         ▼
┌─────────────────┐
│ MCPN8NClient    │
│  (reusable)     │
└────────┬────────┘
         │ HTTP + SSE
         ▼
┌─────────────────┐
│  N8N Workflow   │
│ (MCP Trigger)   │
└────────┬────────┘
         │ OAuth 2.0
         ▼
┌─────────────────┐
│ Google Calendar │
│      API        │
└─────────────────┘
```

---

¿Listo para empezar? ¡Comienza por el **Paso 2** configurando el workflow en N8N!
