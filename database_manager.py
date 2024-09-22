import aiosqlite
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_name='arbitrage_bot.db'):
        self.db_name = db_name

    async def connect(self):
        try:
            self.conn = await aiosqlite.connect(self.db_name)
            logger.info(f"Connected to database: {self.db_name}")
            await self.create_tables()
        except aiosqlite.Error as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise

    async def close(self):
        if self.conn:
            await self.conn.close()
            logger.info("Closed database connection")

    async def create_tables(self):
        try:
            await self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await self.conn.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    exchange TEXT,
                    path TEXT,
                    profit REAL,
                    volume REAL,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            await self.conn.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    order_id TEXT,
                    symbol TEXT,
                    type TEXT,
                    side TEXT,
                    amount REAL,
                    price REAL,
                    status TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await self.conn.execute('''
                CREATE TABLE IF NOT EXISTS stop_losses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    order_id TEXT,
                    symbol TEXT,
                    price REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await self.conn.execute('''
                CREATE TABLE IF NOT EXISTS take_profits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    order_id TEXT,
                    symbol TEXT,
                    price REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await self.conn.commit()
            logger.info("Database tables created successfully")
        except aiosqlite.Error as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise

    async def add_user(self, telegram_id, username):
        try:
            await self.conn.execute('''
                INSERT OR IGNORE INTO users (telegram_id, username)
                VALUES (?, ?)
            ''', (telegram_id, username))
            await self.conn.commit()
            logger.info(f"User added or updated: {telegram_id}")
        except aiosqlite.Error as e:
            logger.error(f"Error adding user: {str(e)}")
            raise

    async def get_user(self, telegram_id):
        try:
            async with self.conn.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)) as cursor:
                return await cursor.fetchone()
        except aiosqlite.Error as e:
            logger.error(f"Error getting user: {str(e)}")
            raise

    async def add_trade(self, user_id, exchange, path, profit, volume):
        try:
            cursor = await self.conn.execute('''
                INSERT INTO trades (user_id, exchange, path, profit, volume, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, exchange, path, profit, volume, 'open'))
            await self.conn.commit()
            logger.info(f"Trade added for user {user_id}")
            return cursor.lastrowid
        except aiosqlite.Error as e:
            logger.error(f"Error adding trade: {str(e)}")
            raise

    async def close_trade(self, trade_id, profit):
        try:
            await self.conn.execute('''
                UPDATE trades
                SET status = ?, profit = ?, closed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', ('closed', profit, trade_id))
            await self.conn.commit()
            logger.info(f"Trade {trade_id} closed")
        except aiosqlite.Error as e:
            logger.error(f"Error closing trade: {str(e)}")
            raise

    async def get_user_trades(self, user_id, status=None):
        try:
            if status:
                async with self.conn.execute('SELECT * FROM trades WHERE user_id = ? AND status = ?', (user_id, status)) as cursor:
                    return await cursor.fetchall()
            else:
                async with self.conn.execute('SELECT * FROM trades WHERE user_id = ?', (user_id,)) as cursor:
                    return await cursor.fetchall()
        except aiosqlite.Error as e:
            logger.error(f"Error getting user trades: {str(e)}")
            raise

    async def get_trade_statistics(self, user_id):
        try:
            async with self.conn.execute('''
                SELECT COUNT(*) as total_trades,
                       SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as profitable_trades,
                       SUM(profit) as total_profit,
                       AVG(profit) as avg_profit
                FROM trades
                WHERE user_id = ? AND status = 'closed'
            ''', (user_id,)) as cursor:
                return await cursor.fetchone()
        except aiosqlite.Error as e:
            logger.error(f"Error getting trade statistics: {str(e)}")
            raise

    async def save_order(self, user_id, order):
        try:
            await self.conn.execute('''
                INSERT INTO orders (user_id, order_id, symbol, type, side, amount, price, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, order['id'], order['symbol'], order['type'], order['side'], order['amount'], order['price'], order['status']))
            await self.conn.commit()
        except aiosqlite.Error as e:
            logger.error(f"Error saving order: {str(e)}")
            raise

    async def update_order(self, user_id, order):
        try:
            await self.conn.execute('''
                UPDATE orders
                SET status = ?, price = ?
                WHERE user_id = ? AND order_id = ?
            ''', (order['status'], order['price'], user_id, order['id']))
            await self.conn.commit()
        except aiosqlite.Error as e:
            logger.error(f"Error updating order: {str(e)}")
            raise

    async def save_stop_loss(self, user_id, order):
        try:
            await self.conn.execute('''
                INSERT INTO stop_losses (user_id, order_id, symbol, price)
                VALUES (?, ?, ?, ?)
            ''', (user_id, order['id'], order['symbol'], order['price']))
            await self.conn.commit()
        except aiosqlite.Error as e:
            logger.error(f"Error saving stop loss: {str(e)}")
            raise

    async def save_take_profit(self, user_id, order):
        try:
            await self.conn.execute('''
                INSERT INTO take_profits (user_id, order_id, symbol, price)
                VALUES (?, ?, ?, ?)
            ''', (user_id, order['id'], order['symbol'], order['price']))
            await self.conn.commit()
        except aiosqlite.Error as e:
            logger.error(f"Error saving take profit: {str(e)}")
            raise

    async def update_order_status(self, user_id, order_id, status):
        try:
            await self.conn.execute('''
                UPDATE orders
                SET status = ?
                WHERE user_id = ? AND order_id = ?
            ''', (status, user_id, order_id))
            await self.conn.commit()
        except aiosqlite.Error as e:
            logger.error(f"Error updating order status: {str(e)}")
            raise

    async def get_order_history(self, user_id):
        try:
            async with self.conn.execute('''
                SELECT * FROM orders
                WHERE user_id = ?
                ORDER BY timestamp DESC
            ''', (user_id,)) as cursor:
                return await cursor.fetchall()
        except aiosqlite.Error as e:
            logger.error(f"Error getting order history: {str(e)}")
            raise

    async def get_user_trades(self, user_id, start_date, end_date):
        try:
            async with self.conn.execute('''
                SELECT * FROM orders
                WHERE user_id = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            ''', (user_id, start_date, end_date)) as cursor:
                return await cursor.fetchall()
        except aiosqlite.Error as e:
            logger.error(f"Error getting user trades: {str(e)}")
            raise