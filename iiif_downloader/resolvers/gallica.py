from .base import BaseResolver

class GallicaResolver(BaseResolver):
    def can_resolve(self, url_or_id):
        return "gallica.bnf.fr" in url_or_id

    def get_manifest_url(self, url_or_id):
        # Input: https://gallica.bnf.fr/ark:/12148/btv1b84260335
        # Output: https://gallica.bnf.fr/iiif/ark:/12148/btv1b84260335/manifest.json
        
        # Clean URL
        clean_url = url_or_id.split("?")[0].strip("/")
        
        # Extract ARK ID part (everything after ark:/...)
        if "ark:/" in clean_url:
            ark_part = "ark:/" + clean_url.split("ark:/")[1]
            
            # If it already looks like a manifest URL, just return it
            if clean_url.endswith("/manifest.json"):
                 return clean_url, ark_part.split("/manifest.json")[0].split("/")[-1]

            # ID is usually the last part of the ark string
            ms_id = ark_part.split("/")[-1]
            manifest_url = f"https://gallica.bnf.fr/iiif/{ark_part}/manifest.json"
            return manifest_url, ms_id
        
        return None, None
