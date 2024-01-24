import os
import shutil

import numpy as np
import fiftyone as fo
import fiftyone.zoo as foz
from fiftyone import ViewField as F
from sklearn.metrics.pairwise import cosine_similarity
from event import Event

dataset: fo.Dataset
session: fo.Session

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
            dataset = fo.Dataset.from_images_dir(dataset_dir)
            model = foz.load_zoo_model(model_name)
            embeddings = dataset.compute_embeddings(model, batch_size=batch_size)

            batch_embeddings = np.array_split(embeddings, batch_size)
            similarity_matrices = []
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
            dataset.save()
            session = fo.launch_app(dataset)
            self.event.emit(f"Session launched:\n{session}")


    def end_curation(self, dataset_dir:str):
        try:
            if session:
                # Remove samples tagged for deletion
                marked = [s for s in dataset if "delete" in s.tags]
                dataset.remove_samples(marked)

                # Export the curated dataset to a temporary directory
                temp_suffix = "_temp"
                temp_export_dir = dataset_dir + temp_suffix
                dataset.export(export_dir=temp_export_dir, dataset_type=fo.types.ImageDirectory)

                session.refresh()
                fo.close_app()

                # Remove the original directory
                if os.path.exists(dataset_dir):
                    shutil.rmtree(dataset_dir)

                os.rename(temp_export_dir, dataset_dir)

                self.event.emit(f"Removed {len(marked)} images from dataset. You now have {len(os.listdir(dataset_dir))} images.")
        except Exception as e:
            self.event.emit(f"Error ending curation: {e}")
