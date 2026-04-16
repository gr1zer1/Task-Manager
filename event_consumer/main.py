import asyncio
import logging
from event_handler import start_consumer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    logger.info("🌟 Starting Event Consumer Service")
    await start_consumer()


if __name__ == "__main__":
    asyncio.run(main())
