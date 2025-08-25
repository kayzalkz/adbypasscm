import requests
import re
import webbrowser

FLARESOLVERR_URL = "http://localhost:8191/v1"
BASE_URL = "https://channelmyanmar.to/"

def movie_name_to_slug(movie_name):
    """Converts a movie name string into a URL-friendly slug."""
    return movie_name.strip().lower().replace(" ", "-")

def get_movie_links(movie_slug):
    """Fetches all MegaUp links from a movie page on Channelmyanmar.to."""
    url = BASE_URL + movie_slug
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"❌ Movie page not found or network error: {e}")
        return []

    # Extract all links and filter for MegaUp links
    links = re.findall(r'href="(https?://[^"]+)"', response.text)
    mega_links = [link for link in links if "megaup.net" in link]
    return mega_links

def get_megaup_final_link(mega_page_url):
    """Resolves an intermediate MegaUp link to the final Megadl.boats download link using FlareSolverr."""
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        # Step 1: Get intermediate download.megaup.net link
        r = requests.get(mega_page_url, headers=headers)
        r.raise_for_status()
        
        m = re.search(r"href='(https://download\.megaup\.net[^']+)'", r.text)
        if not m:
            print("⚠️ Could not extract intermediate MegaUp link.")
            return mega_page_url
        intermediate_link = m.group(1)

        # Step 2: Solve intermediate page with FlareSolverr to bypass Cloudflare
        data = {
            "cmd": "request.get",
            "url": intermediate_link,
            "maxTimeout": 60000 # Increased timeout for robustness
        }
        
        response = requests.post(FLARESOLVERR_URL, json=data).json()
        html = response.get("solution", {}).get("response", "")

        # Step 3: Extract final Megadl.boats link
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

def main():
    while True: # Main loop to continue searching for movies
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

        # Display found MegaUp links
        print("\n✅ MegaUp links found:")
        for i, link in enumerate(mega_links, 1):
            print(f"{i}. {link}")

        # User chooses a link to resolve
        choice = input("\nEnter the number of the MegaUp link to resolve: ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(mega_links)):
            print("⚠️ Invalid choice. Please enter a valid number.")
            continue
        selected_link = mega_links[int(choice) - 1]

        # Resolve the final download link
        print("\n⏳ Resolving final download link... (This may take a moment)")
        final_link = get_megaup_final_link(selected_link)
        print(f"🎯 Final download link: {final_link}")

        # Open the link in the browser
        print("🌍 Opening final download link in your default browser.")
        webbrowser.open(final_link)

if __name__ == "__main__":
    main()
