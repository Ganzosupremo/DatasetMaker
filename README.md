# DatasetMaker
 An app version of the DatasetMaker by [Hollowstrawberry](https://colab.research.google.com/github/hollowstrawberry/kohya-colab/blob/main/Dataset_Maker.ipynb#scrollTo=DCgE3LXsoAJD)

## Installation

 You need to install [python 3.10.](https://www.python.org/downloads/release/python-3109/) in order for this program to work.

 Then download this repo, you can clone it https://github.com/Ganzosupremo/DatasetMaker.git. Or download it as a zip file.

 That's it.

## How to Use

Double click the launch_app.bat file, it should open a terminal and start the app.

This app has 5 different tabs. I'll explain what each tab does, you can get more information inside the app.

### Project Setup

This tab is for setting up your project name, this will create a folder with the name of your chosing at the Pictures directory inside a Lora folder. The structure is like so ./Pictures/Loras/project_name. Btw you can specify subfolders with the same project name like so: ./Pictures/Loras/project_name/subfolder_name. The images will be saved in this subfolder.

### Scrape Images

We'll grab the images from [Gelbooru](https://gelbooru.com/index.php).
Just input the tags you want in the first field, and the app will do the rest.
You can also specify how many images you want to download in total in the second field.

### Image Curation

Next, we'll look for duplicated images and delete them from the dataset, you can adjust how similar two images must be for deletion with the slider.

### Tagging Images

Now, we'll tag the images, you can use waifu diffusion and blip captioning, depending on the type of your images.
Waifu diffusion is used for anime and blip captioning is usually used for photos.
You can specify the batch size on the first field.
In the second field you can specify how many tags will be showed to you in the UI after tagging, put 0 for every single one.
In the third field, you can blacklist the tags you don't want in your images, leave empty for default blacklisted tags.
With the slider you can adjust the level of confidence to add a tag, higher confidence means more tags.


### Curate Dataset's Tags

In this tab you can input an activation tag for your dataset as well remove the tags you don't want, like for example generic tags, i.e. hair color, hair length, eyes color, etc.

### Extras

In this tab you can analyze the tags in your dataset, count how many files you have in your dataset and delete the non-image files that could be found in your dataset.

# That's IT