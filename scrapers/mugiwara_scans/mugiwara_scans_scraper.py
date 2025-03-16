import asyncio
import zendriver as zd
from bs4 import BeautifulSoup
from pathlib import Path


class File:
    def __init__(self, name, url):
        self.name = name
        self.url = url

    def __str__(self):
        return f"Name: {self.name}, URL: {self.url}"


async def accept_cookies(page: zd.Tab):
    cookie_bar_accept = await page.find("consentir", best_match=True)
    if cookie_bar_accept:
        await cookie_bar_accept.click()

    await page.sleep(1)


async def get_chapters(browser: zd.Browser) -> list[File]:
    # visit the target website
    page: zd.Tab = await browser.get(
        "https://www.fireload.com/folder/16f514a491fab2909938bff3faf0ca3c/Capítulos"
    )
    await page

    # get files from all pages
    files = []
    while True:
        files += await page.select_all(".fileIconLi")

        next_page_btn = await page.select("#nextLink")
        button_html = await next_page_btn.parent.get_html()
        element = BeautifulSoup(button_html, "html.parser").find(class_="disabled")
        if element:
            print("Last page reached")
            break
        else:
            print("Next page found")
            await next_page_btn.click()
            await page.sleep(1)

    file_data = []

    for file in files:
        file_html = await file.get_html()
        element = BeautifulSoup(file_html, "html.parser").find(
            attrs={"dttitle": True, "dtfullurl": True}
        )

        data = File(element.get("dttitle"), element.get("dtfullurl"))

        file_data.append(data)

    print(f"Found {len(file_data)} chapters")

    return file_data


async def download_file(browser: zd.Browser, file: File, download_folder: Path):
    file_name = file.name
    file_url = file.url

    print(f"Trying to download: {file_name}")

    page = await browser.get(file_url)
    await page

    await accept_cookies(page)

    print("Waiting for download link...")
    time = 0
    while True:
        if time == 15:
            print("Download link not found")
            break

        download_button = await page.select(".download-button")
        button_html = await download_button.get_html()
        element = BeautifulSoup(button_html, "html.parser").find("a")

        download_url = element.get("href")
        if download_url != "javascript:void(0)":
            print(f"Download link found in {time} seconds")
            break

        await page.sleep(1)
        time += 1

    # download the file
    await page.set_download_path(download_folder)
    file_path = download_folder.joinpath(file_name)

    if file_path.exists():
        file_path.unlink()

    await download_button.click()
    print("Downloading file...")

    time = 0
    while True:
        if time == 60:
            print("Download failed")
            break

        if file_path.exists():
            print(f"Download complete in {time} seconds")
            break

        await page.sleep(1)
        time += 1


async def scraper():
    browser = await zd.start()

    download_folder = Path("downloads/mugiwara_scans")

    file_data = await get_chapters(browser)

    await download_file(browser, file_data[-1], download_folder)

    browser.stop()


# run the scraper function with asyncio
if __name__ == "__main__":
    asyncio.run(scraper())
