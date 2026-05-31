from telegram import Update, Dice
from telegram.ext import ContextTypes
from database import Database
from keyboards import *
from config import *
import random

db = Database()

# ========== СТАРТ И ВЕРИФИКАЦИЯ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    db.create_user(user_id, username)
    user = db.get_user(user_id)
    
    # Если уже верифицирован
    if user[5] and user[6]:  # age_verified и rules_accepted
        await show_main_menu(update, context)
        return
    
    # Если не верифицирован
    await update.message.reply_text(
        AGE_WARNING,
        reply_markup=verification_keyboard()
    )

async def age_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка проверки возраста"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data == "age_yes":
        db.verify_age(user_id)
        await query.edit_message_text(
            RULES_TEXT,
            reply_markup=rules_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "😔 Нам жаль, но вам должно быть 18+ для входа.\n\nВозвращайтесь когда исполнится 18 лет!"
        )

async def rules_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка согласия с правилами"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data == "rules_accept":
        db.accept_rules(user_id)
        
        # Проверка подписки на канал
        try:
            member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
            if member.status in ["member", "administrator", "creator"]:
                db.set_subscribed(user_id, 1)
                await query.edit_message_text("✅ Вы верифицированы! Начнём играть? 🎮")
                await show_main_menu(update, context)
                return
        except:
            pass
        
        await query.edit_message_text(
            SUBSCRIPTION_WARNING,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Я подписан", callback_data="check_subscription")
            ]])
        )
    else:
        await query.edit_message_text(
            AGREEMENT_REQUIRED,
            reply_markup=rules_keyboard()
        )

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка подписки на канал"""
    query = update.callback_query
    user_id = query.from_user.id
    
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        if member.status in ["member", "administrator", "creator"]:
            db.set_subscribed(user_id, 1)
            await query.edit_message_text("✅ Подписка подтверждена! Добро пожаловать! 🎮")
            await show_main_menu(update, context)
            return
    except:
        pass
    
    await query.answer("❌ Вы не подписаны на канал!", show_alert=True)

# ========== ГЛАВНОЕ МЕНЮ ==========
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню"""
    user_id = update.effective_user.id
    
    # Проверка верификации
    if not db.is_verified(user_id):
        await update.callback_query.edit_message_text(
            AGREEMENT_REQUIRED,
            reply_markup=rules_keyboard()
        )
        return
    
    balance = db.get_balance(user_id)
    text = f"""
🎰 **КАЗИНО ALOMEL** 🎰

Добро пожаловать, {update.effective_user.first_name}!

💰 Ваш баланс: **{balance} ⭐**

Выберите действие:
"""
    
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок главного меню"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not db.is_verified(user_id):
        await query.answer(AGREEMENT_REQUIRED, show_alert=True)
        return
    
    if query.data == "main_menu":
        await show_main_menu(update, context)
    elif query.data == "play":
        await show_games(update, context)
    elif query.data == "profile":
        await show_profile(update, context)
    elif query.data == "balance_menu":
        await show_balance_menu(update, context)
    elif query.data == "help":
        await show_help(update, context)

# ========== ПРОФИЛЬ ==========
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать профиль пользователя"""
    query = update.callback_query
    user_id = query.from_user.id
    user = db.get_user(user_id)
    
    text = f"""
👤 **ВАШ ПРОФИЛЬ**

💰 Баланс: **{user[2]} ⭐**
📊 Всего пополнено: **{user[3]} ⭐**
📉 Всего проиграно: **{user[4]} ⭐**
📈 Всего выиграно: **{user[5]} ⭐**

Прибыль/Убыток: **{user[5] - user[4]} ⭐**
"""
    
    await query.edit_message_text(text, reply_markup=back_keyboard("main_menu"), parse_mode="Markdown")

# ========== ИГРЫ ==========
async def show_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список доступных игр"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not db.is_verified(user_id):
        await query.answer(AGREEMENT_REQUIRED, show_alert=True)
        return
    
    text = """
🎮 **ВЫБЕРИТЕ ИГРУ**

🏀 **Футбол** - Угадай Гол или Промах
🏀 **Баскетбол** - Попадание или Промах
🎲 **Кубик** - Чётное или Нечётное
🎳 **Боулинг** - Сбей больше кегель чем бот
"""
    
    await query.edit_message_text(text, reply_markup=games_menu_keyboard(), parse_mode="Markdown")

async def select_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор игры и ставки"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not db.is_verified(user_id):
        await query.answer(AGREEMENT_REQUIRED, show_alert=True)
        return
    
    game_map = {
        "game_football": "🏀 Футбол",
        "game_basketball": "🏀 Баскетбол",
        "game_dice": "🎲 Кубик",
        "game_bowling": "🎳 Боулинг"
    }
    
    game_type = query.data.split("_")[1]
    game_name = game_map[query.data]
    
    context.user_data['selected_game'] = game_type
    
    text = f"""
{game_name}

