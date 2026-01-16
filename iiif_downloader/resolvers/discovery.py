import re
import requests
import xml.etree.ElementTree as ET
from typing import Optional, Tuple, List, Dict
from iiif_downloader.utils import DEFAULT_HEADERS

def resolve_shelfmark(library: str, shelfmark: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve a library name and shelfmark/ID into a IIIF Manifest URL.
    Returns (manifest_url, doc_id).
    """
    s = shelfmark.strip()
    
    if library == "Vaticana (BAV)":
        # Handle full URL if pasted accidentally
        if "digi.vatlib.it" in s:
            ms_id = s.strip("/").split("/")[-1]
            return f"https://digi.vatlib.it/iiif/{ms_id}/manifest.json", ms_id
            
        # Standardize shelfmark: "Urb. Lat. 1779" -> "MSS_Urb.lat.1779"
        # 1. Remove all spaces
        clean_s = s.replace(" ", "")
        # 2. Case normalization (BAV often uses 'lat.' instead of 'Lat.')
        clean_s = clean_s.replace("Lat.", "lat.").replace("Gr.", "gr.").replace("Vat.", "vatic.").replace("Pal.", "pal.")
        
        clean_id = clean_s if clean_s.startswith("MSS_") else f"MSS_{clean_s}"
        return f"https://digi.vatlib.it/iiif/{clean_id}/manifest.json", clean_s
        
    elif library == "Gallica (BnF)":
        # Pattern: ark:/12148/btv1b84260335
        # Manifest: https://gallica.bnf.fr/iiif/ark:/12148/btv1b84260335/manifest.json
        if "ark:/" not in s:
            return None, "Gallica richiede un ID formato ARK (es. ark:/12148/...)"
        
        # Extract doc_id (last part of ARK)
        doc_id = s.split("/")[-1]
        return f"https://gallica.bnf.fr/iiif/{s}/manifest.json", doc_id
        
    elif library == "Bodleian (Oxford)":
        # Pattern: UUID (080f88f5-7586-4b8a-8064-63ab3495393c)
        # Manifest: https://iiif.bodleian.ox.ac.uk/iiif/manifest/{uuid}.json
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        if not re.match(uuid_pattern, s.lower()):
            return None, "Bodleian richiede un UUID valido."
            
        return f"https://iiif.bodleian.ox.ac.uk/iiif/manifest/{s.lower()}.json", s
        
    return None, None

def search_gallica(query: str) -> List[Dict]:
    """Search Gallica using SRU API."""
    url = "https://gallica.bnf.fr/SRU"
    params = {
        "operation": "searchRetrieve",
        "version": "1.2",
        "query": f'(dc.title all "{query}") and (dc.type all "manuscrit")',
        "maximumRecords": "10",
        "startRecord": "1"
    }
    results = []
    try:
        r = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        
        # Namespaces are tricky in SRU
        ns = {
            'srw': 'http://www.loc.gov/zing/srw/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/'
        }
        
        for record in root.findall('.//srw:record', ns):
            title = record.find('.//dc:title', ns)
            identifier = record.find('.//dc:identifier', ns)
            
            if title is not None and identifier is not None:
                ark = identifier.text
                if "ark:/" in ark:
                    doc_id = ark.split("/")[-1]
                    results.append({
                        "id": doc_id,
                        "title": title.text,
                        "manifest_url": f"https://gallica.bnf.fr/iiif/{ark}/manifest.json",
                        "preview_url": f"https://gallica.bnf.fr/{ark}.thumbnail"
                    })
    except Exception as e:
        print(f"Error searching Gallica: {e}")
    return results

def search_oxford(query: str) -> List[Dict]:
    """Search Bodleian digital collections."""
    # Bodleian uses a JSON API for their search
    url = "https://digital.bodleian.ox.ac.uk/api/search/catalog/"
    params = {
        "q": query,
        "format": "json",
        "rows": 10
    }
    results = []
    try:
        r = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        
        for doc in data.get("response", {}).get("docs", []):
            uuid = doc.get("uuid")
            title = doc.get("title_ssm", ["Senza Titolo"])[0]
            if uuid:
                results.append({
                    "id": uuid,
                    "title": title,
                    "manifest_url": f"https://iiif.bodleian.ox.ac.uk/iiif/manifest/{uuid}.json",
                    "preview_url": f"https://iiif.bodleian.ox.ac.uk/iiif/image/{uuid}/full/256,/0/default.jpg"
                })
    except Exception as e:
        print(f"Error searching Oxford: {e}")
    return results
