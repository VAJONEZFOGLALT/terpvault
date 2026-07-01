from typing import Optional

from terpvault.domain.raw_product import RawProduct


class ShopifyNormalizer:
    @staticmethod
    def normalize(product: dict, collection: Optional[str] = None) -> RawProduct:
        title = product.get("title", "")
        variants_raw = product.get("variants", [])
        first_variant = variants_raw[0] if variants_raw else {}
        images_raw = product.get("images", [])

        options = [
            {"name": opt.get("name", ""), "values": opt.get("values", [])}
            for opt in product.get("options", [])
        ]

        normalized_variants = [
            {
                "sku": str(v.get("sku") or v.get("id", "")),
                "price": v.get("price"),
                "available": v.get("available", True),
                "options": {
                    f"Option {i+1}": v.get(f"option{i+1}")
                    for i in range(3)
                    if v.get(f"option{i+1}") is not None
                },
                "position": idx,
            }
            for idx, v in enumerate(variants_raw)
        ]

        normalized_images = [
            {
                "url": img.get("src", ""),
                "position": idx,
                "alt_text": img.get("alt", None),
            }
            for idx, img in enumerate(images_raw)
        ]

        price = None
        compare_at = None
        if first_variant:
            try:
                p = first_variant.get("price")
                if p:
                    price = float(p)
            except (ValueError, TypeError):
                pass
            try:
                cap = first_variant.get("compare_at_price")
                if cap:
                    compare_at = float(cap)
            except (ValueError, TypeError):
                pass

        vendor = product.get("vendor")
        product_type = product.get("product_type")

        return RawProduct(
            external_id=str(first_variant.get("sku") or product.get("id", "") or ""),
            name=title,
            description=product.get("body_html", ""),
            brand=vendor,
            category=product_type,
            collection=collection,
            available=first_variant.get("available", True) if first_variant else True,
            price=price,
            compare_at_price=compare_at,
            unit=None,
            size=None,
            options=options,
            variants=normalized_variants,
            images=normalized_images,
            metadata={
                "vendor": vendor,
                "product_type": product_type,
                "tags": product.get("tags", ""),
                "handle": product.get("handle", ""),
                "published_at": product.get("published_at"),
                "created_at": product.get("created_at"),
                "updated_at": product.get("updated_at"),
            },
            raw=product,
        )
