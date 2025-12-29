#!/usr/bin/env python
"""FinChat Global — Setup Verification Script

Run this to check if everything is properly configured.
"""
import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_required_files():
    """Check if all required files exist."""
    required = [
        'config.py', 'utils.py', 'document_fetcher.py', 'document_processor.py',
        'embedding_manager.py', 'rag_engine.py', 'financial_agent.py', 'app.py',
        'knowledge_graph.py', 'verification_agents.py',
        'requirements.txt', '.env.example'
    ]
    
    missing = []
    for f in required:
        if not Path(f).exists():
            missing.append(f)
    
    if not missing:
        print(f"✓ All {len(required)} required files present")
        return True
    else:
        print(f"✗ Missing files: {missing}")
        return False

def check_env_file():
    """Check if .env file exists."""
    if Path('.env').exists():
        print("✓ .env file exists")
        # Check if it has API key
        with open('.env', 'r') as f:
            content = f.read()
            if 'your_groq_key_here' in content or not any(x in content for x in ['GROQ_API_KEY=gsk_', 'OPENAI_API_KEY=sk_']):
                print("  ⚠ WARNING: No valid API key found in .env")
                print("    Add your Groq key: GROQ_API_KEY=gsk_YOUR_KEY")
                return False
        return True
    else:
        print("✗ .env file not found")
        print("  Run: copy .env.example .env")
        return False

def check_dependencies():
    """Check if key Python packages are installed."""
    packages = [
        ('streamlit', 'Streamlit UI'),
        ('networkx', 'Knowledge Graphs'),
        ('requests', 'HTTP requests'),
        ('bs4', 'Web scraping'),
        ('dotenv', 'Environment variables'),
        ('PyPDF2', 'PDF parsing'),
    ]
    
    missing = []
    for pkg_name, description in packages:
        try:
            __import__(pkg_name)
            print(f"✓ {pkg_name:20} ({description})")
        except ImportError:
            missing.append((pkg_name, description))
    
    if missing:
        print(f"\n✗ Missing packages:")
        for pkg, desc in missing:
            print(f"  - {pkg} ({desc})")
        print("\nRun: pip install -r requirements.txt")
        return False
    return True

def check_imports():
    """Check if FinChat modules import successfully."""
    try:
        from financial_agent import UnifiedFinancialAgent
        print("✓ FinChat modules import successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import FinChat: {e}")
        return False

def print_header():
    print("\n" + "="*70)
    print("  FinChat Global — Setup Verification")
    print("="*70 + "\n")

def print_footer(all_pass):
    print("\n" + "="*70)
    if all_pass:
        print("  ✅ ALL CHECKS PASSED - System is ready!")
        print("\n  Next steps:")
        print("    1. python integration_example.py      (see examples)")
        print("    2. streamlit run app.py               (launch dashboard)")
        print("    3. python tests.py                    (run tests)")
    else:
        print("  ⚠ Some checks failed - see above for fixes")
    print("="*70 + "\n")

def main():
    print_header()
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Files", check_required_files),
        ("Configuration", check_env_file),
        ("Dependencies", check_dependencies),
        ("Imports", check_imports),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        print("-" * 70)
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"✗ Error: {e}")
            results.append(False)
    
    all_pass = all(results)
    print_footer(all_pass)
    
    return 0 if all_pass else 1

if __name__ == '__main__':
    sys.exit(main())
