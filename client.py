import time
from okex import OkEx


class Config:
    def __init__(self):
        pass


cfg = Config()

cfg.access_key = ''
cfg.secret_key = ''

cfg.market = 'btc_usd'
cfg.contract_type = 'quarter'
cfg.lever = 20
cfg.contract_value = 100

cfg.order_valid_time = 60 * 0

cfg.stop_profit_rate_long = 1
cfg.stop_loss_rate_long = 0.4

cfg.stop_profit_rate_short = 1
cfg.stop_loss_rate_short = 0.4

cfg.open_pos_slippage = 0.001
cfg.close_pos_slippage = 0.001

for i in range(1):
    cfg.long_position = dict()
    cfg.short_position = dict()
    cfg.pending_orders = []

    ok = OkEx(cfg)
    price = ok.get_price()
    if price <= 0:
        break

    time.sleep(1)

    ok.sync_account()
    time.sleep(1)

    ok.sync_orders()
    time.sleep(1)

    ok.expire_orders(cfg.pending_orders)
    time.sleep(1)

    ok.check_stop_loss_profit(price)

    time.sleep(2)

