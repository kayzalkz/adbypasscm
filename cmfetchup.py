import requests
from bs4 import BeautifulSoup
import webbrowser
import re
import asyncio
from pyppeteer import launch

BASE_URL = "https://channelmyanmar.to/"

def get_movie_links(movie_slug):
    """Fetch all download links from the movie page."""
    url = BASE_URL + movie_slug
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    
    if response.status_code != 200:
        print("❌ Error: Page not found")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    links = []
    enlaces_box = soup.find("div", class_="enlaces_box")
    if enlaces_box:
        for a in enlaces_box.find_all("a", href=True):
            links.append(a["href"])
    
    return links

def get_usersdrive_direct_link(page_url):
    """Convert Usersdrive link to a direct download URL."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(page_url, headers=headers)
    
    if response.status_code != 200:
        return page_url
    
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    
    download_a = soup.find("a", id="downloadbtn")
    if download_a:
        return download_a["href"]
    
    match = re.search(r'href\s*=\s*"(/d/[^"]+)"', html)
    if match:
        direct_link = "https://dns700.userdrive.org" + match.group(1)
        return direct_link
    
    return page_url

async def get_megaup_direct_link(page_url):
    """Resolve MegaUp link to the final direct download URL using Pyppeteer."""
    browser = None
    try:
        browser = await launch(headless=False)
        page = await browser.newPage()
        
        # Navigate and wait for all redirects and network requests to finish.
        await page.goto(page_url, waitUntil='networkidle0')
        
        # Wait for the download button on the final page.
        await page.waitForSelector('#btn-download', {'visible': True})
        
        # Extract the href from the download button.
        download_link = await page.evaluate(
            '(selector) => document.querySelector(selector).href',
            '#btn-download'
        )
        return download_link
    
    except Exception as e:
        print(f"⚠️ Could not extract Megaup final link: {e}")
        return page_url
    finally:
        if browser:
            await browser.close()

def movie_name_to_slug(movie_name):
    """Convert movie name to a URL slug."""
    return movie_name.strip().lower().replace(" ", "-")

async def main():
    while True:
        movie_name = input("\nEnter movie name (or type 'exit' to quit): ").strip()
        if movie_name.lower() == "exit":
            print("👋 Goodbye!")
            break
        
        movie_slug = movie_name_to_slug(movie_name)
        print(f"🔗 Fetching links from: {BASE_URL + movie_slug}")
        download_links = get_movie_links(movie_slug)
        
        if download_links:
            direct_links = []
            for link in download_links:
                if "usersdrive.com" in link:
                    direct_link = get_usersdrive_direct_link(link)
                elif "megaup.net" in link:
                    direct_link = await get_megaup_direct_link(link)
                else:
                    direct_link = link
                direct_links.append(direct_link)
            
            print("\n✅ Found download links:")
            for i, link in enumerate(direct_links, 1):
                print(f"{i}. {link}")
            
            choice = input("\nEnter the number of the link you want to open (or press Enter to skip): ").strip()
            
            if choice.isdigit():
                choice = int(choice)
                if 1 <= choice <= len(direct_links):
                    selected_link = direct_links[choice - 1]
                    print(f"\n🎯 Opening: {selected_link}")
                    webbrowser.open(selected_link)
                else:
                    print("⚠️ Invalid choice")
            else:
                print("⏭ Skipped opening link")
        else:
            print("⚠️ No download links found.")

if __name__ == "__main__":
    asyncio.run(main())
