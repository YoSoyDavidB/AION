"""
Migration script for system_prompts table.
Creates the table and initializes with default values.
"""

import asyncio

from sqlalchemy import text

from src.infrastructure.database.connection import DatabaseManager
from src.infrastructure.database.system_prompt_repository import SystemPromptRepository, SystemPromptModel
from src.shared.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


async def create_prompts_table():
    """Create system_prompts table if it doesn't exist."""
    db_manager = DatabaseManager()

    # SQL to create the table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS system_prompts (
        prompt_type VARCHAR(50) PRIMARY KEY,
        content TEXT NOT NULL,
        description VARCHAR(500) NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """

    try:
        async with db_manager.get_session() as session:
            await session.execute(text(create_table_sql))
            logger.info("system_prompts_table_created")
            print("✓ Table 'system_prompts' created successfully")

    except Exception as e:
        logger.error("create_table_failed", error=str(e))
        print(f"✗ Failed to create table: {e}")
        raise


async def initialize_prompts():
    """Initialize all prompts with default values."""
    repo = SystemPromptRepository()

    try:
        await repo.initialize_defaults()
        logger.info("default_prompts_initialized")
        print("✓ Default prompts initialized successfully")

    except Exception as e:
        logger.error("initialize_prompts_failed", error=str(e))
        print(f"✗ Failed to initialize prompts: {e}")
        raise


async def verify_prompts():
    """Verify that prompts were created correctly."""
    repo = SystemPromptRepository()

    try:
        prompts = await repo.get_all()
        print(f"\n✓ Verification: Found {len(prompts)} prompts in database:")
        for prompt in prompts:
            status = "✓" if prompt.is_active else "✗"
            print(f"  {status} {prompt.prompt_type.value}: {prompt.description}")

    except Exception as e:
        logger.error("verify_prompts_failed", error=str(e))
        print(f"✗ Failed to verify prompts: {e}")


async def main():
    """Run the migration."""
    print("=" * 60)
    print("AION - System Prompts Migration")
    print("=" * 60)
    print()

    print("Step 1: Creating system_prompts table...")
    await create_prompts_table()

    print("\nStep 2: Initializing default prompts...")
    await initialize_prompts()

    print("\nStep 3: Verifying prompts...")
    await verify_prompts()

    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
