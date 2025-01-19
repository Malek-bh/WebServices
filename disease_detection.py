from transformers import ViTForImageClassification, ViTImageProcessor
from PIL import Image
import torch


model_name = "wambugu71/crop_leaf_diseases_vit"
model = ViTForImageClassification.from_pretrained(model_name)
feature_extractor = ViTImageProcessor.from_pretrained(model_name)

def predict_disease(image_file):
    try:
        image = Image.open(image_file).convert("RGB")
        inputs = feature_extractor(images=image, return_tensors="pt")

        outputs = model(**inputs)
        logits = outputs.logits
        predicted_class = torch.argmax(logits).item()

        # Get class labels
        labels = model.config.id2label
        return {"predicted_class": labels[predicted_class]}
    except Exception as e:
        return {"error": str(e)}
