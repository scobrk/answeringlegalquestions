"""
RAGflow Document Chunking Pipeline
Data Engineering Agent Implementation (KAN-3)
"""

import json
import requests
from typing import List, Dict, Optional, Iterator
from dataclasses import dataclass
import time
import logging
from pathlib import Path

from huggingface_connector import LegalDocument
from nsw_filter import NSWLegislationMetadata

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunked piece of legal document"""
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    token_count: int
    section_context: Optional[str] = None
    metadata: Optional[Dict] = None
    overlap_start: int = 0
    overlap_end: int = 0


class RAGflowClient:
    """
    Client for RAGflow document processing service
    Handles document upload, processing, and chunk retrieval
    """

    def __init__(self, ragflow_url: str = "http://localhost:8080"):
        self.base_url = ragflow_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/v1"
        self.session = requests.Session()

        # Legal document template configuration
        self.legal_template_config = {
            "chunk_size": 512,  # tokens (from KAN-3)
            "overlap": 50,      # tokens (from KAN-3)
            "preserve_structure": True,
            "include_headers": True,
            "legal_mode": True
        }

    def health_check(self) -> bool:
        """
        Check if RAGflow service is available

        Returns:
            True if service is healthy
        """
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"RAGflow health check failed: {e}")
            return False

    def create_knowledge_base(self, name: str, description: str = "") -> str:
        """
        Create a knowledge base for NSW legislation

        Args:
            name: Knowledge base name
            description: Description

        Returns:
            Knowledge base ID
        """
        payload = {
            "name": name,
            "description": description,
            "language": "English",
            "chunk_method": "manual",  # We'll use custom chunking
            "parser_config": self.legal_template_config
        }

        try:
            response = self.session.post(
                f"{self.api_url}/knowledge_bases",
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            kb_id = result.get("id")
            logger.info(f"Created knowledge base: {name} (ID: {kb_id})")
            return kb_id

        except Exception as e:
            logger.error(f"Failed to create knowledge base: {e}")
            raise

    def upload_document(self, kb_id: str, document: LegalDocument) -> str:
        """
        Upload legal document to RAGflow

        Args:
            kb_id: Knowledge base ID
            document: LegalDocument to upload

        Returns:
            Document ID in RAGflow
        """
        # Prepare document for upload
        doc_data = {
            "name": f"{document.act_name}_{document.id}",
            "content": document.content,
            "metadata": {
                "act_name": document.act_name,
                "year": document.year,
                "jurisdiction": document.jurisdiction,
                "document_type": document.document_type,
                "original_title": document.title
            }
        }

        try:
            response = self.session.post(
                f"{self.api_url}/knowledge_bases/{kb_id}/documents",
                json=doc_data,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            doc_id = result.get("id")
            logger.info(f"Uploaded document: {document.title} (ID: {doc_id})")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to upload document {document.title}: {e}")
            raise

    def wait_for_processing(self, kb_id: str, doc_id: str, timeout: int = 300) -> bool:
        """
        Wait for document processing to complete

        Args:
            kb_id: Knowledge base ID
            doc_id: Document ID
            timeout: Maximum wait time in seconds

        Returns:
            True if processing completed successfully
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = self.session.get(
                    f"{self.api_url}/knowledge_bases/{kb_id}/documents/{doc_id}/status",
                    timeout=10
                )
                response.raise_for_status()

                status = response.json().get("status")
                logger.debug(f"Document {doc_id} status: {status}")

                if status == "completed":
                    logger.info(f"Document {doc_id} processing completed")
                    return True
                elif status == "failed":
                    logger.error(f"Document {doc_id} processing failed")
                    return False

                time.sleep(5)  # Wait 5 seconds before checking again

            except Exception as e:
                logger.warning(f"Status check failed: {e}")
                time.sleep(5)

        logger.error(f"Document {doc_id} processing timeout")
        return False

    def get_document_chunks(self, kb_id: str, doc_id: str) -> List[DocumentChunk]:
        """
        Retrieve processed chunks from RAGflow

        Args:
            kb_id: Knowledge base ID
            doc_id: Document ID

        Returns:
            List of DocumentChunk objects
        """
        try:
            response = self.session.get(
                f"{self.api_url}/knowledge_bases/{kb_id}/documents/{doc_id}/chunks",
                timeout=30
            )
            response.raise_for_status()

            chunks_data = response.json().get("chunks", [])
            chunks = []

            for i, chunk_data in enumerate(chunks_data):
                chunk = DocumentChunk(
                    chunk_id=chunk_data.get("id", f"{doc_id}_chunk_{i}"),
                    document_id=doc_id,
                    content=chunk_data.get("content", ""),
                    chunk_index=i,
                    token_count=chunk_data.get("token_count", 0),
                    section_context=chunk_data.get("section_context"),
                    metadata=chunk_data.get("metadata", {}),
                    overlap_start=chunk_data.get("overlap_start", 0),
                    overlap_end=chunk_data.get("overlap_end", 0)
                )
                chunks.append(chunk)

            logger.info(f"Retrieved {len(chunks)} chunks for document {doc_id}")
            return chunks

        except Exception as e:
            logger.error(f"Failed to get chunks for document {doc_id}: {e}")
            raise


