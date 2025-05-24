import asyncio
import time
from typing import Dict, Any, Optional
from app.config import Config
from app.trading.trading_engine import TradingEngine
from app.portfolio_manager import PortfolioManager # Assuming PortfolioManager will be in its own file or DexBot provides it
from app.risk_manager import RiskManager, Position
from app.logger import DexLogger # Or just pass a logger instance

class TradeExecutor:
    def __init__(self, 
                 trading_engine: TradingEngine, 
                 portfolio_manager: PortfolioManager, 
                 risk_manager: RiskManager, 
                 logger: Any): # Logger can be standard logger or DexLogger instance
        self.trading_engine = trading_engine
        self.portfolio_manager = portfolio_manager
        self.risk_manager = risk_manager
        self.logger = logger

    async def execute_trade_signal(self, pair_data: Dict, signal_info: Dict) -> bool:
        """
        Executes a single trade based on a signal package.
        signal_info is a dictionary containing at least 'signal' and 'confidence',
        and potentially 'target_price', 'stop_loss', etc.
        Returns True if trade was successfully submitted, False otherwise.
        """
        try:
            base_token = pair_data.get('baseToken', {})
            token_address = base_token.get('address')
            token_symbol = base_token.get('symbol', 'UNKNOWN')
            # Use current price from pair_data for entry_price, actual fill price comes from Jupiter
            entry_price_estimate = float(pair_data.get('priceUsd', 0.0))
            pair_address_for_db = pair_data.get('pairAddress') 

            signal_type = signal_info.get('signal')
            confidence = signal_info.get('confidence', 0.0)

            if not token_address or entry_price_estimate <= 0:
                self.logger.warning(f"[TradeExecutor] Données de paire invalides pour {token_symbol}: {pair_data}")
                return False

            if signal_type not in ['buy', 'sell']:
                self.logger.info(f"[TradeExecutor] Signal non exécutable '{signal_type}' pour {token_symbol}. Trade ignoré.")
                return False

            # TODO: If signal_type is 'sell', we need to check if we hold this asset
            # and the amount to sell. For now, assuming all signals are for buying the base_token.
            if signal_type == 'sell':
                self.logger.warning(f"[TradeExecutor] La logique de VENTE pour {token_symbol} n'est pas encore implémentée. Trade ignoré.")
                return False

            # Calculate position size using RiskManager
            # RiskManager might use confidence from signal_info in the future
            amount_to_invest_usd = self.risk_manager.calculate_position_size(
                token_address=token_address,
                token_symbol=token_symbol,
                entry_price=entry_price_estimate,
                # confidence=confidence # Optional: pass confidence to risk manager
            )
            
            amount_to_invest_usd = min(amount_to_invest_usd, Config.MAX_ORDER_SIZE_USD)

            if amount_to_invest_usd < Config.MIN_ORDER_VALUE_USD:
                self.logger.info(f"[TradeExecutor] Taille de position calculée ${amount_to_invest_usd:.2f} pour {token_symbol} inférieure au min ${Config.MIN_ORDER_VALUE_USD}. Trade ignoré.")
                return False
            
            available_cash = self.portfolio_manager.get_available_cash()
            if amount_to_invest_usd > available_cash:
                self.logger.warning(f"[TradeExecutor] Fonds disponibles (${available_cash:.2f}) insuffisants pour un trade de ${amount_to_invest_usd:.2f} sur {token_symbol}.")
                return False

            protocol = pair_data.get('dexId', 'jupiter').lower()
            
            self.logger.info(f"[TradeExecutor] Tentative de swap ({signal_type.upper()} {token_symbol}): {amount_to_invest_usd:.2f} {Config.BASE_ASSET} -> {token_symbol} ({token_address}) via {protocol}. Confiance: {confidence:.2f}")
            
            result = await self.trading_engine.execute_swap(
                input_token_mint=Config.BASE_ASSET, # Assuming we always buy with BASE_ASSET
                output_token_mint=token_address,
                amount_in_usd=amount_to_invest_usd # Assuming TradingEngine can handle amount_in_usd directly
            )
            
            if result.get('success', False) and result.get('data', {}).get('signature'):
                trade_details = result['data']
                actual_entry_price = trade_details.get('entryPrice', entry_price_estimate) # Prefer actual fill price
                actual_amount_out = trade_details.get('amountOut', 0) # Actual amount of token received
                # The amount recorded in portfolio manager should be the USD value of the trade

                self.logger.info(f"[TradeExecutor] Swap réussi pour {token_symbol}. Signature: {trade_details['signature']}. Reçu approx {actual_amount_out} {token_symbol}.")
                
                self.portfolio_manager.record_trade_executed(
                    pair_address=pair_address_for_db if pair_address_for_db else f"{Config.BASE_ASSET}_{token_address}",
                    amount_usd=amount_to_invest_usd, # Cost of the trade in USD
                    entry_price=actual_entry_price, 
                    protocol=protocol,
                    token_symbol=token_symbol,
                    trade_id=trade_details['signature']
                    # TODO: Add 'side': signal_type to record_trade_executed and DB
                )
                
                position = Position(
                    id=trade_details['signature'],
                    token_address=token_address,
                    token_symbol=token_symbol,
                    entry_price=actual_entry_price, 
                    size_usd=amount_to_invest_usd, # Store USD value of the position
                    # size_tokens=actual_amount_out, # Optionally store token quantity
                    entry_time=time.time(),
                    trade_type=signal_type # Store trade type
                )
                self.risk_manager.add_position(position)
                self.logger.info(f"[TradeExecutor] Position ajoutée au RiskManager pour {token_symbol}.")
                return True
            else:
                error_msg = result.get('error', 'Unknown error during swap execution')
                self.logger.error(f"[TradeExecutor] Échec du swap pour {token_symbol}: {error_msg}")
                # Consider more specific error logging/handling here based on error_msg
                return False
        except Exception as e:
            self.logger.error(f"[TradeExecutor] Erreur lors de l'exécution du signal pour {pair_data.get('baseToken',{}).get('symbol', 'UNKNOWN')}: {e}", exc_info=True)
            return False 