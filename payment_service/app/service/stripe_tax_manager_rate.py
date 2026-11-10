from decimal import Decimal
from typing import Optional

VAT_RATES = {
    "DE": (Decimal("19.0"), "VAT DE 19%"),
    "FR": (Decimal("20.0"), "VAT FR 20%"),
    "ES": (Decimal("21.0"), "VAT ES 21%"),
    "PL": (Decimal("23.0"), "VAT PL 23%"),
    "AT": (Decimal("20.0"), "VAT AT 20%"),
    "IT": (Decimal("22.0"), "VAT IT 22%"),
    "NL": (Decimal("21.0"), "VAT NL 21%"),
    "UA": (Decimal("20.0"), "VAT UA 20%"),
    "KZ": (Decimal("16.0"), "VAT KZ 16%"),
    "GE": (Decimal("18.0"), "VAT GE 18%"),
    "AM": (Decimal("20.0"), "VAT AM 20%")
}

class StripeTaxRateManager:
    def __init__(self, client):
        self.client = client
        self._cache: dict[str, str] = {}

    async def get_or_create_tax_rate(self, country: str) -> Optional[str]:
        if country in self._cache:
            return self._cache[country]
        rate_info = VAT_RATES.get(country)
        if not rate_info:
            return None
        percentage, display_name = rate_info
        existing = await self.client.v1.tax_rates.list_async(params={"active": True, "limit": 100})
        for tr in existing.data:
            if tr.country == country and tr.display_name == display_name:
                self._cache[country] = tr.id
                return tr.id
        tax_rate = await self.client.v1.tax_rates.create_async(params={
            "display_name": display_name,
            "percentage": float(percentage),
            "inclusive": False,
            "country": country,
            "tax_type": "vat",
            "description": f"Manual VAT rate for {country}"})
        self._cache[country] = tax_rate.id
        return tax_rate.id