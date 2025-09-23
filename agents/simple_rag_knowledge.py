"""
Simple RAG Knowledge Base for FAQ and Troubleshooting
Focused implementation - no cross-agent complexity
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import sqlite3
from datetime import datetime

# Try to import vector database (optional)
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

@dataclass
class KnowledgeItem:
    id: str
    title: str
    content: str
    category: str  # "faq", "troubleshooting", "procedure"
    tags: List[str]
    confidence_threshold: float = 0.7

class SimpleRAGKnowledge:
    """
    Simple RAG for FAQ and Troubleshooting
    - No complex agent integration
    - Fast semantic search
    - Easy to maintain
    """
    
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = knowledge_dir
        self.knowledge_items: List[KnowledgeItem] = []
        
        # Initialize vector database if available
        if CHROMADB_AVAILABLE:
            self.chroma_client = chromadb.Client()
            self.collection = self.chroma_client.create_collection(
                name="hotelops_knowledge",
                get_or_create=True
            )
        else:
            self.chroma_client = None
            print("ChromaDB not available. Using keyword matching fallback.")
        
        # Load knowledge base
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load FAQ and troubleshooting data"""
        
        # Load from JSON files
        knowledge_files = {
            "faq": "context/faq.json",
            "troubleshooting": "context/troubleshooting.json", 
            "procedures": "context/procedures.json"
        }
        
        all_items = []
        
        for category, file_path in knowledge_files.items():
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        items = self._parse_knowledge_file(data, category)
                        all_items.extend(items)
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        
        self.knowledge_items = all_items
        
        # Index in vector database
        if self.chroma_client and all_items:
            self._index_knowledge_items(all_items)
        
        print(f"Loaded {len(all_items)} knowledge items")
    
    def _parse_knowledge_file(self, data: Dict, category: str) -> List[KnowledgeItem]:
        """Parse knowledge file into standardized format"""
        
        items = []
        
        if category == "faq" and isinstance(data, dict):
            # FAQ format: {"question": "answer"}
            for question, answer in data.items():
                item = KnowledgeItem(
                    id=f"faq_{len(items)}",
                    title=question,
                    content=f"Q: {question}\nA: {answer}",
                    category="faq",
                    tags=self._extract_tags(question + " " + answer)
                )
                items.append(item)
        
        elif category == "troubleshooting" and isinstance(data, dict):
            # Troubleshooting format: nested categories
            for problem_category, problems in data.items():
                if isinstance(problems, dict):
                    for problem, solution in problems.items():
                        item = KnowledgeItem(
                            id=f"troubleshoot_{len(items)}",
                            title=problem,
                            content=f"Problem: {problem}\nSolution: {solution}",
                            category="troubleshooting",
                            tags=self._extract_tags(problem + " " + solution) + [problem_category.lower()]
                        )
                        items.append(item)
        
        return items
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text"""
        
        # Common hotel/tech terms
        tag_keywords = {
            'wifi': ['wifi', 'internet', 'connection', 'network'],
            'ac': ['ac', 'air conditioning', 'hvac', 'temperature', 'cooling'],
            'room_service': ['room service', 'dining', 'food', 'restaurant'],
            'housekeeping': ['housekeeping', 'cleaning', 'maintenance'],
            'login': ['login', 'password', 'account', 'access'],
            'booking': ['booking', 'reservation', 'check-in', 'check-out'],
            'payment': ['payment', 'billing', 'credit card', 'charge'],
            'mobile': ['mobile', 'app', 'phone', 'smartphone']
        }
        
        text_lower = text.lower()
        tags = []
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return tags
    
    def _index_knowledge_items(self, items: List[KnowledgeItem]):
        """Index items in vector database"""
        
        if not self.chroma_client:
            return
        
        documents = [item.content for item in items]
        metadatas = [{
            "id": item.id,
            "title": item.title,
            "category": item.category,
            "tags": ",".join(item.tags)
        } for item in items]
        ids = [item.id for item in items]
        
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            print(f"Error indexing knowledge: {e}")
    
    def search_knowledge(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Search knowledge base for relevant information
        """
        
        if self.chroma_client:
            return self._vector_search(query, max_results)
        else:
            return self._keyword_search(query, max_results)
    
    def _vector_search(self, query: str, max_results: int) -> List[Dict]:
        """Semantic search using vector database"""
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=max_results
            )
            
            formatted_results = []
            
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if 'distances' in results else 0
                    
                    formatted_results.append({
                        "title": metadata.get("title", ""),
                        "content": doc,
                        "category": metadata.get("category", ""),
                        "relevance_score": 1 - distance,  # Convert distance to relevance
                        "tags": metadata.get("tags", "").split(",") if metadata.get("tags") else []
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Vector search error: {e}")
            return self._keyword_search(query, max_results)
    
    def _keyword_search(self, query: str, max_results: int) -> List[Dict]:
        """Fallback keyword-based search"""
        
        query_lower = query.lower()
        scored_items = []
        
        for item in self.knowledge_items:
            score = 0
            content_lower = item.content.lower()
            title_lower = item.title.lower()
            
            # Score based on keyword matches
            query_words = query_lower.split()
            for word in query_words:
                if word in title_lower:
                    score += 3  # Title matches are more important
                if word in content_lower:
                    score += 1
                if word in [tag.lower() for tag in item.tags]:
                    score += 2  # Tag matches are important
            
            if score > 0:
                scored_items.append({
                    "title": item.title,
                    "content": item.content,
                    "category": item.category,
                    "relevance_score": score / len(query_words),  # Normalize score
                    "tags": item.tags
                })
        
        # Sort by score and return top results
        scored_items.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_items[:max_results]
    
    def get_category_items(self, category: str) -> List[Dict]:
        """Get all items from a specific category"""
        
        return [{
            "title": item.title,
            "content": item.content,
            "category": item.category,
            "tags": item.tags
        } for item in self.knowledge_items if item.category == category]
    
    def add_knowledge_item(self, title: str, content: str, category: str, tags: List[str] = None):
        """Add new knowledge item (for dynamic updates)"""
        
        item = KnowledgeItem(
            id=f"{category}_{len(self.knowledge_items)}",
            title=title,
            content=content,
            category=category,
            tags=tags or []
        )
        
        self.knowledge_items.append(item)
        
        # Add to vector database
        if self.chroma_client:
            try:
                self.collection.add(
                    documents=[content],
                    metadatas=[{
                        "id": item.id,
                        "title": title,
                        "category": category,
                        "tags": ",".join(tags or [])
                    }],
                    ids=[item.id]
                )
            except Exception as e:
                print(f"Error adding to vector DB: {e}")

# USAGE EXAMPLE:
"""
# Initialize knowledge base
rag_kb = SimpleRAGKnowledge()

# Search for FAQ
results = rag_kb.search_knowledge("how to reset password")

# Search for troubleshooting
results = rag_kb.search_knowledge("wifi not working")

# Get all FAQ items
faq_items = rag_kb.get_category_items("faq")
"""
