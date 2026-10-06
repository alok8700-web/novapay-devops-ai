import httpx


async def check_service(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)

        return {
            "url": url,
            "status_code": response.status_code,
            "healthy": response.is_success,
            "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
        }

    except Exception as exc:
        return {
            "url": url,
            "status_code": None,
            "healthy": False,
            "response_time_ms": None,
            "error": str(exc),
        }
