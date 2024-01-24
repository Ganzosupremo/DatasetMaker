from collections import Counter
import os
import glob
from event import Event


class ExtrasDataset:
    def __init__(self, event:Event, top_tags_event:Event) -> None:
        self.event = event
        self.top_tags_event = top_tags_event
    
    def analyze_tags(self, images_folder:str, show_top_tags:str="50"):
        if show_top_tags == "":
            show_top_tags = "50"
            
        top_tags_int:int = int(show_top_tags)
        top_tags = Counter()

        for txt_file in [f for f in os.listdir(images_folder) if f.lower().endswith(".txt")]:
            with open(os.path.join(images_folder, txt_file), 'r', encoding='utf-8') as file:
                tags = [tag.strip() for tag in file.read().split(",")]
                top_tags.update(tags)

        self.event.emit(f"📊 Top {show_top_tags} tags:")
        complete_message = ""
        for tag, count in top_tags.most_common(top_tags_int):
            complete_message += f"{tag}: {count}\n"
        
        self.top_tags_event.emit(complete_message)
        

    def delete_non_image_files(self, images_folder:str):
        # List all files in the folder
        all_files = glob.glob(os.path.join(images_folder, '*'))

        for file_path in all_files:
            # Check if the file is not an image (png, jpg, jpeg)
            if not file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
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
        