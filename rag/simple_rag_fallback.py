"""
Simple RAG Fallback without embeddings
Uses keyword matching when Gemini embeddings are not available
"""

import json
import os
from typing import List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SimpleRAGFallback:
    """
    Fallback RAG implementation using keyword matching
    """
    
    def __init__(self):
        self.knowledge_items = []
        self._load_knowledge_base()
        logger.info(f"Simple RAG Fallback initialized with {len(self.knowledge_items)} items")
    
    def _load_knowledge_base(self):
        """Load knowledge from JSON files"""
        
        # Load FAQ
        self._load_faq_items()
        
        # Load troubleshooting
        self._load_troubleshooting_items()
        
        # Load procedures
        self._load_procedure_items()
    
    def _load_faq_items(self):
        """Load FAQ items"""
        
        faq_file = Path("context/faq.json")
        if not faq_file.exists():
            faq_file = Path("context/simple_faq.json")
        
        if not faq_file.exists():
            logger.warning("No FAQ file found")
            return
        
        try:
            with open(faq_file, 'r', encoding='utf-8') as f:
                faq_data = json.load(f)
            
            # Handle simple Q&A format
            if isinstance(faq_data, dict):
                for question, answer in faq_data.items():
                    if isinstance(answer, str):
                        item = {
                            "title": question,
                            "content": f"Q: {question}\nA: {answer}",
                            "type": "faq",
                            "source": "faq",
                            "category": "general",
                            "metadata": {
                                "question": question,
                                "answer": answer
                            }
                        }
                        self.knowledge_items.append(item)
            
            logger.info(f"Loaded {len([item for item in self.knowledge_items if item['type'] == 'faq'])} FAQ items")
            
        except Exception as e:
            logger.error(f"Error loading FAQ: {e}")
    
    def _load_troubleshooting_items(self):
        """Load troubleshooting items"""
        
        troubleshooting_file = Path("context/troubleshooting.json")
        if not troubleshooting_file.exists():
            logger.warning("No troubleshooting file found")
            return
        
        try:
            with open(troubleshooting_file, 'r', encoding='utf-8') as f:
                troubleshooting_data = json.load(f)
            
            for category, problems in troubleshooting_data.items():
                if isinstance(problems, dict):
                    for problem, solution in problems.items():
                        item = {
                            "title": problem,
                            "content": f"Problem: {problem}\nSolution: {solution}",
                            "type": "troubleshooting",
                            "source": "troubleshooting",
                            "category": category,
                            "metadata": {
                                "problem": problem,
                                "solution": solution
                            }
                        }
                        self.knowledge_items.append(item)
            
            logger.info(f"Loaded {len([item for item in self.knowledge_items if item['type'] == 'troubleshooting'])} troubleshooting items")
            
        except Exception as e:
            logger.error(f"Error loading troubleshooting: {e}")
    
    def _load_procedure_items(self):
        """Load procedure items"""
        
        procedures_file = Path("context/procedures.json")
        if not procedures_file.exists():
            logger.warning("No procedures file found")
            return
        
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
                    
                    item = {
                        "title": title,
                        "content": content,
                        "type": "procedure",
                        "source": "procedures",
                        "category": "procedures",
                        "metadata": {
                            "procedure_id": procedure_id,
                            "title": title,
                            "steps": steps
                        }
                    }
                    self.knowledge_items.append(item)
            
            logger.info(f"Loaded {len([item for item in self.knowledge_items if item['type'] == 'procedure'])} procedure items")
            
        except Exception as e:
            logger.error(f"Error loading procedures: {e}")
    
    def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search using keyword matching
        """
        
        query_lower = query.lower()
        query_words = query_lower.split()
        
        scored_items = []
        
        for item in self.knowledge_items:
            score = 0
            
            title_lower = item['title'].lower()
            content_lower = item['content'].lower()
            
            # Score based on keyword matches
            for word in query_words:
                # Title matches (higher weight)
                if word in title_lower:
                    score += 3
                
                # Content matches
                if word in content_lower:
                    score += 1
                
                # Category matches
                if word in item['category'].lower():
                    score += 2
                
                # Type-specific scoring
                if item['type'] == 'troubleshooting' and word in ['problem', 'issue', 'error', 'fix', 'help']:
                    score += 2
                elif item['type'] == 'faq' and word in ['how', 'what', 'when', 'where', 'why']:
                    score += 2
                elif item['type'] == 'procedure' and word in ['step', 'process', 'procedure', 'workflow']:
                    score += 2
            
            # Boost score for exact phrase matches
            if query_lower in title_lower:
                score += 5
            elif query_lower in content_lower:
                score += 3
            
            if score > 0:
                result_item = item.copy()
                result_item['relevance_score'] = score
                scored_items.append(result_item)
        
        # Sort by score and return top results
        scored_items.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_items[:max_results]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        
        return {
            "embeddings_available": False,
            "vectorstore_available": False,
            "total_documents": len(self.knowledge_items),
            "faq_items": len([item for item in self.knowledge_items if item['type'] == 'faq']),
            "troubleshooting_items": len([item for item in self.knowledge_items if item['type'] == 'troubleshooting']),
            "procedure_items": len([item for item in self.knowledge_items if item['type'] == 'procedure']),
            "fallback_mode": True
        }
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Add new document"""
        
        item = {
            "title": metadata.get("title", "New Item"),
            "content": content,
            "type": metadata.get("type", "general"),
            "source": metadata.get("source", "manual"),
            "category": metadata.get("category", "general"),
            "metadata": metadata
        }
        
        self.knowledge_items.append(item)
        return True
