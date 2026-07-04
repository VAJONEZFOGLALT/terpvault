from enum import Enum

from pydantic import BaseModel


class ChapterType(str, Enum):
    strain_profiles = "Strain Profiles"
    live_resin = "Live Resin"
    infusion = "Infusion"
    isolates = "Isolates"
    hardware_ingredients = "Hardware & Ingredients"
    sample_packs = "Sample Packs"
    new_releases = "New Releases"
    clearance = "Clearance"


class CanonicalSection(BaseModel):
    key: str
    label: str
    chapter: ChapterType
    description: str
    subtitle: str = ""


CANONICAL_SECTIONS: list[CanonicalSection] = [
    CanonicalSection(
        key="eybna",
        label="Eybna",
        chapter=ChapterType.strain_profiles,
        description="Premium botanical terpene systems from Israel. Palate & Live, Live Plus+, and Enhancer lines.",
        subtitle="Eybna",
    ),
    CanonicalSection(
        key="true_terpenes",
        label="True Terpenes",
        chapter=ChapterType.strain_profiles,
        description="Industry-leading cultivar-specific terpene profiles for professional formulators.",
        subtitle="True Terpenes",
    ),
    CanonicalSection(
        key="terp_belt_farms",
        label="Terp Belt Farms",
        chapter=ChapterType.strain_profiles,
        description="Single-source terpenes from California's legendary Terp Belt region.",
        subtitle="Terp Belt Farms",
    ),
    CanonicalSection(
        key="terpenes_uk_botanical",
        label="Terpenes UK - Botanical",
        chapter=ChapterType.strain_profiles,
        description="House brand botanical strain profiles for everyday applications.",
        subtitle="Terpenes UK",
    ),
    CanonicalSection(
        key="prestige",
        label="Prestige",
        chapter=ChapterType.strain_profiles,
        description="Premium formulations from the Terpenes UK Prestige line.",
        subtitle="Terpenes UK - Prestige",
    ),
    CanonicalSection(
        key="duty_free",
        label="Duty Free Terpenes",
        chapter=ChapterType.strain_profiles,
        description="Limited release terpenes at wholesale prices.",
        subtitle="DFT",
    ),
    CanonicalSection(
        key="live_resin",
        label="Live Resin",
        chapter=ChapterType.live_resin,
        description="Full-spectrum live resin profiles from True Terpenes.",
        subtitle="True Terpenes - Live Resin",
    ),
    CanonicalSection(
        key="concentrated_flavours",
        label="Concentrated Flavours",
        chapter=ChapterType.infusion,
        description="Concentrated flavour formulations for product development.",
        subtitle="Terpenes UK",
    ),
    CanonicalSection(
        key="oil_soluble_flavours",
        label="Oil Soluble Flavours",
        chapter=ChapterType.infusion,
        description="Oil-soluble flavour systems for vape and edible applications.",
        subtitle="Terpenes UK",
    ),
    CanonicalSection(
        key="neu_bag_infusion",
        label="NEU Bag Infusion Packs",
        chapter=ChapterType.infusion,
        description="Complete infusion packs for bag-based extraction systems.",
        subtitle="Terpenes UK",
    ),
    CanonicalSection(
        key="terpene_isolates",
        label="Terpene Isolates",
        chapter=ChapterType.isolates,
        description="Single-molecule terpene isolates for precise formulation and custom blending.",
        subtitle="Terpenes UK",
    ),
    CanonicalSection(
        key="extract_liquidisers",
        label="Extract Liquidisers",
        chapter=ChapterType.hardware_ingredients,
        description="Extract thinning solutions for viscosity control in vape formulations.",
        subtitle="Terpenes UK",
    ),
    CanonicalSection(
        key="diluents",
        label="Diluents",
        chapter=ChapterType.hardware_ingredients,
        description="Carrier fluids for terpene dilution and precise formulation.",
        subtitle="Terpenes UK",
    ),
    CanonicalSection(
        key="vape_hardware",
        label="Vape Hardware",
        chapter=ChapterType.hardware_ingredients,
        description="CCELL cartridges, batteries, syringes, and mixing accessories.",
        subtitle="Hardware",
    ),
    CanonicalSection(
        key="sample_packs",
        label="Sample Packs",
        chapter=ChapterType.sample_packs,
        description="Curated sample sets across all brands for testing and discovery.",
        subtitle="Sample Packs",
    ),
    CanonicalSection(
        key="new_releases",
        label="New Releases",
        chapter=ChapterType.new_releases,
        description="Latest additions to the Terpenes UK catalog.",
        subtitle="New Releases",
    ),
    CanonicalSection(
        key="clearance",
        label="Clearance",
        chapter=ChapterType.clearance,
        description="Discontinued and reduced stock — limited availability.",
        subtitle="Clearance",
    ),
]


SECTION_BY_KEY: dict[str, CanonicalSection] = {s.key: s for s in CANONICAL_SECTIONS}
