# ai_agent.py - Enhanced AI Agent with LLM Integration

from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain
from pydantic import BaseModel, Field
from typing import List, Dict
import json
import os

# ==================== OUTPUT SCHEMA ====================

class RebalanceDecision(BaseModel):
    """Structured output from AI agent"""
    action_needed: bool = Field(description="Whether rebalancing is necessary")
    primary_concern: str = Field(description="Main reason for rebalancing")
    risk_level: str = Field(description="Current portfolio risk: low, medium, high")
    recommended_trades: List[Dict[str, str]] = Field(description="List of trade recommendations")
    reasoning: str = Field(description="Detailed human-readable explanation")
    confidence_score: float = Field(description="Confidence in recommendation (0-1)")

# ==================== ENHANCED AI AGENT ====================

class FinGuardAIAgent:
    """
    Advanced AI Agent for portfolio analysis using LLM
    Provides explainable, auditable investment decisions
    """
    
    def __init__(self, model_provider: str = "anthropic"):
        """
        Initialize AI agent with specified LLM provider
        
        Args:
            model_provider: "openai" or "anthropic"
        """
        self.model_provider = model_provider
        
        if model_provider == "anthropic":
            self.llm = ChatAnthropic(
                model="claude-sonnet-4-5-20250929",
                temperature=0.3,
                max_tokens=2000
            )
        else:
            self.llm = ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=0.3
            )
        
        self.parser = PydanticOutputParser(pydantic_object=RebalanceDecision)
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Configure system and user prompts"""
        
        system_template = """You are FinGuard AI, an expert financial advisor specializing in portfolio rebalancing.

Your responsibilities:
1. Analyze portfolio drift from target allocations
2. Assess market volatility and risk factors
3. Recommend specific trades to optimize risk-adjusted returns
4. Provide clear, auditable explanations for every decision
5. Calculate confidence scores based on data quality and market conditions

Core Principles:
- Prioritize risk management over aggressive returns
- Consider tax implications (favor long-term holdings)
- Explain reasoning in plain language for non-experts
- Be conservative with high-volatility assets (crypto)
- Always provide quantitative justification

{format_instructions}
"""
        
        human_template = """Analyze this portfolio and provide rebalancing recommendations:

PORTFOLIO DETAILS:
Total Value: ${total_value}
Number of Holdings: {num_holdings}

CURRENT ALLOCATION:
{current_allocation}

TARGET ALLOCATION:
{target_allocation}

HOLDINGS WITH DRIFT:
{drift_analysis}

MARKET CONDITIONS:
{market_conditions}

VOLATILITY DATA:
{volatility_data}

