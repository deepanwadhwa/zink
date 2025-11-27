try:
    from gliner import GLiNER
except ImportError:
    GLiNER = None
import warnings
import concurrent.futures
warnings.filterwarnings("ignore")


class EntityExtractor:
    def __init__(
        self, model_name="deepanwa/NuNerZero_onnx"
    ):  
        # previous model - numind/NuNerZero
        if GLiNER is None:
            self.model = None
        else:
            self.model = GLiNER.from_pretrained(
                model_name, load_onnx_model=True, load_tokenizer=True
            )
        self.model_name = model_name
        # NuZero requires lower-cased labels.
        self.labels = ["person", "date", "location"]
    
    def _process_chunk_thread_safe(self, chunk):
        """
        This worker runs in a thread and accesses the class's single model instance.
        """
        # --- Pass 1: Normal threshold on the original text ---
        pass1_entities = self.model.predict_entities(text=self.thread_text, labels=chunk, threshold=0.5)

        # --- Temporary Masking for Pass 2 ---
        temp_mutable_text = list(self.thread_text)
        for entity in pass1_entities:
            for i in range(entity['start'], entity['end']):
                temp_mutable_text[i] = ' '
        masked_text_for_pass2 = "".join(temp_mutable_text)

        # --- Pass 2: High threshold on the temporarily masked text ---
        pass2_entities = self.model.predict_entities(text=masked_text_for_pass2, labels=chunk, threshold=0.9)
        
        return pass1_entities + pass2_entities

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
            
            if _ == 0:
                # 1. Call the model on the current version of the text
                newly_found_entities = self.model.predict_entities(current_text_to_process, predict_labels)
            else:
                # increased threshold for subsequent passes
                # This helps in focusing on more confident predictions after initial masking.
                # The threshold can be adjusted based on the model's performance.
                newly_found_entities = self.model.predict_entities(current_text_to_process, predict_labels, threshold=0.9)


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

    # def predict_thorough(self, text, labels=None, max_passes=2):
    #     """
    #     Performs a more exhaustive, multi-pass entity extraction by processing labels in smaller batches.
    #     This can improve accuracy when many different label types are specified but is more computationally intensive.

    #     Parameters:
    #         text (str): The input text.
    #         labels (list of str, optional): Entity labels to predict. Defaults to the class's default labels.
    #         max_passes (int): The maximum number of passes to run for each chunk of labels.
                
    #     Returns:
    #         list of dict: A list of all unique entities found across all passes and all label chunks.
    #     """
    #     if labels is not None:
    #         predict_labels = [label.lower() for label in labels]
    #     else:
    #         predict_labels = self.labels

    #     if not predict_labels:
    #         return []

    #     all_entities = []
    #     processed_spans = set()
        
    #     mutable_text_list = list(text)

    #     # Chunk the labels into groups of 3 for more focused prediction
    #     label_chunk_size = 3
    #     label_chunks = [predict_labels[i:i + label_chunk_size] for i in range(0, len(predict_labels), label_chunk_size)]

    #     for chunk in label_chunks:
    #         # For each chunk of labels, run the multi-pass prediction logic
    #         for pass_num in range(max_passes):
    #             current_text_to_process = "".join(mutable_text_list)
                
    #             threshold = 0.5 if pass_num == 0 else 0.9
                
    #             newly_found_entities = self.model.predict_entities(current_text_to_process, chunk, threshold=threshold)

    #             if not newly_found_entities:
    #                 break
                
    #             unique_new_entities = []
    #             for ent in newly_found_entities:
    #                 span = (ent['start'], ent['end'])
    #                 if span not in processed_spans:
    #                     unique_new_entities.append(ent)
    #                     processed_spans.add(span)
                
    #             if not unique_new_entities:
    #                 break

    #             all_entities.extend(unique_new_entities)

    #             for entity in unique_new_entities:
    #                 for i in range(entity['start'], entity['end']):
    #                     mutable_text_list[i] = ' '
        
    #     all_entities.sort(key=lambda x: x['start'])
    #     return all_entities
    def predict_thorough(self, text, labels=None):
        """
        Performs a highly detailed entity extraction using a hybrid approach. For each
        chunk of labels, it runs a two-pass process with internal, temporary masking
        to find a comprehensive set of entities. It then resolves overlaps between
        all found entities across all chunks by keeping the label with the highest
        confidence score for each unique text span.

        Parameters:
            text (str): The input text.
            labels (list of str, optional): Entity labels to predict.

        Returns:
            list of dict: A list of the highest-confidence entities for each unique span.
        """
        if labels is not None:
            predict_labels = [label.lower() for label in labels]
        else:
            predict_labels = self.labels

        if not predict_labels:
            return []

        # Final dictionary to hold the best entity for each span across all chunks
        best_entities_by_span = {}

        label_chunk_size = 3
        label_chunks = [predict_labels[i:i + label_chunk_size] for i in range(0, len(predict_labels), label_chunk_size)]

        # Process one chunk of labels at a time
        for chunk in label_chunks:
            
            # --- Pass 1: Normal threshold on the original text ---
            pass1_entities = self.model.predict_entities(text, chunk, threshold=0.5)

            # --- Temporary Masking for Pass 2 ---
            temp_mutable_text = list(text)
            for entity in pass1_entities:
                for i in range(entity['start'], entity['end']):
                    temp_mutable_text[i] = ' '
            masked_text_for_pass2 = "".join(temp_mutable_text)

            # --- Pass 2: High threshold on the temporarily masked text ---
            pass2_entities = self.model.predict_entities(masked_text_for_pass2, chunk, threshold=0.9)

            # Combine all entities found just for this chunk
            entities_from_this_chunk = pass1_entities + pass2_entities

            # --- Conflict Resolution: Update the master dictionary ---
            for entity in entities_from_this_chunk:
                span = (entity['start'], entity['end'])
                existing_entity = best_entities_by_span.get(span)

                if not existing_entity or entity['score'] > existing_entity['score']:
                    best_entities_by_span[span] = entity

        # Convert the dictionary of best entities back to a list and sort
        final_entities = list(best_entities_by_span.values())
        final_entities.sort(key=lambda x: x['start'])
        
        return final_entities
    
    def predict2(self, text, labels=None):
        """
        Performs a highly detailed entity extraction using a MEMORY-EFFICIENT 
        THREAD-BASED parallel approach.
        """
        if labels is not None:
            predict_labels = [label.lower() for label in labels]
        else:
            predict_labels = self.labels

        if not predict_labels:
            return []
        
        # Storing text on self to make it accessible to the thread worker method
        self.thread_text = text

        label_chunk_size = 2
        label_chunks = [predict_labels[i:i + label_chunk_size] for i in range(0, len(predict_labels), label_chunk_size)]

        results_from_all_chunks = []
        # Use a ThreadPoolExecutor, which shares memory.
        # You can control the number of threads with max_workers.
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # The map function distributes the label chunks to threads in the pool.
            # Each thread will call self._process_chunk_thread_safe.
            results_from_all_chunks = list(executor.map(self._process_chunk_thread_safe, label_chunks))

        # --- REDUCE PHASE (Unchanged) ---
        best_entities_by_span = {}
        all_found_entities = [entity for sublist in results_from_all_chunks for entity in sublist]

        for entity in all_found_entities:
            span = (entity['start'], entity['end'])
            existing_entity = best_entities_by_span.get(span)

            if not existing_entity or entity['score'] > existing_entity['score']:
                best_entities_by_span[span] = entity

        final_entities = list(best_entities_by_span.values())
        final_entities.sort(key=lambda x: x['start'])
        
        # Clean up the temporary attribute
        del self.thread_text
        
        return final_entities
    


_DEFAULT_EXTRACTOR = EntityExtractor()
