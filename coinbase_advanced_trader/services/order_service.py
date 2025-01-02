import uuid
from decimal import Decimal
from typing import Dict, Any, Optional

from coinbase.rest import RESTClient

from coinbase_advanced_trader.models import Order, OrderSide, OrderType
from coinbase_advanced_trader.trading_config import (
    BUY_PRICE_MULTIPLIER,
    SELL_PRICE_MULTIPLIER
)
from coinbase_advanced_trader.logger import logger
from coinbase_advanced_trader.utils import calculate_base_size
from .price_service import PriceService


class OrderService:
    """Service for handling order-related operations."""

    def __init__(self, rest_client: RESTClient, price_service: PriceService):
        """
        Initialize the OrderService.

        Args:
            rest_client (RESTClient): The REST client for API calls.
            price_service (PriceService): The service for price-related operations.
        """
        self.rest_client = rest_client
        self.price_service = price_service
        self.MAKER_FEE_RATE = Decimal('0.006')

    def _generate_client_order_id(self) -> str:
        """Generate a unique client order ID."""
        return str(uuid.uuid4())

    def fiat_market_buy(self, product_id: str, fiat_amount: str) -> Order:
        """
        Place a market buy order for a specified fiat amount.

        Args:
            product_id (str): The ID of the product to buy.
            fiat_amount (str): The amount of fiat currency to spend.

        Returns:
            Order: The order object containing details about the executed order.

        Raises:
            Exception: If the order placement fails.
        """
        try:
            order_response = self.rest_client.market_order_buy(
                self._generate_client_order_id(), product_id, fiat_amount
            )
            if not order_response['success']:
                error_response = order_response.get('error_response', {})
                error_message = error_response.get('message', 'Unknown error')
                preview_failure_reason = error_response.get('preview_failure_reason', 'Unknown')
                error_log = (f"Failed to place a market buy order. "
                             f"Reason: {error_message}. "
                             f"Preview failure reason: {preview_failure_reason}")
                logger.error(error_log)
                raise Exception(error_log)
            
            order = Order(
                id=order_response['success_response']['order_id'],
                product_id=product_id,
                side=OrderSide.BUY,
                type=OrderType.MARKET,
                size=Decimal(fiat_amount)
            )
            self._log_order_result(order_response, product_id, fiat_amount)
            return order
        except Exception as e:
            error_message = str(e)
            if "Invalid product_id" in error_message:
                error_log = (f"Failed to place a market buy order. "
                             f"Reason: {error_message}. "
                             f"Preview failure reason: Unknown")
                logger.error(error_log)
            raise

    def fiat_market_sell(self, product_id: str, fiat_amount: str) -> Order:
        """
        Place a market sell order for a specified fiat amount.

        Args:
            product_id (str): The ID of the product to sell (e.g., "BTC-USDC").
            fiat_amount (str): The amount of fiat currency to receive.

        Returns:
            Order: The order object containing details about the executed order.

        Raises:
            Exception: If the order placement fails.
        """
        spot_price = self.price_service.get_spot_price(product_id)
        product_details = self.price_service.get_product_details(product_id)
        base_increment = Decimal(product_details['base_increment'])
        base_size = calculate_base_size(Decimal(fiat_amount), spot_price, base_increment)
        
        try:
            order_response = self.rest_client.market_order_sell(
                self._generate_client_order_id(), product_id, str(base_size)
            )
            if not order_response['success']:
                error_response = order_response.get('error_response', {})
                error_message = error_response.get('message', 'Unknown error')
                preview_failure_reason = error_response.get('preview_failure_reason', 'Unknown')
                error_log = (f"Failed to place a market sell order. "
                             f"Reason: {error_message}. "
                             f"Preview failure reason: {preview_failure_reason}")
                logger.error(error_log)
                raise Exception(error_log)
            
            order = Order(
                id=order_response['success_response']['order_id'],
                product_id=product_id,
                side=OrderSide.SELL,
                type=OrderType.MARKET,
                size=base_size
            )
            self._log_order_result(order_response, product_id, str(base_size), spot_price, OrderSide.SELL)
            return order
        except Exception as e:
            error_message = str(e)
            if "Invalid product_id" in error_message:
                error_log = (f"Failed to place a market sell order. "
                             f"Reason: {error_message}. "
                             f"Preview failure reason: Unknown")
                logger.error(error_log)
            raise

    def fiat_limit_buy(self, product_id: str, fiat_amount: str, limit_price: Optional[str] = None, price_multiplier: float = BUY_PRICE_MULTIPLIER) -> Order:
        """
        Place a limit buy order for a specified fiat amount.

        Args:
            product_id (str): The ID of the product to buy.
            fiat_amount (str): The amount of fiat currency to spend.
            limit_price (Optional[str]): The specific limit price for the order (overrides price_multiplier if provided).
            price_multiplier (float): The multiplier for the current price (used if limit_price is not provided).

        Returns:
            Order: The order object containing details about the executed order.
        """
        return self._place_limit_order(product_id, fiat_amount, limit_price, price_multiplier, OrderSide.BUY)

    def fiat_limit_sell(self, product_id: str, fiat_amount: str, limit_price: Optional[str] = None, price_multiplier: float = SELL_PRICE_MULTIPLIER) -> Order:
        """
        Place a limit sell order for a specified fiat amount.

        Args:
            product_id (str): The ID of the product to sell.
            fiat_amount (str): The amount of fiat currency to receive.
            limit_price (Optional[str]): The specific limit price for the order (overrides price_multiplier if provided).
            price_multiplier (float): The multiplier for the current price (used if limit_price is not provided).

        Returns:
            Order: The order object containing details about the executed order.
        """
        return self._place_limit_order(product_id, fiat_amount, limit_price, price_multiplier, OrderSide.SELL)
    
    def _place_limit_order(self, product_id: str, fiat_amount: str, limit_price: Optional[str], price_multiplier: float, side: OrderSide) -> Order:
        """
        Place a limit order.

        Args:
            product_id (str): The ID of the product.
            fiat_amount (str): The amount of fiat currency.
            limit_price (Optional[str]): The specific limit price for the order (overrides price_multiplier if provided).
            price_multiplier (float): The multiplier for the current price (used if limit_price is not provided).
            side (OrderSide): The side of the order (buy or sell).

        Returns:
            Order: The order object containing details about the executed order.
        """
        logger.info(f"Starting limit order placement - Side: {side}, Product: {product_id}")
        
        current_price = self.price_service.get_spot_price(product_id)
        if current_price is None:
            raise ValueError(f"Could not get current price for {product_id}")
        
        product_details = self.price_service.get_product_details(product_id)
        if product_details is None:
            raise ValueError(f"Could not get product details for {product_id}")

        base_increment = Decimal(product_details['base_increment'])
        quote_increment = Decimal(product_details['quote_increment'])

        # Calculate adjusted price
        adjusted_price = (Decimal(limit_price) if limit_price 
                        else current_price * Decimal(str(price_multiplier))).quantize(quote_increment)

        # Calculate base size
        base_size = (Decimal(fiat_amount) / adjusted_price if side == OrderSide.SELL
                    else calculate_base_size(Decimal(fiat_amount), adjusted_price, base_increment))
        base_size = base_size.quantize(base_increment)

        # Place the order
        order_func = (self.rest_client.limit_order_gtc_buy 
                    if side == OrderSide.BUY 
                    else self.rest_client.limit_order_gtc_sell)
        
        order_response = order_func(
            self._generate_client_order_id(),
            product_id,
            str(base_size),
            str(adjusted_price)
        )

        if order_response["success"]:
            """
            The order was successful. Process, log, and return.
            """
            order = self._build_order(
                order_response['success_response']['order_id'],
                product_id,
                side,
                OrderType.LIMIT,
                base_size,
                adjusted_price
            )
            self._log_order_result(order_response, product_id, base_size, adjusted_price, side)
            logger.info(f"Order: {order}")
            return order
        
        else:
            """
            For some reason, the order placement failed. Log and return "something(?)"
            """
            order_error = order_response['error_response']["error"]
            logger.info(f"Order placed resulted in {order_error}")

            """
            Build an Order object with the error_response.error as the the
            order_id. This convention allows to return an order and be able
            to handle issues with order placement.
            """

            error_order_id = 'ORDER_ERROR_'+order_error

            error_order = self._build_order(
                error_order_id, 
                product_id, 
                side, 
                OrderType.LIMIT, 
                base_size, 
                adjusted_price, 
                'error'
            )

            match order_error:
                case 'INSUFFICIENT_FUND':
                    logger.info("Do NSF stuff here.")
                    return error_order

                case 'INVALID_LIMIT_PRICE_POST_ONLY':
                    logger.info("Do INVALID_LIMIT_PRICE_POST_ONLY stuff here")
                    return error_order

                case 'INVALID_PRICE_PRECISION':
                    logger.info("Do INVALID_PRICE_PRECISION stuff here.")
                    return error_order

                case _:
                    logger.error("An unprocessed order error occurred.")
                    return error_order
                    
    def _build_order(id, product_id, side, type, size, price, status = 'pending') -> Order:
        """
        Helper function to build an Order object. Include 'status' parameter
        to allow for error orders.
        """
        order = Order(
                id=id,
                product_id=product_id,
                side=side,
                type=type,
                size=size,
                price=price,
                status=status
        )
        return order
    
    def _log_order_result(self, order: Dict[str, Any], product_id: str, amount: Any, price: Any = None, side: OrderSide = None) -> None:
        """
        Log the result of an order.

        Args:
            order (Dict[str, Any]): The order response from Coinbase.
            product_id (str): The ID of the product.
            amount (Any): The actual amount of the order.
            price (Any, optional): The price of the order (for limit orders).
            side (OrderSide, optional): The side of the order (buy or sell).
        """
        base_currency, quote_currency = product_id.split('-')
        order_type = "limit" if price else "market"
        side_str = side.name.lower() if side else "unknown"

        if order['success']:
            if price:
                total_amount = Decimal(amount) * Decimal(price)
                log_message = (f"Successfully placed a {order_type} {side_str} order "
                               f"for {amount} {base_currency} "
                               f"(${total_amount:.2f}) at a price of {price} {quote_currency}.")
            else:
                log_message = (f"Successfully placed a {order_type} {side_str} order "
                               f"for {amount} {quote_currency} of {base_currency}.")
            logger.info(log_message)
        else:
            failure_reason = order.get('failure_reason', 'Unknown')
            preview_failure_reason = order.get('error_response', {}).get('preview_failure_reason', 'Unknown')
            logger.error(f"Failed to place a {order_type} {side_str} order. "
                         f"Reason: {failure_reason}. "
                         f"Preview failure reason: {preview_failure_reason}")
        
        logger.info(f"Coinbase response: {order}")