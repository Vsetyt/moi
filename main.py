import asyncio
from arbitrage_bot import ArbitrageBot
from telegram.error import TimedOut, NetworkError
import logging
import sys
from config import load_config

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def run_with_retry(max_retries=5, retry_delay=5):
    config = load_config()
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1} to start the bot")
            bot = ArbitrageBot(config)
            logger.debug("ArbitrageBot instance created")
            logger.info("Starting bot...")
            await bot.run()
            logger.info("Bot finished its work successfully")
            break
        except (TimedOut, NetworkError) as e:
            if attempt < max_retries - 1:
                logger.error(f"Network error occurred: {str(e)}. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.critical(f"Failed to start bot after {max_retries} attempts due to network errors. Last error: {str(e)}")
                raise
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.exception(f"Unexpected error occurred: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.critical(f"Failed to start bot after {max_retries} attempts due to unexpected errors.")
                raise

if __name__ == '__main__':
    logger.info("Starting the bot application")
    try:
        asyncio.run(run_with_retry())
    except Exception as e:
        logger.critical(f"Critical error in main loop: {str(e)}")
    finally:
        logger.info("Bot application has ended")