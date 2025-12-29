#!/usr/bin/env python3
"""Quick test of AAPL loading."""
from financial_agent import UnifiedFinancialAgent

print("Initializing agent...")
agent = UnifiedFinancialAgent()

print("Loading AAPL...")
result = agent.load_ticker("AAPL", market="US")

print("✓ Success!")
print(result)
