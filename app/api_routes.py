from fastapi import FastAPI, Depends, HTTPException, Header, status, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
import asyncio

from app.config import Config
from app.security.security import Security
from app.trading.trading_engine import TradingEngine
from app.analytics_engine import AdvancedTradingStrategy
from app.database import db, User, Trade
from app.wallet import SolanaWallet

# Création de l'application FastAPI
app = FastAPI(title="NumerusX Trading API", version="1.0.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ALLOWED_ORIGINS.split(',') if Config.CORS_ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation des composants
security = Security()
analytics = AdvancedTradingStrategy()
logger = logging.getLogger("api")

# Modèles Pydantic
class TokenRequest(BaseModel):
    username: str
    password: str

class SwapRequest(BaseModel):
    input_token: str
    output_token: str
    amount: float

class AnalysisRequest(BaseModel):
    token_address: str

# Middleware d'authentification
async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token d'authentification manquant")
    
    token = authorization.replace("Bearer ", "")
    is_valid, message = security.verify_token(token)
    
    if not is_valid:
        raise HTTPException(status_code=401, detail=message)
    
    return token

# Routes API
@app.post("/api/auth/token")
async def get_token(request: TokenRequest):
    """Obtenir un token d'authentification"""
    try:
        with db.session() as session:
            user = session.query(User).filter_by(username=request.username).first()
            if not user or not security.verify_password(request.password, user.password_hash):
                raise HTTPException(status_code=401, detail="Identifiants invalides")
                
            token = security.create_token({"user_id": user.id, "username": user.username})
            return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'authentification: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

@app.get("/api/market/tokens")
async def get_available_tokens(token: str = Depends(verify_token)):
    """Obtenir la liste des tokens disponibles"""
    try:
        # Implémentation à compléter pour récupérer les tokens depuis Jupiter
        return {"tokens": [
            {"address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "symbol": "USDC", "name": "USD Coin"},
            {"address": "So11111111111111111111111111111111111111112", "symbol": "SOL", "name": "Solana"},
            # Autres tokens...
        ]}
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des tokens: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

@app.post("/api/trading/swap")
async def create_swap(request: SwapRequest, token: str = Depends(verify_token)):
    """Créer un swap entre deux tokens"""
    try:
        # Initialiser le moteur de trading avec le portefeuille de l'utilisateur
        # Dans une implémentation réelle, on récupérerait le portefeuille de l'utilisateur
        wallet = SolanaWallet()  
        trading_engine = TradingEngine(wallet)
        
        # Exécuter le swap
        result = await trading_engine.execute_swap(
            request.input_token,
            request.output_token,
            request.amount
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Échec du swap'))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du swap: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

@app.post("/api/analytics/analyze")
async def analyze_token(request: AnalysisRequest, token: str = Depends(verify_token)):
    """Analyser un token avec la stratégie avancée"""
    try:
        # Récupération des données (à implémenter avec les vraies API)
        token_data = {"priceHistory": [
            # Données historiques du token
        ]}
        
        # Analyse avec le moteur d'analyse
        analysis = analytics.analyze(token_data)
        signal = analytics.generate_signal(analysis)
        
        return {
            "token": request.token_address,
            "analysis": analysis,
            "signal": signal
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur serveur")
