from os import remove


class Event:
    def __init__(self) -> None:
        self.subscribers = []
        
    def subscribe(self, callback):
        self.subscribers.append(callback)
    
    def emit(self, text):
        for callback in self.subscribers:
            callback(text)
# wd-v1-4-swinv2-tagger-v2 / wd-v1-4-vit-tagger / wd-v1-4-vit-tagger-v2/ wd-v1-4-convnext-tagger / wd-v1-4-convnext-tagger-v2
DEFAULT_WD14_TAGGER_REPO = "SmilingWolf/wd-v1-4-convnext-tagger-v2"
DEFAULT_MODEL_DIR = "wd14_tagger_model"

class TaggerArgs:
    train_data_dir:str
    repo_id:str=DEFAULT_WD14_TAGGER_REPO
    model_dir:str=DEFAULT_MODEL_DIR
    force_download:bool=False
    batch_size:int=1
    max_data_loader_n_workers:int=2
    caption_extention=".txt"
    thresh:float=0.35
    general_threshold=0.0
    character_threshold=0.0
    recursive:bool=False
    remove_underscore:bool=True
    debug:bool=False
    undesired_tags:str=""
    frequency_tags:bool=False
    use_onnx:bool=True
    append_tags:bool=False
    caption_separator:str=", "
    
    def __init__(self, train_data_dir,repo_id=DEFAULT_WD14_TAGGER_REPO,
                 model_dir= DEFAULT_MODEL_DIR,
                 force_download=False,
                 batch_size=1,
                 max_data_loader_n_workers=2,
                 caption_extention=".txt",
                 thresh=0.35,
                 recursive=False,
                 remove_underscore=True,
                 debug=False,
                 undesired_tags="",
                 frequency_tags=False,
                 use_onnx=True,
                 append_tags=False,
                 caption_separator= ", ") -> None:
        
        self.train_data_dir =train_data_dir
        self.repo_id = repo_id
        self.model_dir = model_dir
        self.force_download =force_download
        self.batch_size = batch_size
        self.max_data_loader_n_workers = max_data_loader_n_workers
        self.caption_extention = caption_extention
        self.thresh = thresh
        self.recursive = recursive
        self.remove_underscore = remove_underscore
        self.debug = debug
        self.undesired_tags = undesired_tags
        self.frequency_tags = frequency_tags
        self.use_onnx = use_onnx
        self.append_tags = append_tags
        self.caption_separator = caption_separator
        
        