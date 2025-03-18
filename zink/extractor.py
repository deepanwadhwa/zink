from gliner import GLiNER
import warnings
warnings.filterwarnings("ignore")

class EntityExtractor:
    def __init__(self, model_name="numind/NuNerZero"):
        self.model = GLiNER.from_pretrained(model_name)
        # NuZero requires lower-cased labels.
        self.labels = ["person", "date", "location"]

    def predict(self, text,labels=None):
        """
        Predict entities in the given text.
        Parameters:
            text (str): The input text.
            labels (list of str, optional): Only entities with these labels will be returned.
                If None, all detected entities are returned.
        Returns:
            list of dict: A list of dictionaries, each containing 'start', 'end', 'label', and 'text'.
        """
        if labels is not None:
            labels = [l.lower() for l in labels]
        else:
            labels = self.labels
        return self.model.predict_entities(text, labels)
    
_DEFAULT_EXTRACTOR = EntityExtractor()