💸 **Выберите ставку:**
Минимум: {MIN_BET} ⭐
Максимум: {MAX_BET} ⭐
"""
    
    await query.edit_message_text(text, reply_markup=bet_selection_keyboard(game_type), parse_mode="Markdown")

async def select_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор размера ставки"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Парсинг ставки
    parts = query.data.split("_")
    game_type = parts[1]
    bet_amount = int(parts[2])
    
    # Проверка баланса
    balance = db.get_balance(user_id)
    if balance < bet_amount:
        await query.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    context.user_data['game_type'] = game_type
    context.user_data['bet_amount'] = bet_amount
    
    # Снять ставку с баланса
    db.remove_balance(user_id, bet_amount, transaction_type="bet", game_type=game_type)
    
    # В зависимости от игры
    if game_type == "dice":
        await query.edit_message_text(
            f"🎲 **Кубик**\n\nВаша ставка: **{bet_amount} ⭐**\n\nВыберите: Чётное или Нечётное?",
            reply_markup=dice_choice_keyboard(user_id),
            parse_mode="Markdown"
        )
    elif game_type == "football":
        await play_football(update, context, bet_amount)
    elif game_type == "basketball":
        await play_basketball(update, context, bet_amount)
    elif game_type == "bowling":
        await play_bowling(update, context, bet_amount)

# ========== ИГРА ФУТБОЛ ==========
async def play_football(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount):
    """Игра Футбол"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Отправить стикер
    is_goal = random.choice([True, False])
    
    # Диапазон для football на Telegram
    football_dice = await context.bot.send_dice(
        chat_id=query.from_user.id,
        emoji="⚽"
    )
    
    context.user_data['last_bet'] = bet_amount
    context.user_data['is_goal'] = is_goal
    
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=f"⚽ **Ваша ставка: {bet_amount} ⭐**\n\nРезультат кидаю...",
        parse_mode="Markdown"
    )

# ========== ИГРА КУБИК ==========
async def play_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Игра с кубиком"""
    query = update.callback_query
    user_id = query.from_user.id
    
    choice = query.data.split("_")[1]  # even или odd
    bet_amount = context.user_data.get('bet_amount', 0)
    
    # Отправить кубик
    dice = await context.bot.send_dice(
        chat_id=query.from_user.id,
        emoji="🎲"
    )
    
    context.user_data['dice_choice'] = choice
    context.user_data['dice_value'] = dice.dice.value
    
    # Проверка результата
    is_even = dice.dice.value % 2 == 0
    win = (choice == "even" and is_even) or (choice == "odd" and not is_even)
    
    if win:
        winnings = bet_amount * 2
        db.add_winnings(user_id, winnings, game_type="dice")
        result_text = f"""
✅ **ВЫ ВЫИГРАЛИ!**

🎲 Выпало: {dice.dice.value}
💰 Выигрыш: {winnings} ⭐
"""
    else:
        result_text = f"""
❌ **ВЫ ПРОИГРАЛИ**

🎲 Выпало: {dice.dice.value}
💰 Ставка: {bet_amount} ⭐
"""
    
    balance = db.get_balance(user_id)
    
    result_text += f"\n💳 Новый баланс: {balance} ⭐"
    
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=result_text,
        reply_markup=play_again_keyboard(),
        parse_mode="Markdown"
    )

# ========== СТАБЫ ДЛЯ ОСТАЛЬНЫХ ИГРА ==========
async def play_basketball(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount):
    """Игра Баскетбол (stub)"""
    query = update.callback_query
    user_id = query.from_user.id
    
    is_hit = random.choice([True, False])
    
    if is_hit:
        winnings = bet_amount * 2
        db.add_winnings(user_id, winnings, game_type="basketball")
        result_text = f"✅ **ПОПАДАНИЕ!**\n💰 Выигрыш: {winnings} ⭐"
    else:
        result_text = f"❌ **ПРОМАХ**\n💰 Ставка: {bet_amount} ⭐"
    
    balance = db.get_balance(user_id)
    result_text += f"\n💳 Баланс: {balance} ⭐"
    
    await query.edit_message_text(
        result_text,
        reply_markup=play_again_keyboard(),
        parse_mode="Markdown"
    )

async def play_bowling(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount):
    """Игра Боулинг"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Бот кидает первым
    bot_pins = random.randint(0, 10)
    user_pins = random.randint(0, 10)
    
    if user_pins > bot_pins:
        winnings = bet_amount * 2
        db.add_winnings(user_id, winnings, game_type="bowling")
        result_text = f"""
✅ **ВЫ ВЫИГРАЛИ!**

🎳 Бот сбил: {bot_pins} кегель
🎳 Вы сбили: {user_pins} кегель
💰 Выигрыш: {winnings} ⭐
"""
    else:
        result_text = f"""
❌ **ВЫ ПРОИГРАЛИ**

🎳 Бот сбил: {bot_pins} кегель
🎳 Вы сбили: {user_pins} кегель
💰 Ставка: {bet_amount} ⭐
"""
    
    balance = db.get_balance(user_id)
    result_text += f"\n💳 Баланс: {balance} ⭐"
    
    await query.edit_message_text(
        result_text,
        reply_markup=play_again_keyboard(),
        parse_mode="Markdown"
    )

