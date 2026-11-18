"""One-shot build: ingest + chunk the corpus and build the hybrid index."""
from . import ingest, index


def main():
    chunks = ingest.run()
    print(f"chunks: {len(chunks)}")
    idx, chunks = index.build()
    print(f"index built: {len(chunks)} chunks, "
          f"{len(idx.vectorizer.vocabulary_)} n-gram features")


if __name__ == "__main__":
    main()
