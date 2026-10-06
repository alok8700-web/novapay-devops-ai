import httpx


async def fetch_metrics(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)

        return {
            "url": url,
            "status_code": response.status_code,
            "healthy": response.is_success,
            "metrics": response.text,
        }

    except Exception as exc:
        return {
            "url": url,
            "status_code": None,
            "healthy": False,
            "metrics": "",
            "error": str(exc),
        }
