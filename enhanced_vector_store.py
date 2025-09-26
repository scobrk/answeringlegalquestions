"""
Enhanced Vector Store for Scalable NSW Revenue Legislation
Supports 50+ revenue types with hierarchical organization and cross-referencing
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
import logging
from dataclasses import dataclass
from datetime import datetime, date
import faiss
import networkx as nx
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentMetadata:
    """Enhanced metadata for revenue documents"""
    document_id: str
    title: str
    document_type: str  # act, regulation, ruling, guidance, example
    category: str  # e.g., property_taxes.duties.conveyance_duty
    subcategory: str
    effective_date: datetime
    last_amended: datetime
    version: str
    status: str  # current, superseded, pending, draft
    related_taxes: List[str]
    rate_schedule_id: Optional[str] = None

@dataclass
class ChunkMetadata:
    """Enhanced chunk metadata with tax context"""
    chunk_id: str
    document_id: str
    section_number: str
    tax_category: str
    document_type: str
    effective_date: datetime
    confidence_score: float
    content_type: str  # section, rate_table, example, cross_reference

class EnhancedVectorStore:
    """
    Enhanced vector store supporting 50+ revenue types with:
    - Hierarchical organization
    - Multi-index architecture
    - Relationship modeling
    - Advanced caching
    """

    def __init__(self, data_dir: str = "./data", cache_size: int = 1000):
        self.data_dir = Path(data_dir)
        self.legislation_dir = self.data_dir / "legislation_v2"
        self.metadata_dir = self.data_dir / "metadata"
        self.indexes_dir = self.data_dir / "vector_indexes"

        # Create directory structure
        for dir_path in [self.legislation_dir, self.metadata_dir, self.indexes_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # OpenAI client for embeddings
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Multiple indexes for different purposes
        self.primary_index = None  # Global search across all taxes
        self.category_indexes = {}  # Category-specific indexes
        self.relationship_graph = nx.Graph()  # Tax relationship graph

        # Document and chunk storage
        self.documents = {}  # document_id -> DocumentMetadata
        self.chunks = {}  # chunk_id -> ChunkMetadata
        self.chunk_embeddings = {}  # chunk_id -> embedding

        # Caching
        self.query_cache = {}  # LRU cache for queries
        self.cache_size = cache_size

        # Load existing data
        self._load_metadata()
        self._load_relationships()

        # Try to load indexes if they exist
        if self._indexes_exist():
            self._load_enhanced_indexes()

    def _load_metadata(self) -> None:
        """Load document and chunk metadata"""
        metadata_file = self.metadata_dir / "documents.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                data = json.load(f)

            # Convert to DocumentMetadata objects
            for doc_id, doc_data in data.get('documents', {}).items():
                self.documents[doc_id] = DocumentMetadata(
                    document_id=doc_data['document_id'],
                    title=doc_data['title'],
                    document_type=doc_data['document_type'],
                    category=doc_data['category'],
                    subcategory=doc_data['subcategory'],
                    effective_date=datetime.fromisoformat(doc_data['effective_date']),
                    last_amended=datetime.fromisoformat(doc_data['last_amended']),
                    version=doc_data['version'],
                    status=doc_data['status'],
                    related_taxes=doc_data['related_taxes'],
                    rate_schedule_id=doc_data.get('rate_schedule_id')
                )

    def _load_relationships(self) -> None:
        """Load tax relationship graph"""
        relationships_file = self.metadata_dir / "relationships.json"
        if relationships_file.exists():
            with open(relationships_file, 'r') as f:
                data = json.load(f)

            # Build NetworkX graph from the actual structure
            relationships = data.get('relationships', [])

            # Add nodes and edges from relationship list
            for rel in relationships:
                primary_tax = rel.get('primary_tax')
                secondary_tax = rel.get('secondary_tax')
                relationship_type = rel.get('relationship_type')

                if primary_tax and secondary_tax:
                    # Add nodes if they don't exist
                    if not self.relationship_graph.has_node(primary_tax):
                        self.relationship_graph.add_node(primary_tax, type='tax')
                    if not self.relationship_graph.has_node(secondary_tax):
                        self.relationship_graph.add_node(secondary_tax, type='tax')

                    # Add edge with relationship data
                    self.relationship_graph.add_edge(
                        primary_tax,
                        secondary_tax,
                        relationship=relationship_type,
                        strength=0.8,  # Default strength
                        context=rel.get('interaction_rules', {})
                    )

    def create_enhanced_embeddings(self, force_rebuild: bool = False) -> None:
        """Create embeddings with enhanced chunking and metadata"""

        if not force_rebuild and self._indexes_exist():
            logger.info("Enhanced indexes already exist. Use force_rebuild=True to recreate.")
            return

        logger.info("Creating enhanced embeddings for 50+ revenue types...")

        # Process all categories
        all_chunks = []
        category_chunks = {}

        for category_dir in self.legislation_dir.iterdir():
            if not category_dir.is_dir():
                continue

            category_name = category_dir.name
            category_chunks[category_name] = []

            logger.info(f"Processing category: {category_name}")

            # Process all documents in category
            for doc_file in category_dir.rglob("*.json"):
                chunks = self._process_document_enhanced(doc_file, category_name)
                all_chunks.extend(chunks)
                category_chunks[category_name].extend(chunks)

        # Generate embeddings
        self._generate_embeddings_batch(all_chunks)

        # Create indexes
        self._create_primary_index(all_chunks)
        self._create_category_indexes(category_chunks)

        # Save everything
        self._save_enhanced_indexes()

        logger.info(f"✅ Created enhanced indexes with {len(all_chunks)} chunks across {len(category_chunks)} categories")

    def _process_document_enhanced(self, doc_file: Path, category: str) -> List[Dict]:
        """Process document with enhanced chunking"""

        with open(doc_file, 'r') as f:
            doc_data = json.load(f)

        document_id = doc_data['document_id']

        # Store document metadata
        self.documents[document_id] = DocumentMetadata(
            document_id=document_id,
            title=doc_data['document_metadata']['title'],
            document_type=doc_data['document_metadata']['document_type'],
            category=category,
            subcategory=doc_data['document_metadata'].get('subcategory', ''),
            effective_date=datetime.fromisoformat(doc_data['document_metadata']['effective_date']),
            last_amended=datetime.fromisoformat(doc_data['document_metadata']['last_amended']),
            version=doc_data['document_metadata']['version'],
            status=doc_data['document_metadata']['status'],
            related_taxes=[rel.get('tax_id', '') for rel in doc_data['relationships'].get('related_taxes', [])]
        )

        # Enhanced chunking
        chunks = []
        content = doc_data.get('content', '')

        # Split into sections with enhanced metadata
        sections = self._smart_section_split(content, document_id)

        for i, section in enumerate(sections):
            chunk_id = f"{document_id}_chunk_{i}"

            chunk_data = {
                'chunk_id': chunk_id,
                'content': section['content'],
                'metadata': ChunkMetadata(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    section_number=section['section_number'],
                    tax_category=category,
                    document_type=doc_data['document_metadata']['document_type'],
                    effective_date=datetime.fromisoformat(doc_data['document_metadata']['effective_date']),
                    confidence_score=section.get('confidence_score', 1.0),
                    content_type=section.get('content_type', 'section')
                )
            }

            chunks.append(chunk_data)
            self.chunks[chunk_id] = chunk_data['metadata']

        return chunks

    def _smart_section_split(self, content: str, document_id: str) -> List[Dict]:
        """Enhanced section splitting with semantic awareness"""

        sections = []
        lines = content.split('\n')
        current_section = []
        current_section_number = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect section boundaries with enhanced logic
            if self._is_section_boundary(line):
                # Save previous section
                if current_section:
                    sections.append({
                        'content': '\n'.join(current_section),
                        'section_number': current_section_number or 'Unknown',
                        'content_type': self._classify_content_type('\n'.join(current_section)),
                        'confidence_score': self._calculate_confidence_score('\n'.join(current_section))
                    })

                # Start new section
                current_section = [line]
                current_section_number = self._extract_section_number(line)
            else:
                current_section.append(line)

        # Add final section
        if current_section:
            sections.append({
                'content': '\n'.join(current_section),
                'section_number': current_section_number or 'Final',
                'content_type': self._classify_content_type('\n'.join(current_section)),
                'confidence_score': self._calculate_confidence_score('\n'.join(current_section))
            })

        return sections

    def _is_section_boundary(self, line: str) -> bool:
        """Detect section boundaries with enhanced patterns"""
        section_patterns = [
            r'^Section \d+',
            r'^PART [IVX]+',
            r'^Chapter \d+',
            r'^\d+\.\s',
            r'^[A-Z][A-Z\s]+$'  # All caps headings
        ]

        import re
        for pattern in section_patterns:
            if re.match(pattern, line):
                return True
        return False

    def _classify_content_type(self, content: str) -> str:
        """Classify content type for better retrieval"""
        content_lower = content.lower()

        if 'rate' in content_lower or '$' in content or '%' in content:
            return 'rate_table'
        elif 'example' in content_lower or 'scenario' in content_lower:
            return 'example'
        elif 'see section' in content_lower or 'refer to' in content_lower:
            return 'cross_reference'
        else:
            return 'section'

    def _calculate_confidence_score(self, content: str) -> float:
        """Calculate content quality/confidence score"""
        score = 1.0

        # Reduce score for very short content
        if len(content) < 50:
            score *= 0.7

        # Reduce score for content with many special characters
        special_char_ratio = sum(1 for c in content if not c.isalnum() and not c.isspace()) / len(content)
        if special_char_ratio > 0.3:
            score *= 0.8

        # Increase score for well-structured content
        if any(keyword in content.lower() for keyword in ['section', 'subsection', 'paragraph']):
            score *= 1.1

        return min(score, 1.0)

    def _extract_section_number(self, line: str) -> str:
        """Extract section number from heading"""
        import re

        # Try various patterns
        patterns = [
            r'Section (\d+[A-Z]*)',
            r'PART ([IVX]+)',
            r'Chapter (\d+)',
            r'^(\d+)\.'
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)

        return line[:20]  # Fallback to first 20 chars

    def _generate_embeddings_batch(self, chunks: List[Dict], batch_size: int = 50) -> None:
        """Generate embeddings in optimized batches"""

        logger.info(f"Generating embeddings for {len(chunks)} chunks...")

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_texts = [chunk['content'] for chunk in batch]

            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=batch_texts
                )

                # Store embeddings
                for j, embedding in enumerate(response.data):
                    chunk_id = batch[j]['chunk_id']
                    self.chunk_embeddings[chunk_id] = embedding.embedding

                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")

            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Create zero embeddings as fallback
                for j in range(len(batch)):
                    chunk_id = batch[j]['chunk_id']
                    self.chunk_embeddings[chunk_id] = [0.0] * 1536

    def _create_primary_index(self, chunks: List[Dict]) -> None:
        """Create primary FAISS index with product quantization"""

        # Get embeddings
        embeddings = []
        chunk_ids = []

        for chunk in chunks:
            chunk_id = chunk['chunk_id']
            if chunk_id in self.chunk_embeddings:
                embeddings.append(self.chunk_embeddings[chunk_id])
                chunk_ids.append(chunk_id)

        if not embeddings:
            logger.warning("No embeddings found for primary index")
            return

        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')

        # Create FAISS index with appropriate type based on dataset size
        dimension = embeddings_array.shape[1]
        num_vectors = embeddings_array.shape[0]

        if num_vectors < 1000:
            # Use simple flat index for small datasets
            self.primary_index = faiss.IndexFlatIP(dimension)
            faiss.normalize_L2(embeddings_array)
        else:
            # Use IndexIVFPQ for large datasets
            num_clusters = min(256, num_vectors // 8)  # Ensure enough training points
            quantizer = faiss.IndexFlatL2(dimension)
            self.primary_index = faiss.IndexIVFPQ(quantizer, dimension, num_clusters, 8, 8)

            # Train the index
            faiss.normalize_L2(embeddings_array)
            self.primary_index.train(embeddings_array)

        # Add embeddings
        self.primary_index.add(embeddings_array)

        # Store chunk ID mapping
        self.primary_chunk_ids = chunk_ids

        logger.info(f"Created primary index with {self.primary_index.ntotal} vectors")

    def _create_category_indexes(self, category_chunks: Dict[str, List[Dict]]) -> None:
        """Create category-specific indexes for faster search"""

        for category, chunks in category_chunks.items():
            if not chunks:
                continue

            # Get embeddings for this category
            embeddings = []
            chunk_ids = []

            for chunk in chunks:
                chunk_id = chunk['chunk_id']
                if chunk_id in self.chunk_embeddings:
                    embeddings.append(self.chunk_embeddings[chunk_id])
                    chunk_ids.append(chunk_id)

            if not embeddings:
                continue

            # Create category-specific index (use flat index for exact search)
            embeddings_array = np.array(embeddings).astype('float32')
            dimension = embeddings_array.shape[1]

            category_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            faiss.normalize_L2(embeddings_array)
            category_index.add(embeddings_array)

            self.category_indexes[category] = {
                'index': category_index,
                'chunk_ids': chunk_ids
            }

            logger.info(f"Created category index for {category}: {category_index.ntotal} vectors")

    def search_enhanced(self,
                       query: str,
                       category_filter: Optional[str] = None,
                       document_type_filter: Optional[str] = None,
                       k: int = 10,
                       include_related: bool = True) -> List[Dict]:
        """
        Enhanced search with category filtering and relationship expansion
        """

        # Check cache first
        cache_key = f"{query}_{category_filter}_{document_type_filter}_{k}_{include_related}"
        if cache_key in self.query_cache:
            logger.info("Returning cached result")
            return self.query_cache[cache_key]

        # Generate query embedding
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=[query]
            )
            query_embedding = np.array([response.data[0].embedding]).astype('float32')
            faiss.normalize_L2(query_embedding)

        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            return []

        # Determine which index to use
        if category_filter and category_filter in self.category_indexes:
            # Use category-specific index for faster search
            index_data = self.category_indexes[category_filter]
            scores, indices = index_data['index'].search(query_embedding, k)
            chunk_ids = [index_data['chunk_ids'][idx] for idx in indices[0]]
        else:
            # Use primary index
            if self.primary_index is None:
                logger.warning("Primary index not loaded")
                return []

            scores, indices = self.primary_index.search(query_embedding, k)
            chunk_ids = [self.primary_chunk_ids[idx] for idx in indices[0] if idx < len(self.primary_chunk_ids)]

        # Filter and format results
        results = []
        for i, (score, chunk_id) in enumerate(zip(scores[0], chunk_ids)):
            if chunk_id not in self.chunks:
                continue

            chunk_metadata = self.chunks[chunk_id]

            # Apply filters
            if document_type_filter and chunk_metadata.document_type != document_type_filter:
                continue

            result = {
                'chunk_id': chunk_id,
                'content': self._get_chunk_content(chunk_id),
                'similarity_score': float(score),
                'metadata': {
                    'document_id': chunk_metadata.document_id,
                    'section_number': chunk_metadata.section_number,
                    'tax_category': chunk_metadata.tax_category,
                    'document_type': chunk_metadata.document_type,
                    'effective_date': chunk_metadata.effective_date.isoformat(),
                    'confidence_score': chunk_metadata.confidence_score
                }
            }

            results.append(result)

        # Add related tax information if requested
        if include_related:
            results = self._expand_with_related_taxes(results, query)

        # Cache result
        if len(self.query_cache) >= self.cache_size:
            # Remove oldest entry (simple FIFO, could be improved with LRU)
            oldest_key = next(iter(self.query_cache))
            del self.query_cache[oldest_key]

        self.query_cache[cache_key] = results

        logger.info(f"Found {len(results)} relevant chunks for query: {query[:50]}...")
        return results

    def _expand_with_related_taxes(self, results: List[Dict], query: str) -> List[Dict]:
        """Expand results with related tax information"""

        # Identify tax types mentioned in top results
        mentioned_taxes = set()
        for result in results[:3]:  # Check top 3 results
            tax_category = result['metadata']['tax_category']
            mentioned_taxes.add(tax_category)

        # Find related taxes using relationship graph
        related_taxes = set()
        for tax in mentioned_taxes:
            if tax in self.relationship_graph:
                neighbors = list(self.relationship_graph.neighbors(tax))
                related_taxes.update(neighbors)

        # Search for related tax content
        related_results = []
        for related_tax in related_taxes:
            if related_tax not in mentioned_taxes:  # Don't duplicate
                related_search = self.search_enhanced(
                    query,
                    category_filter=related_tax,
                    k=2,
                    include_related=False
                )

                for result in related_search[:1]:  # Take top result
                    result['is_related_tax'] = True
                    result['related_to'] = list(mentioned_taxes)
                    related_results.append(result)

        return results + related_results

    def _get_chunk_content(self, chunk_id: str) -> str:
        """Get content for a chunk"""
        # This is a simplified implementation
        # In production, content would be stored separately and retrieved here
        if chunk_id in self.chunks:
            chunk_metadata = self.chunks[chunk_id]
            document_id = chunk_metadata.document_id
            section_num = chunk_metadata.section_number

            # Try to find content from the original documents
            for doc_id, doc_metadata in self.documents.items():
                if doc_id == document_id:
                    return f"Content from {document_id}, section {section_num} - {doc_metadata.title}"

        return f"Content for chunk {chunk_id} (placeholder)"

    def _indexes_exist(self) -> bool:
        """Check if enhanced indexes exist"""
        primary_index_file = self.indexes_dir / "primary_index.bin"
        return primary_index_file.exists()

    def _load_enhanced_indexes(self) -> None:
        """Load all indexes and metadata from disk"""
        try:
            # Load primary index
            primary_index_file = self.indexes_dir / "primary_index.bin"
            if primary_index_file.exists():
                self.primary_index = faiss.read_index(str(primary_index_file))

            # Load category indexes
            categories_dir = self.indexes_dir / "categories"
            if categories_dir.exists():
                for category_dir in categories_dir.iterdir():
                    if category_dir.is_dir():
                        category_name = category_dir.name
                        index_file = category_dir / "index.bin"
                        chunk_ids_file = category_dir / "chunk_ids.json"

                        if index_file.exists() and chunk_ids_file.exists():
                            category_index = faiss.read_index(str(index_file))

                            with open(chunk_ids_file, 'r') as f:
                                chunk_ids = json.load(f)

                            self.category_indexes[category_name] = {
                                'index': category_index,
                                'chunk_ids': chunk_ids
                            }

            # Load chunk embeddings
            embeddings_file = self.indexes_dir / "chunk_embeddings.pkl"
            if embeddings_file.exists():
                with open(embeddings_file, 'rb') as f:
                    self.chunk_embeddings = pickle.load(f)

            # Load chunk metadata
            chunks_file = self.metadata_dir / "chunks.json"
            if chunks_file.exists():
                with open(chunks_file, 'r') as f:
                    chunk_metadata_dict = json.load(f)

                for chunk_id, metadata_dict in chunk_metadata_dict.items():
                    self.chunks[chunk_id] = ChunkMetadata(
                        chunk_id=metadata_dict['chunk_id'],
                        document_id=metadata_dict['document_id'],
                        section_number=metadata_dict['section_number'],
                        tax_category=metadata_dict['tax_category'],
                        document_type=metadata_dict['document_type'],
                        effective_date=datetime.fromisoformat(metadata_dict['effective_date']),
                        confidence_score=metadata_dict['confidence_score'],
                        content_type=metadata_dict['content_type']
                    )

            # Load chunk ID mapping for primary index
            primary_chunk_ids_file = self.indexes_dir / "primary_chunk_ids.json"
            if primary_chunk_ids_file.exists():
                with open(primary_chunk_ids_file, 'r') as f:
                    self.primary_chunk_ids = json.load(f)
            else:
                # Fallback: use all chunk IDs
                self.primary_chunk_ids = list(self.chunks.keys())

            logger.info(f"✅ Loaded enhanced indexes with {len(self.chunks)} chunks")

        except Exception as e:
            logger.error(f"Error loading enhanced indexes: {e}")

    def _save_enhanced_indexes(self) -> None:
        """Save all indexes and metadata"""

        # Save primary index
        if self.primary_index:
            faiss.write_index(self.primary_index, str(self.indexes_dir / "primary_index.bin"))

        # Save category indexes
        for category, index_data in self.category_indexes.items():
            category_dir = self.indexes_dir / "categories" / category
            category_dir.mkdir(parents=True, exist_ok=True)
            faiss.write_index(index_data['index'], str(category_dir / "index.bin"))

            with open(category_dir / "chunk_ids.json", 'w') as f:
                json.dump(index_data['chunk_ids'], f)

        # Save chunk embeddings
        with open(self.indexes_dir / "chunk_embeddings.pkl", 'wb') as f:
            pickle.dump(self.chunk_embeddings, f)

        # Save primary chunk IDs mapping
        if hasattr(self, 'primary_chunk_ids'):
            with open(self.indexes_dir / "primary_chunk_ids.json", 'w') as f:
                json.dump(self.primary_chunk_ids, f)

        # Save chunk metadata
        chunk_metadata_dict = {}
        for chunk_id, metadata in self.chunks.items():
            chunk_metadata_dict[chunk_id] = {
                'chunk_id': metadata.chunk_id,
                'document_id': metadata.document_id,
                'section_number': metadata.section_number,
                'tax_category': metadata.tax_category,
                'document_type': metadata.document_type,
                'effective_date': metadata.effective_date.isoformat(),
                'confidence_score': metadata.confidence_score,
                'content_type': metadata.content_type
            }

        with open(self.metadata_dir / "chunks.json", 'w') as f:
            json.dump(chunk_metadata_dict, f, indent=2)

        logger.info(f"✅ Saved enhanced indexes to {self.indexes_dir}")

    def get_tax_relationships(self, tax_type: str) -> Dict:
        """Get relationship information for a specific tax type"""

        if tax_type not in self.relationship_graph:
            return {"relationships": []}

        relationships = []
        for neighbor in self.relationship_graph.neighbors(tax_type):
            edge_data = self.relationship_graph.get_edge_data(tax_type, neighbor)
            relationships.append({
                "related_tax": neighbor,
                "relationship_type": edge_data.get('relationship', 'unknown'),
                "strength": edge_data.get('strength', 0.5),
                "context": edge_data.get('context', '')
            })

        return {"relationships": relationships}

    def get_statistics(self) -> Dict:
        """Get system statistics"""

        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "total_categories": len(self.category_indexes),
            "cache_size": len(self.query_cache),
            "relationship_edges": self.relationship_graph.number_of_edges(),
            "index_memory_usage": self._estimate_memory_usage()
        }

    def _estimate_memory_usage(self) -> str:
        """Estimate memory usage of indexes"""
        # Rough estimation
        primary_size = len(self.chunk_embeddings) * 1536 * 4 / (1024 * 1024)  # MB
        category_size = sum(data['index'].ntotal * 1536 * 4 for data in self.category_indexes.values()) / (1024 * 1024)

        return f"~{primary_size + category_size:.1f} MB"


def main():
    """Test the enhanced vector store"""

    store = EnhancedVectorStore()

    # Test search
    test_queries = [
        "conveyance duty rates for residential property",
        "first home buyer exemptions",
        "land tax principal place of residence",
        "foreign purchaser additional duty"
    ]

    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = store.search_enhanced(query, k=3, include_related=True)

        for i, result in enumerate(results, 1):
            print(f"{i}. {result['metadata']['document_id']} - Section {result['metadata']['section_number']}")
            print(f"   Category: {result['metadata']['tax_category']}")
            print(f"   Score: {result['similarity_score']:.3f}")
            if result.get('is_related_tax'):
                print(f"   Related to: {', '.join(result['related_to'])}")

    # Show statistics
    stats = store.get_statistics()
    print(f"\n📊 System Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    main()