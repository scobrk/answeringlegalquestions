"""
Local Vector Store for NSW Revenue Legislation
Uses FAISS for local vector search without external dependencies
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
from openai import OpenAI
import faiss
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalVectorStore:
    """Local vector store using FAISS for NSW Revenue legislation"""

    def __init__(self, data_dir: str = "./data/legislation_v2", index_dir: str = "./data/vector_index"):
        self.data_dir = Path(data_dir)
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # OpenAI client for embeddings
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Vector index
        self.index = None
        self.documents = []
        self.embeddings = []

        # Index files
        self.index_file = self.index_dir / "faiss_index.bin"
        self.documents_file = self.index_dir / "documents.pkl"
        self.metadata_file = self.index_dir / "metadata.json"

    def create_embeddings(self, force_rebuild: bool = False) -> None:
        """Create embeddings for all legislation documents"""

        if not force_rebuild and self._index_exists():
            logger.info("Vector index already exists. Use force_rebuild=True to recreate.")
            return

        logger.info("Creating embeddings for NSW Revenue legislation...")

        # Load all text and markdown files from comprehensive structure
        documents = []

        # Process .txt files (legacy)
        for txt_file in self.data_dir.glob("*.txt"):
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            sections = self._split_into_sections(content, txt_file.stem)
            documents.extend(sections)

        # Process .md files from new comprehensive structure (all subdirectories)
        for md_file in self.data_dir.glob("**/*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Create document with category information from path
                relative_path = md_file.relative_to(self.data_dir)
                category = str(relative_path.parent).replace('/', '_').replace('\\', '_')

                sections = self._split_into_sections(content, md_file.stem, category=category)
                documents.extend(sections)

                logger.info(f"Processed: {relative_path}")

            except Exception as e:
                logger.warning(f"Could not process {md_file}: {e}")
                continue

        logger.info(f"Processing {len(documents)} document sections...")

        # Generate embeddings in batches
        embeddings = []
        batch_size = 20

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_texts = [doc['content'] for doc in batch]

            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=batch_texts
                )

                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")

            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Create zero embeddings as fallback
                fallback_embeddings = [[0.0] * 1536 for _ in batch]
                embeddings.extend(fallback_embeddings)

        # Store documents and embeddings
        self.documents = documents
        self.embeddings = embeddings

        # Create FAISS index
        self._create_faiss_index()

        # Save to disk
        self._save_index()

        logger.info(f"✅ Created vector index with {len(documents)} sections")

    def _split_into_sections(self, content: str, act_name: str, category: str = None) -> List[Dict]:
        """Split legislation content into sections for better retrieval"""
        sections = []

        # Split by section numbers or major headings
        lines = content.split('\n')
        current_section = []
        current_section_number = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line starts with "Section" or is a heading
            if line.startswith('Section ') or line.startswith('PART '):
                # Save previous section
                if current_section:
                    sections.append({
                        'act_name': act_name,
                        'section_number': current_section_number,
                        'content': '\n'.join(current_section),
                        'content_type': 'section',
                        'category': category or 'general'
                    })

                # Start new section
                current_section = [line]
                current_section_number = line.split(' - ')[0] if ' - ' in line else line
            else:
                current_section.append(line)

        # Add final section
        if current_section:
            sections.append({
                'act_name': act_name,
                'section_number': current_section_number,
                'content': '\n'.join(current_section),
                'content_type': 'section',
                'category': category or 'general'
            })

        # If no sections found, use the whole document
        if not sections:
            sections.append({
                'act_name': act_name,
                'section_number': 'Full Act',
                'content': content,
                'content_type': 'full_document',
                'category': category or 'general'
            })

        return sections

    def _create_faiss_index(self) -> None:
        """Create FAISS index from embeddings"""
        if not self.embeddings:
            raise ValueError("No embeddings to index")

        # Convert to numpy array
        embeddings_array = np.array(self.embeddings).astype('float32')

        # Create FAISS index
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings_array)

        # Add embeddings to index
        self.index.add(embeddings_array)

        logger.info(f"Created FAISS index with {self.index.ntotal} vectors")

    def _save_index(self) -> None:
        """Save index and documents to disk"""
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_file))

        # Save documents
        with open(self.documents_file, 'wb') as f:
            pickle.dump(self.documents, f)

        # Save metadata
        metadata = {
            'total_documents': len(self.documents),
            'embedding_model': 'text-embedding-3-small',
            'dimension': 1536,
            'created_at': import_time().time()
        }

        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"✅ Saved index to {self.index_dir}")

    def _load_index(self) -> None:
        """Load index and documents from disk"""
        if not self._index_exists():
            raise FileNotFoundError("Vector index not found. Run create_embeddings() first.")

        # Load FAISS index
        self.index = faiss.read_index(str(self.index_file))

        # Load documents
        with open(self.documents_file, 'rb') as f:
            self.documents = pickle.load(f)

        logger.info(f"✅ Loaded index with {len(self.documents)} documents")

    def _index_exists(self) -> bool:
        """Check if index files exist"""
        return (self.index_file.exists() and
                self.documents_file.exists() and
                self.metadata_file.exists())

    def search(self, query: str, k: int = 5, threshold: float = 0.7) -> List[Dict]:
        """Search for relevant documents"""

        # Load index if not already loaded
        if self.index is None:
            if self._index_exists():
                self._load_index()
            else:
                logger.warning("No vector index found. Creating new index...")
                self.create_embeddings()

        # Generate query embedding
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=[query]
            )
            query_embedding = np.array([response.data[0].embedding]).astype('float32')

        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            return []

        # Normalize query embedding
        faiss.normalize_L2(query_embedding)

        # Search
        scores, indices = self.index.search(query_embedding, k)

        # Filter results by threshold and format
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score >= threshold and idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc['similarity_score'] = float(score)
                results.append(doc)

        logger.info(f"Found {len(results)} relevant documents for query: {query[:50]}...")
        return results

    def get_act_summary(self, act_name: str) -> Optional[str]:
        """Get summary of a specific act"""
        act_docs = [doc for doc in self.documents if doc['act_name'] == act_name]

        if not act_docs:
            return None

        # Return the first section or full document
        return act_docs[0]['content']

    def list_available_acts(self) -> List[str]:
        """List all available acts in the index"""
        if not self.documents:
            if self._index_exists():
                self._load_index()
            else:
                return []

        acts = list(set(doc['act_name'] for doc in self.documents))
        return sorted(acts)


def import_time():
    """Import time module"""
    import time
    return time


def main():
    """Test the vector store"""
    store = LocalVectorStore()

    # Create embeddings
    store.create_embeddings(force_rebuild=True)

    # Test search
    test_queries = [
        "What is the rate of payroll tax?",
        "Principal place of residence exemption for land tax",
        "First home buyer stamp duty concession"
    ]

    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = store.search(query, k=3)

        for i, result in enumerate(results, 1):
            print(f"{i}. {result['act_name']} - {result['section_number']}")
            print(f"   Score: {result['similarity_score']:.3f}")
            print(f"   Content: {result['content'][:100]}...")

    # List available acts
    print(f"\n📚 Available Acts: {store.list_available_acts()}")


if __name__ == "__main__":
    main()