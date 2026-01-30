#!/usr/bin/env python3
"""
Smart research wrapper - infers topic automatically and runs search
"""
import sys
import json
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

def infer_topic(query):
    """Infer topic using infer_topic.py"""
    result = subprocess.run(
        ['python3', str(SCRIPT_DIR / 'infer_topic.py'), query],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

def run_research(query, topic, k=5):
    """Run research.py with topic"""
    result = subprocess.run(
        ['python3', str(SCRIPT_DIR / 'research.py'), query, '--topic', topic, '--top-k', str(k)],
        capture_output=True,
        text=True
    )
    
    # Filter out logs/warnings, only return JSON
    lines = result.stdout.strip().split('\n')
    json_start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break
    
    if json_start >= 0:
        json_str = '\n'.join(lines[json_start:])
        return json.loads(json_str)
    else:
        return {'error': 'No JSON output from research.py', 'raw': result.stdout}

def main():
    if len(sys.argv) < 2:
        print("Usage: smart_research.py 'your query' [--top-k N] [--interactive]", file=sys.stderr)
        sys.exit(1)
    
    # Parse args
    interactive = '--interactive' in sys.argv
    k = 5
    
    if '--top-k' in sys.argv:
        idx = sys.argv.index('--top-k')
        k = int(sys.argv[idx + 1])
        sys.argv.pop(idx)  # Remove --top-k
        sys.argv.pop(idx)  # Remove value
    
    if '--interactive' in sys.argv:
        sys.argv.remove('--interactive')
    
    query = ' '.join(sys.argv[1:])
    
    print(f"🔍 Analyzing query: {query}\n", file=sys.stderr)
    
    # Infer topic
    inference = infer_topic(query)
    
    if inference['status'] != 'success':
        print("❌ Could not infer topic. Available topics:", file=sys.stderr)
        print(json.dumps(inference['suggestions'], indent=2))
        sys.exit(1)
    
    topic = inference['top_match']
    confidence = inference['confidence']
    
    print(f"📊 Topic inference:", file=sys.stderr)
    print(f"   Top match: {topic} (score: {inference['score']})", file=sys.stderr)
    print(f"   Confidence: {confidence}", file=sys.stderr)
    
    # If medium confidence and interactive, ask
    if confidence == 'medium' and interactive and inference.get('alternatives'):
        print(f"\n⚠️  Medium confidence. Alternatives:", file=sys.stderr)
        for i, alt in enumerate(inference['alternatives'][:3], 1):
            print(f"   {i}. {alt['topic']} (score: {alt['score']})", file=sys.stderr)
        
        choice = input(f"\nUse '{topic}'? (y/n or number): ").strip().lower()
        
        if choice == 'n':
            sys.exit(0)
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(inference['alternatives']):
                topic = inference['alternatives'][idx]['topic']
    
    print(f"\n🚀 Searching in topic: {topic}\n", file=sys.stderr)
    
    # Run research
    results = run_research(query, topic, k)
    
    # Output clean JSON
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
