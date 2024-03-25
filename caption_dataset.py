import asyncio
import os
import subprocess
from collections import Counter
from event import Event


class DatasetTagger:    
    def __init__(self, event, show_tags_event) -> None:
        self.event: Event = event
        self.show_tags_event = show_tags_event
    
    def caption_photo_images(self, train_data_dir:str, caption_weights:str="",batch_size:str="8",
                             max_length:str="75",min_length:str="10",beam_search:bool=True,
                             debug:bool=False,recursive:bool=False) -> None:
        
        # Construct the command to run the script
        script_path = os.path.join("sd-scripts", "finetune", "make_captions.py")

        if batch_size == "":
            batch_size = "8"
        
        workers = 2
        
        command = [
            "python", script_path, train_data_dir,
            "--caption_weights", caption_weights,
            "--batch_size", str(batch_size),
            "--max_data_loader_n_workers", str(workers),
            "--max_length", max_length,
            "--min_length", min_length
        ]

        # Add optional arguments based on the flags
        if beam_search:
            command.append("--beam_search")
        if debug:
            command.append("--debug")
        if recursive:
            command.append("--recursive")

        # Run the script
        subprocess.run(command, check=True)
        
        
        
    async def caption_anime_images(self, train_data_dir:str, force_download:bool=False, 
                             tags_to_show:str="50", blacklist_tags:str="",
                             batch_size:str="8",
                             caption_extension:str=".txt",
                             tag_threshold:float=0.35) -> None:
        
        script_path = os.path.join("sd-scripts","finetune", "tag_images_by_wd14_tagger.py")
        print(script_path)
        
        if batch_size == "":
            batch_size = "8"
        
        workers = "2"
        
        command = [
        "python", script_path, train_data_dir,
        "train_data_dir", train_data_dir,
        "--batch_size", batch_size,
        "--max_data_loader_n_workers", workers,
        "--caption_extention", caption_extension,
        "--thresh", str(tag_threshold),
        ]
        
        command.append("--remove_underscore")
        
        if force_download:
            command.append("--force_download")
        
        subprocess.run(command, check=True)
        
        await asyncio.sleep(5)
        
        self.remove_underscore_and_blacklisted_tags(images_folder=train_data_dir,tags_to_show=tags_to_show,blacklist_tags=blacklist_tags)
    
    
    def remove_underscore_and_blacklisted_tags(self, images_folder:str, tags_to_show:str="50", blacklist_tags:str=""):
        try:
            if blacklist_tags == "":
                blacklist_tags= "bangs, breasts, multicolored hair, two-tone hair, gradient hair, virtual youtuber, official alternate costume, official alternate hairstyle, official alternate hair length, alternate costume, alternate hairstyle, alternate hair length, alternate hair color"
            
            if tags_to_show == "":
                tags_to_show = "50"
            
            blacklisted_tags = [tag.strip() for tag in blacklist_tags.split(",")]
            top_tags = Counter()
        
            for txt_file in [f for f in os.listdir(images_folder) if f.lower().endswith(".txt")]:
                with open(os.path.join(images_folder, txt_file), 'r', encoding='utf-8') as file:
                    tags = [tag.strip() for tag in file.read().split(",")]
                    tags = [t.replace("_", " ") if len(t) > 3 else t for t in tags]
                    tags = [t for t in tags if t not in blacklisted_tags]
                top_tags.update(tags)

                with open(os.path.join(images_folder, txt_file), 'w', encoding='utf-8') as file:
                    file.write(", ".join(tags))
        
            # Display the top tags
            number_tags = int(tags_to_show)
            
            complete_message = ""
            for tag, count in top_tags.most_common(number_tags):
                complete_message += f"{tag}: {count}\n"
            
            self.show_tags_event.emit(complete_message)
            self.event.emit("Done, your Dataset was successfully captioned!")
        except Exception as e:
            self.event.emit(f"Failed the post-processing of dataset tags:\n{e}")

    