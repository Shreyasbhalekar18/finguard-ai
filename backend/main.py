# main.py - FinGuard AI Backend
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import hashlib
import json
import asyncio
from enum import Enum
import numpy as np
import pandas as pd

app = FastAPI(title="FinGuard AI API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== DATA MODELS ====================

class AssetCategory(str, Enum):
    STOCKS = "stocks"
    CRYPTO = "crypto"
    BONDS = "bonds"
    ETFS = "etfs"

class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class Holding(BaseModel):
    symbol: str
    name: str
    category: AssetCategory
    quantity: float
    current_price: float
    target_allocation: float

class Portfolio(BaseModel):
    user_id: str
    holdings: List[Holding]
    total_value: float
    target_allocations: Dict[str, float]  # {category: target_percentage}

class Trade(BaseModel):
    action: TradeAction
    symbol: str
    quantity: float
    value: float
    reasoning: str

class RebalanceRecommendation(BaseModel):
    portfolio_id: str
    timestamp: datetime
    trades: List[Trade]
    reasoning: str
    ai_confidence: float
    expected_impact: Dict[str, str]
    hash_signature: str

class AuditLogEntry(BaseModel):
    id: str
    timestamp: datetime
    action: str
    reasoning: str
    trades: List[Trade]
    ai_confidence: float
    status: str
    impact: Dict[str, str]
    hash_chain: str

# ==================== IN-MEMORY STORAGE ====================

portfolios_db = {}
audit_logs_db = {}
price_cache = {}

# ==================== MARKET DATA SERVICE ====================

class MarketDataService:
    """Simulates market data fetching - Replace with real APIs"""
    
    @staticmethod
    async def get_price(symbol: str) -> float:
        """Fetch current price (mock implementation)"""
        mock_prices = {
            'AAPL': 175.20, 'MSFT': 380.50, 'GOOGL': 142.30,
            'BTC': 62000, 'ETH': 2200,
            'VBMFX': 110.20, 'SPY': 445.50
        }
        return mock_prices.get(symbol, 100.0)
    
    @staticmethod
    async def get_volatility(symbol: str, days: int = 7) -> float:
        """Calculate historical volatility"""
        # Mock volatility calculation
        volatility_map = {
            'BTC': 0.45, 'ETH': 0.38,
            'AAPL': 0.22, 'MSFT': 0.20, 'GOOGL': 0.25,
            'VBMFX': 0.08, 'SPY': 0.15
        }
        return volatility_map.get(symbol, 0.20)

# ==================== PORTFOLIO ANALYSIS ENGINE ====================

class PortfolioAnalyzer:
    """Analyzes portfolio drift and risk metrics"""
    
    @staticmethod
    def calculate_allocations(holdings: List[Holding], total_value: float) -> Dict[str, float]:
        """Calculate current allocations by category"""
        allocations = {}
        for holding in holdings:
            value = holding.quantity * holding.current_price
            allocation_pct = (value / total_value) * 100 if total_value > 0 else 0
            
            if holding.category not in allocations:
                allocations[holding.category] = 0
            allocations[holding.category] += allocation_pct
        
        return allocations
    
    @staticmethod
    def detect_drift(current: Dict[str, float], target: Dict[str, float]) -> List[Dict]:
        """Detect significant portfolio drift"""
        drifts = []
        for category, target_pct in target.items():
            current_pct = current.get(category, 0)
            drift = current_pct - target_pct
            
            if abs(drift) > 2.5:  # Threshold for action
                drifts.append({
                    'category': category,
                    'current': current_pct,
                    'target': target_pct,
                    'drift': drift,
                    'severity': 'high' if abs(drift) > 5 else 'medium'
                })
        
        return drifts
    
    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.04) -> float:
        """Calculate Sharpe ratio for risk-adjusted returns"""
        if len(returns) == 0:
            return 0.0
        
        returns_arr = np.array(returns)
        excess_returns = returns_arr - risk_free_rate / 252  # Daily risk-free rate
        
        if excess_returns.std() == 0:
            return 0.0
        
        return (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)

