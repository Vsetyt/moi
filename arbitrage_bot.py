import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import Config
from binance_api import BinanceAPI
from database_manager import DatabaseManager
from trade_executor import TradeExecutor
from notification_manager import NotificationManager
from performance_monitor import PerformanceMonitor
from external_data_provider import ExternalDataProvider
from security_manager import SecurityManager
from ml_predictor import MLPredictor
from dex_integration import DEXIntegration
from auto_trading import AutoTrader
from defi_integration import DeFiIntegration
from advanced_analytics import AdvancedAnalytics
from buttons import get_main_menu, get_settings_menu
from help_texts import HELP_TEXT, OPPORTUNITY_HELP, AUTO_TRADING_HELP, DEFI_HELP, ADVANCED_REPORT_HELP
import logging
import traceback

logger = logging.getLogger(__name__)

class ArbitrageBot:
    def __init__(self, config: Config):
        self.config = config
        self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        self.binance_api = BinanceAPI(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)
        self.db_manager = DatabaseManager(config.DATABASE_URL)
        self.trade_executor = TradeExecutor(self.binance_api, self.db_manager)
        self.notification_manager = NotificationManager(self.application.bot)
        self.performance_monitor = PerformanceMonitor(self.db_manager)
        self.external_data_provider = ExternalDataProvider()
        self.security_manager = SecurityManager(self.db_manager)
        self.ml_predictor = MLPredictor()
        self.dex_integration = DEXIntegration(config.DEX_CONFIG)
        self.auto_trader = AutoTrader(self, config.AUTO_TRADER_CONFIG)
        self.defi_integration = DeFiIntegration(config.DEFI_CONFIG)
        self.advanced_analytics = AdvancedAnalytics(self.db_manager)

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("balance", self.show_balance))
        self.application.add_handler(CommandHandler("opportunities", self.find_opportunities))
        self.application.add_handler(CommandHandler("execute", self.execute_arbitrage))
        self.application.add_handler(CommandHandler("history", self.show_trade_history))
        self.application.add_handler(CommandHandler("performance", self.show_performance_report))
        self.application.add_handler(CommandHandler("settings", self.show_settings))
        self.application.add_handler(CommandHandler("realtime", self.show_real_time_metrics))
        self.application.add_handler(CommandHandler("crosschain", self.find_cross_chain_opportunities))
        self.application.add_handler(CommandHandler("start_auto_trading", self.start_auto_trading))
        self.application.add_handler(CommandHandler("stop_auto_trading", self.stop_auto_trading))
        self.application.add_handler(CommandHandler("update_auto_trading", self.update_auto_trading_config))
        self.application.add_handler(CommandHandler("defi_opportunities", self.show_defi_opportunities))
        self.application.add_handler(CommandHandler("execute_defi", self.execute_defi_strategy))
        self.application.add_handler(CommandHandler("advanced_report", self.generate_advanced_report))
        
        self.application.add_handler(CallbackQueryHandler(self.handle_button))
        
        self.application.add_error_handler(self.error_handler)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.security_manager.is_user_authorized(user_id):
            await update.message.reply_text("Извините, у вас нет доступа к этому боту.")
            return

        await update.message.reply_text(
            "Добро пожаловать в Арбитражного бота! Используйте /help для получения списка команд.",
            reply_markup=get_main_menu()
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.args:
            command = context.args[0].lower()
            if command == "opportunities":
                await update.message.reply_text(OPPORTUNITY_HELP)
            elif command == "auto_trading":
                await update.message.reply_text(AUTO_TRADING_HELP)
            elif command == "defi":
                await update.message.reply_text(DEFI_HELP)
            elif command == "advanced_report":
                await update.message.reply_text(ADVANCED_REPORT_HELP)
            else:
                await update.message.reply_text(f"Справка для команды /{command} не найдена.")
        else:
            await update.message.reply_text(HELP_TEXT)

    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        balance = await self.binance_api.get_account_balance(user_id)
        await update.message.reply_text(f"Ваш текущий баланс: {balance:.2f} USDT")

    async def find_opportunities(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        opportunities = await self.find_arbitrage_opportunities()
        if opportunities:
            response = "Найденные арбитражные возможности:\n\n"
            for opp in opportunities[:5]:
                response += f"ID: {opp['id']}\n"
                response += f"Пара: {opp['symbol']}\n"
                response += f"Прибыль: {opp['profit']:.2f} USDT\n"
                response += f"Процент прибыли: {opp['profit_percent']:.2%}\n"
                response += f"Объем: {opp['volume']:.2f} USDT\n\n"
            response += "Для выполнения арбитража используйте команду /execute <ID>"
        else:
            response = "В данный момент арбитражных возможностей не найдено."
        await update.message.reply_text(response)

    async def find_arbitrage_opportunities(self):
        markets = await self.binance_api.get_markets()
        opportunities = []
        for market in markets:
            orderbook = await self.binance_api.get_orderbook(market['symbol'])
            opportunity = self.calculate_arbitrage(market, orderbook)
            if opportunity:
                ml_prediction = await self.ml_predictor.predict_opportunity(opportunity)
                opportunity['ml_prediction'] = ml_prediction
                opportunities.append(opportunity)
        
        opportunities.sort(key=lambda x: x['profit'], reverse=True)
        return opportunities

    def calculate_arbitrage(self, market, orderbook):
        best_bid = orderbook['bids'][0][0]
        best_ask = orderbook['asks'][0][0]
        spread = (best_bid - best_ask) / best_ask
        
        if spread > self.config.MIN_SPREAD:
            profit = spread * self.config.TRADE_AMOUNT
            return {
                'id': f"{market['symbol']}_{int(time.time())}",
                'symbol': market['symbol'],
                'profit': profit,
                'profit_percent': spread,
                'volume': self.config.TRADE_AMOUNT,
                'bid': best_bid,
                'ask': best_ask
            }
        return None

    async def execute_arbitrage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not context.args:
            await update.message.reply_text("Пожалуйста, укажите ID возможности.")
            return

        opportunity_id = context.args[0]
        opportunity = self.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            await update.message.reply_text("Неверный ID возможности или возможность устарела.")
            return

        result = await self.trade_executor.execute_arbitrage(opportunity)
        if result['status'] == 'success':
            profit = result['profit']
            await update.message.reply_text(f"Арбитраж выполнен успешно. Прибыль: {profit:.2f} USDT")
            await self.db_manager.add_trade(user_id, opportunity['symbol'], profit)
            await self.notification_manager.send_trade_notification(user_id, opportunity['symbol'], profit)
        else:
            await update.message.reply_text(f"Ошибка при выполнении арбитража: {result['message']}")

    def get_opportunity_by_id(self, opportunity_id):
        opportunities = self.find_arbitrage_opportunities()
        return next((opp for opp in opportunities if opp['id'] == opportunity_id), None)

    async def show_trade_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        history = await self.db_manager.get_user_trade_history(user_id)
        if history:
            response = "История торговли:\n\n"
            for trade in history[:10]:
                response += f"Дата: {trade['timestamp']}\n"
                response += f"Пара: {trade['symbol']}\n"
                response += f"Прибыль: {trade['profit']:.2f} USDT\n\n"
        else:
            response = "История торговли пуста."
        await update.message.reply_text(response)

    async def show_performance_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        report = await self.performance_monitor.generate_performance_report(user_id)
        await update.message.reply_text(report)

    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Настройки:", reply_markup=get_settings_menu())

    async def handle_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == 'find_opportunities':
            await self.find_opportunities(update, context)
        elif query.data == 'show_balance':
            await self.show_balance(update, context)
        elif query.data == 'real_time_metrics':
            await self.show_real_time_metrics(update, context)
        elif query.data == 'cross_chain_opportunities':
            await self.find_cross_chain_opportunities(update, context)
        elif query.data == 'advanced_report':
            await self.generate_advanced_report(update, context)
        elif query.data == 'settings':
            await self.show_settings(update, context)
        elif query.data == 'help':
            await self.help(update, context)
        elif query.data == 'main_menu':
            await query.edit_message_text("Главное меню:", reply_markup=get_main_menu())

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(msg="Exception while handling an update:", exc_info=context.error)
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = ''.join(tb_list)
        
        error_message = f"Произошла ошибка: {context.error}\n\nПожалуйста, свяжитесь с поддержкой, если эта проблема повторится."
        
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=error_message
            )
        
        await context.bot.send_message(
            chat_id=self.config.DEVELOPER_CHAT_ID,
            text=f"Произошла ошибка:\n\n{tb_string}"
        )

    async def start_auto_trading(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.security_manager.is_user_authorized(user_id):
            await update.message.reply_text("У вас нет прав для запуска автоматической торговли.")
            return

        await self.auto_trader.start()
        await update.message.reply_text("Автоматическая торговля запущена.")

    async def stop_auto_trading(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.security_manager.is_user_authorized(user_id):
            await update.message.reply_text("У вас нет прав для остановки автоматической торговли.")
            return

        await self.auto_trader.stop()
        await update.message.reply_text("Автоматическая торговля остановлена.")

    async def update_auto_trading_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.security_manager.is_user_authorized(user_id):
            await update.message.reply_text("У вас нет прав для изменения настроек автоматической торговли.")
            return

        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Пожалуйста, укажите параметр и его значение.")
            return

        param = context.args[0]
        value = context.args[1]

        try:
            new_config = {param: float(value)}
            await self.auto_trader.update_config(new_config)
            await update.message.reply_text(f"Параметр {param} обновлен на {value}")
        except ValueError:
            await update.message.reply_text("Неверный формат значения. Пожалуйста, используйте числовое значение.")

    async def show_defi_opportunities(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        opportunities = await self.defi_integration.get_defi_opportunities()
        if opportunities:
            response = "DeFi возможности:\n\n"
            for i, opp in enumerate(opportunities):
                response += f"ID: {i}\n"
                response += f"Протокол: {opp['protocol']}\n"
                if opp['type'] == 'lending':
                    response += f"Тип: Кредитование\n"
                    response += f"Ставка поставки: {opp['supply_rate']:.2%}\n"
                    response += f"Ставка заимствования: {opp['borrow_rate']:.2%}\n"
                elif opp['type'] == 'yield_farming':
                    response += f"Тип: Yield Farming\n"
                    response += f"Годовая процентная доходность: {opp['apy']:.2%}\n"
                elif opp['type'] == 'liquidity_pool':
                    response += f"Тип: Пул ликвидности\n"
                    response += f"Общая ликвидность: {opp['total_liquidity']:.2f} USD\n"
                    response += f"Годовая процентная доходность (комиссии): {opp['fees_apy']:.2%}\n"
                response += "\n"
            response += "Для выполнения DeFi стратегии используйте команду /execute_defi <ID>"
        else:
            response = "В данный момент DeFi возможностей не найдено."
        await update.message.reply_text(response)

    async def execute_defi_strategy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.security_manager.is_user_authorized(user_id):
            await update.message.reply_text("У вас нет прав для выполнения DeFi стратегий.")
            return

        if not context.args:
            await update.message.reply_text("Пожалуйста, укажите ID возможности.")
            return

        try:
            opportunity_id = int(context.args[0])
            opportunities = await self.defi_integration.get_defi_opportunities()
            if opportunity_id < 0 or opportunity_id >= len(opportunities):
                await update.message.reply_text("Неверный ID возможности.")
                return

            opportunity = opportunities[opportunity_id]
            result = await self.defi_integration.execute_defi_strategy(opportunity)
            if result['status'] == 'success':
                await update.message.reply_text(f"DeFi стратегия выполнена успешно. Результат: {result['result']}")
                await self.db_manager.add_defi_transaction(user_id, opportunity['protocol'], result['result'])
                await self.notification_manager.send_defi_notification(user_id, opportunity['protocol'], result['result'])
            else:
                await update.message.reply_text(f"Ошибка при выполнении DeFi стратегии: {result['message']}")
        except ValueError:
            await update.message.reply_text("Неверный формат ID. Пожалуйста, используйте числовое значение.")

    async def generate_advanced_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.security_manager.is_user_authorized(user_id):
            await update.message.reply_text("У вас нет прав для генерации расширенного отчета.")
            return

        start_date = context.args[0] if len(context.args) > 0 else "2023-01-01"
        end_date = context.args[1] if len(context.args) > 1 else "2023-12-31"

        report = await self.advanced_analytics.generate_advanced_report(user_id, start_date, end_date)
        
        if 'message' in report:
            await update.message.reply_text(report['message'])
            return

        summary_text = (
            f"Расширенный отчет ({start_date} - {end_date}):\n\n"
            f"Общее количество сделок: {report['summary']['total_trades']}\n"
            f"Общая прибыль: {report['summary']['total_profit']:.2f} USDT\n"
            f"Средняя прибыль на сделку: {report['summary']['average_profit']:.2f} USDT\n"
            f"Процент выигрышных сделок: {report['summary']['win_rate']:.2%}\n"
            f"Лучшая сделка: {report['summary']['best_trade']:.2f} USDT\n"
            f"Худшая сделка: {report['summary']['worst_trade']:.2f} USDT\n\n"
            f"Коэффициент Шарпа: {report['performance_metrics']['sharpe_ratio']:.2f}\n"
            f"Коэффициент Сортино: {report['performance_metrics']['sortino_ratio']:.2f}\n"
            f"Profit Factor: {report['performance_metrics']['profit_factor']:.2f}\n"
            f"Ожидание: {report['performance_metrics']['expectancy']:.2f}\n\n"
            f"Максимальная просадка: {report['risk_metrics']['max_drawdown']:.2%}\n"
            f"Value at Risk (5%): {report['risk_metrics']['value_at_risk']:.2f} USDT\n"
            f"Риск разорения: {report['risk_metrics']['risk_of_ruin']:.2%}\n"
        )
        await update.message.reply_text(summary_text)

        # Отправляем визуализации
        await update.message.reply_photo(report['visualizations']['equity_curve'], caption="Кривая капитала")
        await update.message.reply_photo(report['visualizations']['drawdown_chart'], caption="График просадок")
        await update.message.reply_photo(report['visualizations']['profit_distribution'], caption="Распределение прибыли")
        await update.message.reply_photo(report['visualizations']['monthly_returns_heatmap'], caption="Тепловая карта месячной доходности")

    async def show_real_time_metrics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.security_manager.is_user_authorized(user_id):
            await update.message.reply_text("У вас нет прав для просмотра метрик в реальном времени.")
            return

        metrics = await self.performance_monitor.get_real_time_metrics(user_id)
        response = "Метрики в реальном времени:\n\n"
        response += f"Текущий баланс: {metrics['current_balance']:.2f} USDT\n"
        response += f"Открытые позиции: {metrics['open_positions']}\n"
        response += f"Нереализованная прибыль/убыток: {metrics['unrealized_pnl']:.2f} USDT\n"
        response += f"Дневная прибыль: {metrics['daily_profit']:.2f} USDT\n"
        response += f"Недельная прибыль: {metrics['weekly_profit']:.2f} USDT\n"
        response += f"Процент выигрышных сделок (24ч): {metrics['win_rate_24h']:.2%}\n"
        response += f"Средняя продолжительность сделки: {metrics['avg_trade_duration']:.2f} мин\n"
        await update.message.reply_text(response)

    async def find_cross_chain_opportunities(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.security_manager.is_user_authorized(user_id):
            await update.message.reply_text("У вас нет прав для поиска кросс-чейн возможностей.")
            return

        opportunities = await self.dex_integration.get_cross_chain_opportunities()
        if opportunities:
            response = "Найденные кросс-чейн арбитражные возможности:\n\n"
            for i, opp in enumerate(opportunities):
                response += f"ID: {i}\n"
                response += f"Из: {opp['from_chain']} ({opp['from_token']})\n"
                response += f"В: {opp['to_chain']} ({opp['to_token']})\n"
                response += f"Прибыль: {opp['profit']:.2f} USD\n"
                response += f"Процент прибыли: {opp['profit_percent']:.2%}\n\n"
            response += "Для выполнения кросс-чейн арбитража используйте команду /execute_cross_chain <ID>"
        else:
            response = "В данный момент кросс-чейн арбитражных возможностей не найдено."
        await update.message.reply_text(response)

    async def execute_cross_chain_arbitrage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.security_manager.is_user_authorized(user_id):
            await update.message.reply_text("У вас нет прав для выполнения кросс-чейн арбитража.")
            return

        if not context.args:
            await update.message.reply_text("Пожалуйста, укажите ID возможности.")
            return

        try:
            opportunity_id = int(context.args[0])
            opportunities = await self.dex_integration.get_cross_chain_opportunities()
            if opportunity_id < 0 or opportunity_id >= len(opportunities):
                await update.message.reply_text("Неверный ID возможности.")
                return

            opportunity = opportunities[opportunity_id]
            result = await self.dex_integration.execute_cross_chain_arbitrage(opportunity)
            if result['status'] == 'success':
                await update.message.reply_text(f"Кросс-чейн арбитраж выполнен успешно. Прибыль: {result['profit']:.2f} USD")
                await self.db_manager.add_cross_chain_trade(user_id, opportunity['from_chain'], opportunity['to_chain'], result['profit'])
                await self.notification_manager.send_cross_chain_notification(user_id, opportunity['from_chain'], opportunity['to_chain'], result['profit'])
            else:
                await update.message.reply_text(f"Ошибка при выполнении кросс-чейн арбитража: {result['message']}")
        except ValueError:
            await update.message.reply_text("Неверный формат ID. Пожалуйста, используйте числовое значение.")

    def run(self):
        self.setup_handlers()
        self.application.run_polling()

if __name__ == "__main__":
    config = Config()
    bot = ArbitrageBot(config)
    bot.run()