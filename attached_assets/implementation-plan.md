# Multi-Strategy Portfolio Management System
## Implementation Specification for Replit Deployment

---

## 1. Project Overview

### 1.1. System Purpose
A multi-strategy portfolio management system that:
- Optimizes parameters for sub-portfolios across different asset classes
- Dynamically allocates capital between strategies
- Executes trades via Alpaca API
- Aims to maximize Sharpe ratio and minimize drawdown

### 1.2. Functional Requirements
- Daily parameter optimization for each sub-portfolio
- Dynamic capital allocation between strategies
- Position aggregation and trade generation
- Alpaca API integration for trade execution
- Performance monitoring and visualization
- Data persistence and retrieval

---

## 2. Technical Stack

### 2.1. Backend
- **Language:** Python 3.10+
- **Web Framework:** FastAPI
- **Task Scheduling:** APScheduler
- **Database:** SQLite (development), PostgreSQL (production)
- **ORM:** SQLAlchemy
- **Optimization:** Hyperopt or Optuna
- **Data Processing:** Pandas, NumPy
- **Financial Analysis:** PyPortfolioOpt, Pyfolio

### 2.2. Frontend
- **Framework:** React with TypeScript
- **UI Library:** Chakra UI or Material UI
- **Data Visualization:** Plotly.js, React-Vis
- **State Management:** Redux Toolkit or Zustand
- **API Integration:** Axios or React Query

### 2.3. DevOps & Infrastructure
- **Version Control:** Git
- **Hosting:** Replit
- **Continuous Integration:** GitHub Actions (if needed)
- **Secrets Management:** Replit Secrets
- **Logging:** Python logging module + custom solution
- **Monitoring:** Custom dashboard with Plotly.js

---

## 3. Replit Setup Instructions

### 3.1. Initial Project Configuration
1. Create a new Replit using the Python template
2. Set up virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install base requirements:
   ```bash
   pip install fastapi uvicorn sqlalchemy pandas numpy hyperopt alpaca-trade-api apscheduler
   ```
4. Configure `.replit` file for proper execution:
   ```
   language = "python3"
   run = "uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload"
   ```

### 3.2. Environment Variables Setup
1. Set up the following secrets in Replit's Secrets tab:
   - `ALPACA_API_KEY`
   - `ALPACA_SECRET_KEY`
   - `ALPACA_BASE_URL` (paper/live API endpoint)
   - `DATABASE_URL` (if using external DB)
   - `OPTIMIZATION_WORKERS` (number of parallel workers)

### 3.3. Database Setup
1. For SQLite (development):
   ```python
   DATABASE_URL = "sqlite:///./portfolio_system.db"
   ```
2. For PostgreSQL (production):
   - Use a managed PostgreSQL service
   - Configure connection using DATABASE_URL environment variable

---

## 4. Project Structure

```
/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entry point
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py               # SQLAlchemy models
│   │   ├── session.py              # Database session management
│   │   └── repository/             # CRUD operations for each entity
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/              # API endpoints by resource
│   │   ├── dependencies.py         # API dependencies
│   │   └── middleware.py           # API middleware
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Application configuration
│   │   ├── security.py             # Authentication & authorization
│   │   └── scheduler.py            # Task scheduling
│   ├── services/
│   │   ├── __init__.py
│   │   ├── data_service.py         # Market data acquisition
│   │   ├── optimization_service.py # Parameter optimization
│   │   ├── portfolio_service.py    # Portfolio management
│   │   ├── allocation_service.py   # Capital allocation
│   │   └── execution_service.py    # Trade execution
│   └── utils/
│       ├── __init__.py
│       ├── metrics.py              # Performance metrics calculation
│       └── logging.py              # Logging utilities
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/             # UI components
│   │   ├── pages/                  # Application pages
│   │   ├── services/               # API clients
│   │   ├── store/                  # State management
│   │   └── utils/                  # Frontend utilities
│   ├── package.json
│   └── tsconfig.json
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Test configuration
│   ├── test_api/                   # API tests
│   ├── test_services/              # Service tests
│   └── test_utils/                 # Utility tests
├── .replit                         # Replit configuration
├── poetry.lock                     # Dependency lock file
├── pyproject.toml                  # Project metadata and dependencies
└── README.md                       # Project documentation
```

---

## 5. Implementation Phases

### 5.1. Phase 1: Core Infrastructure (Weeks 1-2)

#### 5.1.1. Database Schema & Models
1. Define SQLAlchemy models:
   - Asset classes (ETFs, commodities, bonds)
   - Optimization parameters
   - Strategy configurations
   - Portfolio allocations
   - Performance metrics
   - Trade records

2. Create database migrations:
   - Use Alembic for schema versioning
   - Set up initial schema creation script
   - Define upgrade/downgrade paths

