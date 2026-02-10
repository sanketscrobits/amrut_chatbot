"""
Query Expansion Module for RAG

Improves retrieval recall by generating semantic variations of user queries.
This helps match documents even when vocabulary differs between query and content.
"""

from typing import List
import re

# Synonym mapping for common query terms
SYNONYM_MAP = {
    # Action words
    "mitigation": ["prevention", "remedy", "solution", "countermeasure", "defense"],
    "strategy": ["method", "approach", "technique", "tactic", "plan"],
    "recommended": ["suggested", "advised", "proposed", "endorsed"],
    "implement": ["deploy", "execute", "apply", "install", "set up"],
    
    # Process words  
    "process": ["procedure", "workflow", "steps", "protocol", "method"],
    "guide": ["tutorial", "manual", "handbook", "instructions"],
    "policy": ["regulation", "rule", "guideline", "standard"],
    
    # Question words
    "how to": ["steps to", "way to", "method for", "procedure for"],
    "what is": ["definition of", "meaning of", "explain"],
    "why": ["reason for", "purpose of", "rationale for"],
    
    # Security/LLM terms
    "attack": ["threat", "exploit", "vulnerability", "breach"],
    "security": ["safety", "protection", "defense", "safeguard"],
    "risk": ["danger", "threat", "hazard", "vulnerability"],
    
    # Women safety terms
    "complaint": ["report", "grievance", "allegation", "claim"],
    "harassment": ["abuse", "misconduct", "violation", "assault"],
    "investigation": ["inquiry", "examination", "review", "probe"],
}


def expand_query(query: str, max_expansions: int = 3) -> List[str]:
    """
    Generate semantic variations of a query using synonym replacement.
    
    Args:
        query: Original user query
        max_expansions: Maximum number of variations to generate (including original)
    
    Returns:
        List of query variations, starting with original
    
    Example:
        >>> expand_query("What mitigation strategies are recommended?")
        [
            "What mitigation strategies are recommended?",
            "What prevention strategies are suggested?",
            "What remedy techniques are advised?"
        ]
    """
    expansions = [query]  # Always include original
    query_lower = query.lower()
    
    # Find all matching synonyms in the query
    matches = []
    for original, synonyms in SYNONYM_MAP.items():
        if original in query_lower:
            matches.append((original, synonyms))
    
    # Generate variations by replacing each matched term
    for original, synonyms in matches:
        # Take top 2 synonyms to avoid explosion
        for synonym in synonyms[:2]:
            # Case-insensitive replacement
            expanded = re.sub(
                r'\b' + re.escape(original) + r'\b',
                synonym,
                query,
                flags=re.IGNORECASE
            )
            
            if expanded not in expansions:
                expansions.append(expanded)
            
            # Stop if we've reached max
            if len(expansions) >= max_expansions:
                return expansions
    
    return expansions


def expand_query_smart(query: str) -> List[str]:
    """
    Smart query expansion that adjusts based on query complexity.
    
    - Simple queries: 2 variations
    - Complex queries: 3 variations
    - Very specific queries: Original only (to preserve specificity)
    
    Args:
        query: Original user query
    
    Returns:
        List of query variations
    """
    query_lower = query.lower()
    
    # Check if query is very specific (contains lots of detail)
    # If so, don't expand (preserve specificity)
    specific_indicators = [
        "specific", "exactly", "precise", "particular",
        "step-by-step", "detailed", "complete"
    ]
    
    if any(indicator in query_lower for indicator in specific_indicators):
        # Very specific - don't expand
        return [query]
    
    # Count complexity indicators
    complexity_score = 0
    complexity_score += len(query.split())  # Word count
    complexity_score += query.count("?")    # Multiple questions
    complexity_score += sum(1 for term in SYNONYM_MAP if term in query_lower)
    
    # Adjust expansion count based on complexity
    if complexity_score > 20:
        max_expansions = 3  # Complex query - more variations
    elif complexity_score > 10:
        max_expansions = 2  # Medium query
    else:
        max_expansions = 2  # Simple query
    
    return expand_query(query, max_expansions)


def get_expansion_debug_info(query: str) -> dict:
    """
    Get debug information about query expansion.
    
    Useful for monitoring and optimization.
    """
    expansions = expand_query_smart(query)
    
    return {
        "original": query,
        "expansions": expansions,
        "expansion_count": len(expansions),
        "matched_synonyms": [
            term for term in SYNONYM_MAP.keys()
            if term in query.lower()
        ]
    }


# Example usage
if __name__ == "__main__":
    test_queries = [
        "What mitigation strategies are recommended for prompt injection?",
        "How to implement security policies?",
        "What is the complaint process?",
        "Specific steps for investigation?"
    ]
    
    print("Query Expansion Examples:\n")
    for query in test_queries:
        expansions = expand_query_smart(query)
        print(f"Original: {query}")
        for i, exp in enumerate(expansions):
            if i == 0:
                continue
            print(f"  Variation {i}: {exp}")
        print()
