from financial_agent import UnifiedFinancialAgent
import json

agent = UnifiedFinancialAgent()

print('Loading AAPL...')
load_status = agent.load_ticker('AAPL', market='US')
print('Load status:', load_status)

print('Running query...')
res = agent.query('AAPL', 'Summarize revenue and margin trends.', market='US')

out = {
    'answer': res.get('answer') if res else None,
    'confidence_score': res.get('confidence_score') if res else None,
    'verification_details': res.get('verification_details') if res else None,
}
print(json.dumps(out, indent=2))
