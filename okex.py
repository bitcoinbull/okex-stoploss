import time
import json
from OkcoinFutureAPI import *


class OkEx:
    config = None
    okcoinFuture = None

    def __init__(self, cfg):
        self.config = cfg
        self.okcoinFuture = OKCoinFuture('https://www.okex.com', cfg.access_key, cfg.secret_key)

    def get_price(self):
        resp = self.okcoinFuture.future_ticker(self.config.market, self.config.contract_type)
        data = json.loads(resp)
        return data['ticker']['last']

    def sync_account(self):
        user_info = self.okcoinFuture.future_userinfo_4fix()
        data = json.loads(user_info)
        if not data or not data['result']:
            return False

        cc = self.config.market.split('_')[-2]
        contracts = data['info'][cc]['contracts']
        for contract in contracts:
            if contract['contract_type'] != self.config.contract_type:
                continue

            self.config.ex_ava_bal = contract['available']
            self.config.ex_used_bal = contract['freeze'] + contract['bond']
            self.config.ex_total_bal = contract['available'] + contract['bond'] + contract['unprofit']

        pos_info = self.okcoinFuture.future_position_4fix(self.config.market[-7:], self.config.contract_type, 1)
        data = json.loads(pos_info)
        if not data or not data['result']:
            return False

        self.config.long_position['total_amount'] = 0
        self.config.long_position['total_contract'] = 0
        self.config.long_position['ava_amount'] = 0
        self.config.long_position['ava_contract'] = 0
        self.config.long_position['price'] = 0

        self.config.short_position['total_amount'] = 0
        self.config.short_position['total_contract'] = 0
        self.config.short_position['ava_amount'] = 0
        self.config.short_position['ava_contract'] = 0
        self.config.short_position['price'] = 0

        holdings = data['holding']
        for holding in holdings:
            if holding['lever_rate'] != self.config.lever:
                continue

            if holding['buy_amount'] > 0:
                self.config.long_position['total_amount'] = holding['buy_bond']
                self.config.long_position['total_contract'] = holding['buy_amount']
                self.config.long_position['ava_amount'] = holding['buy_bond'] * 1.0 * holding['buy_available'] / holding['buy_amount']
                self.config.long_position['ava_contract'] = holding['buy_available']
                self.config.long_position['price'] = holding['buy_price_avg']

            if holding['sell_amount'] > 0:
                self.config.short_position['total_amount'] = holding['sell_bond']
                self.config.short_position['total_contract'] = holding['sell_amount']
                self.config.short_position['ava_amount'] = holding['sell_bond'] * 1.0 * holding['sell_available'] / holding['sell_amount']
                self.config.short_position['ava_contract'] = holding['sell_available']
                self.config.short_position['price'] = holding['sell_price_avg']

        return True

    def sync_orders(self):
        orders = self.okcoinFuture.future_orderinfo(self.config.market[-7:], self.config.contract_type, '-1', '1', '1', '2')
        data = json.loads(orders)
        if not data or not data['result']:
            return False

        orders = data['orders']
        for odr in orders:
            if odr['lever_rate'] != self.config.lever:
                continue

            order = dict()
            order['id'] = odr['order_id']
            order['timestamp'] = odr['create_date'] / 1000
            if odr['type'] == 1:
                order['order_type'] = 'bid'
            if odr['type'] == 2:
                order['order_type'] = 'ask'
            if odr['type'] == 3:
                order['order_type'] = 'exit_bid'
            if odr['type'] == 4:
                order['order_type'] = 'exit_ask'

            order['amount'] = odr['amount'] * odr['unit_amount'] / self.config.lever / odr['price']
            order['contract'] = odr['amount']
            order['price'] = odr['price']
            order['status'] = 1

            self.config.pending_orders.append(order)

        return True

    def trade(self, order_type, amount, price):
        trade_type = 1
        contract_amount = 0
        if order_type == 'bid':
            trade_type = 1
            price = price * (1 + self.config.open_pos_slippage)
            contract_amount = int(amount * self.config.lever * price / self.config.contract_value)
        if order_type == 'exit_bid':
            trade_type = 3
            price = price * (1 - self.config.close_pos_slippage)
            contract_amount = amount*self.config.lever*self.config.long_position['price']/self.config.contract_value
            if contract_amount / self.config.long_position['ava_contract'] > 0.95:
                contract_amount = self.config.long_position['ava_contract']
            else:
                contract_amount = int(contract_amount)
        if order_type == 'ask':
            trade_type = 2
            price = price * (1 - self.config.open_pos_slippage)
            contract_amount = int(amount * self.config.lever * price / self.config.contract_value)
        if order_type == 'exit_ask':
            trade_type = 4
            price = price * (1 + self.config.close_pos_slippage)
            contract_amount = amount*self.config.lever*self.config.short_position['price']/self.config.contract_value
            if contract_amount / self.config.short_position['ava_contract'] > 0.95:
                contract_amount = self.config.short_position['ava_contract']
            else:
                contract_amount = int(contract_amount)

        order = dict()
        order['id'] = '-1'
        order['timestamp'] = int(time.time())
        order['order_type'] = order_type
        order['amount'] = amount
        order['contract'] = contract_amount
        order['price'] = price
        order['status'] = 1

        self.okcoinFuture.future_trade(self.config.market[-7:], self.config.contract_type, price, contract_amount, trade_type, '1', self.config.lever)

    def cancel(self, order):
        self.okcoinFuture.future_cancel(self.config.market[-7:], self.config.contract_type, order['id'])

    def bid(self, amount, price, close_ask):
        if not self.check_position('bid', amount):
            return

        self.trade('bid', amount, price)
        if close_ask:
            self.exit_ask(price)

    def exit_bid(self, price):
        if self.config.long_position['ava_amount'] == 0:
            return

        self.trade('exit_bid', self.config.long_position['ava_amount'], price)

    def ask(self, amount, price, close_bid):
        if not self.check_position('ask', amount):
            return

        self.trade('ask', amount, price)
        if close_bid:
            self.exit_bid(price)

    def exit_ask(self, price):
        if self.config.short_position['ava_amount'] == 0:
            return

        self.trade('exit_ask', self.config.short_position['ava_amount'], price)

    def expire_orders(self, orders):
        if len(orders) == 0:
            return

        for order in self.config.pending_orders:
            if order['status'] < 0:
                pass

            cur_time = int(time.time())
            if cur_time - order['timestamp'] > self.config.order_valid_time:
                self.cancel(order)

    def check_stop_loss_profit(self, cur_price):
        if self.config.long_position['ava_amount'] > 0:
            rate = (cur_price - self.config.long_position['price']) / self.config.long_position['price'] * self.config.lever
            if rate >= self.config.stop_profit_rate_long:
                self.exit_bid(cur_price)

            if rate * -1 >= self.config.stop_loss_rate_long:
                self.exit_bid(cur_price)

        if self.config.short_position['ava_amount'] > 0:
            rate = (self.config.short_position['price'] - cur_price) / self.config.short_position['price'] * self.config.lever
            if rate > self.config.stop_profit_rate_short:
                self.exit_ask(cur_price)

            if rate * -1 > self.config.stop_loss_rate_short:
                self.exit_ask(cur_price)



