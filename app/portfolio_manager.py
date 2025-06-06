from app.database import EnhancedDatabase
from app.config_v2 import get_config
from app.market.market_data import MarketDataProvider # Import MarketDataProvider
from typing import List, Dict, Optional, Any
import logging
import time # For timestamping
import json

logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self, market_data_provider: MarketDataProvider, db_path: Optional[str] = None):
        """Manages the portfolio, including cash, positions, and overall value."""
        self.db = EnhancedDatabase(db_path)
        self.market_data_provider = market_data_provider
        self.base_currency = get_config().trading.base_asset # e.g., USDC mint address
        # Initialize cash balance from DB or config, for now, from config.
        # A more robust approach would load last known cash balance from DB.
        self._current_cash_balance_usd = get_config().INITIAL_PORTFOLIO_BALANCE_USD
        logger.info(f"PortfolioManager initialized. Initial cash: ${self._current_cash_balance_usd:.2f} USD")

    def get_available_cash_for_trading(self) -> float:
        """Returns the currently available cash balance in USD."""
        # This could be more complex, e.g., accounting for unsettled trades or margin.
        # For now, it's the main cash balance.
        return self._current_cash_balance_usd

    async def get_total_portfolio_value(self) -> float:
        """Calculates the total current value of the portfolio (cash + value of open positions)."""
        total_value = self._current_cash_balance_usd
        open_positions = self.db.get_active_trades() # Assuming this returns a list of position-like dicts
        
        # TODO: Implement a proper position tracking mechanism instead of just active trades.
        # Active trades might not represent the full picture of all assets held.
        # For now, let's assume get_active_trades gives us enough info to value positions.

        for position in open_positions:
            try:
                # Position dict needs: 'output_token_mint', 'amount_tokens_out' (or similar for asset held)
                # Let's assume a simplified structure for now, needs alignment with DB schema
                token_mint = position.get('output_token_mint') # The asset we hold
                amount_tokens = position.get('amount_tokens_out') # The amount of that asset we hold
                
                if not token_mint or amount_tokens is None:
                    logger.warning(f"Skipping position due to missing mint or amount: {position}")
                    continue

                # Skip if the held asset is the base currency (cash already accounted for)
                if token_mint == self.base_currency:
                    continue

                # Fetch current price of the asset vs. base currency (USD)
                price_response = await self.market_data_provider.get_token_price(token_mint, self.base_currency)
                
                if price_response['success'] and price_response['data']:
                    current_price_usd = price_response['data']['price']
                    position_value_usd = amount_tokens * current_price_usd
                    total_value += position_value_usd
                    logger.debug(f"Valued position: {amount_tokens} of {token_mint} at ${current_price_usd:.4f} = ${position_value_usd:.2f}")
                else:
                    entry_price = position.get('entry_price') # Or avg_buy_price if available
                    if entry_price and amount_tokens:
                         # Fallback: use entry price if current price unavailable, but log warning
                        logger.warning(f"Could not fetch current price for {token_mint}. Using entry price ${entry_price:.4f} for valuation. Error: {price_response.get('error')}")
                        total_value += amount_tokens * entry_price
                    else:
                        logger.error(f"Could not value position for {token_mint} due to missing price and entry_price/amount. Position: {position}")
            except Exception as e:
                logger.error(f"Error valuing position {position.get('pair', 'N/A')}: {e}", exc_info=True)
        
        logger.info(f"Total portfolio value calculated: ${total_value:.2f}")
        return total_value

    def get_open_positions_summary(self) -> List[Dict[str, Any]]:
        """Returns a summary of all currently open positions/active trades."""
        # This should ideally fetch consolidated positions, not just individual trades that are active.
        # For now, uses get_active_trades() as a proxy.
        active_trades = self.db.get_active_trades()
        summary = []
        for trade in active_trades:
            # Assuming trade dictionary from DB has relevant fields
            # Adapt this to the actual structure returned by get_active_trades()
            summary.append({
                "trade_id": trade.get('id'),
                "pair": trade.get('pair'), # e.g., SOL/USDC
                "type": trade.get('side', 'N/A'), # BUY/SELL relative to the pair
                "entry_price": trade.get('entry_price'),
                "amount_in_usd": trade.get('amount'), # Original USD value of trade
                "amount_tokens_out": trade.get('amount_tokens_out'), # Quantity of the acquired token
                "output_token_mint": trade.get('output_token_mint'),
                "timestamp": trade.get('timestamp'),
                # Potentially add current value and P&L if calculable here
            })
        return summary

    def record_executed_trade(
        self,
        trade_id: str,
        pair_address: str, # Mint address of the pair/pool if applicable
        input_token_mint: str,
        output_token_mint: str,
        amount_in_tokens: float, # Amount of input_token_mint
        amount_out_tokens: float, # Amount of output_token_mint received
        price_usd: float, # Effective price of output_token_mint in USD (amount_in_usd / amount_out_tokens)
        amount_in_usd: float, # Total USD value of the input tokens
        side: str, # "BUY" or "SELL" (e.g., BUY SOL/USDC means buying SOL with USDC)
        status: str, # e.g., "FILLED", "PARTIALLY_FILLED"
        fee_usd: Optional[float] = 0.0, # Total fees in USD for the trade
        protocol: Optional[str] = "jupiter",
        transaction_signature: Optional[str] = None,
        jupiter_quote_response: Optional[Dict] = None,
        jupiter_transaction_data: Optional[Dict] = None,
        slippage_bps: Optional[int] = None,
        last_valid_block_height: Optional[int] = None,
        reason_source: Optional[str] = "UNKNOWN" # e.g., AI_AGENT, MANUAL, STRATEGY_X
    ) -> bool:
        """Records an executed trade in the database and updates cash balance."""
        try:
            # Database recording
            db_trade_data = {
                'id': trade_id, # Assuming trade_id is generated by TradeExecutor or AIAgent
                'pair': pair_address, # This might be the pair symbol like SOL/USDC or pool address
                'input_token_mint': input_token_mint,
                'output_token_mint': output_token_mint,
                'amount_tokens_in': amount_in_tokens,
                'amount_tokens_out': amount_out_tokens,
                'entry_price': price_usd, # Price of the token acquired, in USD
                'amount': amount_in_usd, # USD value of the trade
                'side': side, 
                'status': status,
                'fees_usd': fee_usd,
                'protocol': protocol,
                'transaction_signature': transaction_signature,
                'jupiter_quote_response': json.dumps(jupiter_quote_response) if jupiter_quote_response else None,
                'jupiter_transaction_data': json.dumps(jupiter_transaction_data) if jupiter_transaction_data else None,
                'slippage_bps': slippage_bps,
                'last_valid_block_height': last_valid_block_height,
                'timestamp': time.time(), # Record execution timestamp here
                'reason_source': reason_source,
            }
            self.db.record_trade(db_trade_data)
            logger.info(f"Trade {trade_id} recorded in DB. Signature: {transaction_signature}")

            # Update cash balance
            # If we spent base currency (USDC) to buy another token
            if side == "BUY" and input_token_mint == self.base_currency:
                self._current_cash_balance_usd -= (amount_in_usd + (fee_usd or 0.0))
                logger.info(f"BUY trade. Cash reduced by ${amount_in_usd + (fee_usd or 0.0):.2f}. New cash: ${self._current_cash_balance_usd:.2f}")
            # If we sold a token for base currency (USDC)
            elif side == "SELL" and output_token_mint == self.base_currency:
                self._current_cash_balance_usd += (amount_out_tokens - (fee_usd or 0.0)) # amount_out_tokens is USDC amount received
                logger.info(f"SELL trade. Cash increased by ${amount_out_tokens - (fee_usd or 0.0):.2f}. New cash: ${self._current_cash_balance_usd:.2f}")
            # TODO: Handle trades between non-base currencies if portfolio holds multiple crypto assets.
            # For now, assumes trades are always into or out of the base_currency (USD/USDC).

            # Persist current cash balance to DB? Or rely on next startup from config?
            # For robustness, periodic saving of portfolio state (cash, positions) to DB is good.
            # For now, it's in-memory.
            return True
        except Exception as e:
            logger.error(f"Error recording trade {trade_id} or updating cash balance: {e}", exc_info=True)
            # Potentially raise a custom PortfolioManagerError
            return False

    def get_position(self, token_mint: str) -> Optional[Dict[str, Any]]:
        """Retrieves the consolidated position for a given token mint."""
        # This requires a proper positions table in the DB that aggregates trades.
        # Placeholder for now.
        # It should return {'token_mint': ..., 'total_amount': ..., 'average_buy_price': ...}
        logger.warning("get_position is a placeholder and not fully implemented.")
        # Example logic if we had a positions table:
        # return self.db.get_position_by_mint(token_mint)
        # For now, simulate by looking at last BUY trade if any (very naive)
        all_trades = self.db.get_trades_for_token(token_mint)
        if all_trades:
            # This is not a real position, just an example of what kind of data might be needed
            last_buy = next((t for t in reversed(all_trades) if t.get('side') == 'BUY' and t.get('output_token_mint') == token_mint), None)
            if last_buy:
                return {
                    "token_mint": token_mint,
                    "total_amount": last_buy.get('amount_tokens_out'),
                    "average_buy_price": last_buy.get('entry_price')
                }
        return None

    # TODO:
    # - Method to load/save portfolio state (cash, positions) from/to DB for persistence.
    # - More sophisticated position tracking (aggregating buys/sells for a token to get avg price, total amount).
    # - P&L calculation per position and overall. 