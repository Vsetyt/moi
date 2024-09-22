from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("Найти арбитражные возможности", callback_data='find_opportunities')],
        [InlineKeyboardButton("Показать баланс", callback_data='show_balance')],
        [InlineKeyboardButton("Метрики в реальном времени", callback_data='real_time_metrics')],
        [InlineKeyboardButton("Кросс-чейн возможности", callback_data='cross_chain_opportunities')],
        [InlineKeyboardButton("Расширенный отчет", callback_data='advanced_report')],
        [InlineKeyboardButton("Настройки", callback_data='settings')],
        [InlineKeyboardButton("Помощь", callback_data='help')],
        [InlineKeyboardButton("Статистика торговли", callback_data='show_statistics')],
        [InlineKeyboardButton("Оптимизировать параметры", callback_data='optimize_parameters')],
        [InlineKeyboardButton("Уровень риска", callback_data='show_risk_level')],
        [InlineKeyboardButton("Обновить баланс", callback_data='update_balance')],
        [InlineKeyboardButton("Запустить бэктестинг", callback_data='run_backtest')],
        [InlineKeyboardButton("Показать кривую доходности", callback_data='show_profit_chart')],
        [InlineKeyboardButton("Показать распределение сделок", callback_data='show_trade_distribution')],
        [InlineKeyboardButton("Меню торговли", callback_data='trading_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_menu():
    keyboard = [
        [InlineKeyboardButton("Управление рисками", callback_data='risk_management')],
        [InlineKeyboardButton("Настройки уведомлений", callback_data='notification_settings')],
        [InlineKeyboardButton("API ключи", callback_data='api_keys')],
        [InlineKeyboardButton("Выбор бирж", callback_data='exchange_selection')],
        [InlineKeyboardButton("Назад в главное меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_trading_menu(exchanges):
    keyboard = [
        [InlineKeyboardButton("Включить торговлю", callback_data="enable_trading"),
         InlineKeyboardButton("Выключить торговлю", callback_data="disable_trading")],
        [InlineKeyboardButton("Настройки", callback_data="trading_settings")],
        [InlineKeyboardButton("Текущие позиции", callback_data="current_positions")],
        [InlineKeyboardButton("Выбор биржи", callback_data="select_exchange")]
    ]
    for exchange in exchanges:
        keyboard.append([InlineKeyboardButton(f"Арбитраж на {exchange}", callback_data=f"arbitrage_{exchange}")])
    keyboard.append([InlineKeyboardButton("Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def get_trading_settings_menu():
    keyboard = [
        [InlineKeyboardButton("Установить размер позиции", callback_data="set_position_size")],
        [InlineKeyboardButton("Установить Stop-Loss", callback_data="set_stop_loss")],
        [InlineKeyboardButton("Установить Take-Profit", callback_data="set_take_profit")],
        [InlineKeyboardButton("Выбрать режим торговли", callback_data="select_trading_mode")],
        [InlineKeyboardButton("Назад", callback_data="back_to_trading")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_exchange_selection_menu(exchanges):
    keyboard = [[InlineKeyboardButton(exchange, callback_data=f"select_exchange_{exchange}")] for exchange in exchanges]
    keyboard.append([InlineKeyboardButton("Назад", callback_data="back_to_trading")])
    return InlineKeyboardMarkup(keyboard)

def get_stop_button():
    keyboard = [[InlineKeyboardButton("Остановить анализ", callback_data='stop_analysis')]]
    return InlineKeyboardMarkup(keyboard)

def get_back_button(callback_data):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data=callback_data)]])