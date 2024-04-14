import asyncio
from typing import Any, Literal, Tuple
from typing_extensions import Literal
import customtkinter as ctk
import os

from customtkinter.windows.widgets.font import CTkFont
from curate_dataset_tags import DatasetTagCurator
from curate_images import CurateImages
from extras import ExtrasDataset
from scrape_images import ImageScraper
from caption_dataset import DatasetTagger
from utils import Event

ctk.set_default_color_theme("green")
ctk.set_appearance_mode("system")

title_font: ctk.CTkFont
normal_font: ctk.CTkFont
status_label: ctk.CTkLabel

dataset_dir: str
dataset_base_dir: str
project_subfolder:str
step1_completed: bool = False

class MainApp(ctk.CTk):
    def __init__(self) -> None:
        global title_font, normal_font
        super().__init__()
               
        status_update_event = Event()
        status_update_event.subscribe(self.update_status_label)
        
        self.title("Dataset Maker")
        self.geometry("1024x768")
        self.iconbitmap(f"D:\\PythonProjects\\DatasetMaker\\icon.ico")
        title_font = ctk.CTkFont("The Bold Font", size=34)
        normal_font = ctk.CTkFont("Times New Roman", size=17, weight='normal',slant='roman')
        
        self.status_label = ctk.CTkLabel(self, font=normal_font, text="")
        self.status_label.pack(pady=5, side="bottom")
        
        note_text = ctk.CTkLabel(self, font=normal_font, text="Once a button is pressed, the app may freeze.\n"
                         "Don't worry all the proccessing is happening in the background, just wait patiently for the process to complete...")
        note_text.pack(pady=10, side='bottom')
        
        # Create a Notebook (Tab control)
        notebook = ctk.CTkTabview(self,
                                  corner_radius=10, 
                                  border_color='green', 
                                  border_width=3)
        notebook.add('Project Setup')
        notebook.add('Image Scraping')
        notebook.add('Image Curation')
        notebook.add('Tag Images')
        notebook.add('Curate Dataset Tags')
        notebook.add('Extras')
        notebook.pack(expand=True, fill="both", padx=5, pady=5)
        
        project_setup_tab = ProjectSetupTab(master=notebook.tab("Project Setup"), event=status_update_event)
        project_setup_tab.pack(pady=5, expand=True,fill="both")
        scrape_images_tab = ScrapeImagesTab(master=notebook.tab("Image Scraping"), event=status_update_event)
        scrape_images_tab.pack(pady=5, expand=True,fill="both")
        curate_images_tab = CurateImagesTab(master=notebook.tab("Image Curation"), event=status_update_event)
        curate_images_tab.pack(pady=5, expand=True,fill="both")
        tag_images_tab = ScrollableTagImagesTab(master=notebook.tab("Tag Images"), event=status_update_event)
        tag_images_tab.pack(pady=5, expand=True,fill="both")
        curate_tags_tab = CurateDatasetTagsTab(master=notebook.tab("Curate Dataset Tags"), event=status_update_event)
        curate_tags_tab.pack(pady=5, expand=True,fill="both")
        extras_tab = ExtrasTab(master=notebook.tab("Extras"), event=status_update_event)
        extras_tab.pack(pady=5, expand=True,fill="both")
    
    def update_status_label(self, text:str):
        self.status_label.configure(text=text)