# ========== БАЛАНС И ВЫВОД ==========
async def show_balance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню баланса"""
    query = update.callback_query
    user_id = query.from_user.id
    balance = db.get_balance(user_id)
    
    text = f"""
💳 **БАЛАНС**

💰 Текущий баланс: **{balance} ⭐**

Минимальная ставка: {MIN_BET} ⭐
Максимальная ставка: {MAX_BET} ⭐

Минимальный вывод: {MIN_WITHDRAWAL} ⭐
Комиссия вывода: {WITHDRAWAL_FEE} ⭐
"""
    
    await query.edit_message_text(text, reply_markup=balance_menu_keyboard(), parse_mode="Markdown")

async def show_withdrawal_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню вывода"""
    query = update.callback_query
    
    text = """
💸 **ВЫВОД СРЕДСТВ**

Выберите сумму вывода:
"""
    
    await query.edit_message_text(text, reply_markup=withdrawal_amount_keyboard(), parse_mode="Markdown")

async def withdrawal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка вывода"""
    query = update.callback_query
    user_id = query.from_user.id
    
    amount = int(query.data.split("_")[1])
    
    code, message = db.create_withdrawal(user_id, amount)
    
    if code:
        text = f"""
✅ **ЗАЯВКА НА ВЫВОД СОЗДАНА**

Код вывода:
`{code}`

Сумма вывода: {amount - WITHDRAWAL_FEE} ⭐
Комиссия: {WITHDRAWAL_FEE} ⭐

Покажите этот код администратору @Alenovv для подтверждения.
"""
        await query.edit_message_text(text, reply_markup=back_keyboard("balance_menu"), parse_mode="Markdown")
    else:
        await query.answer(f"❌ {message}", show_alert=True)

async def promo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка промокодов"""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.edit_message_text(
        "🎟️ **ВВЕДИТЕ ПРОМОКОД**\n\nОтправьте промокод сообщением:",
        reply_markup=back_keyboard("balance_menu")
    )
    
    context.user_data['waiting_for_promo'] = True

# ========== АДМИН ПАНЕЛЬ ==========
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню админа"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not db.is_admin(user_id):
        await query.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    text = """
🔧 **АДМИН ПАНЕЛЬ**

Выберите действие:
"""
    
    await query.edit_message_text(text, reply_markup=admin_menu_keyboard(), parse_mode="Markdown")

async def admin_withdrawals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр выводов"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not db.is_admin(user_id):
        await query.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    withdrawals = db.get_pending_withdrawals()
    
    if not withdrawals:
        await query.edit_message_text(
            "✅ Нет ожидающих выводов",
            reply_markup=back_keyboard("admin_menu")
        )
        return
    
    text = "💸 **ОЖИДАЮЩИЕ ВЫВОДЫ**\n\n"
    
    for w in withdrawals:
        user = db.get_user(w[1])
        text += f"""
💰 Сумма: {w[2]} ⭐
🧾 Код: `{w[3]}`
👤 Пользователь: {user[1]}
"""
    
    text += "\nОтправьте код вывода чтобы его обработать"
    
    await query.edit_message_text(text, reply_markup=back_keyboard("admin_menu"), parse_mode="Markdown")

# ========== ПОМОЩЬ ==========
async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать справку"""
    query = update.callback_query
    
    text = """
ℹ️ **СПРАВКА**

**/start** - Начать игру
**/admin_help** - Команды администратора
**/profile** - Ваш профиль
**/balance** - Баланс и вывод

📞 Поддержка: @Alenovv
"""
    
    await query.edit_message_text(text, reply_markup=back_keyboard("main_menu"), parse_mode="Markdown")

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команды админа"""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа!")
        return
    
    text = """
🔧 **КОМАНДЫ АДМИНИСТРАТОРА**

**Управление:**
/add_admin <user_id> - Добавить админа
/remove_admin <user_id> - Удалить админа
/admin_list - Список админов

**Выводы:**
/approve_withdrawal <code> - Одобрить вывод
/reject_withdrawal <code> - Отклонить вывод
/pending_withdrawals - Ожидающие выводы

**Промокоды:**
/create_promo <code> <reward> <limit> - Создать промокод
/list_promos - Список промокодов

**Общее:**
/bot_menu - Меню бота
"""
    
    await update.message.reply_text(text, parse_mode="Markdown")
