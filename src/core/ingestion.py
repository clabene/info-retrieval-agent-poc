"""Document ingestion pipeline — loading, chunking, embedding, storage."""

import logging
from pathlib import Path

import trafilatura
from llama_index.core import Document, SimpleDirectoryReader

logger = logging.getLogger(__name__)


def load_pdf_documents(pdf_dir: str = "./data/pdfs") -> list[Document]:
    """Load PDF files from a directory as LlamaIndex Document objects.

    Args:
        pdf_dir: Path to directory containing PDF files.

    Returns:
        List of Document objects with metadata including source_type="pdf".
        Returns empty list if directory doesn't exist or contains no PDFs.
    """
    pdf_path = Path(pdf_dir)

    if not pdf_path.exists():
        logger.warning("PDF directory does not exist: %s", pdf_dir)
        return []

    if not any(pdf_path.glob("*.pdf")):
        logger.info("No PDF files found in: %s", pdf_dir)
        return []

    try:
        reader = SimpleDirectoryReader(
            input_dir=str(pdf_path),
            required_exts=[".pdf"],
            recursive=False,
        )
        documents = reader.load_data()
    except Exception as e:
        logger.warning("Error reading PDFs from %s: %s", pdf_dir, e)
        return []

    # Add source_type metadata to each document
    for doc in documents:
        doc.metadata["source_type"] = "pdf"

    pdf_count = len(list(pdf_path.glob("*.pdf")))
    logger.info("Loaded %d document(s) from %d PDF file(s) in %s", len(documents), pdf_count, pdf_dir)
    return documents


def load_web_documents(urls_file: str = "./data/urls.txt") -> list[Document]:
    """Load web pages from a URL list file via trafilatura.

    Args:
        urls_file: Path to text file with one URL per line.
                   Lines starting with '#' are treated as comments.

    Returns:
        List of Document objects with metadata including source_type="web".
        Returns empty list if file doesn't exist or has no valid URLs.
    """
    urls_path = Path(urls_file)

    if not urls_path.exists():
        logger.warning("URLs file does not exist: %s", urls_file)
        return []

    # Read URLs, skip comments and blank lines
    urls = [
        line.strip()
        for line in urls_path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if not urls:
        logger.info("No URLs found in: %s", urls_file)
        return []

    documents: list[Document] = []
    for url in urls:
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                logger.warning("Failed to fetch URL: %s", url)
                continue

            text = trafilatura.extract(downloaded, include_links=True)
            if not text:
                logger.warning("No extractable content from URL: %s", url)
                continue

            doc = Document(
                text=text,
                metadata={"source_url": url, "source_type": "web", "file_name": url},
            )
            documents.append(doc)
        except Exception as e:
            logger.warning("Error processing URL %s: %s", url, e)
            continue

    logger.info("Loaded %d document(s) from %d URL(s) in %s", len(documents), len(urls), urls_file)
    return documents


def run_ingestion_pipeline(documents: list[Document]) -> int:
    """Chunk, embed, and store documents in Qdrant.

    Uses SentenceSplitter(512, 50) for chunking, OpenAI embeddings for dense vectors,
    and fastembed BM25 for sparse vectors (handled by QdrantVectorStore with hybrid enabled).

    Args:
        documents: List of LlamaIndex Document objects to ingest.

    Returns:
        Number of nodes (chunks) stored.
    """
    if not documents:
        logger.info("No documents to ingest.")
        return 0

    from llama_index.core.ingestion import IngestionPipeline
    from llama_index.core.node_parser import SentenceSplitter

    from src.config.providers import get_embed_model, get_vector_store
    from src.core.vector_store import ensure_collection

    # Ensure Qdrant collection exists before ingestion
    ensure_collection()

    vector_store = get_vector_store()
    embed_model = get_embed_model()

    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(chunk_size=512, chunk_overlap=50),
            embed_model,
        ],
        vector_store=vector_store,
    )

    nodes = pipeline.run(documents=documents, show_progress=True, num_workers=1)
    logger.info("Ingested %d chunks into Qdrant.", len(nodes))
    return len(nodes)
