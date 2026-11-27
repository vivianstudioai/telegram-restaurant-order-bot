# Telegram Restaurant Order Bot

A complete ordering flow inside Telegram: browse a menu by category, add items, write custom requests ("no onion, extra sauce"), review the cart, and confirm. The owner gets every order instantly. Built by Mohamed Salah.

This is the bot from our demo video - a real, runnable version you can deploy for any restaurant, cafe, or food business.

## Features

- **Menu in one file** - edit `menu.json` (categories, items, prices, currency), restart, done.
- **Inline buttons** - customers never type commands; everything is tappable.
- **Free-text customization** - after adding an item, the customer just writes their request in plain language and it is attached to that item.
- **Cart + total** - live cart with running total in your currency.
- **Instant owner notification** - set `OWNER_CHAT_ID` and every confirmed order lands in your Telegram.
- **Order log** - every order appended to `orders.jsonl` (easy to pipe into Google Sheets or a dashboard).
- **Single dependency** - just `python-telegram-bot`.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env   # paste your token from @BotFather
python bot.py
```

Message your bot on Telegram: `/start`, pick a category, add items, confirm.

## Customize

| Setting | Where | Default |
| --- | --- | --- |
| Categories, items, prices | `menu.json` | sample restaurant menu |
| Currency label | `menu.json` -> `currency` | `EGP` |
| Welcome text | `menu.json` -> `welcome` | - |
| Owner order notifications | `OWNER_CHAT_ID` env var | off |

## Deploy

Runs on Render, Railway, a VPS, or a Raspberry Pi. Keep it alive with systemd, Docker, or your platform's worker process.

## License

MIT - see [LICENSE](LICENSE).