#### 5.1.2. Market Data Service
1. Implement data fetching from multiple sources:
   - Alpaca Market Data API
   - Alternative data providers if needed
   - Caching mechanism for efficient retrieval

2. Create data preprocessing utilities:
   - Feature engineering functions
   - Normalization and standardization
   - Handling missing data

#### 5.1.3. Basic API Structure
1. Set up FastAPI application:
   - CORS middleware
   - Authentication middleware
   - Error handling
   - OpenAPI documentation

2. Implement initial endpoints:
   - Health check and status
   - Configuration management
   - Manual trigger for optimization

#### 5.1.4. Task Scheduler
1. Implement APScheduler integration:
   - Daily optimization jobs
   - Market data fetching jobs
   - Performance calculation jobs
   - Periodic database cleanup

### 5.2. Phase 2: Optimization Engine (Weeks 3-4)

#### 5.2.1. Parameter Definition Framework
1. Create configuration schema for optimization parameters:
   - Parameter names, types, ranges
   - Constraints and relationships
   - Sensible defaults

2. Implement parameter validation:
   - Type checking
   - Range validation
   - Inter-parameter consistency checks

#### 5.2.2. Bayesian Optimization Implementation
1. Integrate Hyperopt or Optuna:
   - Define search space
   - Configure parallel processing
   - Implement early stopping

2. Create objective functions:
   - Maximum return
   - Minimum drawdown
   - Maximum Sharpe ratio
   - Custom combinations

#### 5.2.3. Optimization Results Storage
1. Design results storage schema:
   - Parameter combinations
   - Performance metrics
   - Optimization metadata
   - Timestamps and versioning

2. Implement query interfaces:
   - Get best parameters for a given objective
   - Get Pareto-optimal solutions
   - Historical parameter evolution

#### 5.2.4. API Endpoints for Optimization
1. Implement endpoints:
   - Start optimization job
   - Get optimization status
   - Retrieve optimization results
   - Cancel running optimization

### 5.3. Phase 3: Sub-Portfolio Management (Weeks 5-6)

#### 5.3.1. Asset Ranking System
1. Implement momentum-based ranking:
   - Multiple timeframe analysis
   - Relative strength indicators
   - Trend confirmation signals

2. Create position sizing algorithm:
   - Performance-based weighting
   - Volatility normalization
   - Correlation-aware adjustments

#### 5.3.2. Sub-Portfolio Backtesting
1. Adapt existing backtest code:
   - Standardize interface
   - Improve performance
   - Add additional metrics

2. Create backtest result visualization:
   - Equity curves
   - Drawdown charts
   - Performance metrics tables

#### 5.3.3. Regime Detection
1. Implement market regime classification:
   - Volatility-based regimes
   - Trend strength indicators
   - Correlation structure analysis

2. Create regime-specific parameter selection:
   - Mapping regimes to optimal parameters
   - Smooth transition between parameter sets
   - Regime prediction (optional ML component)

#### 5.3.4. Sub-Portfolio API Endpoints
1. Implement endpoints:
   - Get sub-portfolio composition
   - Get performance metrics
   - Update strategy parameters
   - Run backtest with specific parameters

### 5.4. Phase 4: Master Portfolio & Allocation (Weeks 7-8)

#### 5.4.1. Performance Assessment Module
1. Implement performance metrics calculation:
   - Rolling Sharpe ratios
   - Maximum drawdown
   - Return consistency
   - Strategy correlation

2. Create performance monitoring dashboard:
   - Real-time metrics update
   - Historical comparison
   - Risk decomposition charts

#### 5.4.2. Dynamic Allocation Algorithm
1. Implement allocation strategies:
   - Kelly criterion / Fractional Kelly
   - Risk parity
   - Momentum overlay
   - Minimum/maximum constraints

2. Create allocation adjustment process:
   - Gradual reallocation
   - Tracking error control
   - Transaction cost modeling

#### 5.4.3. Capital Allocation API Endpoints
1. Implement endpoints:
   - Get current allocations
   - Update allocation parameters
   - Run allocation optimization
   - Simulate allocation changes

### 5.5. Phase 5: Trade Execution (Weeks 9-10)

#### 5.5.1. Position Aggregation
1. Implement position consolidation:
   - Weighted position aggregation
   - Cash management
   - Handling of position overlaps

2. Create position reconciliation process:
   - Compare target vs. actual positions
   - Identify discrepancies
   - Generate adjustment trades

#### 5.5.2. Alpaca API Integration
1. Implement Alpaca client:
   - Authentication
   - Account information retrieval
   - Order submission and tracking
   - Position management

2. Create trading constraints:
   - Maximum order size
   - Price limits
   - Timing restrictions
   - Risk limits

