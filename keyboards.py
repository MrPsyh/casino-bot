from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# ========== ВЕРИФИКАЦИЯ ==========
def verification_keyboard():
    """Клавиатура для проверки возраста"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, мне 18+", callback_data="age_yes"),
            InlineKeyboardButton("❌ Нет", callback_data="age_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def rules_keyboard():
    """Клавиатура для согласия с правилами"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Согласиться", callback_data="rules_accept"),
            InlineKeyboardButton("❌ Не согласен", callback_data="rules_decline")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def main_menu_keyboard():
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("🎮 Играть", callback_data="play")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("💳 Баланс", callback_data="balance_menu")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ИГРЫ ==========
def games_menu_keyboard():
    """Меню выбора игр"""
    keyboard = [
        [InlineKeyboardButton("🏀 Футбол", callback_data="game_football")],
        [InlineKeyboardButton("🏀 Баскетбол", callback_data="game_basketball")],
        [InlineKeyboardButton("🎲 Кубик", callback_data="game_dice")],
        [InlineKeyboardButton("🎳 Боулинг", callback_data="game_bowling")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def bet_selection_keyboard(game_type):
    """Выбор ставки"""
    keyboard = [
        [InlineKeyboardButton("15 ⭐", callback_data=f"bet_{game_type}_15")],
        [InlineKeyboardButton("25 ⭐", callback_data=f"bet_{game_type}_25")],
        [InlineKeyboardButton("50 ⭐", callback_data=f"bet_{game_type}_50")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="play")]
    ]
    return InlineKeyboardMarkup(keyboard)

def dice_choice_keyboard(game_id):
    """Выбор чёт/нечет для кубика"""
    keyboard = [
        [InlineKeyboardButton("🟢 Чётное", callback_data=f"dice_even_{game_id}")],
        [InlineKeyboardButton("🔴 Нечётное", callback_data=f"dice_odd_{game_id}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="play")]
    ]
    return InlineKeyboardMarkup(keyboard)

def play_again_keyboard():
    """Сыграть ещё или в меню"""
    keyboard = [
        [InlineKeyboardButton("🔄 Сыграть ещё", callback_data="play")],
        [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== БАЛАНС ==========
def balance_menu_keyboard():
    """Меню баланса"""
    keyboard = [
        [InlineKeyboardButton("💰 Пополнить", callback_data="deposit")],
        [InlineKeyboardButton("💸 Вывести", callback_data="withdrawal")],
        [InlineKeyboardButton("🎟️ Промокод", callback_data="promo")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def withdrawal_amount_keyboard():
    """Выбор суммы вывода"""
    keyboard = [
        [InlineKeyboardButton("500 ⭐", callback_data="withdraw_500")],
        [InlineKeyboardButton("750 ⭐", callback_data="withdraw_750")],
        [InlineKeyboardButton("1000 ⭐", callback_data="withdraw_1000")],
        [InlineKeyboardButton("💬 Своя сумма", callback_data="withdraw_custom")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="balance_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== АДМИН ПАНЕЛЬ ==========
def admin_menu_keyboard():
    """Меню админа"""
    keyboard = [
        [InlineKeyboardButton("👥 Управление", callback_data="admin_manage")],
        [InlineKeyboardButton("💸 Выводы", callback_data="admin_withdrawals")],
        [InlineKeyboardButton("🎟️ Промокоды", callback_data="admin_promos")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_manage_keyboard():
    """Управление админами"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить админа", callback_data="add_admin")],
        [InlineKeyboardButton("➖ Удалить админа", callback_data="remove_admin")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard(callback="main_menu"):
    """Простая кнопка назад"""
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data=callback)]
    ]
    return InlineKeyboardMarkup(keyboard)