class LegalDocumentProcessor:
    """
    High-level processor that coordinates RAGflow with NSW filtering
    Implements the complete KAN-3 processing pipeline
    """

    def __init__(self, ragflow_url: str = "http://localhost:8080"):
        self.ragflow_client = RAGflowClient(ragflow_url)
        self.kb_id = None

    def initialize_knowledge_base(self, name: str = "NSW_Revenue_Legislation") -> str:
        """
        Initialize knowledge base for NSW legislation

        Args:
            name: Knowledge base name

        Returns:
            Knowledge base ID
        """
        if not self.ragflow_client.health_check():
            raise RuntimeError("RAGflow service is not available")

        self.kb_id = self.ragflow_client.create_knowledge_base(
            name=name,
            description="NSW Revenue legislation processed for AI assistant"
        )

        return self.kb_id

    def process_document_batch(self, documents: List[LegalDocument]) -> Dict[str, List[DocumentChunk]]:
        """
        Process a batch of legal documents through RAGflow

        Args:
            documents: List of LegalDocument objects

        Returns:
            Dictionary mapping document IDs to their chunks
        """
        if not self.kb_id:
            raise RuntimeError("Knowledge base not initialized")

        results = {}

        for doc in documents:
            try:
                logger.info(f"Processing document: {doc.title}")

                # Upload document
                doc_id = self.ragflow_client.upload_document(self.kb_id, doc)

                # Wait for processing
                if self.ragflow_client.wait_for_processing(self.kb_id, doc_id):
                    # Retrieve chunks
                    chunks = self.ragflow_client.get_document_chunks(self.kb_id, doc_id)
                    results[doc.id] = chunks

                    logger.info(f"Successfully processed {doc.title}: {len(chunks)} chunks")
                else:
                    logger.error(f"Failed to process document: {doc.title}")

            except Exception as e:
                logger.error(f"Error processing document {doc.title}: {e}")
                continue

        return results

    def validate_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Validate chunk quality according to KAN-3 requirements

        Args:
            chunks: List of DocumentChunk objects

        Returns:
            List of validated chunks
        """
        valid_chunks = []

        for chunk in chunks:
            # Check minimum content length
            if len(chunk.content.strip()) < 50:
                logger.warning(f"Chunk {chunk.chunk_id} too short: {len(chunk.content)} chars")
                continue

            # Check token count within expected range
            if chunk.token_count < 100 or chunk.token_count > 600:
                logger.warning(f"Chunk {chunk.chunk_id} unusual token count: {chunk.token_count}")

            # Check for legal structure preservation
            if not any(keyword in chunk.content.lower() for keyword in
                      ["section", "subsection", "act", "regulation"]):
                logger.warning(f"Chunk {chunk.chunk_id} may not preserve legal structure")

            valid_chunks.append(chunk)

        logger.info(f"Validated {len(valid_chunks)} out of {len(chunks)} chunks")
        return valid_chunks

    def save_processed_chunks(self, chunks_by_doc: Dict[str, List[DocumentChunk]],
                            output_file: str = "processed_chunks.json"):
        """
        Save processed chunks to file

        Args:
            chunks_by_doc: Dictionary of chunks by document ID
            output_file: Output filename
        """
        output_data = {}

        for doc_id, chunks in chunks_by_doc.items():
            output_data[doc_id] = []
            for chunk in chunks:
                output_data[doc_id].append({
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "token_count": chunk.token_count,
                    "section_context": chunk.section_context,
                    "metadata": chunk.metadata,
                    "overlap_start": chunk.overlap_start,
                    "overlap_end": chunk.overlap_end
                })

        output_path = Path("./data/cache") / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved processed chunks to {output_path}")


def main():
    """
    Test the RAGflow processor
    """
    processor = LegalDocumentProcessor()

    # Initialize knowledge base
    kb_id = processor.initialize_knowledge_base()

    # Create test document
    test_doc = LegalDocument(
        id="test_1",
        title="Duties Act 1997 NSW - Test Section",
        content="""
        Section 31 of the Duties Act 1997 provides for the calculation of stamp duty on dutiable transactions.

        (1) The duty on a dutiable transaction is calculated at the rate specified in Schedule 1.

        (2) For residential property transactions over $1,000,000, the rate is 5.5 percent.

        (3) First home buyers may be eligible for exemptions under section 31A.
        """,
        jurisdiction="NSW",
        document_type="legislation",
        act_name="Duties Act 1997"
    )

    # Process single document
    result = processor.process_document_batch([test_doc])

    if result:
        for doc_id, chunks in result.items():
            validated_chunks = processor.validate_chunks(chunks)
            print(f"Document {doc_id}: {len(validated_chunks)} valid chunks")

            for chunk in validated_chunks[:2]:  # Show first 2 chunks
                print(f"\nChunk {chunk.chunk_index}:")
                print(f"Content: {chunk.content[:200]}...")
                print(f"Tokens: {chunk.token_count}")

        processor.save_processed_chunks(result)


if __name__ == "__main__":
    main()