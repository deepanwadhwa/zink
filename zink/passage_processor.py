import threading
from zink import redact as core_redact, replace as core_replace, replace_with_my_data as core_replace_with_my_data

def _process_passage(passage, method, **kwargs):
    """
    Helper function that splits a passage into sentences and processes each sentence concurrently.
    
    Parameters:
      passage (str): The full text passage to process.
      method (str): One of "redact", "replace", or "replace_with_my_data".
      kwargs: Additional keyword arguments to pass to the core function.
    
    Returns:
      str: The combined processed passage.
    """
    # A basic sentence splitter: split on period, remove extra whitespace, and add period back.
    sentences = [sentence.strip() + "." for sentence in passage.split(".") if sentence.strip()]
    results = [None] * len(sentences)

    def worker(idx, sentence):
        if method == "redact":
            # For redact, pass categories, placeholder, and use_cache.
            result = core_redact(sentence,
                                 categories=kwargs.get("categories", ("person", "date", "location")),
                                 placeholder=kwargs.get("placeholder"),
                                 use_cache=kwargs.get("use_cache", True))
        elif method == "replace":
            # For replace, pass categories, user_replacements, ensure_consistency, and use_cache.
            result = core_replace(sentence,
                                  categories=kwargs.get("categories", ("person", "date", "location")),
                                  user_replacements=kwargs.get("user_replacements"),
                                  ensure_consistency=kwargs.get("ensure_consistency", True),
                                  use_cache=kwargs.get("use_cache", True))
        elif method == "replace_with_my_data":
            # For replace_with_my_data, caching is not used.
            result = core_replace_with_my_data(sentence,
                                               categories=kwargs.get("categories", ("person", "date", "location")),
                                               user_replacements=kwargs.get("user_replacements"),
                                               ensure_consistency=kwargs.get("ensure_consistency", True))
        else:
            raise ValueError("Invalid method. Use 'redact', 'replace', or 'replace_with_my_data'.")
        results[idx] = result.anonymized_text

    threads = []
    for i, sentence in enumerate(sentences):
        t = threading.Thread(target=worker, args=(i, sentence))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    return " ".join(results)


def redact(passage, categories=("person", "date", "location"), placeholder=None, use_cache=True):
    """
    Process a passage using the 'redact' method.
    
    Parameters:
      passage (str): The full text to process.
      categories (tuple): Categories to filter entities (default: ("person", "date", "location")).
      placeholder (str): Optional placeholder to replace entities.
      use_cache (bool): Whether to use caching (default: True).
      
    Returns:
      str: The processed passage.
    """
    return _process_passage(passage, method="redact",
                            categories=categories,
                            placeholder=placeholder,
                            use_cache=use_cache)


def replace(passage, categories=("person", "date", "location"), user_replacements=None,
            ensure_consistency=True, use_cache=True):
    """
    Process a passage using the 'replace' method.
    
    Parameters:
      passage (str): The full text to process.
      categories (tuple): Categories to filter entities (default: ("person", "date", "location")).
      user_replacements (dict): A dictionary of user-defined replacements.
      ensure_consistency (bool): Whether to enforce consistency (default: True).
      use_cache (bool): Whether to use caching (default: True).
      
    Returns:
      str: The processed passage.
    """
    return _process_passage(passage, method="replace",
                            categories=categories,
                            user_replacements=user_replacements,
                            ensure_consistency=ensure_consistency,
                            use_cache=use_cache)


def replace_with_my_data(passage, categories=("person", "date", "location"), user_replacements=None,
                         ensure_consistency=True):
    """
    Process a passage using the 'replace_with_my_data' method.
    
    Note: Caching is not applied for this method.
    
    Parameters:
      passage (str): The full text to process.
      categories (tuple): Categories to filter entities (default: ("person", "date", "location")).
      user_replacements (dict): A dictionary of user-defined replacements.
      ensure_consistency (bool): Whether to enforce consistency (default: True).
      
    Returns:
      str: The processed passage.
    """
    return _process_passage(passage, method="replace_with_my_data",
                            categories=categories,
                            user_replacements=user_replacements,
                            ensure_consistency=ensure_consistency)
