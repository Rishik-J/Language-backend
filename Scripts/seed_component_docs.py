#!/usr/bin/env python3
# Scripts/seed_component_docs.py

"""
Scripts/seed_component_docs.py

Seed component documentation Markdown files and component templates (JSON) into Chroma DB.
"""
import os
import uuid
import asyncio
import logging
import json

# Import from your top‐level memory/ directory
from memory.vector_store import vector_store

# Point these at your actual folders
DOCS_DIR = os.getenv(
    "COMPONENT_DOCS_DIR",
    "docs"
)

TEMPLATES_DIR = os.getenv(
    "COMPONENT_TEMPLATES_DIR",
    "component_categories"
)

async def seed_docs():
    """Seed component documentation (MD files) into vector store."""
    logging.info("Seeding component documentation...")
    
    for fname in os.listdir(DOCS_DIR):
        if not fname.lower().endswith(".md"):
            continue

        path = os.path.join(DOCS_DIR, fname)
        with open(path, encoding="utf-8") as f:
            content = f.read()

        component_name = os.path.splitext(fname)[0]
        chunk_id = f"doc-{component_name}-{uuid.uuid4().hex[:8]}"

        await vector_store.add_doc_chunk(
            chunk_id=chunk_id,
            document=content,
            component=component_name,
            doc_type="md",
            metadata={"content_type": "documentation"}
        )
        logging.info(f"Seeded documentation '{chunk_id}' for component '{component_name}'")

async def seed_templates():
    """Seed component templates (JSON files) into vector store."""
    logging.info("Seeding component templates...")
    
    for fname in os.listdir(TEMPLATES_DIR):
        if not fname.lower().endswith(".json"):
            continue

        path = os.path.join(TEMPLATES_DIR, fname)
        
        try:
            with open(path, encoding="utf-8") as f:
                templates_dict = json.load(f)
            
            category_name = os.path.splitext(fname)[0]
            
            # Each JSON file contains multiple component templates
            for component_name, template_data in templates_dict.items():
                # Convert template to string for storage
                template_str = json.dumps(template_data, indent=2)
                chunk_id = f"template-{category_name}-{component_name}-{uuid.uuid4().hex[:8]}"
                
                await vector_store.add_doc_chunk(
                    chunk_id=chunk_id,
                    document=template_str,
                    component=component_name,
                    doc_type="json",
                    metadata={
                        "content_type": "template",
                        "category": category_name
                    }
                )
                logging.info(f"Seeded template '{chunk_id}' for component '{component_name}' in category '{category_name}'")
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON in {fname}: {e}")
        except Exception as e:
            logging.error(f"Error processing template {fname}: {e}")

async def main():
    # 1) Connect
    await vector_store.initialize()
    logging.info("Chroma DB initialized for seeding component docs and templates.")

    # 2) Seed documentation
    await seed_docs()
    
    # 3) Seed templates
    await seed_templates()
    
    logging.info("Seeding complete!")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    asyncio.run(main())
