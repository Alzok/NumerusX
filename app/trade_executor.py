import time
import logging # Changed from app.logger import DexLogger to standard logging
from typing import Dict, Any, Optional

from app.config_v2 import get_config
from app.trading.trading_engine import TradingEngine
from app.portfolio_manager import PortfolioManager
from app.risk_manager import RiskManager, Position
from app.market.market_data import MarketDataProvider

# Use standard logger, can be configured externally
logger = logging.getLogger(__name__)

class TradeExecutor:
    def __init__(self, 
                 config: Config, # Added Config
                 trading_engine: TradingEngine, 
                 portfolio_manager: PortfolioManager, 
                 risk_manager: RiskManager, 
                 market_data_provider: MarketDataProvider,
                 # logger instance is now typically handled by importing logging and getting a logger
                 ):
        self.config = config # Store config
        self.trading_engine = trading_engine
        self.portfolio_manager = portfolio_manager
        self.risk_manager = risk_manager
        self.market_data_provider = market_data_provider

    async def execute_agent_order(self, agent_order: Dict[str, Any]) -> bool:
        """
        Executes a trade based on a structured order from the AIAgent.
        Expected agent_order format (from 02-todo-ai-api-gemini.md):
        {
          "decision": "BUY" | "SELL" | "HOLD",
          "token_pair": "SOL/USDC", // Parsed to input/output mints
          "amount_usd": float | null, // Amount in USDC for the trade
          "confidence": float,
          "stop_loss_price": float | null,
          "take_profit_price": float | null,
          "reasoning": "concise explanation...",
          "slippage_bps": Optional[int] // Added for flexibility, defaults to Config
        }
        Returns True if trade was successfully submitted and recorded, False otherwise.
        """
        trade_id_for_logging = f"agent_order_{int(time.time()*1000)}" # Create a unique ID for this attempt
        try:
            decision = agent_order.get('decision')
            token_pair_str = agent_order.get('token_pair') # e.g., "SOL/USDC"
            amount_usd = agent_order.get('amount_usd')
            
            agent_confidence = agent_order.get('confidence')
            agent_stop_loss_price = agent_order.get('stop_loss_price')
            agent_take_profit_price = agent_order.get('take_profit_price')
            agent_reasoning = agent_order.get('reasoning', "No reasoning provided.")
            # Use slippage from agent_order if provided, otherwise from Config
            agent_slippage_bps = agent_order.get('slippage_bps', self.get_config().jupiter.default_slippage_bps)

            if decision == 'HOLD' or not decision:
                logger.info(f"[{trade_id_for_logging}] Agent decision is 'HOLD' or no decision. No trade executed for {token_pair_str}. Reasoning: {agent_reasoning}")
                return True # Not an error, task completed successfully (by not trading)

            if not all([token_pair_str, amount_usd is not None, amount_usd > 0]):
                logger.warning(f"[{trade_id_for_logging}] Agent order missing required fields (token_pair, amount_usd > 0): {agent_order}")
                return False

            # Parse token_pair_str (e.g., "SOL/USDC") into input_mint and output_mint
            # This assumes pair is always BaseAsset/QuoteAsset or QuoteAsset/BaseAsset
            # And BaseAsset is defined in Config (e.g., USDC_MINT_ADDRESS)
            
            parts = token_pair_str.split('/')
            if len(parts) != 2:
                logger.error(f"[{trade_id_for_logging}] Invalid token_pair format: {token_pair_str}. Expected 'TOKEN1/TOKEN2'.")
                return False

            token_symbol_0, token_symbol_1 = parts[0], parts[1]

            # We need mint addresses. MarketDataProvider can help get info by symbol.
            # This is a simplification. A robust system would have a token registry or ensure mints are passed.
            # For now, let's assume we can get mints from symbols, or that AIAgent provides mints directly.
            # If AIAgent provides "SOL/USDC", we need to map these to mints.
            # For this example, let's assume a direct mapping from common symbols to mints if needed,
            # or that the agent_order.pair is actually "MINT1_ADDRESS/MINT2_ADDRESS" or one is get_config().trading.base_asset symbol.

            # Simpler: Assume one of the tokens in the pair is the BASE_ASSET (e.g., USDC)
            # and the other is the one we are interested in trading.
            
            target_token_symbol: Optional[str] = None
            other_token_symbol: Optional[str] = None

            if token_symbol_0 == self.get_config().trading.base_asset_SYMBOL: # e.g. USDC/SOL
                target_token_symbol = token_symbol_1 # e.g. SOL
                other_token_symbol = token_symbol_0  # e.g. USDC
            elif token_symbol_1 == self.get_config().trading.base_asset_SYMBOL: # e.g. SOL/USDC
                target_token_symbol = token_symbol_0 # e.g. SOL
                other_token_symbol = token_symbol_1  # e.g. USDC
            else:
                # Fallback: if neither is BASE_ASSET_SYMBOL, maybe agent_order.pair should be the target token's mint?
                # For now, we require one of them to be the base asset for clarity.
                logger.error(f"[{trade_id_for_logging}] Could not determine target token from pair '{token_pair_str}'. One token must be BASE_ASSET_SYMBOL '{self.get_config().trading.base_asset_SYMBOL}'.")
                return False

            # Get mint addresses for target_token_symbol and other_token_symbol (which is base_asset_symbol)
            # This requires market_data_provider to map symbols to mints or a predefined map.
            # Let's assume market_data_provider.get_token_info_by_symbol exists or we use a simple map.
            # For now, directly use Config for BASE_ASSET mint.
            
            # Simplified: Fetch info for target_token_symbol to get its mint address
            target_token_info_res = await self.market_data_provider.get_token_info(target_token_symbol) # Accepts symbol or mint
            if not target_token_info_res.get('success') or not target_token_info_res.get('data'):
                logger.error(f"[{trade_id_for_logging}] Could not fetch token info for target_token_symbol '{target_token_symbol}'. Error: {target_token_info_res.get('error')}")
                return False
            target_token_mint = target_token_info_res['data']['mint']
            target_token_decimals = target_token_info_res['data']['decimals']
            
            base_asset_mint = self.get_config().trading.base_asset # e.g., USDC mint

            input_token_mint: Optional[str] = None
            output_token_mint: Optional[str] = None
            
            if decision == 'BUY': # Buying target_token_symbol with base_asset
                input_token_mint = base_asset_mint
                output_token_mint = target_token_mint
            elif decision == 'SELL': # Selling target_token_symbol for base_asset
                input_token_mint = target_token_mint
                output_token_mint = base_asset_mint
            else:
                logger.warning(f"[{trade_id_for_logging}] Invalid decision '{decision}' in agent order. Trade ignored.")
                return False

            if not all([input_token_mint, output_token_mint, amount_usd > 0]):
                logger.error(f"[{trade_id_for_logging}] Failed to determine valid params for swap. Mints: {input_token_mint}->{output_token_mint}, AmountUSD: {amount_usd}. Order: {agent_order}")
                return False
            
            # Pre-trade price check for RiskManager (optional, RiskManager might do this)
            current_price_response = await self.market_data_provider.get_token_price(target_token_mint, base_asset_mint)
            if not current_price_response['success'] or not current_price_response.get('data') or current_price_response['data'].get('price') is None:
                logger.error(f"[{trade_id_for_logging}] Could not fetch current price for {target_token_symbol} to perform pre-trade risk assessment. Trade aborted. Error: {current_price_response.get('error')}")
                return False
            current_entry_price_estimate = current_price_response['data']['price']
            if current_entry_price_estimate <= 0:
                 logger.error(f"[{trade_id_for_logging}] Current price for {target_token_symbol} is ${current_entry_price_estimate:.6f}. Cannot proceed. Trade aborted.")
                 return False

            # Risk Management: Calculate/Validate final trade size
            # RiskManager might use proposed_amount_usd and potentially adjust it.
            # For now, let's assume RiskManager.check_trade_risk validates or returns an adjusted amount.
            # The current risk_manager.calculate_position_size seems more about initial sizing.
            # We need a pre-flight check here.
            # Let's simplify: if RiskManager has a method `is_trade_approved(token_mint, amount_usd, side)`
            
            # Using existing RiskManager.calculate_position_size as a validation/adjustment step.
            # It might cap amount_usd based on its rules.
            final_trade_amount_usd = self.risk_manager.calculate_position_size(
                token_address=target_token_mint, 
                token_symbol=target_token_symbol, 
                entry_price=current_entry_price_estimate, 
                proposed_amount_usd=amount_usd, # Agent's proposed amount
                stop_loss_price=agent_stop_loss_price, 
                agent_confidence=agent_confidence
            )

            if final_trade_amount_usd <= 0:
                logger.info(f"[{trade_id_for_logging}] RiskManager determined trade size for {target_token_symbol} to be ${final_trade_amount_usd:.2f} (original: ${amount_usd:.2f}). Trade aborted.")
                return False
            
            if final_trade_amount_usd < amount_usd:
                 logger.info(f"[{trade_id_for_logging}] RiskManager adjusted trade size for {target_token_symbol} from ${amount_usd:.2f} to ${final_trade_amount_usd:.2f}.")
            
            # Ensure final_trade_amount_usd doesn't exceed available cash for BUYs
            available_cash_usd = self.portfolio_manager.get_available_cash_for_trading()
            if decision == 'BUY' and final_trade_amount_usd > available_cash_usd:
                logger.warning(f"[{trade_id_for_logging}] Insufficient available cash (${available_cash_usd:.2f}) for BUY of {target_token_symbol} at ${final_trade_amount_usd:.2f}. Trade aborted.")
                return False
            
            if decision == 'SELL':
                # For SELLs, check if portfolio holds enough of input_token_mint (target_token_mint)
                # This requires converting final_trade_amount_usd back to token quantity
                tokens_to_sell = final_trade_amount_usd / current_entry_price_estimate if current_entry_price_estimate > 0 else float('inf')
                
                # PortfolioManager needs a method like get_position(token_mint) -> {'total_amount': float, ...}
                position_data = self.portfolio_manager.get_position(target_token_mint)
                owned_tokens = position_data.get('total_amount', 0) if position_data else 0

                if tokens_to_sell > owned_tokens:
                    logger.warning(f"[{trade_id_for_logging}] Insufficient balance to sell {tokens_to_sell:.6f} {target_token_symbol} (target USD: ${final_trade_amount_usd:.2f}). Have {owned_tokens:.6f}. Trade aborted.")
                    return False
                logger.info(f"[{trade_id_for_logging}] SELL order for {target_token_symbol}: attempting to sell approx {tokens_to_sell:.6f} tokens (for target ${final_trade_amount_usd:.2f} USD).")


            logger.info(f"[{trade_id_for_logging}] Executing Agent Order ({decision.upper()} {target_token_symbol} for ${final_trade_amount_usd:.2f}). SL: {agent_stop_loss_price}, TP: {agent_take_profit_price}. Slippage: {agent_slippage_bps}bps.")

            # Use TradingEngine's async context manager
            async with self.trading_engine:
                swap_result = await self.trading_engine.execute_swap(
                    input_token_mint_str=input_token_mint,
                    output_token_mint_str=output_token_mint,
                    amount_in_usd=final_trade_amount_usd, # TradingEngine now accepts amount_in_usd
                    slippage_bps=agent_slippage_bps
                    # swap_mode can be added if agent provides it or defaults in TradingEngine/Config
                )

            if swap_result.get('success') and swap_result.get('signature'):
                tx_signature = swap_result['signature']
                swap_details = swap_result.get('details', {})
                
                # Extract details for recording. PortfolioManager.record_executed_trade expects specific fields.
                # We need to get actual amounts from quote_response if possible, or use estimates.
                # The new TradingEngine.execute_swap details include quote_response.
                quote_response_data = swap_details.get('quote_response') # This is the SDK QuoteResponse object or dict-like
                
                # Extracting actual amounts and price from the quote response
                # The structure of quote_response_data (SDK's QuoteResponse) needs to be known
                # Example: quote_response_data.in_amount, quote_response_data.out_amount
                # For simplicity, let's assume keys like 'inAmountLamports' and 'outAmountLamports' exist after conversion.
                # These should be derived from the actual quote.
                # Fallback to estimates if not available directly.
                
                amount_in_lamports_from_quote = quote_response_data.route.market_infos[0].in_amount if quote_response_data and hasattr(quote_response_data, 'route') and quote_response_data.route.market_infos else swap_details.get('amount_lamports_swapped')
                amount_out_lamports_from_quote = quote_response_data.out_amount if hasattr(quote_response_data, 'out_amount') else 0

                # Get decimals for input and output tokens to convert lamports to float for recording
                input_token_info = await self.market_data_provider.get_token_info(input_token_mint)
                output_token_info = await self.market_data_provider.get_token_info(output_token_mint)

                input_decimals = input_token_info['data']['decimals'] if input_token_info.get('success') else 0
                output_decimals = output_token_info['data']['decimals'] if output_token_info.get('success') else 0
                
                amount_in_tokens_float_actual = float(amount_in_lamports_from_quote) / (10**input_decimals) if input_decimals else 0
                amount_out_tokens_float_actual = float(amount_out_lamports_from_quote) / (10**output_decimals) if output_decimals else 0

                # Price: USD value of output token / amount of output tokens
                # Or amount_in_usd (which is value of input tokens) / amount_out_tokens_float_actual
                # Ensure final_trade_amount_usd is what was actually used as input value.
                effective_price_usd = final_trade_amount_usd / amount_out_tokens_float_actual if amount_out_tokens_float_actual > 0 else current_entry_price_estimate

                logger.info(f"[{trade_id_for_logging}] Agent order swap successful for {target_token_symbol}. Sig: {tx_signature}.")
                logger.debug(f"[{trade_id_for_logging}] Swap execution details: {swap_details}")
                
                # PortfolioManager.record_executed_trade arguments:
                # trade_id, pair_address (symbol like SOL/USDC or pool), input_token_mint, output_token_mint,
                # amount_in_tokens, amount_out_tokens, price_usd (of output token), amount_in_usd (value of input),
                # side, status, fee_usd, protocol, transaction_signature, jupiter_quote_response, ...
                
                self.portfolio_manager.record_executed_trade(
                    trade_id=tx_signature, # Use signature as trade_id
                    pair_address=token_pair_str, # e.g., "SOL/USDC"
                    input_token_mint=input_token_mint,
                    output_token_mint=output_token_mint,
                    amount_in_tokens=amount_in_tokens_float_actual, # Actual from quote
                    amount_out_tokens=amount_out_tokens_float_actual, # Actual from quote
                    price_usd=effective_price_usd, # Effective price of output token
                    amount_in_usd=final_trade_amount_usd, # The USD value of the input tokens
                    side=decision.upper(), # BUY or SELL
                    status="FILLED", # Assuming full fill from Jupiter swap
                    fee_usd=None, # TODO: Jupiter SDK might provide fee info in quote or tx data
                    protocol="jupiter",
                    transaction_signature=tx_signature,
                    jupiter_quote_response=quote_response_data, # Pass the whole quote object/dict
                    jupiter_transaction_data=swap_details.get('transaction_data'),
                    slippage_bps=agent_slippage_bps,
                    last_valid_block_height=swap_details.get('last_valid_block_height'),
                    reason_source=f"AI_AGENT ({agent_order.get('model_name', 'Gemini')})" # Add model if known
                )
                
                # Add to RiskManager's open positions
                # Position needs: id, token_address (output token if BUY, input if SELL), token_symbol,
                # entry_price, size_usd, size_tokens (of the token held), entry_time, trade_type, SL, TP
                
                position_token_mint = output_token_mint if decision == 'BUY' else input_token_mint
                position_token_symbol = target_token_symbol # The asset we are now exposed to or have sold from
                position_size_tokens = amount_out_tokens_float_actual if decision == 'BUY' else amount_in_tokens_float_actual
                position_entry_price = effective_price_usd

                position = Position(
                    id=tx_signature,
                    token_address=position_token_mint, 
                    token_symbol=position_token_symbol,
                    entry_price=position_entry_price, 
                    size_usd=final_trade_amount_usd, # The value of the trade
                    size_tokens=position_size_tokens, 
                    entry_time=time.time(),
                    trade_type=decision.upper(),
                    stop_loss=agent_stop_loss_price,
                    take_profit=agent_take_profit_price,
                    reasoning=agent_reasoning
                )
                self.risk_manager.add_position(position)
                logger.info(f"[{trade_id_for_logging}] Position {decision.upper()} for {target_token_symbol} (value: ${final_trade_amount_usd:.2f}) added to RiskManager.")
                return True
            else:
                error_msg = swap_result.get('error', 'Unknown error during agent order swap')
                logger.error(f"[{trade_id_for_logging}] Agent order swap failed for {target_token_symbol}: {error_msg}. Full result: {swap_result}")
                # Optionally record a FAILED trade attempt to PortfolioManager
                # For now, just log and return False
                return False

        except Exception as e:
            logger.critical(f"[{trade_id_for_logging}] Unexpected critical error during agent order execution for {agent_order.get('token_pair')}: {e}", exc_info=True)
            return False

    async def execute_trade_signal(self, pair_data: Dict, signal_info: Dict) -> bool:
        """
        DEPRECATED: This method was for older signal-based trading.
        The new approach is to use execute_agent_order with decisions from AIAgent.
        """
        logger.warning("[TradeExecutor] execute_trade_signal is DEPRECATED. Use execute_agent_order.")
        # Simplified example of how it might have worked, now mostly illustrative
        # ... (rest of the old method, largely can be removed or commented out) ...
        return False
        # ... (old implementation details removed for brevity) 