from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from config import OWNER_ID, SENIOR_ADMIN_ID

db = Database()

# ========== УПРАВЛЕНИЕ АДМИНАМИ ==========
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить админа: /add_admin <user_id>"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Только владелец может добавлять админов!")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /add_admin <user_id>")
        return
    
    try:
        admin_id = int(context.args[0])
        db.add_admin(admin_id, f"admin_{admin_id}", role="admin")
        await update.message.reply_text(f"✅ Админ {admin_id} добавлен!")
    except ValueError:
        await update.message.reply_text("❌ Неверный user_id!")

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить админа: /remove_admin <user_id>"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Только владелец может удалять админов!")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /remove_admin <user_id>")
        return
    
    try:
        admin_id = int(context.args[0])
        if admin_id == OWNER_ID or admin_id == SENIOR_ADMIN_ID:
            await update.message.reply_text("❌ Нельзя удалить главных администраторов!")
            return
        
        db.remove_admin(admin_id)
        await update.message.reply_text(f"✅ Админ {admin_id} удален!")
    except ValueError:
        await update.message.reply_text("❌ Неверный user_id!")

async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список всех админов: /admin_list"""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа!")
        return
    
    admins = db.get_all_admins()
    
    if not admins:
        await update.message.reply_text("📋 Админов нет")
        return
    
    text = "👥 **СПИСОК АДМИНИСТРАТОРОВ**\n\n"
    for admin in admins:
        role = "👑 Владелец" if admin[0] == OWNER_ID else ("⭐ Старший" if admin[0] == SENIOR_ADMIN_ID else "🔧 Админ")
        text += f"{role}\nID: {admin[0]}\nИмя: {admin[1]}\n\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

# ========== ВЫВОДЫ ==========
async def approve_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Одобрить вывод: /approve_withdrawal <code>"""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа!")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /approve_withdrawal <код>")
        return
    
    code = context.args[0]
    success, message = db.approve_withdrawal(code, user_id)
    
    if success:
        withdrawal = db.get_withdrawal_by_code(code)
        user = db.get_user(withdrawal[1])
        
        text = f"""
✅ **ВЫВОД ОДОБРЕН**

💰 Сумма: {withdrawal[2] - withdrawal[3]} ⭐
👤 Пользователь: {user[1]}
🧾 Код: {code}

Отправьте эти звёзды пользователю {user[1]}.
"""
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ {message}")

async def reject_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отклонить вывод: /reject_withdrawal <code>"""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа!")
        return
    
    if not context.args:
        await update.message.reply_text("Использование: /reject_withdrawal <код>")
        return
    
    code = context.args[0]
    success, message = db.reject_withdrawal(code, user_id)
    
    if success:
        withdrawal = db.get_withdrawal_by_code(code)
        await update.message.reply_text(
            f"✅ Вывод отклонен\n💰 {withdrawal[2] - withdrawal[3]} ⭐ возвращены пользователю",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"❌ {message}")

async def pending_withdrawals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать ожидающие выводы: /pending_withdrawals"""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа!")
        return
    
    withdrawals = db.get_pending_withdrawals()
    
    if not withdrawals:
        await update.message.reply_text("✅ Нет ожидающих выводов")
        return
    
    text = "💸 **ОЖИДАЮЩИЕ ВЫВОДЫ**\n\n"
    
    for w in withdrawals:
        user = db.get_user(w[1])
        text += f"""
👤 Пользователь: {user[1]}
💰 Сумма: {w[2] - w[3]} ⭐ (комиссия: {w[3]} ⭐)
🧾 Код: `{w[3]}`
⏰ Создан: {w[7]}

"""
    
    text += "Используйте /approve_withdrawal <код> или /reject_withdrawal <код>"
    
    await update.message.reply_text(text, parse_mode="Markdown")

# ========== ПРОМОКОДЫ ==========
async def create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создать промокод: /create_promo <код> <награда> <лимит>"""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа!")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text("Использование: /create_promo <код> <награда> <лимит>")
        return
    
    code = context.args[0].upper()
    
    try:
        reward = int(context.args[1])
        limit = int(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ Награда и лимит должны быть числами!")
        return
    
    success = db.create_promo(code, reward, limit, user_id)
    
    if success:
        await update.message.reply_text(
            f"✅ Промокод создан!\n\n"
            f"Код: **{code}**\n"
            f"Награда: **{reward} ⭐**\n"
            f"Лимит: **{limit}** использований",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Промокод с таким названием уже существует!")

async def list_promos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список промокодов: /list_promos"""
    user_id = update.effective_user.id
    
    if not db.is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа!")
        return
    
    promos = db.get_all_promos()
    
    if not promos:
        await update.message.reply_text("📋 Промокодов нет")
        return
    
    text = "🎟️ **СПИСОК ПРОМОКОДОВ**\n\n"
    
    for promo in promos:
        text += f"""
Код: **{promo[1]}**
Награда: {promo[2]} ⭐
Использовано: {promo[4]}/{promo[3]}
Статус: {'✅ Активен' if promo[3] > promo[4] else '❌ Закончился'}

"""
    
    await update.message.reply_text(text, parse_mode="Markdown")
