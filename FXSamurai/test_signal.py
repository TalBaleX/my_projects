# test_order.py
from screen_executor import login, select_symbol, place_order
from config import BrokerConfig, StrategyConfig

symbol = StrategyConfig.symbol.replace("/", "")  # → "GBPUSD"

print("1. Логин...")
login(BrokerConfig.terminal_url,
      BrokerConfig.account,
      BrokerConfig.password,
      BrokerConfig.server)

print("2. Выбор символа...")
select_symbol(symbol)

print("3. Ордер...")
# Подставь любые реалистичные цифры вручную
place_order(
    direction   = "LONG",
    stop        = 1.34100,   # ← замени на близкие к текущей цене
    take_profit = 1.34700,   # ← замени
    symbol      = symbol
)

print("Готово.")