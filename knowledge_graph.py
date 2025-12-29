"""Knowledge Graph Layer for Neuro-Symbolic Financial RAG.

Uses NetworkX to build a symbolic representation of company relationships,
sectors, peers, and key financial metrics for enhanced context.
"""
from typing import Dict, List, Optional, Tuple, Set
import networkx as nx
import re
from datetime import datetime
from utils import logger, save_json, load_json


class FinancialKnowledgeGraph:
    """NetworkX-based knowledge graph for financial entities and relationships."""

    def __init__(self):
        self.graph = nx.DiGraph()  # Directed graph for relationships
        self.metadata: Dict = {}  # Store node attributes
        self.metrics_history: Dict[str, Dict[int, float]] = {}  # ticker -> {year: value}

    def add_company_node(self, ticker: str, company_name: str, sector: str, market: str = "US") -> None:
        """Add a company node to the graph."""
        self.graph.add_node(ticker, node_type="company", name=company_name, sector=sector, market=market)
        self.metadata[ticker] = {"name": company_name, "sector": sector, "market": market, "created_at": datetime.utcnow().isoformat()}

    def add_metric_node(self, ticker: str, metric_name: str, value: float, year: int) -> None:
        """Add or update a key metric node (Revenue, NetIncome, Margin, EPS, etc.)."""
        metric_key = f"{ticker}_{metric_name}_{year}"
        self.graph.add_node(
            metric_key,
            node_type="metric",
            ticker=ticker,
            metric=metric_name,
            value=value,
            year=year
        )
        self.graph.add_edge(ticker, metric_key, relationship="has_metric")

        # Track historical metrics
        if ticker not in self.metrics_history:
            self.metrics_history[ticker] = {}
        if metric_name not in self.metrics_history[ticker]:
            self.metrics_history[ticker][metric_name] = {}
        self.metrics_history[ticker][metric_name][year] = value

    def add_sector_node(self, sector: str) -> None:
        """Add a sector node."""
        if sector not in self.graph:
            self.graph.add_node(sector, node_type="sector")

    def add_peer_relationship(self, ticker1: str, ticker2: str, similarity: float = 0.8) -> None:
        """Add a peer relationship between two companies."""
        self.graph.add_edge(ticker1, ticker2, relationship="peer", similarity=similarity)

    def add_sector_relationship(self, ticker: str, sector: str) -> None:
        """Link a company to its sector."""
        self.add_sector_node(sector)
        self.graph.add_edge(ticker, sector, relationship="belongs_to")

    def get_peers(self, ticker: str) -> List[str]:
        """Get all peer companies for a ticker."""
        peers = []
        for node, edge_data in self.graph[ticker].items():
            if edge_data.get("relationship") == "peer":
                peers.append(node)
        return peers

    def get_metrics(self, ticker: str, metric_name: Optional[str] = None) -> Dict[int, float]:
        """Get historical metrics for a company."""
        if ticker not in self.metrics_history:
            return {}
        if metric_name:
            return self.metrics_history[ticker].get(metric_name, {})
        return self.metrics_history[ticker]

    def get_trend(self, ticker: str, metric_name: str) -> Tuple[List[int], List[float], str]:
        """Get historical trend for a metric.

        Returns: (years, values, trend_direction) where trend_direction is 'up', 'down', or 'stable'
        """
        metrics = self.get_metrics(ticker, metric_name)
        if not metrics or len(metrics) < 2:
            return [], [], "unknown"

        years = sorted(metrics.keys())
        values = [metrics[y] for y in years]

        # Detect trend
        if len(values) >= 2:
            first = values[0]
            last = values[-1]
            change_pct = ((last - first) / abs(first)) * 100 if first != 0 else 0
            if change_pct > 5:
                trend = "up"
            elif change_pct < -5:
                trend = "down"
            else:
                trend = "stable"
        else:
            trend = "unknown"

        return years, values, trend

    def extract_metrics_from_text(self, text: str, ticker: str, year: int) -> Dict[str, float]:
        """Extract key financial metrics from unstructured text using regex patterns."""
        metrics = {}

        # Revenue patterns (in billions or millions)
        rev_patterns = [
            (r"(?:total\s+)?revenue[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:B|Billion)", 1e9),
            (r"(?:total\s+)?revenue[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:M|Million)", 1e6),
            (r"(?:net\s+)?sales[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:B|Billion)", 1e9),
            (r"(?:net\s+)?sales[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:M|Million)", 1e6),
        ]
        for pattern, multiplier in rev_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    val = float(m.group(1).replace(",", "")) * multiplier
                    metrics["revenue"] = val
                    break
                except:
                    pass

        # Net Income patterns
        ni_patterns = [
            (r"(?:net\s+)?income[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:B|Billion)", 1e9),
            (r"(?:net\s+)?income[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:M|Million)", 1e6),
            (r"(?:net\s+)?profit[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:B|Billion)", 1e9),
            (r"(?:net\s+)?profit[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:M|Million)", 1e6),
        ]
        for pattern, multiplier in ni_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    val = float(m.group(1).replace(",", "")) * multiplier
                    metrics["net_income"] = val
                    break
                except:
                    pass

        # Margin patterns (percentage)
        margin_patterns = [
            r"(?:net\s+)?margin[:\s]+([0-9,]+(?:\.[0-9]+)?)\s*%",
            r"(?:operating\s+)?margin[:\s]+([0-9,]+(?:\.[0-9]+)?)\s*%",
        ]
        for pattern in margin_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    val = float(m.group(1).replace(",", ""))
                    metrics["margin"] = val
                    break
                except:
                    pass

        # EPS patterns
        eps_pattern = r"(?:earnings?\s+per\s+share|EPS)[:\s]+\$?([0-9,]+(?:\.[0-9]+)?)"
        m = re.search(eps_pattern, text, re.IGNORECASE)
        if m:
            try:
                metrics["eps"] = float(m.group(1).replace(",", ""))
            except:
                pass

        # Add extracted metrics to graph
        for metric_name, value in metrics.items():
            self.add_metric_node(ticker, metric_name, value, year)

        return metrics

    def get_context_prompt(self, ticker: str) -> str:
        """Generate a context string from the knowledge graph for LLM prompt."""
        context_parts = []

        # Company info
        if ticker in self.graph:
            attrs = self.graph.nodes[ticker]
            context_parts.append(f"Company: {attrs.get('name', ticker)} ({ticker})")
            context_parts.append(f"Sector: {attrs.get('sector', 'Unknown')}")

        # Peers
        peers = self.get_peers(ticker)
        if peers:
            context_parts.append(f"Peers: {', '.join(peers)}")

        # Key metrics
        metrics = self.get_metrics(ticker)
        if metrics:
            context_parts.append("\nKey Metrics (Historical):")
            for metric_name, years_data in metrics.items():
                if years_data:
                    latest_year = max(years_data.keys())
                    latest_value = years_data[latest_year]
                    context_parts.append(f"  {metric_name.title()} ({latest_year}): {latest_value:,.2f}")

        return "\n".join(context_parts)

    def save(self, path: str) -> None:
        """Save graph to JSON (simplified serialization)."""
        data = {
            "nodes": list(self.graph.nodes(data=True)),
            "edges": list(self.graph.edges(data=True)),
            "metrics_history": {k: {m: {str(y): v for y, v in yd.items()} for m, yd in mv.items()} 
                               for k, mv in self.metrics_history.items()},
            "metadata": self.metadata
        }
        save_json(data, path)

    def load(self, path: str) -> None:
        """Load graph from JSON."""
        data = load_json(path)
        if not data:
            return
        # Reconstruct graph
        self.graph.clear()
        for node, attrs in data.get("nodes", []):
            self.graph.add_node(node, **attrs)
        for src, dst, attrs in data.get("edges", []):
            self.graph.add_edge(src, dst, **attrs)
        # Reconstruct metrics history
        self.metrics_history = {k: {m: {int(y): v for y, v in yd.items()} 
                                    for m, yd in mv.items()} 
                               for k, mv in data.get("metrics_history", {}).items()}
        self.metadata = data.get("metadata", {})

    def visualize_summary(self, ticker: str) -> str:
        """Return a text summary of the knowledge graph for a ticker."""
        lines = [f"=== Knowledge Graph for {ticker} ==="]

        # Node count
        total_nodes = self.graph.number_of_nodes()
        ticker_related = sum(1 for n in self.graph.nodes() if n.startswith(ticker))
        lines.append(f"Total nodes in graph: {total_nodes}")
        lines.append(f"Nodes related to {ticker}: {ticker_related}")

        # Peers
        peers = self.get_peers(ticker)
        if peers:
            lines.append(f"Peers: {', '.join(peers)}")

        # Metrics
        metrics = self.get_metrics(ticker)
        if metrics:
            lines.append(f"Tracked metrics: {', '.join(metrics.keys())}")
            for metric_name, years_data in metrics.items():
                years, values, trend = self.get_trend(ticker, metric_name)
                lines.append(f"  {metric_name}: {trend} ↑" if trend == "up" else f"  {metric_name}: {trend}")

        return "\n".join(lines)