#### 5.5.3. Order Management
1. Implement order generation:
   - Create orders from position differences
   - Order sizing and rounding
   - Order type selection (market, limit, etc.)

2. Create execution monitoring:
   - Track order status
   - Handle partial fills
   - Implement retry logic

#### 5.5.4. Trade Execution API Endpoints
1. Implement endpoints:
   - Get current positions
   - Get pending orders
   - Submit manual orders
   - Cancel/modify orders

### 5.6. Phase 6: Frontend & Integration (Weeks 11-12)

#### 5.6.1. Dashboard Components
1. Implement React components:
   - Portfolio summary widget
   - Performance charts
   - Allocation visualizations
   - Trade history table

2. Create interactive elements:
   - Parameter adjustment controls
   - Allocation sliders
   - Execution buttons
   - Filter controls

#### 5.6.2. State Management
1. Implement Redux store (or alternative):
   - Application state definition
   - Actions and reducers
   - Asynchronous action handling
   - State persistence

2. Create API integration services:
   - RESTful API clients
   - WebSocket for real-time updates
   - Error handling and retries

#### 5.6.3. User Interface Pages
1. Implement main application pages:
   - Dashboard overview
   - Strategy configuration
   - Allocation management
   - Trade execution
   - Performance analytics
   - System settings

2. Create responsive layouts:
   - Desktop optimization
   - Mobile compatibility
   - Dark/light theme support

#### 5.6.4. Final Integration & Testing
1. Perform end-to-end integration:
   - Connect all components
   - Test complete workflows
   - Measure performance and optimize

2. Conduct comprehensive testing:
   - Unit tests for critical components
   - Integration tests for services
   - User acceptance testing

---

## 6. Data Models

### 6.1. Asset Class
```python
class AssetClass(Base):
    __tablename__ = "asset_classes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    assets = relationship("Asset", back_populates="asset_class")
    strategies = relationship("Strategy", back_populates="asset_class")
```

### 6.2. Asset
```python
class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    name = Column(String)
    asset_class_id = Column(Integer, ForeignKey("asset_classes.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    asset_class = relationship("AssetClass", back_populates="assets")
    positions = relationship("Position", back_populates="asset")
    price_history = relationship("PriceHistory", back_populates="asset")
```

### 6.3. Strategy
```python
class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    asset_class_id = Column(Integer, ForeignKey("asset_classes.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    asset_class = relationship("AssetClass", back_populates="strategies")
    parameters = relationship("StrategyParameter", back_populates="strategy")
    allocations = relationship("Allocation", back_populates="strategy")
    positions = relationship("Position", back_populates="strategy")
    optimizations = relationship("Optimization", back_populates="strategy")
```

### 6.4. StrategyParameter
```python
class StrategyParameter(Base):
    __tablename__ = "strategy_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    name = Column(String)
    value = Column(Float)
    min_value = Column(Float)
    max_value = Column(Float)
    step = Column(Float)
    is_optimizable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    strategy = relationship("Strategy", back_populates="parameters")
```

### 6.5. Optimization
```python
class Optimization(Base):
    __tablename__ = "optimizations"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    objective = Column(String)  # "return", "drawdown", "sharpe", "custom"
    status = Column(String)  # "pending", "running", "completed", "failed"
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    strategy = relationship("Strategy", back_populates="optimizations")
    results = relationship("OptimizationResult", back_populates="optimization")
```

### 6.6. OptimizationResult
```python
class OptimizationResult(Base):
    __tablename__ = "optimization_results"
    
    id = Column(Integer, primary_key=True, index=True)
    optimization_id = Column(Integer, ForeignKey("optimizations.id"))
    parameters = Column(JSON)  # Stored as JSON
    metrics = Column(JSON)  # Stored as JSON
    rank = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    optimization = relationship("Optimization", back_populates="results")
```

### 6.7. Allocation
```python
class Allocation(Base):
    __tablename__ = "allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    weight = Column(Float)
    effective_date = Column(Date)
    expiry_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    strategy = relationship("Strategy", back_populates="allocations")
```

### 6.8. Position
```python
class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"))
    quantity = Column(Float)
    target_weight = Column(Float)
    entry_date = Column(DateTime)
    exit_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    strategy = relationship("Strategy", back_populates="positions")
    asset = relationship("Asset", back_populates="positions")
    trades = relationship("Trade", back_populates="position")
```

### 6.9. Trade
```python
class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"))
    order_id = Column(String, nullable=True)  # Alpaca order ID
    side = Column(String)  # "buy" or "sell"
    quantity = Column(Float)
    price = Column(Float, nullable=True)
    status = Column(String)  # "pending", "filled", "canceled", "failed"
    execution_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    position = relationship("Position", back_populates="trades")
```

