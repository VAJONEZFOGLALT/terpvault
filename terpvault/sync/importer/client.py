import asyncio
import hashlib
from typing import Any

import httpx

from terpvault.config.supplier_config import SupplierConfig


class SupplierClient:
    def __init__(self, config: SupplierConfig):
        self.config = config
        self._client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={"User-Agent": "TerpVault/1.0"},
        )
        self._semaphore = asyncio.Semaphore(config.rate_limit_per_second)

    async def close(self):
        await self._client.aclose()

    async def get_json(self, url: str) -> Any:
        for attempt in range(self.config.retry_max + 1):
            async with self._semaphore:
                try:
                    resp = await self._client.get(url)
                    resp.raise_for_status()
                    return resp.json()
                except (httpx.HTTPError, httpx.TimeoutException) as e:
                    if attempt == self.config.retry_max:
                        raise
                    await asyncio.sleep(2 ** attempt)

    async def get_text(self, url: str) -> str:
        async with self._semaphore:
            resp = await self._client.get(url)
            resp.raise_for_status()
            return resp.text

    @staticmethod
    def compute_hash(data: dict) -> str:
        raw = str(sorted(data.items())).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
