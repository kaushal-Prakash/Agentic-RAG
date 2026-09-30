import sys

from app.rag.ingestion import ingest_document


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m app.rag.ingest <file_path>")
        return
    file_path = sys.argv[1]
    print(f"Ingesting: {file_path}")
    ids = ingest_document(file_path)
    print(f"Successfully ingested {len(ids)} chunks.")
    print("Chunk IDs:")
    for document_id in ids:
        print(document_id)


if __name__ == "__main__":
    main()