from collections import Counter
import os
import glob
from utils import Event

IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".PNG", ".JPG", ".JPEG", ".WEBP", ".BMP"]

def glob_images_pathlib(dir_path, recursive):
    image_paths = []
    if recursive:
        for ext in IMAGE_EXTENSIONS:
            image_paths += list(dir_path.rglob("*" + ext))
    else:
        for ext in IMAGE_EXTENSIONS:
            image_paths += list(dir_path.glob("*" + ext))
    image_paths = list(set(image_paths))
    image_paths.sort()
    return image_paths


class ExtrasDataset:
    def __init__(self, event:Event, top_tags_event:Event) -> None:
        self.event = event
        self.top_tags_event = top_tags_event
    
    def analyze_tags(self, images_folder:str, show_top_tags_text:str=""):
        if show_top_tags_text == "":
            show_top_tags_text = "50"
            
        top_tags_int:int = int(show_top_tags_text)
        top_tags = Counter()

        for txt_file in [f for f in os.listdir(images_folder) if f.lower().endswith(".txt")]:
            with open(os.path.join(images_folder, txt_file), 'r', encoding='utf-8') as file:
                tags = [tag.strip() for tag in file.read().split(",")]
                top_tags.update(tags)

        complete_message = ""
        if show_top_tags_text == "0":
            for tag, count in top_tags.most_common(None):
                complete_message += f"{tag}: {count}\n"
            self.event.emit(f"📊 Showing all tags")
        else:
            for tag, count in top_tags.most_common(top_tags_int):
                complete_message += f"{tag}: {count}\n"
            self.event.emit(f"📊 Top {show_top_tags_text} tags")
            
        
        self.top_tags_event.emit(complete_message)
        
    def delete_non_image_files(self, images_folder:str):
        # List all files in the folder
        all_files = glob.glob(os.path.join(images_folder, '*'))

        for file_path in all_files:
            for ext in IMAGE_EXTENSIONS:
            # Check if the file is not an image (png, jpg, jpeg)
                if not file_path.lower().endswith(ext):
                    # Delete the file
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        self.event.emit(f"Error deleting file {file_path}:\n{e}")
        self.event.emit("Folder Cleared!!")

    
    def count_datasets(self, images_folder:str):
        tree = {}
        exclude = ("_logs", "output", "config")  # Directories to exclude

        for root, dirs, files in os.walk(images_folder, topdown=True):
            # Exclude specified directories
            dirs[:] = [d for d in dirs if all(ex not in d for ex in exclude)]

            # Count images, captions, and other files
            images = sum(f.lower().endswith((".png", ".jpg", ".jpeg")) for f in files)
            captions = sum(f.lower().endswith(".txt") for f in files)
            others = len(files) - images - captions

            # Format the path and store counts
            path = root[len(images_folder):].strip(os.sep)
            tree[path] = None if not images else f"{images:>4} images | {captions:>4} captions |"
            if tree[path] and others:
                tree[path] += f" {others:>4} other files"

            # Calculate padding for alignment
            pad = max(len(k) for k in tree)
            self.event.emit("\n".join(f"📁{k.ljust(pad)} | {v}" for k, v in tree.items() if v))
        