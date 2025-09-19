"""
Hugging Face Dataset Connector for NSW Legal Corpus
Data Engineering Agent Implementation (KAN-3)
"""

import os
import json
from typing import List, Dict, Iterator, Optional
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import requests
from datasets import load_dataset, Dataset
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LegalDocument:
    """Structure for legal document metadata"""
    id: str
    title: str
    content: str
    jurisdiction: str
    document_type: str
    act_name: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    metadata: Optional[Dict] = None


class HuggingFaceConnector:
    """
    Connects to the Australian Legal Corpus dataset
    Applies NSW-specific filtering for Revenue legislation
    """

    def __init__(self, cache_dir: str = "./data/cache"):
        self.dataset_name = "isaacus/open-australian-legal-corpus"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # NSW Revenue-specific legislation patterns
        self.nsw_revenue_patterns = [
            "duties act",
            "payroll tax act",
            "land tax act",
            "land tax management act",
            "revenue administration act",
            "stamp duties act",
            "taxation administration act",
            "fines act",
            "penalty notices enforcement act"
        ]

        # NSW jurisdiction identifiers
        self.nsw_identifiers = [
            "nsw",
            "new south wales",
            "NSW Caselaw",
            "NSW Legislation"
        ]

    def load_dataset(self, streaming: bool = True) -> Dataset:
        """
        Load the Australian Legal Corpus dataset

        Args:
            streaming: Use streaming mode for large dataset (recommended)

        Returns:
            Dataset object
        """
        try:
            logger.info(f"Loading dataset: {self.dataset_name}")

            if streaming:
                dataset = load_dataset(
                    self.dataset_name,
                    streaming=True,
                    trust_remote_code=True
                )
                logger.info("Dataset loaded in streaming mode")
                return dataset
            else:
                dataset = load_dataset(
                    self.dataset_name,
                    cache_dir=self.cache_dir,
                    trust_remote_code=True
                )
                logger.info(f"Dataset loaded with {len(dataset)} records")
                return dataset

        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise

    def is_nsw_document(self, document: Dict) -> bool:
        """
        Check if document is NSW jurisdiction

        Args:
            document: Document dictionary from dataset

        Returns:
            True if document is NSW-related
        """
        text_content = str(document.get('text', '')).lower()
        title = str(document.get('title', '')).lower()

        # Check for NSW identifiers
        for identifier in self.nsw_identifiers:
            if identifier.lower() in text_content or identifier.lower() in title:
                return True

        return False

    def is_revenue_legislation(self, document: Dict) -> bool:
        """
        Check if document is revenue-related legislation

        Args:
            document: Document dictionary from dataset

        Returns:
            True if document relates to revenue/taxation
        """
        text_content = str(document.get('text', '')).lower()
        title = str(document.get('title', '')).lower()

        # Check for revenue legislation patterns
        for pattern in self.nsw_revenue_patterns:
            if pattern in text_content or pattern in title:
                return True

        return False

    def extract_act_metadata(self, document: Dict) -> Dict:
        """
        Extract act metadata from document

        Args:
            document: Document dictionary

        Returns:
            Metadata dictionary
        """
        text = str(document.get('text', ''))
        title = str(document.get('title', ''))

        metadata = {
            'original_title': title,
            'source': document.get('source', 'unknown'),
            'jurisdiction': 'NSW',
            'document_type': 'legislation'
        }

        # Extract year if present in title
        import re
        year_match = re.search(r'(\d{4})', title)
        if year_match:
            metadata['year'] = int(year_match.group(1))

        # Extract act name
        for pattern in self.nsw_revenue_patterns:
            if pattern in title.lower():
                metadata['act_name'] = pattern.title()
                break

        return metadata

    def filter_nsw_revenue_documents(self, dataset: Dataset, max_documents: int = 1000) -> Iterator[LegalDocument]:
        """
        Filter dataset for NSW revenue documents

        Args:
            dataset: Hugging Face dataset
            max_documents: Maximum documents to process (for free tier)

        Yields:
            LegalDocument objects for NSW revenue legislation
        """
        logger.info("Starting NSW revenue document filtering...")

        processed_count = 0
        filtered_count = 0

        try:
            for document in dataset:
                processed_count += 1

                # Check if NSW and revenue-related
                if self.is_nsw_document(document) and self.is_revenue_legislation(document):
                    metadata = self.extract_act_metadata(document)

                    legal_doc = LegalDocument(
                        id=str(filtered_count),
                        title=document.get('title', f"Document {filtered_count}"),
                        content=document.get('text', ''),
                        jurisdiction='NSW',
                        document_type='legislation',
                        act_name=metadata.get('act_name'),
                        year=metadata.get('year'),
                        metadata=metadata
                    )

                    filtered_count += 1
                    logger.info(f"Found NSW revenue document {filtered_count}: {legal_doc.title}")

                    yield legal_doc

                # Stop at max_documents for free tier compliance
                if filtered_count >= max_documents:
                    logger.info(f"Reached maximum document limit: {max_documents}")
                    break

                # Log progress every 1000 documents
                if processed_count % 1000 == 0:
                    logger.info(f"Processed {processed_count} documents, found {filtered_count} NSW revenue documents")

        except Exception as e:
            logger.error(f"Error during filtering: {e}")
            raise

        logger.info(f"Filtering complete. Processed {processed_count} documents, found {filtered_count} NSW revenue documents")

    def save_filtered_documents(self, documents: List[LegalDocument], output_file: str = "nsw_revenue_docs.json"):
        """
        Save filtered documents to local cache

        Args:
            documents: List of LegalDocument objects
            output_file: Output filename
        """
        output_path = self.cache_dir / output_file

        doc_data = []
        for doc in documents:
            doc_data.append({
                'id': doc.id,
                'title': doc.title,
                'content': doc.content,
                'jurisdiction': doc.jurisdiction,
                'document_type': doc.document_type,
                'act_name': doc.act_name,
                'year': doc.year,
                'metadata': doc.metadata
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(documents)} documents to {output_path}")

    def get_sample_documents(self, count: int = 10) -> List[LegalDocument]:
        """
        Get a sample of NSW revenue documents for testing

        Args:
            count: Number of sample documents

        Returns:
            List of sample LegalDocument objects
        """
        dataset = self.load_dataset(streaming=True)
        documents = []

        for doc in self.filter_nsw_revenue_documents(dataset['train'], max_documents=count):
            documents.append(doc)
            if len(documents) >= count:
                break

        return documents


def main():
    """
    Main function for testing the connector
    """
    connector = HuggingFaceConnector()

    # Get sample documents
    logger.info("Getting sample NSW revenue documents...")
    sample_docs = connector.get_sample_documents(count=5)

    for doc in sample_docs:
        print(f"\nTitle: {doc.title}")
        print(f"Act: {doc.act_name}")
        print(f"Year: {doc.year}")
        print(f"Content length: {len(doc.content)} characters")
        print(f"Metadata: {doc.metadata}")

    # Save samples
    connector.save_filtered_documents(sample_docs, "sample_nsw_docs.json")


if __name__ == "__main__":
    main()