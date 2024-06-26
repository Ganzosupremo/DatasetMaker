import asyncio
import requests
import os
from utils import Event

max_resolution:int = 3072
semaphore = asyncio.Semaphore(10)

class ImageScraper:
    def __init__(self, event) -> None:
        self.event: Event = event
    
    
    async def scrape_images(self, tags:str, dataset_dir:str, include_posts_with_parent:bool=True, total_image_limit:str="800") -> int:
        tags = tags.replace(" ", "+").replace("(", "%28").replace(")", "%29").replace(":", "%3a").replace("&", "%26")
        url = f"https://gelbooru.com/index.php?page=dapi&json=1&s=post&q=index&limit=100&tags={tags}"
        user_agent = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/93.0.4577.83 Safari/537.36"
        
        total_limit:int = 800
        if total_image_limit != "" or total_image_limit.isnumeric():
            total_limit:int = int(total_image_limit)
        
        supported_types = (".png", ".jpg", ".jpeg")

        def get_json(_url):
            response = requests.get(_url, headers={"User-Agent": user_agent})
            return response.json()

        def filter_images(_data):
            return [p["file_url"] if p["width"] * p["height"] <= max_resolution ** 2 else p["sample_url"]
                    for p in _data["post"]
                    if (p["parent_id"] == 0 or include_posts_with_parent)
                    and p["file_url"].lower().endswith(supported_types)]

        data = get_json(url)
        count = data["@attributes"]["count"]

        if count == 0:
            print("No results found")
            return -1

        self.event.emit(f"Found {count} images...")
        print(f"Found {count} images...")
        image_urls = set()
        image_urls.update(filter_images(data))
        for i in range(total_limit // 100):
            count -= 100
            if count <= 0:
                break
            image_urls.update(filter_images(get_json(url + f"&pid={i + 1}")))

        # Create a list of coroutine objects for downloading images
        total_images = len(image_urls)
        download_tasks = []
        for i, url in enumerate(image_urls):
            if url.strip():
                download_tasks.append(self.download_image(url=url.strip(), dataset_dir=dataset_dir,current=i))

        # Run the download tasks concurrently
        self.event.emit(f"Downloading {total_images} images in 5 seconds...")
        print(f"Downloading {total_images} images in 5 seconds...")
        await asyncio.sleep(5.0)
        await asyncio.gather(*download_tasks)
        self.event.emit(f"Done scrapping images to {dataset_dir}.\n Downloaded a total of {total_images} images.")
        print(f"Done scrapping images to {dataset_dir}.\n Downloaded a total of {total_images} images.")
        return total_images

    
    async def download_image(self, url:str, dataset_dir:str, current:int=0):
        async with semaphore:
            if not url:
                self.event.emit("Empty URL, skipping")
                print("Empty URL, skipping")
                return
            try:
                response = requests.get(url)
                response.raise_for_status()
                image_name = url.split("/")[-1]
                with open(os.path.join(dataset_dir, image_name), 'wb') as f:
                    f.write(response.content)
                    print(f"Downloaded: {current}: {image_name}.")
            except requests.RequestException as e:
                self.event.emit(f"Failed to download {url}:\n{e}")
                print(f"Failed to download {url}:\n{e}")
    
    