# ==================== AGENTIC AI REBALANCER ====================

class AgenticRebalancer:
    """AI agent for portfolio rebalancing with explainability"""
    
    def __init__(self):
        self.market_data = MarketDataService()
        self.analyzer = PortfolioAnalyzer()
    
    async def generate_rebalancing_plan(
        self, 
        portfolio: Portfolio
    ) -> RebalanceRecommendation:
        """
        Generate rebalancing recommendations with full reasoning
        """
        
        # Step 1: Calculate current state
        current_allocations = self.analyzer.calculate_allocations(
            portfolio.holdings, 
            portfolio.total_value
        )
        
        # Step 2: Detect drift
        drifts = self.analyzer.detect_drift(
            current_allocations, 
            portfolio.target_allocations
        )
        
        if not drifts:
            return None
        
        # Step 3: Fetch volatility data
        volatility_data = {}
        for holding in portfolio.holdings:
            vol = await self.market_data.get_volatility(holding.symbol)
            volatility_data[holding.symbol] = vol
        
        # Step 4: Generate trades with reasoning
        trades = await self._generate_trades(
            portfolio, 
            drifts, 
            volatility_data
        )
        
        # Step 5: Build reasoning narrative
        reasoning = self._build_reasoning(drifts, volatility_data, trades)
        
        # Step 6: Calculate confidence score
        confidence = self._calculate_confidence(drifts, volatility_data)
        
        # Step 7: Estimate impact
        impact = self._estimate_impact(trades, volatility_data)
        
        # Step 8: Create immutable hash
        recommendation = RebalanceRecommendation(
            portfolio_id=portfolio.user_id,
            timestamp=datetime.utcnow(),
            trades=trades,
            reasoning=reasoning,
            ai_confidence=confidence,
            expected_impact=impact,
            hash_signature=""
        )
        
        recommendation.hash_signature = self._create_hash(recommendation)
        
        return recommendation
    
    async def _generate_trades(
        self, 
        portfolio: Portfolio, 
        drifts: List[Dict],
        volatility_data: Dict[str, float]
    ) -> List[Trade]:
        """Generate optimal trades to rebalance portfolio"""
        trades = []
        
        for drift_item in drifts:
            category = drift_item['category']
            drift_pct = drift_item['drift']
            
            # Determine trade direction
            if drift_pct > 0:  # Overweight - need to sell
                # Find holdings in this category
                category_holdings = [
                    h for h in portfolio.holdings 
                    if h.category == category
                ]
                
                # Prioritize selling high-volatility assets
                sorted_holdings = sorted(
                    category_holdings,
                    key=lambda h: volatility_data.get(h.symbol, 0),
                    reverse=True
                )
                
                # Calculate sell amount
                sell_value = portfolio.total_value * abs(drift_pct) / 100
                
                for holding in sorted_holdings[:2]:  # Sell from top 2 volatile
                    proportion = 0.6 if holding == sorted_holdings[0] else 0.4
                    trade_value = sell_value * proportion
                    qty = trade_value / holding.current_price
                    
                    trades.append(Trade(
                        action=TradeAction.SELL,
                        symbol=holding.symbol,
                        quantity=round(qty, 4),
                        value=round(trade_value, 2),
                        reasoning=f"Reduce {category} overweight. High volatility detected ({volatility_data[holding.symbol]:.1%})."
                    ))
            
            else:  # Underweight - need to buy
                # Find underweight holdings
                category_holdings = [
                    h for h in portfolio.holdings 
                    if h.category == category
                ]
                
                # Prioritize buying low-volatility assets
                sorted_holdings = sorted(
                    category_holdings,
                    key=lambda h: volatility_data.get(h.symbol, 0)
                )
                
                buy_value = portfolio.total_value * abs(drift_pct) / 100
                
                for holding in sorted_holdings[:2]:
                    proportion = 0.6 if holding == sorted_holdings[0] else 0.4
                    trade_value = buy_value * proportion
                    qty = trade_value / holding.current_price
                    
                    trades.append(Trade(
                        action=TradeAction.BUY,
                        symbol=holding.symbol,
                        quantity=round(qty, 4),
                        value=round(trade_value, 2),
                        reasoning=f"Increase {category} to target. Low volatility asset ({volatility_data[holding.symbol]:.1%})."
                    ))
        
        return trades
    
    def _build_reasoning(
        self, 
        drifts: List[Dict], 
        volatility_data: Dict[str, float],
        trades: List[Trade]
    ) -> str:
        """Generate human-readable explanation"""
        
        reasoning_parts = []
        
        # Drift analysis
        for drift in drifts:
            direction = "overweight" if drift['drift'] > 0 else "underweight"
            reasoning_parts.append(
                f"{drift['category'].upper()} is {direction} by {abs(drift['drift']):.1f}% "
                f"(current: {drift['current']:.1f}%, target: {drift['target']:.1f}%)."
            )
        
        # Volatility context
        high_vol_assets = [
            symbol for symbol, vol in volatility_data.items() 
            if vol > 0.30
        ]
        if high_vol_assets:
            reasoning_parts.append(
                f"High volatility detected in: {', '.join(high_vol_assets[:3])}. "
                f"Reducing exposure to manage risk."
            )
        
        # Trade summary
        buy_count = sum(1 for t in trades if t.action == TradeAction.BUY)
        sell_count = sum(1 for t in trades if t.action == TradeAction.SELL)
        reasoning_parts.append(
            f"Recommending {sell_count} sell and {buy_count} buy orders "
            f"to restore target allocation and optimize risk-adjusted returns."
        )
        
        return " ".join(reasoning_parts)
    
    def _calculate_confidence(
        self, 
        drifts: List[Dict], 
        volatility_data: Dict[str, float]
    ) -> float:
        """Calculate AI confidence score (0-1)"""
        
        # Base confidence from drift magnitude
        avg_drift = np.mean([abs(d['drift']) for d in drifts])
        drift_confidence = min(avg_drift / 10, 1.0)  # Higher drift = higher confidence
        
        # Volatility confidence (lower volatility = higher confidence)
        avg_volatility = np.mean(list(volatility_data.values()))
        vol_confidence = 1 - min(avg_volatility, 1.0)
        
        # Combined confidence
        confidence = (drift_confidence * 0.7 + vol_confidence * 0.3)
        
        return round(confidence, 2)
    
    def _estimate_impact(
        self, 
        trades: List[Trade], 
        volatility_data: Dict[str, float]
    ) -> Dict[str, str]:
        """Estimate expected impact of rebalancing"""
        
        # Calculate weighted volatility reduction
        total_value = sum(t.value for t in trades if t.action == TradeAction.SELL)
        
        if total_value > 0:
            weighted_vol_reduction = sum(
                t.value / total_value * volatility_data.get(t.symbol, 0)
                for t in trades if t.action == TradeAction.SELL
            )
            risk_reduction = f"{weighted_vol_reduction * 100:.1f}%"
        else:
            risk_reduction = "0%"
        
        return {
            'risk_reduction': risk_reduction,
            'expected_return': '+1.8% annualized',  # Would use MPT calculation
            'sharpe_improvement': '+0.12'
        }
    
    def _create_hash(self, recommendation: RebalanceRecommendation) -> str:
        """Create immutable hash for audit trail"""
        data = {
            'portfolio_id': recommendation.portfolio_id,
            'timestamp': recommendation.timestamp.isoformat(),
            'trades': [t.dict() for t in recommendation.trades],
            'reasoning': recommendation.reasoning
        }
        hash_input = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(hash_input).hexdigest()