### 6.10. PerformanceMetric
```python
class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id", nullable=True))
    metric_type = Column(String)  # "return", "drawdown", "sharpe", etc.
    timeframe = Column(String)  # "daily", "weekly", "monthly", "annual"
    value = Column(Float)
    date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    strategy = relationship("Strategy")
```

---

## 7. API Endpoints

### 7.1. Asset Management
- `GET /api/assets` - List all assets
- `GET /api/assets/{asset_id}` - Get asset details
- `GET /api/asset-classes` - List all asset classes
- `GET /api/asset-classes/{class_id}/assets` - List assets in class

### 7.2. Strategy Management
- `GET /api/strategies` - List all strategies
- `GET /api/strategies/{strategy_id}` - Get strategy details
- `GET /api/strategies/{strategy_id}/parameters` - Get strategy parameters
- `PUT /api/strategies/{strategy_id}/parameters` - Update strategy parameters
- `GET /api/strategies/{strategy_id}/performance` - Get strategy performance

### 7.3. Optimization
- `POST /api/optimizations` - Start new optimization
- `GET /api/optimizations` - List optimizations
- `GET /api/optimizations/{optimization_id}` - Get optimization details
- `GET /api/optimizations/{optimization_id}/results` - Get optimization results
- `DELETE /api/optimizations/{optimization_id}` - Cancel optimization

### 7.4. Allocation
- `GET /api/allocations` - Get current allocations
- `POST /api/allocations` - Update allocations
- `GET /api/allocations/history` - Get allocation history
- `POST /api/allocations/optimize` - Optimize allocations

### 7.5. Position Management
- `GET /api/positions` - Get current positions
- `GET /api/positions/history` - Get position history
- `POST /api/positions/reconcile` - Reconcile positions

### 7.6. Trade Execution
- `GET /api/trades` - Get trade history
- `POST /api/trades` - Create new trade
- `GET /api/orders` - Get pending orders
- `DELETE /api/orders/{order_id}` - Cancel order

### 7.7. Performance Analytics
- `GET /api/performance/portfolio` - Get portfolio performance
- `GET /api/performance/strategies` - Get strategies comparison
- `GET /api/performance/metrics` - Get specific metrics

---

## 8. Optimization Service Implementation

### 8.1. Parameter Optimization Class
```python
class ParameterOptimizer:
    def __init__(
        self, 
        strategy_id: int, 
        start_date: datetime, 
        end_date: datetime,
        objective: str = "sharpe",
        max_evals: int = 100,
        parallel_workers: int = 4
    ):
        self.strategy_id = strategy_id
        self.start_date = start_date
        self.end_date = end_date
        self.objective = objective
        self.max_evals = max_evals
        self.parallel_workers = parallel_workers
        self.db = SessionLocal()
        self.strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()
        self.params = self._get_parameter_space()
        
    def _get_parameter_space(self):
        """Get parameter space definition from database"""
        params = {}
        param_records = self.db.query(StrategyParameter).filter(
            StrategyParameter.strategy_id == self.strategy_id,
            StrategyParameter.is_optimizable == True
        ).all()
        
        for param in param_records:
            params[param.name] = hp.uniform(param.name, param.min_value, param.max_value)
            # Alternative for integer parameters:
            # if param is integer:
            #     params[param.name] = hp.quniform(param.name, param.min_value, param.max_value, 1)
            
        return params
    
    def objective_function(self, params):
        """Evaluate a parameter set and return the objective value"""
        # Implement backtest with provided parameters
        # This would call your existing backtest code
        backtest_results = self._run_backtest(params)
        
        if self.objective == "return":
            return -backtest_results["total_return"]  # Negative because we're minimizing
        elif self.objective == "drawdown":
            return backtest_results["max_drawdown"]
        elif self.objective == "sharpe":
            return -backtest_results["sharpe_ratio"]  # Negative because we're minimizing
        elif self.objective == "custom":
            # Custom objective mixing multiple metrics
            return -(0.6 * backtest_results["sharpe_ratio"] - 0.4 * backtest_results["max_drawdown"])
    
    def _run_backtest(self, params):
        """Run backtest with given parameters"""
        # This would implement or call your existing backtest code
        # Return metrics dictionary
        pass
    
    def optimize(self):
        """Run the optimization process"""
        # Create optimization record
        optimization = Optimization(
            strategy_id=self.strategy_id,
            start_date=self.start_date,
            end_date=self.end_date,
            objective=self.objective,
            status="running"
        )
        self.db.add(optimization)
        self.db.commit()
        
        try:
            # Run Hyperopt optimization
            trials = Trials()
            best = fmin(
                fn=self.objective_function,
                space=self.params,
                algo=tpe.suggest,
                max_evals=self.max_evals,
                trials=trials
            )
            
            # Store results
            for i, trial in enumerate(trials.trials):
                result = OptimizationResult(
                    optimization_id=optimization.id,
                    parameters=trial['misc']['vals'],
                    metrics={
                        "loss": trial['result']['loss'],
                        "status": trial['result']['status']
                    },
                    rank=i + 1
                )
                self.db.add(result)
            
            # Update optimization status
            optimization.status = "completed"
            optimization.completed_at = datetime.utcnow()
            self.db.commit()
            
            return best
            
        except Exception as e:
            # Handle errors
            optimization.status = "failed"
            self.db.commit()
            raise e
        finally:
            self.db.close()
```

