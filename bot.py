import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application, CommandHandler, CallbackQueryHandler,
MessageHandler, filters, ContextTypes, ConversationHandler
)
from parser_krisha import search_krisha

logging.basicConfig(
format=’%(asctime)s - %(name)s - %(levelname)s - %(message)s’,
level=logging.INFO
)
logger = logging.getLogger(**name**)

DEAL_TYPE, CITY, DISTRICT, ROOMS, PRICE_MIN, PRICE_MAX, AREA_MIN, AREA_MAX, COMPLEX = range(9)

CITIES = {
“Астана”: “astana”,
“Алматы”: “almaty”,
“Шымкент”: “shymkent”,
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
“Привет! Я бот для поиска недвижимости на Krisha.kz\n\n”
“Ищу топ-5 лучших объявлений по твоим параметрам.\n\n”
“/search - начать поиск\n”
“/help - справка”
)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
“Как пользоваться:\n\n”
“/search - начать новый поиск\n”
“/cancel - отменить поиск\n\n”
“Бот спросит:\n”
“1. Аренда или продажа\n”
“2. Город\n”
“3. Район (можно пропустить)\n”
“4. Количество комнат\n”
“5. Диапазон цены\n”
“6. Площадь\n”
“7. ЖК (можно пропустить)\n\n”
“И выдаст топ-5 объявлений со ссылками!”
)

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data.clear()
keyboard = [
[
InlineKeyboardButton(“Аренда”, callback_data=“rent”),
InlineKeyboardButton(“Продажа”, callback_data=“sale”)
]
]
await update.message.reply_text(
“Новый поиск\n\nЧто тебя интересует?”,
reply_markup=InlineKeyboardMarkup(keyboard)
)
return DEAL_TYPE

async def deal_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
context.user_data[‘deal_type’] = query.data

```
keyboard = [
    [InlineKeyboardButton(city, callback_data=slug)]
    for city, slug in CITIES.items()
]
await query.edit_message_text(
    "Выбери город:",
    reply_markup=InlineKeyboardMarkup(keyboard)
)
return CITY
```

async def city_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
context.user_data[‘city’] = query.data
await query.edit_message_text(
“Введи район (например: Есиль, Алматы, Байконур)\n\n”
“Или напиши: пропустить”
)
return DISTRICT

async def district_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text.strip()
context.user_data[‘district’] = None if text.lower() == ‘пропустить’ else text

```
keyboard = [
    [
        InlineKeyboardButton("1", callback_data="1"),
        InlineKeyboardButton("2", callback_data="2"),
        InlineKeyboardButton("3", callback_data="3"),
    ],
    [
        InlineKeyboardButton("4", callback_data="4"),
        InlineKeyboardButton("5+", callback_data="5"),
        InlineKeyboardButton("Любое", callback_data="any"),
    ]
]
await update.message.reply_text(
    "Количество комнат:",
    reply_markup=InlineKeyboardMarkup(keyboard)
)
return ROOMS
```

async def rooms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
context.user_data[‘rooms’] = None if query.data == ‘any’ else query.data
await query.edit_message_text(
“Минимальная цена (тенге)\n\nНапример: 100000\nИли: пропустить”
)
return PRICE_MIN

async def price_min_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text.strip()
if text.lower() == ‘пропустить’:
context.user_data[‘price_min’] = None
else:
try:
context.user_data[‘price_min’] = int(text.replace(’ ‘, ‘’).replace(’\xa0’, ‘’))
except ValueError:
await update.message.reply_text(“Введи число или напиши: пропустить”)
return PRICE_MIN

```
await update.message.reply_text(
    "Максимальная цена (тенге)\n\nНапример: 300000\nИли: пропустить"
)
return PRICE_MAX
```

async def price_max_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text.strip()
if text.lower() == ‘пропустить’:
context.user_data[‘price_max’] = None
else:
try:
context.user_data[‘price_max’] = int(text.replace(’ ‘, ‘’).replace(’\xa0’, ‘’))
except ValueError:
await update.message.reply_text(“Введи число или напиши: пропустить”)
return PRICE_MAX

