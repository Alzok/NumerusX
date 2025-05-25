import asyncio
import time
from typing import Dict, Any, Optional
from app.config import Config
from app.trading.trading_engine import TradingEngine
from app.portfolio_manager import PortfolioManager # Assuming PortfolioManager will be in its own file or DexBot provides it
from app.risk_manager import RiskManager, Position
from app.market.market_data import MarketDataProvider # Added for fetching current price
from app.logger import DexLogger # Or just pass a logger instance

class TradeExecutor:
    def __init__(self, 
                 trading_engine: TradingEngine, 
                 portfolio_manager: PortfolioManager, 
                 risk_manager: RiskManager, 
                 market_data_provider: MarketDataProvider, # Added
                 logger: Any): # Logger can be standard logger or DexLogger instance
        self.trading_engine = trading_engine
        self.portfolio_manager = portfolio_manager
        self.risk_manager = risk_manager
        self.market_data_provider = market_data_provider # Added
        self.logger = logger

    async def execute_agent_order(self, agent_order: Dict[str, Any]) -> bool:
        """
        Executes a trade based on a structured order from the AIAgent.
        Agent order structure is expected to be:
        {
            'action': 'BUY' | 'SELL' | 'HOLD',
            'pair': 'TOKEN_MINT_ADDRESS', # Initially, base token to trade against Config.BASE_ASSET
            'amount': float, # Quantity
            'amount_is_quote': bool, # True if 'amount' is in quote currency (e.g., USDC), False if in base currency
            'order_type': 'MARKET' | 'LIMIT', # Initially, only MARKET is fully supported
            'limit_price': Optional[float],
            'stop_loss': Optional[float],
            'take_profit': Optional[float],
            'reasoning': str,
            'confidence_score': Optional[float]
        }
        Returns True if trade was successfully submitted, False otherwise.
        """
        try:
            action = agent_order.get('action')
            pair_identifier = agent_order.get('pair') # Expected to be the base token mint address
            amount_proposed_by_agent = agent_order.get('amount')
            amount_is_quote = agent_order.get('amount_is_quote', False)
            order_type = agent_order.get('order_type', 'MARKET')
            agent_confidence = agent_order.get('confidence_score')
            agent_stop_loss_price = agent_order.get('stop_loss')
            agent_take_profit_price = agent_order.get('take_profit')
            agent_slippage_bps = agent_order.get('slippage_bps', Config.SLIPPAGE_BPS)

            if action == 'HOLD' or not action:
                self.logger.info(f"[TradeExecutor] Agent order is 'HOLD' or no action specified. No trade executed.")
                return False # Not an error, but no trade executed

            if not all([pair_identifier, amount_proposed_by_agent, amount_proposed_by_agent > 0]):
                self.logger.warning(f"[TradeExecutor] Agent order missing required fields (pair, amount>0): {agent_order}")
                return False

            if order_type != 'MARKET':
                self.logger.warning(f"[TradeExecutor] Only 'MARKET' order_type is currently supported by TradingEngine. Order: {agent_order}")
                # For now, we can choose to proceed as market or reject.
                # Let's reject to avoid misinterpretation.
                return False

            input_token_mint: Optional[str] = None
            output_token_mint: Optional[str] = None
            proposed_amount_usd_for_risk_calc: Optional[float] = None
            target_token_mint = pair_identifier 
            # TODO: Robustly get token_symbol from target_token_mint (e.g. via MarketDataProvider)
            target_token_symbol_res = await self.market_data_provider.get_token_info(target_token_mint)
            if target_token_symbol_res['success'] and target_token_symbol_res['data']:
                target_token_symbol = target_token_symbol_res['data'].get('symbol', target_token_mint[:6] + "...")
            else:
                target_token_symbol = target_token_mint[:6] + "..."

            current_price_response = await self.market_data_provider.get_token_price(target_token_mint)
            if not current_price_response['success'] or current_price_response['data'] is None:
                self.logger.error(f"[TradeExecutor] Could not fetch current price for {target_token_symbol} ({target_token_mint}) to perform pre-trade risk assessment. Trade aborted.")
                return False
            current_entry_price_estimate = current_price_response['data']
            if current_entry_price_estimate <= 0:
                self.logger.error(f"[TradeExecutor] Current price for {target_token_symbol} is ${current_entry_price_estimate:.6f}. Cannot proceed. Trade aborted.")
                return False

            if action == 'BUY':
                input_token_mint = Config.BASE_ASSET
                output_token_mint = target_token_mint
                if amount_is_quote:
                    proposed_amount_usd_for_risk_calc = float(amount_proposed_by_agent)
                else: # Amount is in base tokens (output tokens)
                    self.logger.error(f"[TradeExecutor] For BUY orders, amount in base tokens (amount_is_quote=False) requires price conversion for risk calc. Not fully supported yet. Order: {agent_order}")
                    # Tentative: convert to USD for risk manager, but engine still needs USD or input tokens
                    proposed_amount_usd_for_risk_calc = float(amount_proposed_by_agent) * current_entry_price_estimate
                    # This sets proposed_amount_usd_for_risk_calc. The engine will later need amount_in_usd.
                    # If execute_swap primarily takes amount_in_usd, this is fine.
            elif action == 'SELL':
                input_token_mint = target_token_mint
                output_token_mint = Config.BASE_ASSET
                if amount_is_quote: # Amount is desired USD from sale
                    self.logger.error(f"[TradeExecutor] For SELL orders, amount in quote (amount_is_quote=True) requires complex conversion. Not fully supported. Order: {agent_order}")
                    return False # Needs to determine how many tokens to sell for X USD
                else: # Amount is in base tokens to sell (input_token_mint)
                    proposed_amount_usd_for_risk_calc = float(amount_proposed_by_agent) * current_entry_price_estimate
            else:
                self.logger.warning(f"[TradeExecutor] Invalid action '{action}' in agent order. Trade ignoré.")
                return False

            if not input_token_mint or not output_token_mint or proposed_amount_usd_for_risk_calc is None or proposed_amount_usd_for_risk_calc <=0:
                self.logger.error(f"[TradeExecutor] Failed to determine valid params for risk calc/engine. Mints: {input_token_mint}->{output_token_mint}, AmountUSD_proposed: {proposed_amount_usd_for_risk_calc}. Order: {agent_order}")
                return False

            # Risk Management: Calculate/Validate final trade size
            final_trade_amount_usd = self.risk_manager.calculate_position_size(
                token_address=target_token_mint, 
                token_symbol=target_token_symbol, 
                entry_price=current_entry_price_estimate, 
                proposed_amount_usd=proposed_amount_usd_for_risk_calc, 
                stop_loss_price=agent_stop_loss_price, 
                agent_confidence=agent_confidence
            )

            if final_trade_amount_usd <= 0:
                self.logger.info(f"[TradeExecutor] RiskManager determined trade size for {target_token_symbol} to be ${final_trade_amount_usd:.2f}. Trade aborted.")
                return False
            
            # Ensure final_trade_amount_usd doesn't exceed available cash for BUYs
            available_cash = self.portfolio_manager.get_available_cash()
            if action == 'BUY' and final_trade_amount_usd > available_cash:
                self.logger.warning(f"[TradeExecutor] Fonds disponibles (${available_cash:.2f}) insuffisants pour un achat de ${final_trade_amount_usd:.2f} (post-risk). Trade ignoré.")
                return False
            
            # TODO: For SELLs, check portfolio if we hold enough of `input_token_mint` (using final_trade_amount_usd and current_price_estimate to get token quantity).
            if action == 'SELL':
                tokens_to_sell = final_trade_amount_usd / current_entry_price_estimate if current_entry_price_estimate > 0 else float('inf')
                # This needs PortfolioManager to have a method like `get_token_balance(mint_address)`
                # owned_tokens = self.portfolio_manager.get_token_balance(input_token_mint)
                # if tokens_to_sell > owned_tokens:
                #     self.logger.warning(f"[TradeExecutor] Insufficient balance to sell {tokens_to_sell:.6f} {target_token_symbol}. Trade aborted.")
                #     return False
                self.logger.info(f"[TradeExecutor] SELL order for {target_token_symbol}: {tokens_to_sell:.6f} tokens (equiv. ${final_trade_amount_usd:.2f}). Portfolio check for sufficient balance is a TODO.")

            self.logger.info(f"[TradeExecutor] Executing Agent Order ({action.upper()} {target_token_symbol}): ${final_trade_amount_usd:.2f} USD. SL: {agent_stop_loss_price}, TP: {agent_take_profit_price}.")

            result = await self.trading_engine.execute_swap(
                input_token_mint=input_token_mint,
                output_token_mint=output_token_mint,
                amount_in_usd=final_trade_amount_usd,
                slippage_bps=agent_slippage_bps
            )

            if result.get('success', False) and result.get('data', {}).get('signature'):
                trade_details = result['data']
                actual_entry_price = trade_details.get('entryPrice', current_entry_price_estimate) 
                actual_amount_out_tokens = trade_details.get('amountOut', 0) 
                actual_amount_in_tokens = trade_details.get('amountIn', 0) 
                recorded_amount_usd = final_trade_amount_usd # Use the amount approved by RiskManager

                self.logger.info(f"[TradeExecutor] Agent order swap successful for {target_token_symbol}. Sig: {trade_details['signature']}.")
                self.logger.debug(f"[TradeExecutor] Trade Details: {trade_details}")
                
                pair_address_for_db = f"{input_token_mint}_{output_token_mint}"

                self.portfolio_manager.record_trade_executed(
                    pair_address=pair_address_for_db, 
                    amount_usd=recorded_amount_usd, 
                    entry_price=actual_entry_price, 
                    protocol=trade_details.get('protocol', 'jupiter'), 
                    token_symbol=target_token_symbol, 
                    trade_id=trade_details['signature'],
                    side=action 
                )
                
                # Determine size_tokens for the Position object
                # If BUY, output_token_mint is target_token_mint, amountOut is size_tokens
                # If SELL, input_token_mint is target_token_mint, amountIn is size_tokens
                position_size_tokens = actual_amount_out_tokens if action == 'BUY' else actual_amount_in_tokens

                position = Position(
                    id=trade_details['signature'],
                    token_address=target_token_mint, 
                    token_symbol=target_token_symbol,
                    entry_price=actual_entry_price, 
                    size_usd=recorded_amount_usd,
                    size_tokens=position_size_tokens, 
                    entry_time=time.time(),
                    trade_type=action,
                    stop_loss=agent_stop_loss_price,
                    take_profit=agent_take_profit_price
                )
                self.risk_manager.add_position(position)
                self.logger.info(f"[TradeExecutor] Position {action} for {target_token_symbol} added to RiskManager.")
                return True
            else:
                error_msg = result.get('error', 'Unknown error during agent order swap')
                self.logger.error(f"[TradeExecutor] Agent order swap failed for {target_token_symbol}: {error_msg}")
                return False

        except Exception as e:
            self.logger.error(f"[TradeExecutor] Major error executing agent order: {agent_order}. Error: {e}", exc_info=True)
            return False

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