---

## 9. Allocation Service Implementation

### 9.1. Capital Allocator Class
```python
class CapitalAllocator:
    def __init__(
        self,
        lookback_days: int = 90,
        min_allocation: float = 0.05,
        max_allocation: float = 0.30,
        risk_target: float = 0.10,  # 10% annualized volatility
        max_daily_change: float = 0.05  # Maximum 5% allocation change per day
    ):
        self.lookback_days = lookback_days
        self.min_allocation = min_allocation
        self.max_allocation = max_allocation
        self.risk_target = risk_target
        self.max_daily_change = max_daily_change
        self.db = SessionLocal()
    
    def get_strategy_metrics(self):
        """Get performance metrics for all active strategies"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        # Get all active strategies
        strategies = self.db.query(Strategy).filter(Strategy.is_active == True).all()
        
        metrics = {}
        for strategy in strategies:
            # Get daily returns
            returns = self._get_strategy_returns(strategy.id, start_date, end_date)
            
            # Calculate metrics
            metrics[strategy.id] = {
                "name": strategy.name,
                "returns": returns,
                "mean_return": np.mean(returns),
                "volatility": np.std(returns) * np.sqrt(252),  # Annualize
                "sharpe": self._calculate_sharpe(returns),
                "max_drawdown": self._calculate_max_drawdown(returns),
                "win_rate": self._calculate_win_rate(returns)
            }
        
        return metrics
    
    def _get_strategy_returns(self, strategy_id, start_date, end_date):
        """Get daily returns for a strategy"""
        # Implement query to get returns from database
        # This could be calculated from position values or from stored metrics
        pass
    
    def _calculate_sharpe(self, returns, risk_free_rate=0.0):
        """Calculate Sharpe ratio"""
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    
    def _calculate_max_drawdown(self, returns):
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative / running_max) - 1
        return np.min(drawdown)
    
    def _calculate_win_rate(self, returns):
        """Calculate win rate (percentage of positive days)"""
        return np.sum(returns > 0) / len(returns)
    
    def allocate_capital_risk_parity(self):
        """Allocate capital using risk parity approach"""
        metrics = self.get_strategy_metrics()
        
        # Calculate inverse volatility weights
        inv_vol = {sid: 1/metrics[sid]["volatility"] for sid in metrics}
        total_inv_vol = sum(inv_vol.values())
        vol_weights = {sid: inv_vol[sid]/total_inv_vol for sid in inv_vol}
        
        # Apply min/max constraints
        weights = self._apply_allocation_constraints(vol_weights)
        
        # Apply maximum daily change constraint
        weights = self._apply_daily_change_constraint(weights)
        
        return weights
    
    def allocate_capital_momentum(self):
        """Allocate capital based on recent performance momentum"""
        metrics = self.get_strategy_metrics()
        
        # Calculate performance score (e.g., Sharpe ratio)
        scores = {sid: metrics[sid]["sharpe"] for sid in metrics}
        
        # Handle negative scores by shifting all scores to be positive
        min_score = min(scores.values())
        if min_score < 0:
            scores = {sid: scores[sid] - min_score + 0.1 for sid in scores}
        
        # Calculate weights proportional to scores
        total_score = sum(scores.values())
        weights = {sid: scores[sid]/total_score for sid in scores}
        
        # Apply min/max constraints
        weights = self._apply_allocation_constraints(weights)
        
        # Apply maximum daily change constraint
        weights = self._apply_daily_change_constraint(weights)
        
        return weights
    
    def _apply_allocation_constraints(self, weights):
        """Apply minimum and maximum allocation constraints"""
        constrained_weights = weights.copy()
        
        # Apply minimum constraint
        below_min = {sid: weight for sid, weight in constrained_weights.items() if weight < self.min_allocation}
        if below_min:
            total_below = sum(below_min.values())
            total_above = sum(weight for sid, weight in constrained_weights.items() if weight >= self.min_allocation)
            
            # Set below minimum to minimum
            for sid in below_min:
                constrained_weights[sid] = self.min_allocation
            
            # Reduce weights for those above minimum proportionally
            if total_above > 0:
                scale_factor = (1 - len(below_min) * self.min_allocation) / total_above
                for sid, weight in constrained_weights.items():
                    if sid not in below_min:
                        constrained_weights[sid] = weight * scale_factor
        
        # Apply maximum constraint
        above_max = {sid: weight for sid, weight in constrained_weights.items() if weight > self.max_allocation}
        if above_max:
            excess = sum(weight - self.max_allocation for weight in above_max.values())
            below_max = {sid: weight for sid, weight in constrained_weights.items() if weight < self.max_allocation}
            
            # Set above maximum to maximum
            for sid in above_max:
                constrained_weights[sid] = self.max_allocation
            
            # Redistribute excess proportionally to those below maximum
            if below_max:
                total_below = sum(below_max.values())
                for sid in below_max:
                    constrained_weights[sid] += excess * (below_max[sid] / total_below)
        
        # Normalize to ensure sum is 1.0
        total_weight = sum(constrained_weights.values())
        if abs(total_weight - 1.0) > 1e-6:
            constrained_weights = {sid: weight/total_weight for sid, weight in constrained_weights.items()}
        
        return constrained_weights
    
    def _apply_daily_change_constraint(self, new_weights):
        """Limit daily allocation changes"""
        # Get current weights
        current_weights = self._get_current_allocations()
        
        # Apply maximum change constraint
        constrained_weights = {}
        for sid, new_weight in new_weights.items():
            current_weight = current_weights.get(sid, 0.0)
            max_change = self.max_daily_change
            
            if new_weight > current_weight + max_change:
                constrained_weights[sid] = current_weight + max_change
            elif new_weight < current_weight - max_change:
                constrained_weights[sid] = current_weight - max_change
            else:
                constrained_weights[sid] = new_weight
        
        # Normalize to ensure sum is 1.0
        total_weight = sum(constrained_weights.values())
        if abs(total_weight - 1.0) > 1e-6:
            constrained_weights = {sid: weight/total_weight for sid, weight in constrained_weights.items()}
        
        return constrained_weights
    
    def _get_current_allocations(self):
        """Get current strategy allocations"""
        today = datetime.now().date()
        
        allocations = self.db.query(Allocation).filter(
            Allocation.effective_date <= today,
            or_(
                Allocation.expiry_date == None,
                Allocation.expiry_date >= today
            )
        ).all()
        
        return {a.strategy_id: a.weight for a in allocations}
    
    def update_allocations(self, new_weights):
        """Save new allocations to database"""
        today = datetime.now().date()
        
        # Expire current allocations
        current_allocations = self.db.query(Allocation).filter(
            Allocation.effective_date <= today,
            or_(
                Allocation.expiry_date == None,
                Allocation.expiry_date >= today
            )
        ).all()
        
        for allocation in current_allocations:
            allocation.expiry_date = today
        
        # Create new allocations
        for strategy_id, weight in new_weights.items():
            new_allocation = Allocation(
                strategy_id=strategy_id,
                weight=weight,
                effective_date=today + timedelta(days=1)  # Effective tomorrow
            )
            self.db.add(new_allocation)
        
        self.db.commit()
        return new_weights
```

