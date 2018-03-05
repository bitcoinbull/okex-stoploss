### 用途

OkEx期货止损用的程序，服务器端监控，达到止损位自动止损


### 参数说明

打开client.py，需要修改一下参数

cfg.access_key = '' # ApiKey

cfg.secret_key = '' # SecretKey

cfg.market = 'btc_usd' # 交易对

cfg.contract_type = 'quarter' # 可选this_week, next_week, quarter

cfg.lever = 20 # 杠杆倍数

cfg.contract_value = 100 # 一张合约价值

cfg.order_valid_time = 60 * 1 # 订单有效时间

cfg.stop_profit_rate_long = 1 # 多头止赢比例

cfg.stop_loss_rate_long = 0.6 # 多头止损比例，0.6表60%

cfg.stop_profit_rate_short = 1 # 空头止赢比例

cfg.stop_loss_rate_short = 1 # 空头止损比例

cfg.open_pos_slippage = 0.001 # 开单滑点

cfg.close_pos_slippage = 0.001 # 平仓滑点

### 部署流程

1. 购买一台阿里云，系统要求Ubuntu
2. 安装python环境，sudo apt-get install python python-pip
3. 安装requests模块, sudo pip install requests
4. 把程序拷贝到用户目录下，运行deploy.sh脚本即可，先修改登录需要的username，password，url
5. 登录服务器，创建定时任务crontab -e，最后一行添加 */3 * * * * /bin/bash /home/username/stoploss/run.sh，将run.sh文件中的username改成自己的
