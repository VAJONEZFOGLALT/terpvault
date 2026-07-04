from terpvault.domain.models import ProductData


def classify(product: ProductData) -> str:
    name = (product.name or "").lower()
    brand = (product.brand or "").lower()
    collection = (product.collection or "").lower()
    category = (product.category or "").lower()

    is_sample = "sample pack" in name or "sample" in name

    if is_sample:
        return "sample_packs"

    if brand == "hardware" or collection == "vape hardware":
        return "vape_hardware"

    if "liquidiser" in collection or brand == "terpenes uk - liquidisers":
        return "extract_liquidisers"

    if collection == "diluents" or brand == "terpenes uk - diluents":
        return "diluents"

    if "isolate" in collection or brand == "terpenes uk - isolates":
        return "terpene_isolates"

    if collection == "oil soluble flavours" or brand == "terpenes uk - oil soluble flavours":
        return "oil_soluble_flavours"

    if collection == "concentrated flavours" or brand == "terpenes uk - flavour concentrates":
        return "concentrated_flavours"

    if collection == "neu bag infusion packs":
        return "neu_bag_infusion"

    if collection == "live resin" or brand == "true terpenes - live resin":
        return "live_resin"

    if collection == "clearance":
        return "clearance"

    if collection == "duty free terpenes":
        return "duty_free"

    if collection == "prestige" or brand == "terpenes uk - prestige":
        return "prestige"

    if brand == "eybna":
        return "eybna"

    if collection == "true terpenes" or brand == "true terpenes - strain profiles":
        return "true_terpenes"

    if collection == "terpene belt farms":
        return "terp_belt_farms"

    if collection in ("terpenes uk", "strain profiles") or brand in (
        "terpenes uk - strain profiles", "terpenes uk"
    ):
        return "terpenes_uk_botanical"

    if collection == "bundle":
        return "sample_packs"

    if brand == "dft":
        return "duty_free"

    if collection == "new releases":
        return "new_releases"

    return "new_releases"
