"""
RAG System with LangChain + Gemini Embeddings + ChromaDB
Focused implementation for FAQ and troubleshooting knowledge
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

# LangChain imports
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain.schema import BaseRetriever

# Import your existing environment setup
from dotenv import load_dotenv

# Import fallback system
from .simple_rag_fallback import SimpleRAGFallback

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class HotelOpsRAG:
    """
    Complete RAG system for HotelOpsAI knowledge base
    Uses Gemini embeddings + ChromaDB for semantic search
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize RAG system with Gemini embeddings"""
        
        self.persist_directory = persist_directory
        self.embeddings = None
        self.vectorstore = None
        self.retriever = None
        self.fallback = None
        
        # Initialize embeddings
        self._setup_embeddings()
        
        # Initialize or load vector store
        self._setup_vectorstore()
        
        # Load knowledge base
        self._load_knowledge_base()
        
        # Initialize fallback if embeddings not available
        if not self.embeddings:
            self.fallback = SimpleRAGFallback()
            logger.info("HotelOpsRAG initialized with fallback keyword matching")
        else:
            logger.info("HotelOpsRAG system initialized with Gemini embeddings")
    
    def _setup_embeddings(self):
        """Setup Gemini embeddings through LangChain"""
        
        try:
            # Get API key from environment or use existing setup
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GEN_API_KEY")
            
            if not api_key:
                logger.warning("No Google API key found. RAG will use fallback keyword matching.")
                self.embeddings = None
                return
            
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=api_key
            )
            
            logger.info("Gemini embeddings initialized successfully")
            
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                logger.warning(f"Quota exceeded for embeddings. Using fallback: {e}")
            else:
                logger.error(f"Failed to initialize Gemini embeddings: {e}")
            self.embeddings = None
    
    def _setup_vectorstore(self):
        """Setup ChromaDB vector store"""
        
        try:
            if self.embeddings:
                # Create ChromaDB vector store with Gemini embeddings
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                    collection_name="hotelops_knowledge"
                )
                
                # Create retriever
                self.retriever = self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 5}  # Return top 5 results
                )
                
                logger.info("ChromaDB vector store initialized")
            else:
                logger.warning("Vector store not initialized - no embeddings available")
                
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            self.vectorstore = None
            self.retriever = None
    
    def _load_knowledge_base(self):
        """Load and index knowledge base content"""
        
        if not self.vectorstore:
            logger.warning("Cannot load knowledge base - vector store not available")
            return
        
        try:
            # Check if we already have documents in the vector store
            existing_docs = self.vectorstore.get()
            if existing_docs and len(existing_docs.get('ids', [])) > 0:
                logger.info(f"Found {len(existing_docs['ids'])} existing documents in vector store")
                return
            
            # Load documents from knowledge files
            documents = []
            
            # Load FAQ
            faq_docs = self._load_faq_documents()
            documents.extend(faq_docs)
            
            # Load troubleshooting
            troubleshooting_docs = self._load_troubleshooting_documents()
            documents.extend(troubleshooting_docs)
            
            # Load procedures
            procedure_docs = self._load_procedure_documents()
            documents.extend(procedure_docs)
            
            if documents:
                # Split documents if they're too large
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len,
                )
                
                split_docs = text_splitter.split_documents(documents)
                
                # Add to vector store
                self.vectorstore.add_documents(split_docs)
                
                # Persist the vector store
                self.vectorstore.persist()
                
                logger.info(f"Loaded {len(split_docs)} document chunks into vector store")
            else:
                logger.warning("No documents found to load")
                
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
    
    def _load_faq_documents(self) -> List[Document]:
        """Load FAQ documents"""
        
        documents = []
        # Use original FAQ knowledge base first
        faq_file = Path("context/faq.json")
        if not faq_file.exists():
            faq_file = Path("context/simple_faq.json")
        
        if not faq_file.exists():
            logger.warning(f"FAQ file not found: {faq_file}")
            return documents
        
        try:
            with open(faq_file, 'r', encoding='utf-8') as f:
                faq_data = json.load(f)
            
            # Handle different FAQ formats
            if isinstance(faq_data, dict):
                for category, items in faq_data.items():
                    if isinstance(items, list):
                        # Categorized format
                        for item in items:
                            if isinstance(item, dict) and 'question' in item and 'answer' in item:
                                content = f"Q: {item['question']}\nA: {item['answer']}"
                                doc = Document(
                                    page_content=content,
                                    metadata={
                                        "source": "faq",
                                        "category": category,
                                        "type": "faq",
                                        "question": item['question']
                                    }
                                )
                                documents.append(doc)
                    elif isinstance(items, str):
                        # Simple Q&A format
                        content = f"Q: {category}\nA: {items}"
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source": "faq",
                                "category": "general",
                                "type": "faq",
                                "question": category
                            }
                        )
                        documents.append(doc)
            
            logger.info(f"Loaded {len(documents)} FAQ documents")
            
        except Exception as e:
            logger.error(f"Error loading FAQ documents: {e}")
        
        return documents
    
    def _load_troubleshooting_documents(self) -> List[Document]:
        """Load troubleshooting documents"""
        
        documents = []
        troubleshooting_file = Path("context/troubleshooting.json")
        
        if not troubleshooting_file.exists():
            logger.warning(f"Troubleshooting file not found: {troubleshooting_file}")
            return documents
        
        try:
            with open(troubleshooting_file, 'r', encoding='utf-8') as f:
                troubleshooting_data = json.load(f)
            
            for category, problems in troubleshooting_data.items():
                if isinstance(problems, dict):
                    for problem, solution in problems.items():
                        content = f"Problem: {problem}\nSolution: {solution}"
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source": "troubleshooting",
                                "category": category,
                                "type": "troubleshooting",
                                "problem": problem
                            }
                        )
                        documents.append(doc)
            
            logger.info(f"Loaded {len(documents)} troubleshooting documents")
            
        except Exception as e:
            logger.error(f"Error loading troubleshooting documents: {e}")
        
        return documents
    
    def _load_procedure_documents(self) -> List[Document]:
        """Load procedure documents"""
        
        documents = []
        procedures_file = Path("context/procedures.json")
        
        if not procedures_file.exists():
            logger.warning(f"Procedures file not found: {procedures_file}")
            return documents
        
        try:
            with open(procedures_file, 'r', encoding='utf-8') as f:
                procedures_data = json.load(f)
            
            for procedure_id, procedure in procedures_data.items():
                if isinstance(procedure, dict) and 'title' in procedure:
                    title = procedure['title']
                    steps = procedure.get('steps', [])
                    
                    if steps:
                        steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
                        content = f"Procedure: {title}\n\nSteps:\n{steps_text}"
                    else:
                        content = f"Procedure: {title}"
                    
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": "procedures",
                            "category": "procedures",
                            "type": "procedure",
                            "procedure_id": procedure_id,
                            "title": title
                        }
                    )
                    documents.append(doc)
            
            logger.info(f"Loaded {len(documents)} procedure documents")
            
        except Exception as e:
            logger.error(f"Error loading procedure documents: {e}")
        
        return documents
    
    def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search the knowledge base using semantic similarity
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        
        # Use fallback if embeddings not available
        if self.fallback:
            return self.fallback.search(query, max_results)
        
        if not self.retriever:
            logger.warning("RAG retriever not available - returning empty results")
            return []
        
        try:
            # Update retriever to return requested number of results
            self.retriever.search_kwargs["k"] = max_results
            
            # Perform semantic search
            docs = self.retriever.get_relevant_documents(query)
            
            # Format results
            results = []
            for doc in docs:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", "unknown"),
                    "type": doc.metadata.get("type", "unknown"),
                    "category": doc.metadata.get("category", "general")
                }
                
                # Extract question/title for display
                if doc.metadata.get("type") == "faq":
                    result["title"] = doc.metadata.get("question", "FAQ Item")
                elif doc.metadata.get("type") == "troubleshooting":
                    result["title"] = doc.metadata.get("problem", "Troubleshooting Item")
                elif doc.metadata.get("type") == "procedure":
                    result["title"] = doc.metadata.get("title", "Procedure")
                else:
                    result["title"] = "Knowledge Item"
                
                results.append(result)
            
            logger.info(f"RAG search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                logger.warning(f"Quota exceeded during search. Switching to fallback.")
                # Initialize fallback on the fly if quota exceeded
                if not self.fallback:
                    self.fallback = SimpleRAGFallback()
                return self.fallback.search(query, max_results)
            else:
                logger.error(f"RAG search failed: {e}")
                return []
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Add a new document to the knowledge base"""
        
        if not self.vectorstore:
            return False
        
        try:
            doc = Document(page_content=content, metadata=metadata)
            self.vectorstore.add_documents([doc])
            self.vectorstore.persist()
            
            logger.info(f"Added new document: {metadata.get('title', 'Untitled')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        
        # Use fallback stats if available
        if self.fallback:
            return self.fallback.get_stats()
        
        stats = {
            "embeddings_available": self.embeddings is not None,
            "vectorstore_available": self.vectorstore is not None,
            "total_documents": 0,
            "last_updated": datetime.now().isoformat()
        }
        
        if self.vectorstore:
            try:
                existing_docs = self.vectorstore.get()
                stats["total_documents"] = len(existing_docs.get('ids', []))
            except Exception as e:
                logger.error(f"Failed to get vectorstore stats: {e}")
        
        return stats

# Global RAG instance (singleton pattern)
_rag_system = None

def get_rag_system() -> HotelOpsRAG:
    """Get or create the global RAG system instance"""
    global _rag_system
    if _rag_system is None:
        _rag_system = HotelOpsRAG()
    return _rag_system
