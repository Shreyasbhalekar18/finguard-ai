# database.py - Database Models & Blockchain-Style Audit Trail

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import hashlib
import json
from typing import Optional, List, Dict

Base = declarative_base()

# ==================== DATABASE MODELS ====================

class User(Base):
    """User account model"""
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    subscription_tier = Column(String, default='free')  # free, basic, premium, enterprise
    is_active = Column(Boolean, default=True)
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

class Portfolio(Base):
    """User portfolio model"""
    __tablename__ = 'portfolios'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    name = Column(String, default="Main Portfolio")
    total_value = Column(Float, default=0.0)
    currency = Column(String, default='USD')
    risk_tolerance = Column(String, default='moderate')  # conservative, moderate, aggressive
    target_allocations = Column(JSON)  # {"stocks": 40, "crypto": 20, ...}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    rebalance_recommendations = relationship("RebalanceRecommendation", back_populates="portfolio")

class Holding(Base):
    """Individual asset holding"""
    __tablename__ = 'holdings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String, ForeignKey('portfolios.id'), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    name = Column(String)
    category = Column(String, nullable=False)  # stocks, crypto, bonds, etfs
    quantity = Column(Float, nullable=False)
    average_buy_price = Column(Float)
    current_price = Column(Float)
    target_allocation = Column(Float)  # Target percentage
    purchase_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    
    @property
    def current_value(self) -> float:
        return self.quantity * (self.current_price or 0)
    
    @property
    def total_return(self) -> float:
        if not self.average_buy_price or not self.current_price:
            return 0.0
        return ((self.current_price - self.average_buy_price) / self.average_buy_price) * 100

class RebalanceRecommendation(Base):
    """AI-generated rebalancing recommendations"""
    __tablename__ = 'rebalance_recommendations'
    
    id = Column(String, primary_key=True)
    portfolio_id = Column(String, ForeignKey('portfolios.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String, default='pending')  # pending, approved, rejected, executed
    
    # AI Decision Data
    action_needed = Column(Boolean, default=True)
    primary_concern = Column(Text)
    risk_level = Column(String)  # low, medium, high
    recommended_trades = Column(JSON)  # List of trade dictionaries
    reasoning = Column(Text)  # Human-readable explanation
    ai_confidence = Column(Float)
    
    # Impact Projections
    expected_return_change = Column(String)
    expected_risk_reduction = Column(String)
    expected_sharpe_improvement = Column(String)
    
    # Audit Trail
    hash_signature = Column(String, nullable=False)  # SHA-256 hash
    previous_hash = Column(String)  # Links to previous recommendation (blockchain-style)
    model_version = Column(String, default='1.0.0')
    
    # Execution
    executed_at = Column(DateTime)
    execution_notes = Column(Text)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="rebalance_recommendations")

class AuditLog(Base):
    """Immutable audit trail for all portfolio actions"""
    __tablename__ = 'audit_logs'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    portfolio_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Action Details
    action_type = Column(String, nullable=False)  # rebalance, trade, alert, config_change
    action_description = Column(Text)
    affected_assets = Column(JSON)  # List of symbols affected
    
    # AI/System Context
    triggered_by = Column(String, default='ai_agent')  # ai_agent, user, system, scheduled
    ai_confidence = Column(Float)
    reasoning = Column(Text)
    
    # Blockchain-Style Chain
    hash_chain = Column(String, nullable=False, unique=True)
    previous_hash = Column(String, index=True)
    block_number = Column(Integer, autoincrement=True)
    
    # Metadata
    metadata = Column(JSON)  # Additional context
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action_type} at {self.timestamp}>"