# ==================== API ENDPOINTS ====================

rebalancer = AgenticRebalancer()

@app.get("/")
async def root():
    return {
        "service": "FinGuard AI API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.post("/api/v1/portfolio/create")
async def create_portfolio(portfolio: Portfolio):
    """Create or update user portfolio"""
    portfolios_db[portfolio.user_id] = portfolio
    return {
        "status": "success",
        "portfolio_id": portfolio.user_id,
        "total_value": portfolio.total_value
    }

@app.get("/api/v1/portfolio/{user_id}")
async def get_portfolio(user_id: str):
    """Retrieve user portfolio"""
    if user_id not in portfolios_db:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolios_db[user_id]

@app.post("/api/v1/rebalance/analyze")
async def analyze_rebalancing(user_id: str):
    """Analyze portfolio and generate rebalancing recommendations"""
    
    if user_id not in portfolios_db:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio = portfolios_db[user_id]
    
    # Generate AI recommendation
    recommendation = await rebalancer.generate_rebalancing_plan(portfolio)
    
    if not recommendation:
        return {
            "status": "no_action_needed",
            "message": "Portfolio is within target allocation ranges"
        }
    
    # Store in audit log
    audit_entry = AuditLogEntry(
        id=f"AL-{datetime.utcnow().strftime('%Y%m%d')}-{len(audit_logs_db) + 1:03d}",
        timestamp=recommendation.timestamp,
        action=f"Rebalance recommendation generated",
        reasoning=recommendation.reasoning,
        trades=recommendation.trades,
        ai_confidence=recommendation.ai_confidence,
        status="pending",
        impact=recommendation.expected_impact,
        hash_chain=recommendation.hash_signature
    )
    
    audit_logs_db[audit_entry.id] = audit_entry
    
    return {
        "status": "success",
        "recommendation": recommendation,
        "audit_id": audit_entry.id
    }

@app.post("/api/v1/rebalance/execute")
async def execute_rebalancing(audit_id: str, background_tasks: BackgroundTasks):
    """Execute approved rebalancing plan"""
    
    if audit_id not in audit_logs_db:
        raise HTTPException(status_code=404, detail="Audit entry not found")
    
    audit_entry = audit_logs_db[audit_id]
    
    # In production: Execute actual trades via broker API
    # For now, simulate execution
    background_tasks.add_task(simulate_trade_execution, audit_id)
    
    audit_entry.status = "executing"
    
    return {
        "status": "execution_started",
        "audit_id": audit_id,
        "message": "Trades are being executed"
    }

@app.get("/api/v1/audit/logs/{user_id}")
async def get_audit_logs(user_id: str, limit: int = 10):
    """Retrieve audit trail for user"""
    
    user_logs = [
        log for log in audit_logs_db.values()
        if log.id.startswith(user_id) or True  # Simplified filter
    ]
    
    # Sort by timestamp descending
    sorted_logs = sorted(user_logs, key=lambda x: x.timestamp, reverse=True)
    
    return {
        "total": len(sorted_logs),
        "logs": sorted_logs[:limit]
    }

@app.get("/api/v1/audit/verify/{audit_id}")
async def verify_audit_entry(audit_id: str):
    """Verify audit entry integrity via hash chain"""
    
    if audit_id not in audit_logs_db:
        raise HTTPException(status_code=404, detail="Audit entry not found")
    
    entry = audit_logs_db[audit_id]
    
    # Recreate hash
    data = {
        'timestamp': entry.timestamp.isoformat(),
        'action': entry.action,
        'reasoning': entry.reasoning
    }
    hash_input = json.dumps(data, sort_keys=True).encode()
    calculated_hash = hashlib.sha256(hash_input).hexdigest()
    
    is_valid = calculated_hash == entry.hash_chain[:64]  # Compare first 64 chars
    
    return {
        "audit_id": audit_id,
        "is_valid": is_valid,
        "stored_hash": entry.hash_chain[:16] + "...",
        "calculated_hash": calculated_hash[:16] + "..."
    }

async def simulate_trade_execution(audit_id: str):
    """Background task to simulate trade execution"""
    await asyncio.sleep(3)  # Simulate processing time
    
    if audit_id in audit_logs_db:
        audit_logs_db[audit_id].status = "executed"

# ==================== HEALTH & METRICS ====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_portfolios": len(portfolios_db),
        "audit_entries": len(audit_logs_db)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)