import requests
import re
import webbrowser
import unicodedata
import os
import sys

FLARESOLVERR_URL = "http://flaresolverr-render.onrender.com/v1"
BASE_URL = "https://channelmyanmar.to/"

def movie_name_to_slug(movie_name):
    """Converts a movie name string into a URL-friendly slug."""
    normalized = unicodedata.normalize("NFKD", movie_name)
    ascii_name = normalized.encode("ascii", "ignore").decode("utf-8")
    ascii_name = ascii_name.lower()
    ascii_name = re.sub(r"[^a-z0-9\s-]", "", ascii_name)
    ascii_name = re.sub(r"[\s_]+", "-", ascii_name)
    ascii_name = re.sub(r"-+", "-", ascii_name)
    ascii_name = ascii_name.strip("-")
    return ascii_name

def get_movie_links(movie_slug):
    url = BASE_URL + movie_slug
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Movie page not found or network error: {e}")
        return []

    links = re.findall(r'href="(https?://[^"]+)"', response.text)
    mega_links = [link for link in links if "megaup.net" in link]
    return mega_links

def get_megaup_final_link(mega_page_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(mega_page_url, headers=headers)
        r.raise_for_status()
        m = re.search(r"href='(https://download\.megaup\.net[^']+)'", r.text)
        if not m:
            print("⚠️ Could not extract intermediate MegaUp link.")
            return mega_page_url
        intermediate_link = m.group(1)

        data = {
            "cmd": "request.get",
            "url": intermediate_link,
            "maxTimeout": 60000
        }
        response = requests.post(FLARESOLVERR_URL, json=data).json()
        html = response.get("solution", {}).get("response", "")

        m_final = re.search(r'href="(https://megadl\.boats/download/[^"]+)"', html)
        if m_final:
            return m_final.group(1)
        else:
            print("⚠️ Could not find final Megadl.boats link.")
            return intermediate_link
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed during link resolution: {e}")
        return mega_page_url
    except Exception as e:
        print(f"❌ FlareSolverr request failed: {e}")
        return mega_page_url

def open_link(final_link):
    """Open link on desktop or Termux/Android"""
    if "ANDROID_ROOT" in os.environ:  # Detect Termux environment
        os.system(f'termux-open "{final_link}"')
    else:
        webbrowser.open(final_link)

def main():
    while True:
        movie_name = input("\nEnter movie name (or type 'exit' to quit): ").strip()
        if not movie_name or movie_name.lower() == 'exit':
            print("👋 Exiting program. Goodbye!")
            break

        slug = movie_name_to_slug(movie_name)
        print(f"🔗 Searching MegaUp links for: {BASE_URL + slug}")

        mega_links = get_movie_links(slug)
        if not mega_links:
            print("⚠️ No MegaUp links found for this movie. Please try another name.")
            continue

        print("\n✅ MegaUp links found:")
        for i, link in enumerate(mega_links, 1):
            print(f"{i}. {link}")

        choice = input("\nEnter the number of the MegaUp link to resolve: ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(mega_links)):
            print("⚠️ Invalid choice. Please enter a valid number.")
            continue
        selected_link = mega_links[int(choice) - 1]

        print("\n⏳ Resolving final download link... (This may take a moment)")
        final_link = get_megaup_final_link(selected_link)
        print(f"🎯 Final download link: {final_link}")

        print("🌍 Opening final download link in your browser.")
        open_link(final_link)

if __name__ == "__main__":
    main()
