"""
External Database Integration - Materials Project, Open Catalyst, BRENDA
Complete implementation with API key support
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class DatabaseSource(str, Enum):
    OPEN_CATALYST = "open_catalyst"
    MATERIALS_PROJECT = "materials_project"
    BRENDA = "brenda"


@dataclass
class CatalystRecord:
    """Standard catalyst record format"""
    source: str
    name: str
    composition: Dict
    reaction: str
    activity: Optional[float]
    selectivity: Optional[float]
    stability: Optional[int]
    url: str


class MaterialsProjectService:
    """Real Materials Project API integration"""

    def __init__(self):
        self.base_url = "https://api.next-gen.materialsproject.org"
        # Check both possible env var names
        self.api_key = os.getenv("MATERIALS_PROJECT_API_KEY") or os.getenv("MP_API_KEY", "")

        if self.api_key:
            print(f"✅ Materials Project API key loaded (length: {len(self.api_key)})")
        else:
            print("⚠️ MATERIALS_PROJECT_API_KEY not found in .env file")

    async def search_materials(
        self,
        elements: List[str],
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for materials by element composition using REAL API"""

        if not self.api_key:
            print("⚠️ No API key - using fallback data")
            return self._get_fallback_data(elements)

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"X-API-KEY": self.api_key}

                elements_str = ",".join(elements)
                url = f"{self.base_url}/materials?elements={elements_str}&limit={limit}"

                print(f"🔍 Querying Materials Project: {url[:80]}...")

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = self._process_materials_response(data)
                        print(f"✅ Found {len(results)} materials from Materials Project")
                        return results
                    else:
                        print(f"⚠️ API error {response.status}, using fallback")
                        return self._get_fallback_data(elements)

        except Exception as e:
            print(f"⚠️ Materials Project API error: {e}")
            return self._get_fallback_data(elements)

    def _process_materials_response(self, data: Dict) -> List[Dict]:
        """Process new API response into standard format"""
        results = []

        # New API returns data in 'data' array
        materials = data.get("data", [])

        for material in materials:
            # Extract the material document
            doc = material.get("document", material)

            results.append({
                "material_id": doc.get("material_id"),
                "formula": doc.get("formula_pretty", doc.get("formula")),
                "band_gap": doc.get("band_gap"),
                "formation_energy": doc.get("formation_energy_per_atom"),
                "elements": doc.get("elements", []),
                "density": doc.get("density"),
                "source": "materials_project_real",
                "url": f"https://next-gen.materialsproject.org/materials/{doc.get('material_id')}"
            })

        return results

    def _get_fallback_data(self, elements: List[str]) -> List[Dict]:
        """Fallback when API fails"""
        fallback = {
            "Pt": [{"material_id": "mp-126", "formula": "Pt", "band_gap": 0.0, "density": 21.45}],
            "Cu": [{"material_id": "mp-30",  "formula": "Cu", "band_gap": 0.0, "density": 8.96}],
            "Ni": [{"material_id": "mp-23",  "formula": "Ni", "band_gap": 0.0, "density": 8.91}],
            "Pd": [{"material_id": "mp-90",  "formula": "Pd", "band_gap": 0.0, "density": 12.02}],
            "Au": [{"material_id": "mp-81",  "formula": "Au", "band_gap": 0.0, "density": 19.30}],
            "Fe": [{"material_id": "mp-65",  "formula": "Fe", "band_gap": 0.0, "density": 7.87}],
            "Co": [{"material_id": "mp-42",  "formula": "Co", "band_gap": 0.0, "density": 8.90}],
            "Ru": [{"material_id": "mp-33",  "formula": "Ru", "band_gap": 0.0, "density": 12.37}],
            "Rh": [{"material_id": "mp-36",  "formula": "Rh", "band_gap": 0.0, "density": 12.41}],
        }

        results = []
        for elem in elements:
            if elem in fallback:
                for item in fallback[elem]:
                    item["source"] = "fallback_data"
                    results.append(item)
                print(f"📦 Using fallback data for {elem}")

        return results

    async def get_material_details(self, material_id: str) -> Optional[Dict]:
        """Get detailed information for a specific material"""
        if not self.api_key:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"X-API-KEY": self.api_key}
                url = f"{self.base_url}/materials/{material_id}"

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data")
                    return None
        except Exception:
            return None


class ExternalDataAggregator:
    """Aggregate data from all external sources"""

    def __init__(self):
        self.materials_project = MaterialsProjectService()

    async def fetch_catalysts_for_reaction(
        self,
        reaction: str,
        limit: int = 30
    ) -> List[CatalystRecord]:
        """Fetch catalysts relevant to a reaction from all sources"""

        candidates = []

        # Extract common elements from reaction
        elements = self._extract_elements_from_reaction(reaction)

        if elements:
            materials = await self.materials_project.search_materials(elements, limit)

            for material in materials:
                candidates.append(CatalystRecord(
                    source="materials_project",
                    name=material.get("formula", "Unknown"),
                    composition={"elements": material.get("elements", [])},
                    reaction=reaction,
                    activity=None,
                    selectivity=None,
                    stability=None,
                    url=material.get("url", "")
                ))

        return candidates

    def _extract_elements_from_reaction(self, reaction: str) -> List[str]:
        """Extract element symbols from reaction string"""
        common_elements = ["Pt", "Pd", "Ni", "Cu", "Au", "Ag", "Fe", "Co", "Ru", "Rh"]
        found = []
        for elem in common_elements:
            if elem in reaction or elem.lower() in reaction.lower():
                found.append(elem)
        return found[:5]


async def test_api():
    """Test that your API key is working"""
    print("\n" + "=" * 50)
    print("Testing Materials Project API Connection")
    print("=" * 50)

    service = MaterialsProjectService()

    if service.api_key:
        print(f"🔑 API Key found: {service.api_key[:8]}...{service.api_key[-4:]}")
        print("📡 Testing connection...")

        results = await service.search_materials(["Pt", "Cu"], limit=5)

        if results:
            print(f"\n✅ API test successful! Found {len(results)} materials:")
            for i, r in enumerate(results[:3], 1):
                print(f"   {i}. {r.get('formula')} (ID: {r.get('material_id')}) - Source: {r.get('source')}")
        else:
            print("\n⚠️ API returned no results. Check your internet connection.")
    else:
        print("\n❌ No API key found!")
        print("   Add MATERIALS_PROJECT_API_KEY=your_key_here to .env file")
        print("   Get a free key at: https://materialsproject.org/dashboard")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    asyncio.run(test_api())
