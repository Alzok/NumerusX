"""
Market Data API routes for NumerusX v1.
C5 Implementation - Expose market data via REST API using MarketDataCache.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import logging
from enum import Enum

from .auth_routes import verify_token, TokenData
from app.services.market_data_cache import MarketDataCache
from app.config import get_config

router = APIRouter()
logger = logging.getLogger(__name__)

# Global MarketDataCache instance
_market_data_cache: Optional[MarketDataCache] = None

async def get_market_data_cache() -> MarketDataCache:
    """Dependency to get MarketDataCache instance."""
    global _market_data_cache
    if _market_data_cache is None:
        config = get_config()
        _market_data_cache = MarketDataCache(config)
        # Initialize async context if needed
        await _market_data_cache.__aenter__()
    return _market_data_cache

# Pydantic Models for API responses

class TokenInfo(BaseModel):
    """Token information model."""
    address: str = Field(..., description="Token mint address")
    symbol: str = Field(..., description="Token symbol")
    name: str = Field(..., description="Token name")
    decimals: Optional[int] = Field(None, description="Token decimals")
    logo_uri: Optional[str] = Field(None, description="Token logo URL")
    tags: List[str] = Field(default_factory=list, description="Token tags")
    market_cap_usd: Optional[float] = Field(None, description="Market cap in USD")
    total_supply: Optional[float] = Field(None, description="Total token supply")
    
class PriceData(BaseModel):
    """Token price data model."""
    token_address: str = Field(..., description="Token address")
    price_usd: float = Field(..., description="Current price in USD")
    price_change_24h: Optional[float] = Field(None, description="24h price change percentage")
    volume_24h_usd: Optional[float] = Field(None, description="24h volume in USD")
    timestamp: datetime = Field(..., description="Price data timestamp")
    source: str = Field(..., description="Data source")

class LiquidityData(BaseModel):
    """Liquidity information model."""
    token_address: str = Field(..., description="Token address")
    liquidity_usd: float = Field(..., description="Total liquidity in USD")
    pool_count: Optional[int] = Field(None, description="Number of liquidity pools")
    top_pairs: List[Dict[str, Any]] = Field(default_factory=list, description="Top trading pairs")
    dex_distribution: Dict[str, float] = Field(default_factory=dict, description="Liquidity by DEX")

class HistoricalPrice(BaseModel):
    """Historical price point."""
    timestamp: datetime = Field(..., description="Price timestamp")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price") 
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: float = Field(..., description="Trading volume")

class TokenHolder(BaseModel):
    """Token holder information."""
    address: str = Field(..., description="Holder address")
    balance: float = Field(..., description="Token balance")
    percentage: float = Field(..., description="Percentage of total supply")
    is_whale: bool = Field(False, description="Is whale address")

class Transaction(BaseModel):
    """Token transaction model."""
    signature: str = Field(..., description="Transaction signature")
    timestamp: datetime = Field(..., description="Transaction timestamp")
    type: str = Field(..., description="Transaction type (BUY/SELL/TRANSFER)")
    amount: float = Field(..., description="Token amount")
    price_usd: Optional[float] = Field(None, description="USD price at transaction")
    from_address: str = Field(..., description="From address")
    to_address: str = Field(..., description="To address")

class MarketSummary(BaseModel):
    """Market summary for multiple tokens."""
    total_tokens: int = Field(..., description="Total number of tokens")
    total_market_cap: float = Field(..., description="Total market cap USD")
    total_volume_24h: float = Field(..., description="Total 24h volume USD")
    trending_tokens: List[str] = Field(..., description="Trending token addresses")
    top_gainers: List[Dict[str, Any]] = Field(..., description="Top gaining tokens")
    top_losers: List[Dict[str, Any]] = Field(..., description="Top losing tokens")

class TimeframeEnum(str, Enum):
    """Supported timeframes for historical data."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m" 
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

# API Routes

@router.get("/tokens/{token_address}/info", response_model=TokenInfo)
async def get_token_info(
    token_address: str = Path(..., description="Token mint address"),
    cache: MarketDataCache = Depends(get_market_data_cache),
    token_data: TokenData = Depends(verify_token)
):
    """
    Get comprehensive token information.
    
    Returns token metadata, market cap, supply and other details.
    """
    try:
        logger.info(f"API request: token info for {token_address}")
        
        # Get token info from cache
        result = await cache.get_token_info(token_address)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Token information not found: {result.get('error', 'Unknown error')}"
            )
        
        data = result['data']
        
        # Convert to API model
        token_info = TokenInfo(
            address=data.get('address', token_address),
            symbol=data.get('symbol', 'UNKNOWN'),
            name=data.get('name', 'Unknown Token'),
            decimals=data.get('decimals'),
            logo_uri=data.get('logoURI'),
            tags=data.get('tags', []),
            market_cap_usd=data.get('market_cap_usd'),
            total_supply=data.get('total_supply')
        )
        
        return token_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting token info for {token_address}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/tokens/{token_address}/price", response_model=PriceData)