---

## 10. Trade Execution Service Implementation

### 10.1. Alpaca Trade Executor Class
```python
class AlpacaTradeExecutor:
    def __init__(self):
        # Initialize Alpaca API client
        self.api = tradeapi.REST(
            os.environ.get("ALPACA_API_KEY"),
            os.environ.get("ALPACA_SECRET_KEY"),
            base_url=os.environ.get("ALPACA_BASE_URL")
        )
        self.db = SessionLocal()
    
    def get_account_info(self):
        """Get Alpaca account information"""
        try:
            account = self.api.get_account()
            return {
                "id": account.id,
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "maintenance_margin": float(account.maintenance_margin),
                "day_trade_count": account.day_trade_count,
                "status": account.status
            }
        except Exception as e:
            logging.error(f"Error getting account info: {str(e)}")
            raise
    
    def get_current_positions(self):
        """Get current positions from Alpaca"""
        try:
            positions = self.api.list_positions()
            return [
                {
                    "symbol": position.symbol,
                    "qty": float(position.qty),
                    "market_value": float(position.market_value),
                    "cost_basis": float(position.cost_basis),
                    "unrealized_pl": float(position.unrealized_pl),
                    "current_price": float(position.current_price)
                }
                for position in positions
            ]
        except Exception as e:
            logging.error(f"Error getting positions: {str(e)}")
            raise
    
    def get_target_positions(self):
        """Get target positions from the database"""
        # Get current allocations
        allocator = CapitalAllocator()
        strategy_allocations = allocator._get_current_allocations()
        
        # Get account equity
        account = self.get_account_info()
        total_equity = account["equity"]
        
        # Get strategy positions
        target_positions = {}
        for strategy_id, allocation in strategy_allocations.items():
            strategy_equity = total_equity * allocation
            
            # Get latest positions for this strategy
            positions = self.db.query(Position).filter(
                Position.strategy_id == strategy_id,
                Position.exit_date == None
            ).all()
            
            for position in positions:
                symbol = self.db.query(Asset).filter(Asset.id == position.asset_id).first().symbol
                
                if symbol not in target_positions:
                    target_positions[symbol] = {
                        "qty": 0,
                        "target_value": 0
                    }
                
                # Calculate target value based on weight and strategy allocation
                target_value = strategy_equity * position.target_weight
                target_positions[symbol]["target_value"] += target_value
        
        # Convert target values to quantities
        for symbol, data in target_positions.items():
            current_price = self._get_current_price(symbol)
            target_positions[symbol]["qty"] = int(data["target_value"] / current_price)
        
        return target_positions
    
    def _get_current_price(self, symbol):
        """Get current price for a symbol"""
        try:
            bars = self.api.get_latest_bar(symbol)
            return float(bars.c)
        except Exception as e:
            logging.error(f"Error getting price for {symbol}: {str(e)}")
            raise
    
    def generate_orders(self):
        """Generate orders based on target vs. current positions"""
        current_positions = {p["symbol"]: p for p in self.get_current_positions()}
        target_positions = self.get_target_positions()
        
        orders = []
        
        # Process targets that exist in current or target positions
        all_symbols = set(list(current_positions.keys()) + list(target_positions.keys()))
        
        for symbol in all_symbols:
            current_qty = float(current_positions.get(symbol, {}).get("qty", 0))
            target_qty = target_positions.get(symbol, {}).get("qty", 0)
            
            # Calculate difference
            qty_diff = target_qty - current_qty
            
            # Skip if difference is too small
            if abs(qty_diff) < 1:
                continue
            
            # Generate order
            side = "buy" if qty_diff > 0 else "sell"
            orders.append({
                "symbol": symbol,
                "qty": abs(qty_diff),
                "side": side,
                "type": "market",
                "time_in_force": "day"
            })
        
        return orders
    
    def execute_orders(self, orders=None):
        """Execute generated orders"""
        if orders is None:
            orders = self.generate_orders()
        
        results = []
        for order_data in orders:
            try:
                # Submit order to Alpaca
                order = self.api.submit_order(
                    symbol=order_data["symbol"],
                    qty=order_data["qty"],
                    side=order_data["side"],
                    type=order_data["type"],
                    time_in_force=order_data["time_in_force"]
                )
                
                # Record in database
                asset = self.db.query(Asset).filter(Asset.symbol == order_data["symbol"]).first()
                
                # Find corresponding position
                position = self.db.query(Position).filter(
                    Position.asset_id == asset.id,
                    Position.exit_date == None
                ).first()
                
                if not position and order_data["side"] == "buy":
                    # Create new position if buying and doesn't exist
                    position = Position(
                        asset_id=asset.id,
                        strategy_id=None,  # Would need logic to determine strategy
                        quantity=0,
                        target_weight=0,
                        entry_date=datetime.utcnow()
                    )
                    self.db.add(position)
                    self.db.commit()
                
                # Create trade record
                trade = Trade(
                    position_id=position.id if position else None,
                    order_id=order.id,
                    side=order_data["side"],
                    quantity=order_data["qty"],
                    status="pending",
                    created_at=datetime.utcnow()
                )
                self.db.add(trade)
                self.db.commit()
                
                results.append({
                    "order_id": order.id,
                    "symbol": order_data["symbol"],
                    "qty": order_data["qty"],
                    "side": order_data["side"],
                    "status": order.status
                })
            
            except Exception as e:
                logging.error(f"Error executing order for {order_data['symbol']}: {str(e)}")
                results.append({
                    "symbol": order_data["symbol"],
                    "error": str(e),
                    "status": "failed"
                })
        
        return results
    
    def update_order_status(self):
        """Update status of pending orders"""
        # Get pending trades
        pending_trades = self.db.query(Trade).filter(
            Trade.status == "pending",
            Trade.order_id != None
        ).all()
        
        for trade in pending_trades:
            try:
                # Get order status from Alpaca
                order = self.api.get_order(trade.order_id)
                
                # Update trade record
                trade.status = order.status
                if order.status == "filled":
                    trade.price = float(order.filled_avg_price)
                    trade.execution_time = order.filled_at
                    
                    # Update position quantity
                    if trade.position_id:
                        position = self.db.query(Position).filter(Position.id == trade.position_id).first()
                        if position:
                            if trade.side == "buy":
                                position.quantity += trade.quantity
                            else:
                                position.quantity -= trade.quantity
                                
                                # Close position if quantity is zero or negative
                                if position.quantity <= 0:
                                    position.exit_date = datetime.utcnow()
                
                self.db.commit()
                
            except Exception as e:
                logging.error(f"Error updating order status for trade {trade.id}: {str(e)}")
        
        return len(pending_trades)
```

