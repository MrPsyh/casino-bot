import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN
from handlers import (
    start,
    age_verification,
    rules_verification,
    check_subscription,
    main_menu_callback,
    show_profile,
    show_games,
    select_game,
    select_bet,
    play_dice,
    show_balance_menu,
    show_withdrawal_menu,
    withdrawal_handler,
    promo_handler,
    admin_menu,
    admin_withdrawals,
    show_help,
    admin_help
)
from admin_commands import (
    add_admin,
    remove_admin,
    list_admins,
    approve_withdrawal,
    reject_withdrawal,
    pending_withdrawals,
    create_promo,
    list_promos
)
from database import Database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Проверка промокода
    if context.user_data.get('waiting_for_promo'):
        success, message = db.use_promo(user_id, text)
        context.user_data['waiting_for_promo'] = False
        
        await update.message.reply_text(message)
        return
    
    # Кастомная сумма вывода
    if context.user_data.get('waiting_for_withdrawal_amount'):
        try:
            amount = int(text)
            code, message = db.create_withdrawal(user_id, amount)
            
            if code:
                result_text = f"""
✅ **ЗАЯВКА НА ВЫВОД СОЗДАНА**

Код вывода:
`{code}`

Сумма вывода: {amount - 50} ⭐
Комиссия: 50 ⭐

Покажите этот код администратору @Alenovv для подтверждения.
"""
                await update.message.reply_text(result_text, parse_mode="Markdown")
            else:
                await update.message.reply_text(f"❌ {message}")
        except ValueError:
            await update.message.reply_text("❌ Введите число!")
        finally:
            context.user_data['waiting_for_withdrawal_amount'] = False

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    """Запуск бота"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin_help", admin_help))
    
    # Команды администратора
    app.add_handler(CommandHandler("add_admin", add_admin))
    app.add_handler(CommandHandler("remove_admin", remove_admin))
    app.add_handler(CommandHandler("admin_list", list_admins))
    app.add_handler(CommandHandler("approve_withdrawal", approve_withdrawal))
    app.add_handler(CommandHandler("reject_withdrawal", reject_withdrawal))
    app.add_handler(CommandHandler("pending_withdrawals", pending_withdrawals))
    app.add_handler(CommandHandler("create_promo", create_promo))
    app.add_handler(CommandHandler("list_promos", list_promos))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(age_verification, pattern="^age_"))
    app.add_handler(CallbackQueryHandler(rules_verification, pattern="^rules_"))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="^check_subscription$"))
    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$|^play$|^profile$|^balance_menu$|^help$"))
    app.add_handler(CallbackQueryHandler(show_games, pattern="^play$"))
    app.add_handler(CallbackQueryHandler(select_game, pattern="^game_"))
    app.add_handler(CallbackQueryHandler(select_bet, pattern="^bet_"))
    app.add_handler(CallbackQueryHandler(play_dice, pattern="^dice_"))
    app.add_handler(CallbackQueryHandler(show_balance_menu, pattern="^balance_menu$"))
    app.add_handler(CallbackQueryHandler(show_withdrawal_menu, pattern="^withdrawal$"))
    app.add_handler(CallbackQueryHandler(withdrawal_handler, pattern="^withdraw_"))
    app.add_handler(CallbackQueryHandler(promo_handler, pattern="^promo$"))
    app.add_handler(CallbackQueryHandler(admin_menu, pattern="^admin$"))
    app.add_handler(CallbackQueryHandler(admin_withdrawals, pattern="^admin_withdrawals$"))
    
    # Text handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    # Запуск
    print("✅ Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
