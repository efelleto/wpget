import requests
import re
from bs4 import BeautifulSoup


class SteamAPI:
    @staticmethod
    def extract_id(url):
        """Extrai o ID numérico da URL do Steam Workshop."""
        match = re.search(r"id=(\d+)", url)
        return match.group(1) if match else None

    @staticmethod
    def get_metadata(item_id):
        """Recupera informações detalhadas do wallpaper via scraping."""
        url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={item_id}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Título
            title_elem = soup.find("div", class_="workshopItemTitle")
            title = title_elem.text.strip() if title_elem else f"Wallpaper {item_id}"

            # Thumbnail (preview)
            thumb_elem = soup.find("img", id="mainItemImage")
            thumb_url = thumb_elem['src'] if thumb_elem else None

            # Autor
            author_elem = soup.find("div", class_="creatorsBlock")
            if author_elem:
                author_link = author_elem.find("a")
                author = author_link.text.strip() if author_link else "Unknown"
            else:
                author = "Unknown"

            # Tipo (video/scene/web) - procura nas tags
            type_elem = soup.find("a", href=re.compile(r"browse[^\"]*?tag"))
            wallpaper_type = "scene"  # default
            if type_elem:
                tag_text = type_elem.text.lower()
                if "video" in tag_text:
                    wallpaper_type = "video"
                elif "web" in tag_text:
                    wallpaper_type = "web"
                elif "scene" in tag_text:
                    wallpaper_type = "scene"

            # Resolução - procura no texto da página
            resolution = "unknown"
            details = soup.find("div", class_="detailsStatsContainerRight")
            if details:
                text = details.get_text()
                # Procura padrões como "1920 x 1080" ou "3840x2160"
                res_match = re.search(r"(\d{3,4})\s*x\s*(\d{3,4})", text)
                if res_match:
                    resolution = f"{res_match.group(1)}x{res_match.group(2)}"

            return {
                "id": item_id,
                "title": title,
                "thumb": thumb_url,
                "url": url,
                "author": author,
                "type": wallpaper_type,
                "resolution": resolution
            }

        except Exception as e:
            print(f"[ INFO ] API Error: {e}")
            return None
