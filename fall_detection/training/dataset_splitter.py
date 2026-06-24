import os
import shutil
import random


def split_data(label_dir, image_dir, output_dir, train_ratio=0.8, val_ratio=0.2):
    try:
        all_labels = [f for f in os.listdir(label_dir) if f.endswith(".txt")]
        random.shuffle(all_labels)
        total = len(all_labels)
        n_train = int(train_ratio * total)

        splits = {
            "train": all_labels[:n_train],
            "val": all_labels[n_train:],
        }

        for split, files in splits.items():
            for t in ["images", "labels"]:
                os.makedirs(os.path.join(output_dir, t, split), exist_ok=True)
            for label_file in files:
                image_file = label_file.replace(".txt", ".jpg")
                shutil.copy(os.path.join(label_dir, label_file), os.path.join(output_dir, "labels", split, label_file))
                shutil.copy(os.path.join(image_dir, image_file), os.path.join(output_dir, "images", split, image_file))

        return True, "Done"
    except Exception as e:
        return False, str(e)