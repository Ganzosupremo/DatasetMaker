import os
from utils import Event

class DatasetTagCurator:
    def __init__(self, event:Event, show_modified_tags_event:Event) -> None:
        self.event = event
        self.show_modified_tags_event = show_modified_tags_event
    
    def curate_tags(self, images_folder:str, global_activation_tag:str, remove_tags:str):
        
        def split_tags(tagstr):
            return [s.strip() for s in tagstr.split(",") if s.strip()]

        activation_tag_list = split_tags(global_activation_tag)
        remove_tags_list = split_tags(remove_tags)
        
        activation_tag_list.reverse()
        remove_count = 0

        for txt_file in [f for f in os.listdir(images_folder) if f.lower().endswith(".txt")]:
            with open(os.path.join(images_folder, txt_file), 'r', encoding='utf-8') as file:
                tags = [tag.strip() for tag in file.read().split(",")]
            
            # Add global activation tag at the beginning
            for act_tag in activation_tag_list:
                if act_tag in tags:
                    tags.remove(act_tag)
                tags.insert(0, act_tag)
            
            # Remove the specified tags
            for rem_tag in remove_tags_list:
                if rem_tag in tags:
                    remove_count += 1
                    tags.remove(rem_tag)

            # Write the modified tags back to the file
            with open(os.path.join(images_folder, txt_file), 'w', encoding='utf-8') as file:
                file.write(", ".join(tags))

        # Output messages
        if global_activation_tag:
            self.show_modified_tags_event.emit(f"\n📎 Applied new activation tag(s): {', '.join(activation_tag_list)}")
        if remove_tags:
            self.event.emit(f"✅ Done! Tags have been curated.\n🚮 Removed {remove_count} tags.")