class ProjectSetupTab(ctk.CTkFrame):
    def __init__(self, master: Any, event:Event, width: int = 200, height: int = 200, corner_radius: int | str | None = None, border_width: int | str | None = None, bg_color: str | Tuple[str, str] = "transparent", fg_color: str | Tuple[str, str] | None = None, border_color: str | Tuple[str, str] | None = None, background_corner_colors: Tuple[str | Tuple[str, str]] | None = None, overwrite_preferred_drawing_method: str | None = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)

        self.event = event
        self.dataset_base_dir:str = ""
        ctk.CTkLabel(master, text="Project Setup", font=title_font).pack(pady=15, expand=True, fill="both")
        ctk.CTkLabel(master, font=normal_font, text="Welcome! This app is a modified version of the Dataset Maker by Hollowstrawberry."
                    "\nThis app is designed to run on the local machine instead of Google Drive, for the ones that do not like working with Drive.\n"
                    "Let's begin at the beginning, set up the name of your project, the app will save the project on your Pictures directory under a folder called 'Loras'."
                    "\nYou can also specify a project subfolder to separate diffent characters, styles, etc, like this: project_name/subfolder_name.").pack(pady=10, expand=True, fill="both")

        self.project_name_entry = ctk.CTkEntry(master, font=normal_font, width=250, height=36, corner_radius=10, border_color='green', border_width=2, placeholder_text="Project Name")
        self.project_name_entry.pack(pady=5)

        folder_structure_options = ["Organize by project", "Organize by category"]
        folder_structure_optionmenu = ctk.CTkOptionMenu(master, font=normal_font, width=250, height=36, corner_radius=10,values=folder_structure_options)
        folder_structure_optionmenu.pack(pady=3)

        setup_button = ctk.CTkButton(master, font=normal_font, width=200, height=32, corner_radius=10, border_color='green', border_width=2, text="Setup Project", command=self.setup_project)
        setup_button.pack(pady=30)
    
    def setup_project(self):
        global dataset_base_dir, project_subfolder, dataset_dir, step1_completed
        try:
            project_input = self.project_name_entry.get()

            # Basic validation for project input
            if not project_input or any(c in project_input for c in " .()\"'"):
                self.event.emit(text="Invalid project input. Please retry.")
                return

            # Split the project input into base and subfolder names
            project_parts = project_input.split('/')
            project_base = project_parts[0]
            project_subfolder = project_parts[1] if len(project_parts) > 1 else ""

            # Determine the base directory based on the folder structure option
            base_dir = os.path.expanduser(f"~\\Pictures\\Loras")

            # Create the main project directory
            project_dir = os.path.join(base_dir, project_base)
            os.makedirs(project_dir, exist_ok=True)

            # Create the 'config' directory in the main project directory
            config_dir = os.path.join(project_dir, "Config")
            os.makedirs(config_dir, exist_ok=True)

            # Create the 'datasets' directory and subfolder if specified
            dataset_base_dir = os.path.join(project_dir, "datasets")
            if project_subfolder:
                dataset_dir = os.path.join(dataset_base_dir, project_subfolder)
            else:
                dataset_dir = dataset_base_dir

            os.makedirs(dataset_dir, exist_ok=True)

            self.event.emit(text=f"Project setup completed at {dataset_dir}")
            print(f"Project setup completed at {dataset_dir}")
            step1_completed = True
        except Exception as e:
            self.event.emit(text=f"Failed to create directory:\n {e}")
            print(f"Failed to create directory:\n {e}")
        

class ScrapeImagesTab(ctk.CTkFrame):
    def __init__(self, master: Any, event:Event,width: int = 200, height: int = 200, corner_radius: int | str | None = None, border_width: int | str | None = None, bg_color: str | Tuple[str, str] = "transparent", fg_color: str | Tuple[str, str] | None = None, border_color: str | Tuple[str, str] | None = None, background_corner_colors: Tuple[str | Tuple[str, str]] | None = None, overwrite_preferred_drawing_method: str | None = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)
        ctk.CTkLabel(master, text="Image Scraping",font=title_font).pack(pady=15, expand=True, fill="both")
        text:str = "We will grab images from the popular anime gallery Gelbooru.\nImages are sorted by tags, including poses, scenes, character traits, character names, artists, etc.\nIf you instead want to use your own images, Copy them to Pictures/Loras/project_name/dataset folder.\nUp to 1000 images may be downloaded by this step in just one minute. Remember, with great power, comes great responsability.\n\nYour target tags should include the relevant tags for your character/concept/artstyle, \nand exclude undesired tags (for example, explicit images may affect learning).\nSeparate words with underscores, separate tags with spaces, and use - to exclude a tag. You can also include a minimum score: score:>10"

        self.event:Event = event
        ctk.CTkLabel(master, text=text,height=32,font=normal_font, compound="left").pack(pady=20, expand=True)
        self.tags_entry = ctk.CTkEntry(master, 
                                       placeholder_text='Enter your desired tags here...', 
                                       width=450,
                                       height=35,
                                       corner_radius=10,
                                       border_width=2,
                                       border_color='green',
                                       font=normal_font)
        self.tags_entry.pack(pady=5)
        
        self.total_image_limit_entry = ctk.CTkEntry(master=master,
                                                    placeholder_text="Defines the max total of images to be downloaded at once. Default is 800",
                                                    width=450,
                                                    height=35,
                                                    corner_radius=10,
                                                    border_width=2,
                                                    border_color='green',
                                                    font=normal_font)
        self.total_image_limit_entry.pack(pady=5)
        
        scrape_button = ctk.CTkButton(master, text="Scrape Images",
                                      width=300,
                                      height=32,
                                      corner_radius=10, 
                                      border_color='green',
                                      border_width=2,
                                      font=normal_font, 
                                      command=self.on_scrape_button_clicked)
        scrape_button.pack(pady=5)
    
    
    def on_scrape_button_clicked(self):
        asyncio.run(self.scrape_images())
    
    async def scrape_images(self):
        if not step1_completed:
            self.event.emit(text=f"Project Directory not set. Please set one on the Project Setup Tab first...")
            return
        try:
            self.event.emit("Starting to fetch the images with desired tags...")
            scraper = ImageScraper(event=self.event)
            await scraper.scrape_images(tags=self.tags_entry.get(),dataset_dir=dataset_dir, total_image_limit=self.total_image_limit_entry.get())
        except Exception as e:
            self.event.emit(f"Failed to scrape images from Gelbooru:\n{e}")
            print(f"Failed to scrape images from Gelbooru:\n{e}")
        
            
