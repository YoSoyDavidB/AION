# Prompt Management System

Sistema de gestión de prompts del sistema AION que permite personalizar el comportamiento de la IA a través de la interfaz de usuario.

## 📋 Descripción General

El sistema de gestión de prompts permite a los usuarios modificar y personalizar los prompts que controlan el comportamiento de AION en diferentes contextos, sin necesidad de modificar código.

## 🎯 Tipos de Prompts

El sistema gestiona 8 tipos diferentes de prompts:

### 1. **Main Assistant** (`main_assistant`)
Prompt principal que define el comportamiento general del asistente, sus capacidades y guías de interacción.

### 2. **Memory Extraction** (`memory_extraction`)
Controla cómo AION extrae y clasifica información importante de las conversaciones para almacenar en memoria a largo plazo.

### 3. **Summarization** (`summarization`)
Define cómo se resumen conversaciones y documentos, enfocándose en puntos clave y decisiones.

### 4. **Intent Classification** (`intent_classification`)
Controla la clasificación de mensajes del usuario en categorías (pregunta, comando, chitchat, tarea, búsqueda).

### 5. **Entity Description** (`entity_description`)
Genera descripciones concisas para entidades identificadas en el texto.

### 6. **Entity Extraction** (`entity_extraction`)
Extrae entidades nombradas del texto (personas, organizaciones, ubicaciones, proyectos, conceptos, tecnologías).

### 7. **Relationship Extraction** (`relationship_extraction`)
Identifica y extrae relaciones entre entidades del texto.

### 8. **RAG System** (`rag_system`)
Controla el comportamiento del sistema de Retrieval-Augmented Generation para responder preguntas usando la base de conocimiento.

## 🏗️ Arquitectura

### Backend (Python/FastAPI)

```
src/
├── domain/entities/system_prompt.py        # Entidad de dominio
├── infrastructure/
│   ├── database/
│   │   └── system_prompt_repository.py     # Repositorio PostgreSQL
│   └── llm/
│       ├── prompt_service.py                # Servicio con caché
│       └── llm_service.py                   # Integración LLM
└── presentation/api/routes/prompts.py       # Endpoints REST
```

### Frontend (React/TypeScript)

```
frontend/src/
├── lib/api/prompts.ts                       # Cliente API
└── pages/Prompts.tsx                        # Interfaz de usuario
```

### Base de Datos

```sql
CREATE TABLE system_prompts (
    prompt_type VARCHAR(50) PRIMARY KEY,
    content TEXT NOT NULL,
    description VARCHAR(500) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## 🔌 API Endpoints

### Listar todos los prompts
```http
GET /api/v1/prompts
```

**Respuesta:**
```json
{
  "prompts": [
    {
      "prompt_type": "main_assistant",
      "content": "You are AION...",
      "description": "Main assistant prompt",
      "is_active": true,
      "created_at": "2025-11-09T17:08:26.421500",
      "updated_at": "2025-11-09T17:08:26.421503"
    }
  ],
  "total": 8
}
```

### Obtener un prompt específico
```http
GET /api/v1/prompts/{prompt_type}
```

### Actualizar un prompt
```http
PUT /api/v1/prompts/{prompt_type}
Content-Type: application/json

{
  "content": "Your updated prompt content...",
  "description": "Optional description"
}
```

### Resetear a valor por defecto
```http
POST /api/v1/prompts/{prompt_type}/reset
```

### Inicializar todos los prompts
```http
POST /api/v1/prompts/initialize-defaults
```

## 💻 Uso desde la UI

1. Navega a http://localhost:5174/prompts
2. Verás la lista de 8 prompts con iconos de colores
3. Haz clic en "Edit" para modificar un prompt
4. Edita el contenido y/o descripción
5. Haz clic en "Save Changes"
6. Usa el botón de reset (↻) para restaurar el valor por defecto

## 🔧 Características Técnicas

### Caché en Memoria
El `PromptService` implementa un sistema de caché en memoria para optimizar el rendimiento:

```python
async def get_prompt(self, prompt_type: PromptType) -> str:
    # Check cache first
    cache_key = f"prompt_{prompt_type.value}"
    if cache_key in self._cache:
        return self._cache[cache_key]

    # Fetch from DB and cache
    prompt = await self.repository.get(prompt_type)
    self._cache[cache_key] = prompt.content
    return prompt.content
```

### Fallback Automático
Si hay un error al obtener un prompt de la base de datos, el sistema automáticamente usa el valor por defecto:

```python
except Exception as e:
    self.logger.warning("prompt_fetch_failed_using_default", ...)
    default = self._get_default_prompt(prompt_type)
    self._cache[cache_key] = default
    return default
```

### Valores Por Defecto
Todos los prompts tienen valores por defecto definidos en el código, garantizando que el sistema siempre funcione aunque la base de datos esté vacía.

## 📦 Migración

Para inicializar la tabla y los prompts por defecto:

```bash
poetry run python scripts/migrate_prompts.py
```

El script:
1. Crea la tabla `system_prompts` si no existe
2. Inicializa los 8 prompts con valores por defecto
3. Verifica la creación exitosa

## 🎨 Interfaz de Usuario

La página de prompts incluye:
- **Lista visual**: Muestra todos los prompts con iconos de colores
- **Edición inline**: Textarea expandible para editar contenido
- **Gestión de descripción**: Campo para actualizar descripciones
- **Reset individual**: Botón para resetear cada prompt
- **Feedback visual**: Mensajes de éxito/error con animaciones
- **Estados de carga**: Indicadores mientras se procesan operaciones

## 🔒 Seguridad

- Los prompts son críticos para el comportamiento del sistema
- Solo usuarios autorizados deberían poder modificarlos
- Los cambios se registran con timestamps
- Se mantiene historial implícito a través de updated_at

## 🚀 Casos de Uso

### Personalizar comportamiento del asistente
Modifica el `main_assistant` prompt para cambiar personalidad, tono o capacidades.

### Ajustar extracción de memorias
Edita `memory_extraction` para cambiar qué tipo de información se guarda.

### Mejorar resúmenes
Personaliza `summarization` para enfocar resúmenes en aspectos específicos.

### Optimizar RAG
Ajusta `rag_system` para mejorar respuestas basadas en conocimiento.

## 📊 Estado Actual

- ✅ Backend completo implementado
- ✅ API REST funcional
- ✅ Interfaz de usuario operativa
- ✅ Sistema de caché implementado
- ✅ Fallback a valores por defecto
- ✅ Migración de base de datos
- ✅ Integración con LLMService

## 🔮 Próximas Mejoras

- [ ] Historial de cambios en prompts
- [ ] Versioning de prompts
- [ ] Templates de prompts comunes
- [ ] Exportar/Importar prompts
- [ ] A/B testing de prompts
- [ ] Métricas de efectividad por prompt