async def get_token_price(
    token_address: str = Path(..., description="Token mint address"),
    vs_currency: str = Query("USDC", description="Quote currency"),
    cache: MarketDataCache = Depends(get_market_data_cache),
    token_data: TokenData = Depends(verify_token)
):
    """
    Get current token price.
    
    Returns real-time price data from multiple sources.
    """
    try:
        logger.info(f"API request: price for {token_address} vs {vs_currency}")
        
        # Get price from cache
        result = await cache.get_token_price(token_address, vs_currency)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Price data not found: {result.get('error', 'Unknown error')}"
            )
        
        data = result['data']
        
        # Convert to API model
        price_data = PriceData(
            token_address=token_address,
            price_usd=data.get('price_usd', 0.0),
            price_change_24h=data.get('price_change_24h'),
            volume_24h_usd=data.get('volume_24h_usd'),
            timestamp=datetime.utcnow(),
            source=result.get('source', 'cache')
        )
        
        return price_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price for {token_address}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/tokens/{token_address}/liquidity", response_model=LiquidityData)
async def get_token_liquidity(
    token_address: str = Path(..., description="Token mint address"),
    cache: MarketDataCache = Depends(get_market_data_cache),
    token_data: TokenData = Depends(verify_token)
):
    """
    Get token liquidity information.
    
    Returns liquidity pools, DEX distribution and market depth.
    """
    try:
        logger.info(f"API request: liquidity for {token_address}")
        
        # Get liquidity from cache
        result = await cache.get_liquidity_data(token_address)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Liquidity data not found: {result.get('error', 'Unknown error')}"
            )
        
        data = result['data']
        
        # Convert to API model
        liquidity_data = LiquidityData(
            token_address=token_address,
            liquidity_usd=data.get('liquidity_usd', 0.0),
            pool_count=data.get('pool_count'),
            top_pairs=data.get('top_pairs', []),
            dex_distribution=data.get('dex_distribution', {})
        )
        
        return liquidity_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting liquidity for {token_address}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/tokens/{token_address}/history", response_model=List[HistoricalPrice])
async def get_historical_prices(
    token_address: str = Path(..., description="Token mint address"),
    timeframe: TimeframeEnum = Query(TimeframeEnum.H1, description="Price timeframe"),
    limit: int = Query(100, ge=1, le=1000, description="Number of data points"),
    start_time: Optional[datetime] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO format)"),
    cache: MarketDataCache = Depends(get_market_data_cache),
    token_data: TokenData = Depends(verify_token)
):
    """
    Get historical price data.
    
    Returns OHLCV data for charting and technical analysis.
    """
    try:
        logger.info(f"API request: historical prices for {token_address}, timeframe={timeframe}, limit={limit}")
        
        # Get historical data from cache
        result = await cache.get_historical_prices(
            token_address=token_address,
            timeframe=timeframe.value,
            limit=limit
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Historical data not found: {result.get('error', 'Unknown error')}"
            )
        
        data = result['data']
        if not isinstance(data, list):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid historical data format"
            )
        
        # Convert to API model
        historical_prices = []
        for point in data:
            if isinstance(point, dict):
                historical_prices.append(HistoricalPrice(
                    timestamp=point.get('timestamp', datetime.utcnow()),
                    open=point.get('open', 0.0),
                    high=point.get('high', 0.0),
                    low=point.get('low', 0.0),
                    close=point.get('close', 0.0),
                    volume=point.get('volume', 0.0)
                ))
        
        # Apply time filtering if specified
        if start_time or end_time:
            filtered_prices = []
            for price in historical_prices:
                if start_time and price.timestamp < start_time:
                    continue
                if end_time and price.timestamp > end_time:
                    continue
                filtered_prices.append(price)
            historical_prices = filtered_prices
        
        return historical_prices
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical prices for {token_address}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/tokens/{token_address}/holders", response_model=List[TokenHolder])
async def get_token_holders(
    token_address: str = Path(..., description="Token mint address"),
    limit: int = Query(50, ge=1, le=1000, description="Number of top holders"),
    cache: MarketDataCache = Depends(get_market_data_cache),
    token_data: TokenData = Depends(verify_token)
):
    """
    Get token holder distribution.
    
    Returns top holders and whale analysis.
    """
    try:
        logger.info(f"API request: holders for {token_address}, limit={limit}")
        
        # Get holders from cache
        result = await cache.get_token_holders(
            token_address=token_address,
            limit=limit
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Holder data not found: {result.get('error', 'Unknown error')}"
            )
        
        data = result['data']
        holders_list = data.get('holders', []) if isinstance(data, dict) else []
        
        # Convert to API model
        token_holders = []
        for holder in holders_list:
            if isinstance(holder, dict):
                token_holders.append(TokenHolder(
                    address=holder.get('address', ''),
                    balance=holder.get('balance', 0.0),
                    percentage=holder.get('percentage', 0.0),
                    is_whale=holder.get('percentage', 0.0) >= 5.0  # 5%+ is whale
                ))
        
        return token_holders
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting holders for {token_address}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/tokens/{token_address}/transactions", response_model=List[Transaction])
async def get_token_transactions(
    token_address: str = Path(..., description="Token mint address"),
    limit: int = Query(50, ge=1, le=1000, description="Number of recent transactions"),
    tx_type: Optional[str] = Query(None, description="Filter by transaction type"),
    cache: MarketDataCache = Depends(get_market_data_cache),
    token_data: TokenData = Depends(verify_token)
):
    """
    Get recent token transactions.
    
    Returns recent trading activity and transfers.
    """
    try:
        logger.info(f"API request: transactions for {token_address}, limit={limit}")
        
        # Get transactions from cache
        result = await cache.get_token_transactions(
            token_address=token_address,
            limit=limit
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction data not found: {result.get('error', 'Unknown error')}"
            )
        
        data = result['data']
        transactions_list = data if isinstance(data, list) else []
        
        # Convert to API model
        transactions = []
        for tx in transactions_list:
            if isinstance(tx, dict):
                # Filter by type if specified
                if tx_type and tx.get('type') != tx_type:
                    continue
                    
                transactions.append(Transaction(
                    signature=tx.get('signature', ''),
                    timestamp=tx.get('timestamp', datetime.utcnow()),
                    type=tx.get('type', 'UNKNOWN'),
                    amount=tx.get('amount', 0.0),
                    price_usd=tx.get('price_usd'),
                    from_address=tx.get('from_address', ''),
                    to_address=tx.get('to_address', '')
                ))
        
        return transactions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transactions for {token_address}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/market/summary", response_model=MarketSummary)
