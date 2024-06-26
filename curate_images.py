import os
import shutil
import time

import numpy as np
import fiftyone as fo
import fiftyone.zoo as foz
from fiftyone import ViewField as F
from sklearn.metrics.pairwise import cosine_similarity
from utils import Event

dataset: fo.Dataset
session: fo.Session


FIFTYONE_DATABASE_URI='mongodb://localhost:27017/DatasetMakerDB'

class CurateImages:
    def __init__(self, event):
        self.event: Event = event


    def start_curating(self, dataset_dir:str, sim_threshold:float=0.985) -> None:
        global session, dataset

        os.chdir(dataset_dir)
        
        model_name = "clip-vit-base32-torch"
        supported_types = (".png", ".jpg", ".jpeg")
        img_count = len(os.listdir(dataset_dir))
        batch_size = min(250, img_count)

        non_images = [f for f in os.listdir(dataset_dir) if not f.lower().endswith(supported_types)]
        if non_images:
            self.event.emit(f"💥 Error: Found non-image file {non_images[0]} - This program doesn't allow it. Sorry! Use the Extras to clean the folder.")
            return
        elif img_count == 0:
            self.event.emit(f"💥 Error: No images found in {dataset_dir}")
            return
        else:
            self.event.emit("\n💿 Analyzing dataset...\n")
            print("\n💿 Analyzing dataset...\n")
            dataset = fo.Dataset.from_images_dir(dataset_dir)
            model = foz.load_zoo_model(model_name)
            
            # embeddings = dataset.compute_embeddings(model, batch_size=batch_size)
            # print(embeddings.shape)

            # # Compute similarity matrices for each batch separately
            # similarity_matrix = np.zeros((len(embeddings), len(embeddings)))

            # for i in range(0, len(embeddings), batch_size):
            #     print(np.isnan(i).any())
            #     batch_end = min(i + batch_size, len(embeddings))
            #     batch_embeddings = embeddings[i:batch_end]
            #     batch_similarity = cosine_similarity(batch_embeddings)
            #     similarity_matrix[i:batch_end, i:batch_end] = batch_similarity

            # # Subtract the identity matrix to ignore self-similarity
            # np.fill_diagonal(similarity_matrix, 0)
    
            embeddings = dataset.compute_embeddings(model=model, batch_size=batch_size)

            batch_embeddings = np.array_split(embeddings, batch_size)
            similarity_matrices = []
            print(similarity_matrices)
            
            
            max_size_x = max(array.shape[0] for array in batch_embeddings)
            max_size_y = max(array.shape[1] for array in batch_embeddings)

            for i, batch_embedding in enumerate(batch_embeddings):
                similarity = cosine_similarity(batch_embedding)
                # Pad 0 for np.concatenate
                padded_array = np.zeros((max_size_x, max_size_y))
                padded_array[0:similarity.shape[0], 0:similarity.shape[1]] = similarity
                similarity_matrices.append(padded_array)

            similarity_matrix = np.concatenate(similarity_matrices, axis=0)
            similarity_matrix = similarity_matrix[0:embeddings.shape[0], 0:embeddings.shape[0]]

            similarity_matrix = cosine_similarity(embeddings)
            similarity_matrix -= np.identity(len(similarity_matrix))
            
            # for start_idx in range(0, len(embeddings), batch_size):
            #     end_idx = min(start_idx + batch_size, len(embeddings))
            #     batch_embeddings = embeddings[start_idx:end_idx]
            #     # Compute cosine similarity for the batch
            #     batch_similarity = cosine_similarity(batch_embeddings)
            #     # Place the result in the full matrix
            #     similarity_matrix[start_idx:end_idx, start_idx:end_idx] = batch_similarity

            # # Subtract the identity matrix to ignore self-similarity
            # np.fill_diagonal(similarity_matrix, 0)
            
            
            dataset.match(F("max_similarity") > sim_threshold)
            dataset.tags = ["delete", "has_duplicates"]

            id_map = [s.id for s in dataset.select_fields(["id"])]
            samples_to_remove = set()
            samples_to_keep = set()

            for idx, sample in enumerate(dataset):
                if sample.id not in samples_to_remove:
                    # Keep the first instance of two duplicates
                    samples_to_keep.add(sample.id)

                    dup_idxs = np.where(similarity_matrix[idx] > sim_threshold)[0]
                    for dup in dup_idxs:
                        # We kept the first instance so remove all other duplicates
                        samples_to_remove.add(id_map[dup])

                    if len(dup_idxs) > 0:
                        sample.tags.append("has_duplicates")
                        sample.save()
                else:
                    sample.tags.append("delete")
                    sample.save()

            sidebar_groups = fo.DatasetAppConfig.default_sidebar_groups(dataset)
            for group in sidebar_groups[1:]:
                group.expanded = False
            dataset.app_config.sidebar_groups = sidebar_groups
            fo.config.database_uri = FIFTYONE_DATABASE_URI
            dataset.save()
            session = fo.launch_app(dataset=dataset, desktop=False)
            
            self.event.emit(f"Session launched:\n{session}")
            print(f"Session launched:\n{session}")


    def finish_curating(self, images_folder:str, project_subfolder:str) -> None:
        marked = [s for s in dataset if "delete" in s.tags]
        dataset.remove_samples(marked)
        
        temp_suffix = "_temp"
        temp_subfolder = f"{images_folder}{temp_suffix}"
        os.makedirs(temp_subfolder)
        
        dataset.export(export_dir=temp_subfolder, dataset_type=fo.types.ImageDirectory)

        
        # Renaming and moving directories with os and shutil
        # temp_dir = f"{project_subfolder}{temp_suffix}"
        # os.rename(project_subfolder, temp_subfolder)
        shutil.move(temp_subfolder, images_folder)
        shutil.rmtree(temp_subfolder)

        session.refresh()
        fo.close_app()

        message = f"Removed {len(marked)} images from dataset. You now have {len(os.listdir(images_folder))} images."
        self.event.emit(message)
        print(message)
    
    
    def end_curation(self, dataset_dir:str, project_subfolder:str) -> None:
        def move_curated_dataset(dataset_dir:str, temp_dir:str):
            # Delete the contents of the original directory
            for filename in os.listdir(dataset_dir):
                file_path = os.path.join(dataset_dir, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            
            # Move contents from the temp directory to the original directory
            for filename in os.listdir(temp_dir):
                shutil.move(os.path.join(temp_dir, filename), dataset_dir)

            # Remove the now empty temp directory
            shutil.rmtree(temp_dir)
        
        if session:
            print("Ending session and deleting samples...")
            # Remove samples tagged for deletion
            marked = [s for s in dataset if "delete" in s.tags]
            dataset.remove_samples(marked)
            
            # Define the temporary and original directory paths
            original_dir = dataset_dir
            temp_dir = f"{original_dir}_temp"
            
            # Ensure the temporary directory exists
            os.makedirs(temp_dir, exist_ok=True)
            
            # Export the curated dataset to the temporary directory
            dataset.export(export_dir=temp_dir, dataset_type=fo.types.ImageDirectory)
            
            # Clear the dataset and close the session
            dataset.clear()
            session.close()
            fo.close_app()
            
            
            move_curated_dataset(dataset_dir=original_dir, temp_dir=temp_dir)
            # # Wait a bit for all file handles to be released
            # time.sleep(5)
            
            # # Remove the original directory and rename the temporary one
            # os.rename(original_dir, f"{original_dir}__")
            # os.rename(temp_dir, original_dir)

            # time.sleep(5)
            
            # shutil.rmtree(original_dir)
            
            # # Export the curated dataset to a temporary directory
            # temp_suffix = "_temp"
            # temp_dir = f"{dataset_dir}{temp_suffix}"
            # os.makedirs(temp_dir, exist_ok=True)
            
            # dataset.export(export_dir=temp_dir, dataset_type=fo.types.ImageDirectory)
            # dataset.clear()
            
            # session.close()
            # fo.close_app()
            
            # time.sleep(5)
            
            # # Remove the original dataset directory and rename the temporary one
            # shutil.rmtree(dataset_dir)  # Remove original directory
            # os.rename(temp_dir, dataset_dir)  # Rename temp back to dataset dir

            self.event.emit(f"Removed {len(marked)} images from dataset. You now have {len(os.listdir(dataset_dir))} images.")
            print(f"Removed {len(marked)} images from dataset. You now have {len(os.listdir(dataset_dir))} images.")
