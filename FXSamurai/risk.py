# risk.py
class RiskManager:
    def __init__(
        self,
        start_balance,
        risk_percent=0.05,
        stop_loss_ratio=0.5,
        min_trade=1.0,
        base_x=10.0,
        multiplier=1.5,
        checkpoint_stop_ratio=0.83,
    ):
        self.start_balance = float(start_balance)
        self.current_checkpoint = float(start_balance)
        self.y = 0

        self.risk_percent = float(risk_percent)
        self.stop_loss_ratio = float(stop_loss_ratio)
        self.min_trade = float(min_trade)
        self.base_x = float(base_x)
        self.multiplier = float(multiplier)
        self.checkpoint_stop_ratio = float(checkpoint_stop_ratio)

    def update_checkpoint(self, balance):
        target = self.start_balance * (self.multiplier ** (self.y + 1))
        if balance >= target:
            self.y += 1
            self.current_checkpoint = target
            print(f"[CHECKPOINT] достигнут: {target:.2f}")

    def should_stop(self, balance):
        if balance <= self.start_balance * self.stop_loss_ratio:
            return True
        if balance <= self.current_checkpoint * self.checkpoint_stop_ratio:
            return True
        return False

    def trade_amount(self, balance):
        staged = self.base_x * (self.multiplier ** self.y)
        risk_cap = balance * self.risk_percent
        amount = max(self.min_trade, min(staged, risk_cap))
        return round(amount, 2)