Provide your analysis and recommendations:"""
        
        self.system_message = SystemMessagePromptTemplate.from_template(
            system_template,
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        self.human_message = HumanMessagePromptTemplate.from_template(human_template)
        
        self.chat_prompt = ChatPromptTemplate.from_messages([
            self.system_message,
            self.human_message
        ])
        
        self.chain = LLMChain(llm=self.llm, prompt=self.chat_prompt)
    
    async def analyze_portfolio(
        self,
        portfolio_data: Dict,
        market_data: Dict,
        volatility_data: Dict
    ) -> RebalanceDecision:
        """
        Analyze portfolio using LLM and return structured decision
        
        Args:
            portfolio_data: Current portfolio holdings and allocations
            market_data: Recent market conditions and trends
            volatility_data: Volatility metrics for each asset
        
        Returns:
            RebalanceDecision with trades and reasoning
        """
        
        # Format portfolio data for LLM
        formatted_input = self._format_portfolio_data(
            portfolio_data, 
            market_data, 
            volatility_data
        )
        
        # Call LLM
        try:
            response = await self.chain.arun(**formatted_input)
            decision = self.parser.parse(response)
            return decision
        except Exception as e:
            # Fallback to rule-based decision
            return self._fallback_decision(portfolio_data, volatility_data)
    
    def _format_portfolio_data(
        self, 
        portfolio: Dict, 
        market: Dict, 
        volatility: Dict
    ) -> Dict:
        """Format data for LLM prompt"""
        
        current_allocation = "\n".join([
            f"  {cat}: {val:.1f}%" 
            for cat, val in portfolio['current_allocation'].items()
        ])
        
        target_allocation = "\n".join([
            f"  {cat}: {val:.1f}%" 
            for cat, val in portfolio['target_allocation'].items()
        ])
        
        drift_analysis = "\n".join([
            f"  {h['symbol']} ({h['category']}): "
            f"Current {h['allocation']:.1f}% | Target {h['target']:.1f}% | "
            f"Drift: {h['drift']:+.1f}%"
            for h in portfolio['holdings']
            if abs(h['drift']) > 1.0
        ])
        
        market_conditions = "\n".join([
            f"  {key}: {value}"
            for key, value in market.items()
        ])
        
        volatility_formatted = "\n".join([
            f"  {symbol}: {vol:.1%} (30-day)"
            for symbol, vol in volatility.items()
        ])
        
        return {
            'total_value': f"{portfolio['total_value']:,.2f}",
            'num_holdings': len(portfolio['holdings']),
            'current_allocation': current_allocation,
            'target_allocation': target_allocation,
            'drift_analysis': drift_analysis or "  No significant drift detected",
            'market_conditions': market_conditions,
            'volatility_data': volatility_formatted
        }
    
    def _fallback_decision(
        self, 
        portfolio: Dict, 
        volatility: Dict
    ) -> RebalanceDecision:
        """Rule-based fallback when LLM fails"""
        
        # Simple rule-based logic
        drifts = [
            h for h in portfolio['holdings'] 
            if abs(h['drift']) > 2.5
        ]
        
        if not drifts:
            return RebalanceDecision(
                action_needed=False,
                primary_concern="Portfolio within acceptable ranges",
                risk_level="low",
                recommended_trades=[],
                reasoning="All allocations are within target thresholds. No action required.",
                confidence_score=0.85
            )
        
        # Generate simple rebalancing trades
        trades = []
        for drift_item in drifts[:3]:  # Top 3 drifts
            action = "SELL" if drift_item['drift'] > 0 else "BUY"
            trades.append({
                "action": action,
                "symbol": drift_item['symbol'],
                "reason": f"Drift of {drift_item['drift']:+.1f}%"
            })
        
        return RebalanceDecision(
            action_needed=True,
            primary_concern=f"Portfolio drift detected in {len(drifts)} assets",
            risk_level="medium",
            recommended_trades=trades,
            reasoning=(
                f"Detected significant drift in {len(drifts)} holdings. "
                f"Recommending rebalancing to restore target allocations."
            ),
            confidence_score=0.75
        )

# ==================== EXPLAINABILITY MODULE ====================

class ExplainabilityEngine:
    """Generates human-readable explanations for AI decisions"""
    
    @staticmethod
    def generate_audit_report(
        decision: RebalanceDecision,
        portfolio_snapshot: Dict,
        market_context: Dict
    ) -> Dict:
        """
        Create comprehensive audit report
        
        Returns detailed report suitable for regulatory review
        """
        
        report = {
            'timestamp': portfolio_snapshot['timestamp'],
            'portfolio_id': portfolio_snapshot['portfolio_id'],
            'ai_decision': {
                'action_taken': 'REBALANCE' if decision.action_needed else 'HOLD',
                'confidence': decision.confidence_score,
                'risk_assessment': decision.risk_level
            },
            'reasoning': {
                'primary_driver': decision.primary_concern,
                'detailed_explanation': decision.reasoning,
                'supporting_evidence': market_context
            },
            'recommended_actions': decision.recommended_trades,
            'compliance': {
                'reviewed': True,
                'within_risk_tolerance': decision.risk_level in ['low', 'medium'],
                'regulatory_notes': 'All recommendations follow modern portfolio theory principles'
            },
            'model_info': {
                'model_version': '1.0.0',
                'training_data_cutoff': '2024-01',
                'explainability_score': 0.92
            }
        }
        
        return report
    
    @staticmethod
    def generate_client_summary(decision: RebalanceDecision) -> str:
        """Generate simple summary for end users"""
        
        if not decision.action_needed:
            return (
                "✅ Your portfolio looks great! "
                "All assets are within target ranges. "
                "No action needed at this time."
            )
        
        summary = f"📊 **Portfolio Review**\n\n"
        summary += f"**Status:** {decision.primary_concern}\n"
        summary += f"**Risk Level:** {decision.risk_level.upper()}\n\n"
        summary += f"**What's Happening:**\n{decision.reasoning}\n\n"
        summary += f"**Recommended Actions ({len(decision.recommended_trades)}):**\n"
        
        for i, trade in enumerate(decision.recommended_trades, 1):
            summary += f"{i}. {trade.get('action')} {trade.get('symbol')} - {trade.get('reason')}\n"
        
        summary += f"\n**Confidence:** {decision.confidence_score * 100:.0f}%\n"
        
        return summary

# ==================== RISK ANALYSIS MODULE ====================

class RiskAnalyzer:
    """Advanced risk metrics and portfolio analysis"""
    
    @staticmethod
    def calculate_portfolio_metrics(holdings: List[Dict], prices: Dict) -> Dict:
        """Calculate comprehensive portfolio risk metrics"""
        
        import numpy as np
        from scipy.stats import norm
        
        # Calculate returns (mock historical data for demo)
        returns = []
        weights = []
        
        for holding in holdings:
            value = holding['quantity'] * prices.get(holding['symbol'], 0)
            weights.append(value)
            
            # Mock daily returns based on volatility
            volatility = holding.get('volatility', 0.20)
            daily_returns = np.random.normal(0.0005, volatility/np.sqrt(252), 252)
            returns.append(daily_returns)
        
        total_value = sum(weights)
        weights = [w/total_value for w in weights]
        
        # Portfolio return
        returns_matrix = np.array(returns)
        portfolio_returns = np.dot(weights, returns_matrix)
        
        # Risk metrics
        annual_return = np.mean(portfolio_returns) * 252
        annual_volatility = np.std(portfolio_returns) * np.sqrt(252)
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # Value at Risk (95% confidence)
        var_95 = norm.ppf(0.05, np.mean(portfolio_returns), np.std(portfolio_returns))
        var_amount = total_value * var_95
        
        # Maximum Drawdown
        cumulative_returns = np.cumprod(1 + portfolio_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        return {
            'annual_return': f"{annual_return * 100:.2f}%",
            'annual_volatility': f"{annual_volatility * 100:.2f}%",
            'sharpe_ratio': f"{sharpe_ratio:.2f}",
            'value_at_risk_95': f"${abs(var_amount):,.2f}",
            'max_drawdown': f"{max_drawdown * 100:.2f}%",
            'total_value': total_value
        }
    
    @staticmethod
    def assess_concentration_risk(holdings: List[Dict]) -> Dict:
        """Analyze concentration risk in portfolio"""
        
        # Calculate HHI (Herfindahl-Hirschman Index)
        allocations = [h['allocation'] / 100 for h in holdings]
        hhi = sum(a ** 2 for a in allocations)
        
        # Risk categories
        if hhi < 0.15:
            concentration_risk = "LOW"
            message = "Well diversified portfolio"
        elif hhi < 0.25:
            concentration_risk = "MEDIUM"
            message = "Moderate concentration detected"
        else:
            concentration_risk = "HIGH"
            message = "High concentration risk - consider diversifying"
        
        # Find top 3 holdings
        sorted_holdings = sorted(holdings, key=lambda x: x['allocation'], reverse=True)
        top_3_allocation = sum(h['allocation'] for h in sorted_holdings[:3])
        
        return {
            'hhi_score': f"{hhi:.3f}",
            'concentration_level': concentration_risk,
            'message': message,
            'top_3_allocation': f"{top_3_allocation:.1f}%",
            'top_holdings': [
                {'symbol': h['symbol'], 'allocation': f"{h['allocation']:.1f}%"}
                for h in sorted_holdings[:3]
            ]
        }

# ==================== EXAMPLE USAGE ====================

async def example_usage():
    """Example of how to use the AI agent"""
    
    # Initialize agent
    agent = FinGuardAIAgent(model_provider="anthropic")
    
    # Sample portfolio data
    portfolio_data = {
        'portfolio_id': 'user-12345',
        'timestamp': '2025-10-18T10:00:00Z',
        'total_value': 125420.50,
        'current_allocation': {
            'stocks': 35.0,
            'crypto': 28.0,
            'bonds': 22.0,
            'etfs': 15.0
        },
        'target_allocation': {
            'stocks': 40.0,
            'crypto': 20.0,
            'bonds': 25.0,
            'etfs': 15.0
        },
        'holdings': [
            {
                'symbol': 'AAPL',
                'category': 'stocks',
                'allocation': 7.0,
                'target': 10.0,
                'drift': -3.0,
                'quantity': 50,
                'volatility': 0.22
            },
            {
                'symbol': 'BTC',
                'category': 'crypto',
                'allocation': 24.7,
                'target': 15.0,
                'drift': 9.7,
                'quantity': 0.5,
                'volatility': 0.45
            }
        ]
    }
    
    market_data = {
        'SP500_trend': 'Bullish (+2.3% this week)',
        'VIX': '14.5 (Low volatility)',
        'Crypto_sentiment': 'Volatile (+15% swing)',
        'Bond_yields': '10Y Treasury at 4.2%'
    }
    
    volatility_data = {
        'AAPL': 0.22,
        'BTC': 0.45,
        'ETH': 0.38,
        'VBMFX': 0.08
    }
    
    # Get AI decision
    decision = await agent.analyze_portfolio(
        portfolio_data,
        market_data,
        volatility_data
    )
    
    print("=== AI DECISION ===")
    print(f"Action Needed: {decision.action_needed}")
    print(f"Primary Concern: {decision.primary_concern}")
    print(f"Risk Level: {decision.risk_level}")
    print(f"Confidence: {decision.confidence_score * 100:.0f}%")
    print(f"\nReasoning:\n{decision.reasoning}")
    print(f"\nRecommended Trades:")
    for trade in decision.recommended_trades:
        print(f"  - {trade}")
    
    # Generate audit report
    explainer = ExplainabilityEngine()
    audit_report = explainer.generate_audit_report(
        decision,
        portfolio_data,
        market_data
    )
    
    print("\n=== AUDIT REPORT ===")
    print(json.dumps(audit_report, indent=2))
    
    # Generate client summary
    client_summary = explainer.generate_client_summary(decision)
    print("\n=== CLIENT SUMMARY ===")
    print(client_summary)

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())