---

## 11. Deployment and Production Considerations

### 11.1. Replit Deployment Instructions
1. Set up `nix.toml` for Python and Node.js support:
   ```toml
   [env]
   PATH = "/root/$USER/.local/bin:$PATH"

   [target.x86_64-unknown-linux-gnu]
   packages = [
       "python310",
       "poetry",
       "nodejs-18_x",
       "yarn"
   ]
   ```

2. Create deployment script:
   ```bash
   #!/bin/bash
   # setup.sh

   # Install backend dependencies
   poetry install

   # Build frontend
   cd frontend
   yarn install
   yarn build
   cd ..

   # Run database migrations
   poetry run alembic upgrade head

   # Start the application
   poetry run uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```

3. Configure `.replit` file:
   ```
   run = "bash setup.sh"
   language = "python3"
   ```

4. Set environment variables in Replit Secrets:
   - `ALPACA_API_KEY`
   - `ALPACA_SECRET_KEY`
   - `ALPACA_BASE_URL`
   - `DATABASE_URL` (if using external PostgreSQL)

### 11.2. Production Considerations
1. Database Management
   - For larger applications, consider using a managed PostgreSQL service
   - Implement regular database backups
   - Set up database migrations using Alembic

2. Scalability
   - Set up task queues for long-running jobs
   - Implement caching for frequently accessed data
   - Consider serverless functions for optimization tasks