class CurateImagesTab(ctk.CTkFrame):
    def __init__(self, master: Any, event: Event, width: int = 200, height: int = 200, corner_radius: int | str | None = None, border_width: int | str | None = None, bg_color: str | Tuple[str, str] = "transparent", fg_color: str | Tuple[str, str] | None = None, border_color: str | Tuple[str, str] | None = None, background_corner_colors: Tuple[str | Tuple[str, str]] | None = None, overwrite_preferred_drawing_method: str | None = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)
        ctk.CTkLabel(self, text="Curate Images", font=title_font).pack(pady=15, expand=True, fill="x")
        ctk.CTkLabel(self, font=normal_font, text="In this section we wil find the duplicated images with the FiftyOne AI and mark them for deletion.\n"
                                "A new tab in your browser will open, you can manually mark the images you don't like for deletion.\n"
                                "Once done press the End Curation button.").pack(pady=5)
        
        self.event: Event = event
        self.set_sim_frame()
        
        
        ctk.CTkButton(self, corner_radius=10, border_width=1, border_color='green', text="Curate Images",
              command=self.curate_images).pack(pady=10)
        ctk.CTkButton(self, corner_radius=10, border_width=1, border_color='green',text="End Curation",
              command=self.end_curation).pack(pady=10)

    def set_sim_frame(self):
        sim_frame = ctk.CTkFrame(self,width=250,
                                 height=100,
                                 border_width=1,
                                 border_color='blue',
                                 corner_radius=10)
        sim_frame.pack(expand=True,padx=15,fill="x")
        ctk.CTkLabel(sim_frame, font=normal_font, text="This is how similar 2 images must be to be marked for deletion. I recommend 0.97 to 0.99:").pack(pady=5)
        self.sim_slider = ctk.CTkSlider(sim_frame, width=250, height=20, command=self.similarity_slider)
        self.sim_slider.pack(padx=10)
        self.similarity_label = ctk.CTkLabel(sim_frame, width=50, height=20, font=normal_font, text="")
        self.similarity_label.pack(pady=5)
    
    def curate_images(self):
    # Ensure the dataset directory is set
        if not step1_completed:
            self.event.emit(text="Dataset directory not set. Please set up your project first.")
            return
        try:
            curate_images = CurateImages(event=self.event)
            curate_images.start_curating(dataset_dir=dataset_dir, sim_threshold=self.sim_slider.get())
        except Exception as e:
            self.event.emit(text=f"Error during curation: {e}")
            print(f"Error ending curation: {e}")


    def end_curation(self) -> None:
        try:
            curate_images = CurateImages(event=self.event)
            curate_images.end_curation(dataset_dir=dataset_dir, project_subfolder=project_subfolder)
            # curate_images.finish_curating(images_folder=dataset_base_dir, project_subfolder=project_subfolder)
        except Exception as e:
            self.event.emit(text=f"Error ending curation: {e}")
            print(f"Error ending curation: {e}")
             
             
    def similarity_slider(self, value):
        self.similarity_label.configure(text=f"{value}")



