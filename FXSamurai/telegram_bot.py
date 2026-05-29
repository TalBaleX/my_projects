import requests
from datetime import datetime
from config import TelegramConfig

class TelegramNotifier:
    def __init__(self, token: str = TelegramConfig.token,
             chat_id: str = TelegramConfig.chat_id):
        self.token    = token
        self.chat_id  = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"

    def send_signal(self, signal_data: dict) -> bool:
        msg = self._format(signal_data)
        return self._send(msg)

    def _format(self, d: dict) -> str:
        emoji = "🟢" if d['direction'] == 'LONG' else "🔴"
        return (
            f"{emoji} *{d['direction']}* — {d['timestamp'].strftime('%H:%M %d.%m')}\n"
        f"💱 {d.get('symbol', 'GBP/USD')}\n\n"  # <-- добавил
            f"💰 Вход:  `{d['entry']:.5f}`\n"
            f"🛑 Стоп:  `{d['stop']:.5f}`\n"
            f"🎯 Тейк:  `{d['take_profit']:.5f}`\n\n"
            f"📈 R:R:   *1 : {d['rr_ratio']:.2f}*\n"
            f"📉 GMM:   {d['gmm_osc']:.3f}\n"
            f"📊 ADX:   {d['adx']:.1f}"
        )

    def _send(self, text: str) -> bool:
        try:
            resp = requests.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=10,
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"[Telegram] Ошибка: {e}")
            return False