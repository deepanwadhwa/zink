from gliner import GLiNER
import warnings

warnings.filterwarnings("ignore")


class EntityExtractor:
    def __init__(
        self, model_name="deepanwa/NuNerZero_onnx"
    ):  # previous model - numind/NuNerZero
        self.model = GLiNER.from_pretrained(
            model_name, load_onnx_model=True, load_tokenizer=True
        )
        # NuZero requires lower-cased labels.
        self.labels = ["person", "date", "location"]

    # def predict(self, text, labels=None):
    #     """
    #     Predict entities in the given text.

    #     Parameters:
    #         text (str): The input text.
    #         labels (list of str, ): Only entities with these labels will be returned.
    #             If None, all detected entities are returned.
                
    #     Returns:
    #         list of dict: A list of dictionaries, each containing 'start', 'end', 'label', and 'text'.
    #     """
    #     if labels is not None:
    #         labels = [label.lower() for label in labels]
    #     else:
    #         labels = self.labels
        
    #     return self.model.predict_entities(text, labels)

    def predict(self, text, labels=None, max_passes=2):
        """
        Iteratively finds entities by masking found entities and re-running the model.

        Parameters:
            text (str): The input text.
            labels (list of str, optional): Entity labels to predict. Defaults to None.
            max_passes (int): A safeguard to prevent potential infinite loops.
                
        Returns:
            list of dict: A list of all unique entities found across all passes.
        """
        if labels is not None:
            predict_labels = [label.lower() for label in labels]
        else:
            predict_labels = self.labels

        all_entities = []
        processed_spans = set()
        
        # Use a list of characters for easy replacement
        mutable_text_list = list(text)

        for _ in range(max_passes):
            current_text_to_process = "".join(mutable_text_list)
            
            # 1. Call the model on the current version of the text
            newly_found_entities = self.model.predict_entities(current_text_to_process, predict_labels)

            # If the model finds nothing, we can stop
            if not newly_found_entities:
                break
            
            # Filter out any entities we've already processed to avoid loops
            unique_new_entities = []
            for ent in newly_found_entities:
                span = (ent['start'], ent['end'])
                if span not in processed_spans:
                    unique_new_entities.append(ent)
                    processed_spans.add(span)
            
            # If there were no *genuinely* new entities, stop
            if not unique_new_entities:
                break

            # 2. Add the unique new finds to our master list
            all_entities.extend(unique_new_entities)

            # 3. "Mask" the found entities by replacing them with spaces
            # This preserves the indices for the next pass.
            for entity in unique_new_entities:
                for i in range(entity['start'], entity['end']):
                    mutable_text_list[i] = ' '
        
        # Sort the final combined list by start position
        all_entities.sort(key=lambda x: x['start'])
        return all_entities


_DEFAULT_EXTRACTOR = EntityExtractor()