class ScrollableTagImagesTab(ctk.CTkScrollableFrame):
    def __init__(self, master: Any, event: Event, width: int = 200, height: int = 200, corner_radius: int | str | None = None, border_width: int | str | None = None, bg_color: str | Tuple[str, str] = "transparent", fg_color: str | Tuple[str, str] | None = None, border_color: str | Tuple[str, str] | None = None, scrollbar_fg_color: str | Tuple[str, str] | None = None, scrollbar_button_color: str | Tuple[str, str] | None = None, scrollbar_button_hover_color: str | Tuple[str, str] | None = None, label_fg_color: str | Tuple[str, str] | None = None, label_text_color: str | Tuple[str, str] | None = None, label_text: str = "", label_font: tuple | CTkFont | None = None, label_anchor: str = "center", orientation: Literal['vertical', 'horizontal'] = "vertical"):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, scrollbar_fg_color, scrollbar_button_color, scrollbar_button_hover_color, label_fg_color, label_text_color, label_text, label_font, label_anchor, orientation)
        self.event:Event = event
        
        self.show_tags_event: Event = Event()
        self.show_tags_event.subscribe(self.on_tag_show_event)
        
        ctk.CTkLabel(self,font=title_font,
                     text="Tag Images").pack(pady=15, fill="both", expand=True)
        
        ctk.CTkLabel(self, font=normal_font,
                     width=300, 
                     text="We will be using AI to automatically tag your images, specifically Waifu Diffusion in the case of anime and BLIP in the case of photos.\nGiving tags/captions to your images allows for much better training.\nDepending on your PC and the amount of images, this may take a while...").pack(pady=5, fill="both")
        
        self.set_first_frame()
        
        self.set_tags_frame()
        
        self.set_second_frame()
        
        self.set_third_frame()

        ctk.CTkButton(self, text="Start Tagging Images", width=200, height=32, corner_radius=10, border_width=1,
                    border_color='green', command=self.on_button_pressed).pack(pady=10)

    def set_third_frame(self):
        third_frame = ctk.CTkFrame(self,corner_radius=10,width=400, height=250, border_width=1, border_color='green')
        third_frame.pack(pady=5,expand=True, fill="x")
        
        ctk.CTkLabel(third_frame, font=normal_font,
                     text="These options only work on the Photo Captions Option.").pack(pady=5)
        self.max_length_entry = ctk.CTkEntry(third_frame,
                                             font=normal_font,
                                             width=250,
                                             height=30,
                                             placeholder_text="The max length of tokens/words in each caption. Default is 75")
        self.max_length_entry.pack(pady=5)
        self.min_length_entry = ctk.CTkEntry(third_frame, 
                                             font=normal_font,
                                             width=250,
                                             height=30,
                                             placeholder_text="The min length of tokens/words in each caption. Default is 10")
        self.min_length_entry.pack(pady=5)

    def set_second_frame(self):
        second_frame = ctk.CTkFrame(self,corner_radius=10,width=400, height=300, border_width=1, border_color='green')
        second_frame.pack(pady=5,expand=True, fill="x")
        
        ctk.CTkLabel(second_frame, font=normal_font, 
                     text="These options only work on the Anime Tags Option.\nBelow you can blacklist tags that you DON'T want in your dataset. Leave empty for default blacklisted tags.").pack(pady=5)
        self.blacklist_tags_entry = ctk.CTkEntry(second_frame,
                                                 width=250,
                                                 height=30,
                                                 font=normal_font,
                                                 placeholder_text="bangs, breasts, multicolored hair, two-tone hair, gradient hair, virtual youtuber, official alternate costume, official alternate hairstyle, official alternate hair length, alternate costume, alternate hairstyle, alternate hair length, alternate hair color")
        self.blacklist_tags_entry.pack(pady=2)
        ctk.CTkLabel(second_frame,
                     width=250,
                     text="The threshold is the minimum level of confidence the tagger must have in order to include a tag.\nLower threshold = More tags. Recommended 0.35 to 0.5",
                     font=normal_font).pack(pady=5)
        self.tag_threshold_entry = ctk.CTkSlider(second_frame,
                                                 from_=0,
                                                 width=250,
                                                 height=20, 
                                                 to=1,
                                                 command=self.on_slider_changed)
        self.tag_threshold_entry.pack(pady=2)
        self.tag_threshold_label = ctk.CTkLabel(second_frame,
                                                width=250,
                                                font=normal_font,
                                                text="")
        self.tag_threshold_label.pack(pady=5)

    def set_tags_frame(self):
        tag_frame = ctk.CTkScrollableFrame(self, 
                                           corner_radius=10, 
                                           width=200, 
                                           height=200,
                                           label_text="Top Tags on Dataset:",
                                           label_font=normal_font)
        tag_frame.pack(pady=5, expand=True,fill="x")
        self.tags_label = ctk.CTkLabel(master=tag_frame,
                                       font=normal_font,
                                       text="")
        self.tags_label.pack(pady=2,fill="x")

    def set_first_frame(self):
        first_frame = ctk.CTkFrame(master=self,corner_radius=10,width=400, height=300, border_width=1, border_color='green')
        first_frame.pack(pady=5, expand=True,fill="x", side="top")
        
        tag_images_options = ["Anime Tags", "Photo Captions"]
        self.tagging_options_menu = ctk.CTkOptionMenu(master=first_frame,values=tag_images_options)
        self.tagging_options_menu.pack(pady=5, side="top")
        
        child_first_frame = ctk.CTkFrame(first_frame, corner_radius=10,width=300, height=200, border_width=1, border_color='green')
        child_first_frame.pack(padx=10, expand=True, fill="x")
        
        self.force_download_checkbox = ctk.CTkCheckBox(master=child_first_frame,
                                                       text="Force Download of Tagging Model",
                                                       font=normal_font,
                                                       corner_radius=10)
        self.force_download_checkbox.pack(pady=5)
        
        self.batch_size_entry = ctk.CTkEntry(master=child_first_frame,
                                             font=normal_font,
                                             width=160,
                                             placeholder_text="Batch Size. Default is 8.")
        self.batch_size_entry.pack(pady=5)
        
        self.tags_to_show_entry = ctk.CTkEntry(master=child_first_frame,
                                               font=normal_font,
                                               width=250,
                                               placeholder_text="The amount of tags to show once the captioning is done.")
        self.tags_to_show_entry.pack(pady=5)
        
    def on_slider_changed(self, value):
        self.tag_threshold_label.configure(text=f"{value}")
    
    def on_button_pressed(self):
        asyncio.run(self.start_image_tagging())
    
    async def start_image_tagging(self) -> None:
        if not step1_completed:
            self.event.emit("Dataset Directory not set. Please set one in the Project Setup tab first...")
            return
        dataset_tagger = DatasetTagger(event=self.event, show_tags_event=self.show_tags_event)
        tagging_option = self.tagging_options_menu.get()
        if tagging_option == "Photo Captions":
            self.run_photo_captions(train_data_dir=dataset_dir, tagger= dataset_tagger,
                                    max_length=self.max_length_entry.get(), min_length=self.min_length_entry.get())
        else:
            await self.run_anime_tagging(train_data_dir=dataset_dir, tagger=dataset_tagger, 
                                threshold=self.tag_threshold_entry.get(),
                                blacklist_tags=self.blacklist_tags_entry.get(),
                                tags_to_show=self.tags_to_show_entry.get())

    async def run_anime_tagging(self, tagger: DatasetTagger,train_data_dir, batch_size="8",
                        threshold=0.35, blacklist_tags:str="", tags_to_show:str="50") -> None:
        
        await tagger.caption_anime_images(train_data_dir=train_data_dir,batch_size=batch_size,  
                                    tag_threshold=threshold,
                                    blacklist_tags=blacklist_tags,
                                    tags_to_show=tags_to_show)

    def run_photo_captions(self, tagger: DatasetTagger, train_data_dir, caption_weights="", batch_size:str="8", max_length:str="75", min_length:str="10",
                        beam_search=True, debug=False, recursive=False):
        tagger.caption_photo_images(train_data_dir, caption_weights=caption_weights,batch_size=batch_size,
                            max_length=max_length, min_length=min_length,recursive=recursive, beam_search=beam_search, debug=debug)
    
    def on_tag_show_event(self, text):
        self.tags_label.configure(text=text)


