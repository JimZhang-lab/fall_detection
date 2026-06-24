from ultralytics import YOLO

def train_model(data_yaml_path, model_config_path, epochs=50):
    try:
        model = YOLO(model_config_path)
        model.train(
            data=data_yaml_path,
            epochs=epochs,
            imgsz=640,
            batch=16,
            project="runs",
            name="fall_train"
        )
        return True, "OK"
    except Exception as e:
        return False, str(e)