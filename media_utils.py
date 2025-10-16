import logging

logger = logging.getLogger(__name__)

BASE_FRAGMENT_URL = "https://nft.fragment.com/gift/{slug}.medium.jpg"

async def download_thumbnail_image(client, document, slug: str) -> str | None:
    """
    Не качает ничего — просто строит URL превью на основе slug.
    Пример: https://nft.fragment.com/gift/SnakeBox-29826.medium.jpg
    """
    try:
        if not slug:
            logger.warning("Нет slug — нельзя построить ссылку на превью.")
            return None

        full_url = BASE_FRAGMENT_URL.format(slug=slug)
        logger.info(f"Генерирую Fragment URL: {full_url}")
        return full_url

    except Exception as e:
        logger.error(f"Ошибка при формировании Fragment URL: {e}")
        return None