class CurateDatasetTagsTab(ctk.CTkFrame):
    def __init__(self, master: Any, event:Event, width: int = 200, height: int = 200, corner_radius: int | str | None = None, border_width: int | str | None = None, bg_color: str | Tuple[str, str] = "transparent", fg_color: str | Tuple[str, str] | None = None, border_color: str | Tuple[str, str] | None = None, background_corner_colors: Tuple[str | Tuple[str, str]] | None = None, overwrite_preferred_drawing_method: str | None = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)
        
        self.event = event
        self.on_modified_tags_event = Event()
        self.on_modified_tags_event.subscribe(self.on_dataset_tags_modified)
        
        ctk.CTkLabel(self,font=title_font,
                     text="Curate Dataset Tags").pack(pady=15, fill="both", expand=True)
        
        ctk.CTkLabel(self, font=normal_font,
                     width=300, 
                     text="Modify your dataset's tags. You can run this cell multiple times with different parameters.\n Put an activation tag at the start of every text file. This is useful to make learning better and activate your Lora easier. Set keep_tokens to 1 when training.\nCommon tags that are removed such as hair color, etc. will be 'absorbed' by your activation tag.").pack(pady=5, fill="both")
        
        self.set_first_frame()
        
        self.set_second_frame()
        
        ctk.CTkButton(master=self, width=160,
                      height=30,
                      corner_radius=10,
                      border_color='green',
                      border_width=1,
                      font=normal_font,
                      text="Start Curating Tags",
                      command=self.on_button_pressed).pack(pady=5)
        
    def set_second_frame(self):
        second_frame = ctk.CTkScrollableFrame(master=self,
                                              corner_radius=10,
                                              border_color='green',
                                              border_width=1,
                                              height=150,
                                              label_font=normal_font,
                                              label_text="New Activation Tag(s):")
        second_frame.pack(pady=5,fill="x", expand=True)
        
        self.modified_dataset_tags_label = ctk.CTkLabel(master=second_frame,
                                                        font=normal_font,
                                                        text="")
        self.modified_dataset_tags_label.pack(pady=5)

    def set_first_frame(self):
        first_frame = ctk.CTkFrame(self, corner_radius=10, border_color='green',border_width=1)
        first_frame.pack(pady=10, fill="x", expand=True)
        
        self.activation_tag_entry = ctk.CTkEntry(master=first_frame,
                                                 corner_radius=10,
                                                 width=250,
                                                 font=normal_font,
                                                 placeholder_text="Place your activation tag(s) here...")
        self.activation_tag_entry.pack(pady=5,expand=True)
        
        self.remove_tags_entry = ctk.CTkEntry(master=first_frame,
                                              corner_radius=10,
                                              width=250,
                                              font=normal_font,
                                              placeholder_text="Put the tag(s) you wanna remove here.")
        self.remove_tags_entry.pack(pady=5, expand=True)
    
    def on_dataset_tags_modified(self, text:str):
        self.modified_dataset_tags_label.configure(text=text)

    def on_button_pressed(self):
        if not step1_completed:
            self.event.emit("Dataset Directory not set. Please set one in the Project Setup tab first...")
            return
        
        tags_curator = DatasetTagCurator(event=self.event,show_modified_tags_event=self.on_modified_tags_event)
        tags_curator.curate_tags(images_folder=dataset_dir,global_activation_tag=self.activation_tag_entry.get(), remove_tags=self.remove_tags_entry.get())


