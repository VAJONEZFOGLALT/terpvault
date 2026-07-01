import re
from typing import Optional

from terpvault.config.supplier_config import SupplierConfig
from terpvault.domain.raw_product import RawProduct
from terpvault.sync.importer.client import SupplierClient
from terpvault.sync.importer.normalizer import ShopifyNormalizer


class TerpenesUKImporter:
    def __init__(self, config: SupplierConfig):
        self.config = config
        self.client = SupplierClient(config)

    async def fetch_products(self) -> list[RawProduct]:
        try:
            return await self._fetch_via_sitemap()
        except Exception:
            return await self._fetch_via_collections()

    async def _fetch_via_sitemap(self) -> list[RawProduct]:
        url = f"{self.config.base_url}/sitemap_products_1.xml"
        text = await self.client.get_text(url)
        urls = re.findall(r"<loc>(.*?)</loc>", text)
        all_products = []
        for product_url in urls:
            product_data = await self._fetch_single(product_url)
            if product_data:
                all_products.append(product_data)
        return all_products

    async def _fetch_via_collections(self) -> list[RawProduct]:
        collections_url = f"{self.config.base_url}/collections.json"
        data = await self.client.get_json(collections_url)
        collections = data.get("collections", [])
        all_products = []
        for col in collections:
            handle = col.get("handle")
            if not handle:
                continue
            products = await self._fetch_collection_products(handle, col.get("title"))
            all_products.extend(products)
        return all_products

    async def _fetch_collection_products(self, handle: str, collection_name: Optional[str]) -> list[RawProduct]:
        results = []
        page = 1
        while True:
            url = f"{self.config.base_url}/collections/{handle}/products.json?page={page}&limit=250"
            data = await self.client.get_json(url)
            products = data.get("products", [])
            if not products:
                break
            for p in products:
                results.append(ShopifyNormalizer.normalize(p, collection_name))
            page += 1
        return results

    async def _fetch_single(self, product_url: str) -> Optional[RawProduct]:
        json_url = f"{product_url}.json"
        try:
            data = await self.client.get_json(json_url)
            product = data.get("product", data)
            return ShopifyNormalizer.normalize(product)
        except Exception:
            return None

    async def close(self):
        await self.client.close()