3. Monitoring and Logging
   - Implement structured logging
   - Set up error alerting
   - Monitor system health metrics

4. Security
   - Implement proper authentication
   - Store secrets in environment variables
   - Regular security audits
   - Implement rate limiting

---

## 12. Testing Strategy

### 12.1. Unit Tests
1. Create tests for core business logic:
   - Optimization algorithms
   - Capital allocation
   - Position sizing
   - Trade generation

2. Service-level tests:
   - Data service tests
   - Optimization service tests
   - Portfolio service tests
   - Execution service tests

3. Mock external dependencies:
   - Market data APIs
   - Alpaca API
   - Database

### 12.2. Integration Tests
1. API endpoint tests:
   - Request/response validation
   - Authentication/authorization
   - Error handling

2. Database integration tests:
   - CRUD operations
   - Transaction management
   - Data integrity

3. Scheduler integration tests:
   - Job scheduling
   - Job execution
   - Error recovery

### 12.3. Backtest Validation
1. Implement historical simulation:
   - Compare expected vs. actual results
   - Validate optimization improvements
   - Test allocation strategies

2. Stress testing:
   - Extreme market conditions
   - Parameter sensitivity analysis
   - "What-if" scenarios

---

## 13. Documentation Requirements

### 13.1. Technical Documentation
1. API Documentation:
   - OpenAPI/Swagger documentation
   - Endpoint descriptions
   - Example requests/responses

2. Code Documentation:
   - Docstrings for all functions and classes
   - Architecture diagrams
   - Dependency documentation

3. Database Documentation:
   - Entity-relationship diagrams
   - Migration history
   - Query optimization guidelines

### 13.2. User Documentation
1. Configuration Guide:
   - System setup instructions
   - Configuration parameters
   - Troubleshooting guide

2. User Manual:
   - Feature descriptions
   - Workflow explanations
   - Screenshots and examples

3. Maintenance Guide:
   - Backup procedures
   - Update process
   - Monitoring instructions

---

## 14. Implementation Timeline

### Phase 1: Core Infrastructure (Weeks 1-2)
- Week 1: Project setup, database design, basic API structure
- Week 2: Market data service, task scheduler implementation

### Phase 2: Optimization Engine (Weeks 3-4)
- Week 3: Parameter optimization framework, objective functions
- Week 4: Optimization results storage, API endpoints

### Phase 3: Sub-Portfolio Management (Weeks 5-6)
- Week 5: Asset ranking system, backtesting integration
- Week 6: Regime detection, sub-portfolio API endpoints

### Phase 4: Master Portfolio & Allocation (Weeks 7-8)
- Week 7: Performance assessment module, metrics calculation
- Week 8: Dynamic allocation algorithm, allocation API endpoints

### Phase 5: Trade Execution (Weeks 9-10)
- Week 9: Position aggregation, order generation
- Week 10: Alpaca API integration, execution monitoring

### Phase 6: Frontend & Integration (Weeks 11-12)
- Week 11: Dashboard components, state management
- Week 12: User interface pages, end-to-end testing

---

This implementation plan provides a comprehensive roadmap for building a production-ready multi-strategy portfolio management system on Replit. The modular architecture allows for incremental development and testing, while the detailed specifications ensure alignment with the original requirements.