class ExtrasTab(ctk.CTkScrollableFrame):
    def __init__(self, master: Any, event:Event, width: int = 200, height: int = 200, corner_radius: int | str | None = None, border_width: int | str | None = None, bg_color: str | Tuple[str, str] = "transparent", fg_color: str | Tuple[str, str] | None = None, border_color: str | Tuple[str, str] | None = None, scrollbar_fg_color: str | Tuple[str, str] | None = None, scrollbar_button_color: str | Tuple[str, str] | None = None, scrollbar_button_hover_color: str | Tuple[str, str] | None = None, label_fg_color: str | Tuple[str, str] | None = None, label_text_color: str | Tuple[str, str] | None = None, label_text: str = "", label_font: tuple | CTkFont | None = None, label_anchor: str = "center", orientation: Literal['vertical', 'horizontal'] = "vertical"):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, scrollbar_fg_color, scrollbar_button_color, scrollbar_button_hover_color, label_fg_color, label_text_color, label_text, label_font, label_anchor, orientation)
        self.event = event
        self.top_tags_event = Event()
        self.top_tags_event.subscribe(self.on_top_tags)
        self.subtitle_font = ctk.CTkFont(family="The Bold Font", size=21)
        
        ctk.CTkLabel(self,font=title_font,
                     text="Extras").pack(pady=15, fill="both", expand=True)
        
        ctk.CTkLabel(self, font=normal_font,
                     width=300, 
                     text="Just some miscelaneous that can be useful.").pack(pady=5, fill="both")
        
        self.set_first_frame()
        
        self.set_second_frame()
        
        ctk.CTkButton(master=self,
                      width=180,
                      corner_radius=10,
                      border_color='green',
                      border_width=1,
                      font=normal_font,
                      text="Analyze Tags",
                      command=self.on_button_pressed).pack(pady=5)
        
        self.set_count_dataset_frame()
        
        self.set_delete_files_frame()

    def set_delete_files_frame(self):
        delete_files_frame = ctk.CTkFrame(master=self,
                                          width=250,
                                          corner_radius=10,
                                          border_color='green',
                                          border_width=2)
        delete_files_frame.pack(pady=15, padx=10,fill='x',expand=True)
        
        ctk.CTkLabel(master=delete_files_frame,
                     font=self.subtitle_font,
                     text="Delete Non Images Files").pack(pady=8,expand=True)
        
        ctk.CTkButton(master=delete_files_frame,
                      width=250,
                      height=32,
                      corner_radius=10,
                      border_color='green',
                      fg_color='red',
                      text_color='black',
                      border_width=1,
                      font=normal_font,
                      text="WARNING!! This will delete all the non-images files on the folder.",
                      command=self.on_delete_button_pressed).pack(pady=10, padx=10)
        
    def set_count_dataset_frame(self):
        count_frame = ctk.CTkFrame(master=self,
                                   width=250,
                                   corner_radius=10,
                                   border_color='green',
                                   border_width=2)
        count_frame.pack(pady=15, padx=10, expand=True,fill="x")
        
        ctk.CTkLabel(master=count_frame,
                     font=self.subtitle_font,
                     text="Count Files in Dataset").pack(pady=8,expand=True)
        
        ctk.CTkButton(master=count_frame,
                      width=180,
                      height=32,
                      corner_radius=10,
                      border_color='green',
                      border_width=1,
                      font=normal_font,
                      text="Start Counting...",
                      command=self.on_count_button_pressed).pack(pady=15, padx=10)

    def set_first_frame(self):
        first_frame = ctk.CTkFrame(master=self,
                                   corner_radius=10,
                                   height=150)
        first_frame.pack(pady=5, expand=True,fill="both")
        
        self.show_tags_entry = ctk.CTkEntry(master=first_frame,
                                            corner_radius=10,
                                            font=normal_font,
                                            placeholder_text="input how many tags you want the UI to display at once, default is 50 tags...")
        self.show_tags_entry.pack(pady=10,fill="x")

    def set_second_frame(self):
        second_frame = ctk.CTkScrollableFrame(master=self,
                                   corner_radius=10,
                                   height=150,
                                   label_font=normal_font,
                                   label_text="Analyzed Tags:")
        second_frame.pack(pady=5, expand=True,fill="both")
        
        self.top_tags_label = ctk.CTkLabel(master=second_frame,
                                           font=normal_font,
                                           text="")
        self.top_tags_label.pack(pady=5, fill="x")
    
    def on_count_button_pressed(self):
        if not step1_completed:
            self.event.emit("Dataset Directory not set. Please set one in the Project Setup tab first...")
            return
        
        analyze_tags = ExtrasDataset(event=self.event, top_tags_event=self.top_tags_event)
        analyze_tags.count_datasets(images_folder=dataset_dir)
    
    def on_delete_button_pressed(self):
        if not step1_completed:
            self.event.emit("Dataset Directory not set. Please set one in the Project Setup tab first...")
            return
        
        analyze_tags = ExtrasDataset(event=self.event, top_tags_event=self.top_tags_event)
        analyze_tags.delete_non_image_files(images_folder=dataset_dir)
    
    def on_button_pressed(self):
        if not step1_completed:
            self.event.emit("Dataset Directory not set. Please set one in the Project Setup tab first...")
            return
            
        analyze_tags = ExtrasDataset(event=self.event, top_tags_event=self.top_tags_event)
        
        analyze_tags.analyze_tags(images_folder=dataset_dir, show_top_tags_text=self.show_tags_entry.get())
    
    def on_top_tags(self,text:str):
        self.top_tags_label.configure(text=text)