async def get_market_summary(
    cache: MarketDataCache = Depends(get_market_data_cache),
    token_data: TokenData = Depends(verify_token)
):
    """
    Get overall market summary.
    
    Returns market overview, trending tokens and top movers.
    """
    try:
        logger.info("API request: market summary")
        
        # For now, return mock data since MarketDataCache doesn't have a summary method
        # In production, this would aggregate data from multiple tokens
        
        summary = MarketSummary(
            total_tokens=1500,
            total_market_cap=2.1e12,  # $2.1T
            total_volume_24h=8.5e10,  # $85B
            trending_tokens=[
                "So11111111111111111111111111111111111111112",  # SOL
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            ],
            top_gainers=[
                {"token": "So11111111111111111111111111111111111111112", "change_24h": 15.5},
                {"token": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "change_24h": 2.1}
            ],
            top_losers=[
                {"token": "SampleToken123", "change_24h": -8.3},
                {"token": "SampleToken456", "change_24h": -5.1}
            ]
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting market summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/tokens/batch/prices")
async def get_batch_prices(
    token_addresses: str = Query(..., description="Comma-separated token addresses"),
    vs_currency: str = Query("USDC", description="Quote currency"),
    cache: MarketDataCache = Depends(get_market_data_cache),
    token_data: TokenData = Depends(verify_token)
):
    """
    Get prices for multiple tokens in one request.
    
    Returns price data for up to 50 tokens efficiently.
    """
    try:
        addresses = [addr.strip() for addr in token_addresses.split(',') if addr.strip()]
        
        if len(addresses) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 tokens allowed per batch request"
            )
        
        logger.info(f"API request: batch prices for {len(addresses)} tokens")
        
        results = {}
        for address in addresses:
            try:
                result = await cache.get_token_price(address, vs_currency)
                if result.get('success'):
                    data = result['data']
                    results[address] = {
                        "price_usd": data.get('price_usd', 0.0),
                        "price_change_24h": data.get('price_change_24h'),
                        "volume_24h_usd": data.get('volume_24h_usd'),
                        "source": result.get('source', 'cache'),
                        "success": True
                    }
                else:
                    results[address] = {
                        "success": False,
                        "error": result.get('error', 'Unknown error')
                    }
            except Exception as e:
                results[address] = {
                    "success": False,
                    "error": str(e)
                }
        
        return {
            "request_count": len(addresses),
            "successful_count": len([r for r in results.values() if r.get('success')]),
            "vs_currency": vs_currency,
            "timestamp": datetime.utcnow().isoformat(),
            "data": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch price request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/health")
async def health_check(
    cache: MarketDataCache = Depends(get_market_data_cache)
):
    """
    Health check for market data API.
    
    Returns service status and cache metrics.
    """
    try:
        # Basic health check
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "market_data_api",
            "version": "1.0.0",
            "cache_available": cache is not None
        }
        
        # Try to get cache stats if available
        try:
            # This would be implemented in MarketDataCache if needed
            health_status["cache_stats"] = {
                "redis_connected": False,  # Would check actual Redis connection
                "cache_hits": 0,
                "cache_misses": 0
            }
        except Exception:
            health_status["cache_stats"] = "unavailable"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        ) 