# Obsidian Sync Agent

El agente de sincronización de Obsidian permite integrar automáticamente tu vault de Obsidian con la base de conocimiento de AION.

## Características

- **Sincronización automática** de archivos Markdown desde tu vault de Obsidian
- **Extracción de metadatos** desde YAML frontmatter (título, tags)
- **Detección de cambios** usando hashes SHA256 para evitar sincronizaciones innecesarias
- **Tracking de estado** con SQLite para mantener el historial de sincronización
- **Limpieza automática** de archivos eliminados del vault
- **Soporte para tags** tanto en frontmatter como inline (#tag)

## Configuración

### 1. Configurar la ruta del vault

Edita el archivo `.env` y configura la ruta a tu vault de Obsidian:

```bash
# GitHub Configuration (Obsidian Vault Sync)
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault
```

Ejemplo en macOS/Linux:
```bash
OBSIDIAN_VAULT_PATH=/Users/david/Documents/Obsidian/MyVault
```

Ejemplo en Windows:
```bash
OBSIDIAN_VAULT_PATH=C:/Users/david/Documents/Obsidian/MyVault
```

### 2. Carpetas excluidas

Por defecto, el agente excluye estas carpetas:
- `.obsidian` - Configuración de Obsidian
- `.git` - Control de versiones
- `.trash` - Papelera de Obsidian
- `templates` - Templates de Obsidian

Puedes modificar la lista de carpetas excluidas al crear el agente.

## Uso

### Opción 1: API REST

#### Sincronizar vault

```bash
POST /api/v1/obsidian/sync
Content-Type: application/json

{
  "user_id": "david",
  "force": false
}
```

Parámetros:
- `user_id`: ID del usuario
- `force`: Si es `true`, fuerza la sincronización de todos los archivos (ignora el estado previo)

Respuesta:
```json
{
  "total_files": 50,
  "synced": 45,
  "failed": 0,
  "skipped": 5,
  "vault_path": "/path/to/vault"
}
```

#### Obtener estado de sincronización

```bash
GET /api/v1/obsidian/status?user_id=david
```

Respuesta:
```json
{
  "vault_path": "/path/to/vault",
  "vault_configured": true,
  "total_synced_files": 45
}
```

#### Limpiar archivos eliminados

```bash
POST /api/v1/obsidian/cleanup?user_id=david
```

Respuesta:
```json
{
  "cleaned_files": 3
}
```

### Opción 2: Script de prueba

Ejecuta el script de prueba para sincronizar archivos de ejemplo:

```bash
poetry run python test_obsidian_sync.py
```

Este script:
1. Crea un vault de prueba en `./obsidian_vault`
2. Genera 3 archivos Markdown de ejemplo
3. Ejecuta la sincronización
4. Muestra un resumen de los resultados

### Opción 3: Uso programático

```python
from src.application.agents.obsidian_sync_agent import ObsidianSyncAgent
from src.application.use_cases.document_use_cases import (
    UploadDocumentUseCase,
    DeleteDocumentUseCase,
)
from src.infrastructure.vector_store.document_repository_impl import (
    QdrantDocumentRepository,
)

# Inicializar dependencias
doc_repo = QdrantDocumentRepository()
upload_use_case = UploadDocumentUseCase(document_repo=doc_repo)
delete_use_case = DeleteDocumentUseCase(document_repo=doc_repo)

# Crear agente
agent = ObsidianSyncAgent(
    vault_path="/path/to/vault",
    user_id="david",
    upload_use_case=upload_use_case,
    delete_use_case=delete_use_case,
)

# Sincronizar
summary = await agent.sync_vault()
print(f"Synced {summary['synced']} files!")

# Limpiar archivos eliminados
cleaned = await agent.cleanup_deleted_files()
print(f"Cleaned {cleaned} deleted files")
```

## Formato de archivos soportado

El agente extrae metadatos del YAML frontmatter:

```markdown
---
title: Mi Documento
tags: [proyecto, desarrollo, ia]
date: 2025-01-09
---

# Contenido del documento

También puedes usar tags inline: #importante #revisar

El contenido completo del documento se indexa para búsqueda semántica.
```

### Extracción de título

El agente intenta obtener el título en este orden:
1. Campo `title` en frontmatter
2. Primer encabezado H1 (`# Título`)
3. Nombre del archivo (sin extensión)

### Extracción de tags

- Tags en frontmatter: `tags: [tag1, tag2]` o `tags: tag1, tag2`
- Tags inline: `#tag1 #tag2`
- Los tags que empiezan con `obsidian` se excluyen automáticamente

## Estado de sincronización

El agente mantiene una base de datos SQLite en `data/sync_state.db` con:

- Ruta del archivo
- Hash del contenido (SHA256)
- Última modificación
- Última sincronización
- Estado (pending, synced, failed, deleted)
- ID del documento en AION
- Mensaje de error (si falló)

Esto permite:
- **Sincronización incremental**: Solo se procesan archivos nuevos o modificados
- **Detección de eliminaciones**: Se eliminan documentos de archivos borrados del vault
- **Reintento de errores**: Archivos con estado `failed` se reintentan en la próxima sincronización

## Sincronización automática

Para configurar sincronización automática periódica, puedes:

### 1. Usar cron (Linux/macOS)

```bash
# Sincronizar cada hora
0 * * * * cd /path/to/AION && poetry run python -c "import asyncio; from test_obsidian_sync import test_sync; asyncio.run(test_sync())"
```

### 2. Usar Task Scheduler (Windows)

Crea una tarea programada que ejecute:
```
poetry run python test_obsidian_sync.py
```

### 3. Implementar un worker en background

Agrega un worker a tu aplicación que ejecute la sincronización periódicamente:

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def sync_obsidian_job():
    """Job para sincronizar Obsidian periódicamente."""
    agent = ObsidianSyncAgent(...)
    await agent.sync_vault()

# Ejecutar cada hora
scheduler.add_job(sync_obsidian_job, 'interval', hours=1)
scheduler.start()
```

## Solución de problemas

### Error: "Vault path does not exist"

Verifica que la ruta en `OBSIDIAN_VAULT_PATH` existe y es correcta.

### Error: "Obsidian vault path not configured"

Configura `OBSIDIAN_VAULT_PATH` en el archivo `.env`.

### Archivos no se sincronizan

1. Verifica que no estén en carpetas excluidas (`.obsidian`, `.git`, etc.)
2. Revisa los logs para ver errores específicos
3. Intenta forzar la sincronización con `force: true`

### Duplicados en la base de conocimiento

El sistema usa el estado de sincronización para evitar duplicados. Si ocurren duplicados:
1. Limpia la base de datos de sync state: `rm data/sync_state.db`
2. Elimina documentos duplicados manualmente
3. Vuelve a sincronizar

## Seguridad

- Los archivos se leen localmente, no se envían a servicios externos
- Los embeddings se generan usando OpenRouter (configurado en `.env`)
- Los vectores se almacenan localmente en Qdrant
- No se modifica el vault de Obsidian (solo lectura)

## Próximas mejoras

- [ ] Sincronización bidireccional (AION → Obsidian)
- [ ] Soporte para archivos adjuntos e imágenes
- [ ] Resolución de conflictos
- [ ] Sincronización selectiva (solo carpetas específicas)
- [ ] Webhooks para notificar cambios
- [ ] Interfaz gráfica para configuración
