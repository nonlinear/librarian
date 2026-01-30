#!/usr/bin/env python3
"""
Infer topic from query using keyword matching + fuzzy search
"""
import sys
import json
from pathlib import Path
from difflib import get_close_matches

BOOKS_DIR = Path(__file__).parent.parent.parent / "books"
METADATA_FILE = BOOKS_DIR / "library-index.json"

def load_topics():
    """Load all topic IDs from metadata"""
    with open(METADATA_FILE) as f:
        data = json.load(f)
    return [t['id'] for t in data['topics']]

def infer_topic(query, topics):
    """Infer topic from query using keyword matching"""
    query_lower = query.lower()
    
    # Direct keyword matches
    scores = {}
    for topic_id in topics:
        score = 0
        topic_lower = topic_id.lower()
        
        # Split topic ID by underscore/slash
        topic_parts = topic_id.replace('_', ' ').replace('/', ' ').lower().split()
        query_words = query_lower.split()
        
        # Exact word matches get high score
        for part in topic_parts:
            if part in query_lower:
                score += 10
        
        # Partial matches
        for qword in query_words:
            if len(qword) >= 4:  # Only match words 4+ chars
                for part in topic_parts:
                    if qword in part or part in qword:
                        score += 3
        
        if score > 0:
            scores[topic_id] = score
    
    # Sort by score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    return ranked

def main():
    if len(sys.argv) < 2:
        print("Usage: infer_topic.py 'your query here'", file=sys.stderr)
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    topics = load_topics()
    matches = infer_topic(query, topics)
    
    if not matches:
        print(json.dumps({
            'status': 'no_match',
            'query': query,
            'suggestions': topics[:10]  # Show first 10 topics
        }, indent=2))
        sys.exit(1)
    
    # High confidence if top match is significantly higher than second
    confidence = 'high' if len(matches) == 1 or matches[0][1] > matches[1][1] * 1.5 else 'medium'
    
    result = {
        'status': 'success',
        'query': query,
        'confidence': confidence,
        'top_match': matches[0][0],
        'score': matches[0][1],
        'alternatives': [{'topic': t, 'score': s} for t, s in matches[1:6]]
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
