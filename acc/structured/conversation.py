import json
import re
from typing import List, Dict, Any

class ConversationCompressor:
    def __init__(self, backend="hybrid"):
        self.backend = backend
        
    def deterministic_extract(self, text: str) -> str:
        """
        Stage 1: Deterministic Extraction
        Extracts TODOs, action items, URLs, decisions with explicit markers.
        Very cheap.
        """
        extracted = []
        lines = text.split('\n')
        
        # Regex patterns for high-signal lines
        patterns = [
            r'(?i)\bTODO\b',
            r'(?i)\bDECISION:',
            r'(?i)\bCONSTRAINT:',
            r'(?i)<goal>',
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        ]
        
        # Also capture command invocations, e.g., 'TOOL CALL: run_command'
        for line in lines:
            if any(re.search(p, line) for p in patterns):
                extracted.append(line)
            # Keep a small footprint of recent agent actions without outputs
            elif "TOOL CALL:" in line:
                extracted.append(line)
                
        return "\n".join(extracted)
        
    def segment(self, text: str) -> List[str]:
        """
        Stage 2: Conversation Segmentation
        Splits conversation into manageable logical chunks to reduce semantic workload.
        """
        chunks = []
        current_chunk = []
        
        # Segment by User/Agent turns or line count
        for line in text.split('\n'):
            if line.startswith("USER:") and len(current_chunk) > 200:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
            current_chunk.append(line)
            
            if len(current_chunk) > 500:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                
        if current_chunk:
            chunks.append("\n".join(current_chunk))
            
        return chunks

    def semantic_extract(self, chunk: str) -> Dict[str, List[str]]:
        """
        Stage 3: Semantic Extraction (Pluggable Backend)
        Supported Backends: cloud, local, heuristic
        """
        from acc.core.llm import extract_semantic_state
        return extract_semantic_state(chunk, self.backend)

    def state_merger(self, states: List[Dict[str, List[str]]]) -> Dict[str, List[str]]:
        """
        Stage 4: State Merger
        Merges chunk outputs, deduplicates, resolves conflicts.
        """
        merged = {
            "goals": [],
            "constraints": [],
            "decisions": [],
            "current_state": [],
            "open_tasks": []
        }
        
        for s in states:
            for k in merged.keys():
                merged[k].extend(s.get(k, []))
                
        # Deduplicate while preserving recency order
        for k in merged.keys():
            merged[k] = list(dict.fromkeys(merged[k]))
            
        return merged

    def compress(self, text: str) -> str:
        # Optional: We could run semantic extraction ON the deterministic extraction
        # to save even more tokens, or combine both.
        # Following the architecture: Text -> Deterministic -> Segmenter -> Semantic -> Merger
        
        # We'll use deterministic extract as a fast-pass filter to reduce the text
        # before passing it to the segmenter and LLM to save tokens.
        reduced_text = self.deterministic_extract(text)
        
        # Fallback to original text if deterministic extraction missed context
        if not reduced_text.strip():
            reduced_text = text
            
        chunks = self.segment(reduced_text)
        states = [self.semantic_extract(chunk) for chunk in chunks]
        final_state = self.state_merger(states)
        
        return json.dumps(final_state, indent=2)

def compress_conversation(text: str, backend: str = "heuristic") -> str:
    compressor = ConversationCompressor(backend=backend)
    return compressor.compress(text)