```
await update.message.reply_text(
    "Минимальная площадь (кв.м)\n\nНапример: 45\nИли: пропустить"
)
return AREA_MIN
```

async def area_min_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text.strip()
if text.lower() == ‘пропустить’:
context.user_data[‘area_min’] = None
else:
try:
context.user_data[‘area_min’] = float(text.replace(’,’, ‘.’))
except ValueError:
await update.message.reply_text(“Введи число или напиши: пропустить”)
return AREA_MIN

```
await update.message.reply_text(
    "Максимальная площадь (кв.м)\n\nНапример: 80\nИли: пропустить"
)
return AREA_MAX
```

async def area_max_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text.strip()
if text.lower() == ‘пропустить’:
context.user_data[‘area_max’] = None
else:
try:
context.user_data[‘area_max’] = float(text.replace(’,’, ‘.’))
except ValueError:
await update.message.reply_text(“Введи число или напиши: пропустить”)
return AREA_MAX

```
await update.message.reply_text(
    "Название ЖК (например: Нурсая, Highvill, Комфорт)\n\nИли: пропустить"
)
return COMPLEX
```

async def complex_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text.strip()
context.user_data[‘complex’] = None if text.lower() == ‘пропустить’ else text

```
await update.message.reply_text("Ищу объявления, подожди немного...")

params = context.user_data.copy()

try:
    results = search_krisha(params)
except Exception as e:
    logger.error(f"Ошибка поиска: {e}")
    await update.message.reply_text(
        "Произошла ошибка при поиске. Попробуй ещё раз — /search"
    )
    return ConversationHandler.END

if not results:
    await update.message.reply_text(
        "По твоему запросу ничего не найдено.\n\n"
        "Попробуй изменить параметры — /search"
    )
    return ConversationHandler.END

deal_label = "Аренда" if params.get('deal_type') == 'rent' else "Продажа"
await update.message.reply_text(
    f"Топ-{len(results)} объявлений | {deal_label}\n"
    f"{'—' * 25}"
)

for i, ad in enumerate(results, 1):
    lines = [f"#{i} — {ad['price']}"]
    lines.append(f"Адрес: {ad['address']}")
    if ad.get('rooms'):
        lines.append(f"Комнат: {ad['rooms']}")
    if ad.get('area'):
        lines.append(f"Площадь: {ad['area']}")
    if ad.get('floor'):
        lines.append(f"Этаж: {ad['floor']}")
    if ad.get('description'):
        lines.append(f"{ad['description'][:120]}...")
    lines.append(f"\nСсылка: {ad['url']}")

    await update.message.reply_text("\n".join(lines))

await update.message.reply_text("Новый поиск — /search")
return ConversationHandler.END
```

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data.clear()
await update.message.reply_text(“Поиск отменён. Начать заново — /search”)
return ConversationHandler.END

def main():
token = os.environ.get(“TELEGRAM_BOT_TOKEN”)
if not token:
raise ValueError(“Нет TELEGRAM_BOT_TOKEN в переменных окружения!”)

```
app = Application.builder().token(token).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('search', search)],
    states={
        DEAL_TYPE: [CallbackQueryHandler(deal_type_handler)],
        CITY: [CallbackQueryHandler(city_handler)],
        DISTRICT: [MessageHandler(filters.TEXT & ~filters.COMMAND, district_handler)],
        ROOMS: [CallbackQueryHandler(rooms_handler)],
        PRICE_MIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, price_min_handler)],
        PRICE_MAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, price_max_handler)],
        AREA_MIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, area_min_handler)],
        AREA_MAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, area_max_handler)],
        COMPLEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, complex_handler)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True,
)

app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('help', help_cmd))
app.add_handler(conv_handler)

logger.info("Бот запущен!")
app.run_polling(allowed_updates=Update.ALL_TYPES)
```

if **name** == ‘**main**’:
main()