class MarketData(Base):
    """Cached market data for performance"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Price Data
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)
    
    # Volatility Metrics
    volatility_30d = Column(Float)
    beta = Column(Float)
    
    # Market Indicators
    rsi = Column(Float)
    moving_avg_50d = Column(Float)
    moving_avg_200d = Column(Float)

# ==================== BLOCKCHAIN-STYLE AUDIT TRAIL ====================

class BlockchainAuditTrail:
    """
    Implements blockchain-style immutable audit trail
    Each entry links to previous entry via hash chain
    """
    
    def __init__(self, session):
        self.session = session
    
    def create_audit_entry(
        self,
        user_id: str,
        portfolio_id: str,
        action_type: str,
        action_description: str,
        affected_assets: List[str],
        triggered_by: str = 'ai_agent',
        ai_confidence: Optional[float] = None,
        reasoning: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> AuditLog:
        """
        Create new audit log entry with blockchain-style hash chain
        """
        
        # Get the most recent audit log for this user
        previous_entry = self.session.query(AuditLog)\
            .filter(AuditLog.user_id == user_id)\
            .order_by(AuditLog.block_number.desc())\
            .first()
        
        previous_hash = previous_entry.hash_chain if previous_entry else "0" * 64
        block_number = (previous_entry.block_number + 1) if previous_entry else 1
        
        # Generate unique ID
        entry_id = f"AL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{block_number:06d}"
        
        # Create entry
        audit_entry = AuditLog(
            id=entry_id,
            user_id=user_id,
            portfolio_id=portfolio_id,
            action_type=action_type,
            action_description=action_description,
            affected_assets=affected_assets,
            triggered_by=triggered_by,
            ai_confidence=ai_confidence,
            reasoning=reasoning,
            previous_hash=previous_hash,
            block_number=block_number,
            metadata=metadata or {}
        )
        
        # Calculate hash for this entry
        audit_entry.hash_chain = self._calculate_hash(audit_entry)
        
        # Save to database
        self.session.add(audit_entry)
        self.session.commit()
        
        return audit_entry
    
    def _calculate_hash(self, entry: AuditLog) -> str:
        """Calculate SHA-256 hash for audit entry"""
        
        hash_data = {
            'id': entry.id,
            'user_id': entry.user_id,
            'portfolio_id': entry.portfolio_id,
            'timestamp': entry.timestamp.isoformat(),
            'action_type': entry.action_type,
            'action_description': entry.action_description,
            'affected_assets': entry.affected_assets,
            'previous_hash': entry.previous_hash,
            'block_number': entry.block_number
        }
        
        hash_input = json.dumps(hash_data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(hash_input).hexdigest()
    
    def verify_chain_integrity(self, user_id: str) -> Dict:
        """
        Verify the integrity of the audit chain for a user
        Returns verification report
        """
        
        entries = self.session.query(AuditLog)\
            .filter(AuditLog.user_id == user_id)\
            .order_by(AuditLog.block_number.asc())\
            .all()
        
        if not entries:
            return {'valid': True, 'total_entries': 0, 'message': 'No entries found'}
        
        issues = []
        
        for i, entry in enumerate(entries):
            # Verify hash calculation
            calculated_hash = self._calculate_hash(entry)
            if calculated_hash != entry.hash_chain:
                issues.append({
                    'entry_id': entry.id,
                    'issue': 'Hash mismatch',
                    'stored': entry.hash_chain[:16] + '...',
                    'calculated': calculated_hash[:16] + '...'
                })
            
            # Verify chain linkage
            if i > 0:
                if entry.previous_hash != entries[i-1].hash_chain:
                    issues.append({
                        'entry_id': entry.id,
                        'issue': 'Chain break',
                        'expected_previous': entries[i-1].hash_chain[:16] + '...',
                        'actual_previous': entry.previous_hash[:16] + '...'
                    })
        
        return {
            'valid': len(issues) == 0,
            'total_entries': len(entries),
            'verified_entries': len(entries) - len(issues),
            'issues': issues,
            'message': 'Chain integrity verified' if not issues else f'{len(issues)} issues found'
        }
    
    def get_audit_trail(
        self, 
        user_id: str, 
        limit: int = 50,
        action_type: Optional[str] = None
    ) -> List[AuditLog]:
        """Retrieve audit trail with optional filtering"""
        
        query = self.session.query(AuditLog)\
            .filter(AuditLog.user_id == user_id)
        
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

# ==================== DATABASE INITIALIZATION ====================

def init_database(database_url: str = "postgresql://localhost/finguard_db"):
    """Initialize database and create tables"""
    
    engine = create_engine(database_url, echo=True)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal

def get_db_session():
    """Get database session (for dependency injection)"""
    SessionLocal = sessionmaker(bind=create_engine("postgresql://localhost/finguard_db"))
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Initialize database
    Session = init_database("sqlite:///finguard_test.db")  # SQLite for testing
    session = Session()
    
    # Create blockchain audit trail
    audit_trail = BlockchainAuditTrail(session)
    
    # Create sample audit entries
    entry1 = audit_trail.create_audit_entry(
        user_id="user-12345",
        portfolio_id="portfolio-001",
        action_type="rebalance",
        action_description="AI-recommended rebalancing to reduce crypto exposure",
        affected_assets=["BTC", "ETH", "AAPL"],
        triggered_by="ai_agent",
        ai_confidence=0.94,
        reasoning="Bitcoin volatility increased by 32% over 7 days. Reducing allocation from 24.7% to 15%.",
        metadata={"market_condition": "high_volatility"}
    )
    print(f"Created audit entry: {entry1.id}")
    print(f"Hash: {entry1.hash_chain[:16]}...")
    
    # Verify chain integrity
    verification = audit_trail.verify_chain_integrity("user-12345")
    print(f"\nChain verification: {verification}")
    
    session.close()