import sqlite3
import string
from datetime import datetime
from config import DB_PATH, MIN_WITHDRAWAL, WITHDRAWAL_FEE

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                total_deposit INTEGER DEFAULT 0,
                total_lost INTEGER DEFAULT 0,
                total_won INTEGER DEFAULT 0,
                age_verified BOOLEAN DEFAULT 0,
                rules_accepted BOOLEAN DEFAULT 0,
                subscribed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица транзакций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                type TEXT,
                game_type TEXT,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица заявок на вывод
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                commission INTEGER,
                withdrawal_code TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                admin_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица админов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER PRIMARY KEY,
                username TEXT,
                role TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица промокодов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                reward INTEGER,
                usage_limit INTEGER,
                times_used INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(created_by) REFERENCES admins(admin_id)
            )
        ''')
        
        # Таблица использованных промокодов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promo_uses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                code_id INTEGER,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(code_id) REFERENCES promo_codes(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ========== ПОЛЬЗОВАТЕЛИ ==========
    def user_exists(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def create_user(self, user_id, username=None):
        if not self.user_exists(user_id):
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (user_id, username)
                VALUES (?, ?)
            ''', (user_id, username))
            conn.commit()
            conn.close()
    
    def get_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def update_user(self, user_id, **kwargs):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for key, value in kwargs.items():
            cursor.execute(f'UPDATE users SET {key} = ? WHERE user_id = ?', (value, user_id))
        
        conn.commit()
        conn.close()
    
    def verify_age(self, user_id):
        self.update_user(user_id, age_verified=1)
    
    def accept_rules(self, user_id):
        self.update_user(user_id, rules_accepted=1)
    
    def set_subscribed(self, user_id, subscribed=1):
        self.update_user(user_id, subscribed=subscribed)
    
    def is_verified(self, user_id):
        """Проверка прошёл ли пользователь верификацию"""
        user = self.get_user(user_id)
        return user and user[5] and user[6]  # age_verified и rules_accepted
    
    # ========== БАЛАНС ==========
    def add_balance(self, user_id, amount, transaction_type="deposit", game_type=None):
        """Добавить на баланс"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Добавить транзакцию
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, game_type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, transaction_type, game_type))
        
        # Обновить баланс
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        current = cursor.fetchone()[0]
        cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', 
                      (current + amount, user_id))
        
        if transaction_type == "deposit":
            cursor.execute('SELECT total_deposit FROM users WHERE user_id = ?', (user_id,))
            total = cursor.fetchone()[0]
            cursor.execute('UPDATE users SET total_deposit = ? WHERE user_id = ?', 
                          (total + amount, user_id))
        
        conn.commit()
        conn.close()
    
    def remove_balance(self, user_id, amount, transaction_type="loss", game_type=None):
        """Снять с баланса"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        current = cursor.fetchone()[0]
        
        if current < amount:
            conn.close()
            return False
        
        # Добавить транзакцию
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, game_type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, -amount, transaction_type, game_type))
        
        # Обновить баланс
        cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', 
                      (current - amount, user_id))
        
        if transaction_type == "loss":
            cursor.execute('SELECT total_lost FROM users WHERE user_id = ?', (user_id,))
            total = cursor.fetchone()[0]
            cursor.execute('UPDATE users SET total_lost = ? WHERE user_id = ?', 
                          (total + amount, user_id))
        
        conn.commit()
        conn.close()
        return True
    
    def add_winnings(self, user_id, amount, game_type=None):
        """Добавить выигрыш"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Добавить транзакцию
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, game_type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, 'win', game_type))
        
        # Обновить баланс
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        current = cursor.fetchone()[0]
        cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', 
                      (current + amount, user_id))
        
        # Обновить статистику выигрышей
        cursor.execute('SELECT total_won FROM users WHERE user_id = ?', (user_id,))
        total = cursor.fetchone()[0]
        cursor.execute('UPDATE users SET total_won = ? WHERE user_id = ?', 
                      (total + amount, user_id))
        
        conn.commit()
        conn.close()
    
    def get_balance(self, user_id):
        user = self.get_user(user_id)
        return user[2] if user else 0
    
    # ========== ВЫВОДЫ ==========
    def generate_withdrawal_code(self):
        """Генерирует уникальный код вывода"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM withdrawals')
        count = cursor.fetchone()[0]
        
        if count < 1000000:
            code = f"#{count + 1}"
        else:
            # После миллиона идёт a1, a2, ... a1000000, потом b1
            letters = string.ascii_lowercase
            cycle = (count - 1000000) // 1000000
            
            if cycle >= 26:  # Все буквы закончились
                conn.close()
                return None  # Выводы недоступны
            
            pos = (count - 1000000) % 1000000
            code = f"#{letters[cycle]}{pos + 1}"
        
        conn.close()
        return code
    
    def create_withdrawal(self, user_id, amount):
        """Создать заявку на вывод"""
        balance = self.get_balance(user_id)
        
        if balance < amount:
            return None, "Недостаточно средств"
        
        if amount < MIN_WITHDRAWAL:
            return None, f"Минимальный вывод: {MIN_WITHDRAWAL} ⭐"
        
        code = self.generate_withdrawal_code()
        if not code:
            return None, "Выводы временно недоступны"
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO withdrawals (user_id, amount, commission, withdrawal_code)
                VALUES (?, ?, ?, ?)
            ''', (user_id, amount, WITHDRAWAL_FEE, code))
            
            # Снять сумму с баланса
            self.remove_balance(user_id, amount, transaction_type="withdrawal")
            
            conn.commit()
            conn.close()
            
            return code, f"Выводит: {amount - WITHDRAWAL_FEE} ⭐ (комиссия: {WITHDRAWAL_FEE} ⭐)"
        except Exception as e:
            conn.close()
            return None, str(e)
    
    def get_withdrawal_by_code(self, code):
        """Получить информацию о выводе по коду"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM withdrawals WHERE withdrawal_code = ?', (code,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def approve_withdrawal(self, code, admin_id):
        """Одобрить вывод"""
        withdrawal = self.get_withdrawal_by_code(code)
        
        if not withdrawal:
            return False, "Вывод не найден"
        
        if withdrawal[5] != 'pending':
            return False, "Вывод уже обработан"
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE withdrawals 
            SET status = 'approved', approved_at = ?, admin_id = ?
            WHERE withdrawal_code = ?
        ''', (datetime.now(), admin_id, code))
        
        conn.commit()
        conn.close()
        return True, "Вывод одобрен"
    
    def reject_withdrawal(self, code, admin_id):
        """Отклонить вывод и вернуть деньги"""
        withdrawal = self.get_withdrawal_by_code(code)
        
        if not withdrawal:
            return False, "Вывод не найден"
        
        user_id = withdrawal[1]
        amount = withdrawal[2]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE withdrawals 
            SET status = 'rejected', admin_id = ?
            WHERE withdrawal_code = ?
        ''', (admin_id, code))
        
        # Вернуть деньги на баланс
        self.add_balance(user_id, amount, transaction_type="rejection")
        
        conn.commit()
        conn.close()
        return True, "Вывод отклонен, деньги возвращены"
    
    def get_pending_withdrawals(self):
        """Получить все ожидающие выводы"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM withdrawals WHERE status = "pending"')
        results = cursor.fetchall()
        conn.close()
        return results
    
    # ========== АДМИНЫ ==========
    def add_admin(self, admin_id, username, role="admin"):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO admins (admin_id, username, role)
            VALUES (?, ?, ?)
        ''', (admin_id, username, role))
        conn.commit()
        conn.close()
    
    def remove_admin(self, admin_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admins WHERE admin_id = ?', (admin_id,))
        conn.commit()
        conn.close()
    
    def is_admin(self, user_id):
        from config import ADMINS
        return user_id in ADMINS
    
    def get_all_admins(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins')
        results = cursor.fetchall()
        conn.close()
        return results
    
    # ========== ПРОМОКОДЫ ==========
    def create_promo(self, code, reward, usage_limit, created_by):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO promo_codes (code, reward, usage_limit, created_by)
                VALUES (?, ?, ?, ?)
            ''', (code.upper(), reward, usage_limit, created_by))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def use_promo(self, user_id, code):
        """Использовать промокод"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM promo_codes WHERE code = ?', (code.upper(),))
        promo = cursor.fetchone()
        
        if not promo:
            conn.close()
            return False, "Промокод не найден"
        
        if promo[3] <= promo[4]:  # usage_limit <= times_used
            conn.close()
            return False, "Промокод больше не действителен"
        
        # Проверить, использовал ли пользователь этот код
        cursor.execute('''
            SELECT * FROM promo_uses WHERE user_id = ? AND code_id = ?
        ''', (user_id, promo[0]))
        
        if cursor.fetchone():
            conn.close()
            return False, "Вы уже использовали этот промокод"
        
        # Добавить использование
        cursor.execute('''
            INSERT INTO promo_uses (user_id, code_id)
            VALUES (?, ?)
        ''', (user_id, promo[0]))
        
        # Обновить счётчик
        cursor.execute('''
            UPDATE promo_codes SET times_used = times_used + 1 WHERE id = ?
        ''', (promo[0],))
        
        # Добавить награду на баланс
        self.add_balance(user_id, promo[2], transaction_type="promo", game_type=code)
        
        conn.commit()
        conn.close()
        return True, f"Промокод применён! +{promo[2]} ⭐"
    
    def get_promo(self, code):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM promo_codes WHERE code = ?', (code.upper(),))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_all_promos(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM promo_codes')
        results = cursor.fetchall()
        conn.close()
        return results
