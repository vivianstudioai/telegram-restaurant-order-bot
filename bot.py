"""Telegram restaurant order bot - menu, cart, custom requests, order confirmation.

Vivian Studio - https://github.com/vivianstudioai
"""
import json
import logging
import os
import time
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

MENU_PATH = Path(os.getenv("MENU_PATH", "menu.json"))
ORDERS_LOG = Path(os.getenv("ORDERS_LOG", "orders.jsonl"))
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")  # where new orders are forwarded

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger("order-bot")

MENU = json.loads(MENU_PATH.read_text(encoding="utf-8"))
CARTS = {}  # chat_id -> list of {item, note}


def cart(chat_id):
    return CARTS.setdefault(chat_id, [])


def categories_kb():
    rows = [[InlineKeyboardButton(c["name"], callback_data=f"cat:{i}")]
            for i, c in enumerate(MENU["categories"])]
    rows.append([InlineKeyboardButton("View cart / عرض السلة", callback_data="cart")])
    return InlineKeyboardMarkup(rows)


def items_kb(cat_index):
    cat = MENU["categories"][cat_index]
    rows = [[InlineKeyboardButton(f'{i["name"]} - {i["price"]} {MENU["currency"]}',
                                  callback_data=f"add:{cat_index}:{j}")]
            for j, i in enumerate(cat["items"])]
    rows.append([InlineKeyboardButton("Back", callback_data="menu")])
    return InlineKeyboardMarkup(rows)


def cart_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Confirm order", callback_data="confirm")],
        [InlineKeyboardButton("Clear cart", callback_data="clear")],
    ])


def cart_text(entries):
    if not entries:
        return "Your cart is empty."
    lines = [f'- {e["item"]["name"]}' + (f' ({e["note"]})' if e.get("note") else "")
             + f' - {e["item"]["price"]} {MENU["currency"]}' for e in entries]
    total = sum(e["item"]["price"] for e in entries)
    return "Your order:\n" + "\n".join(lines) + f'\n\nTotal: {total} {MENU["currency"]}'


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MENU["welcome"], reply_markup=categories_kb())


async def buttons(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    chat_id = q.message.chat_id
    action, *parts = q.data.split(":")
    if action == "menu":
        await q.edit_message_text(MENU["welcome"], reply_markup=categories_kb())
    elif action == "cat":
        await q.edit_message_text("Choose an item:", reply_markup=items_kb(int(parts[0])))
    elif action == "add":
        item = MENU["categories"][int(parts[0])]["items"][int(parts[1])]
        cart(chat_id).append({"item": item, "note": ""})
        ctx.user_data["awaiting_note_for"] = len(cart(chat_id)) - 1
        await q.edit_message_text(
            f'Added: {item["name"]}.\nSend any customization now (e.g. "no onion, extra sauce"), or /skip.',
            reply_markup=cart_kb())
    elif action == "cart":
        await q.edit_message_text(cart_text(cart(chat_id)), reply_markup=cart_kb())
    elif action == "clear":
        CARTS[chat_id] = []
        await q.edit_message_text("Cart cleared.", reply_markup=categories_kb())
    elif action == "confirm":
        entries = cart(chat_id)
        if not entries:
            await q.edit_message_text("Your cart is empty.", reply_markup=categories_kb())
            return
        order = {"ts": int(time.time()), "chat_id": chat_id,
                 "user": q.from_user.full_name, "items": entries}
        with ORDERS_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(order, ensure_ascii=False) + "\n")
        CARTS[chat_id] = []
        await q.edit_message_text(cart_text(entries) + "\n\nOrder confirmed! "
                                  "We will message you here when it is on the way.")
        if OWNER_CHAT_ID:
            await ctx.bot.send_message(int(OWNER_CHAT_ID),
                                       "NEW ORDER:\n" + cart_text(entries))


async def note(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    idx = ctx.user_data.get("awaiting_note_for")
    if idx is not None and idx < len(cart(chat_id)):
        cart(chat_id)[idx]["note"] = update.message.text
        ctx.user_data["awaiting_note_for"] = None
        await update.message.reply_text("Noted! " + cart_text(cart(chat_id)),
                                        reply_markup=cart_kb())
    else:
        await update.message.reply_text("Use /start to browse the menu.")


async def skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["awaiting_note_for"] = None
    await update.message.reply_text(cart_text(cart(update.message.chat_id)),
                                    reply_markup=cart_kb())


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]  # from @BotFather
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("skip", skip))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, note))
    log.info("Bot running. Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
