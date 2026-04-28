"""CLI entry point for document ingestion."""

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the full ingestion pipeline: load PDFs + web pages, chunk, embed, store."""
    from src.config.settings import get_settings

    # Validate configuration early
    try:
        get_settings()
    except Exception as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)

    from src.core.ingestion import load_pdf_documents, load_web_documents, run_ingestion_pipeline

    # Load documents from both sources
    logger.info("Loading PDF documents...")
    pdf_docs = load_pdf_documents()

    logger.info("Loading web documents...")
    web_docs = load_web_documents()

    all_docs = pdf_docs + web_docs

    if not all_docs:
        logger.warning("No documents found to ingest. Add PDFs to ./data/pdfs/ or URLs to ./data/urls.txt")
        sys.exit(0)

    logger.info("Total documents loaded: %d (%d from PDFs, %d from web)", len(all_docs), len(pdf_docs), len(web_docs))

    # Run ingestion pipeline
    chunks_stored = run_ingestion_pipeline(all_docs)
    logger.info("Ingestion complete. %d chunks stored in Qdrant.", chunks_stored)


if __name__ == "__main__":
    main()
