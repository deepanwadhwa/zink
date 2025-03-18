class EntityMerger:
    """
    Merges entities based on their labels and positions in the text.
    This class is designed to handle entities that are close together or have the same label,
    merging them into a single entity when appropriate.
    """
    def merge(self, entities, text):
        if not entities:
            return []
        merged = []
        current = entities[0].copy()
        current['count'] = 1

        for next_entity in entities[1:]:
            if (next_entity['label'] == current['label'] and 
                (next_entity['start'] == current['end'] or next_entity['start'] == current['end'] + 1)):
                # Merge text from current start to next entity's end
                current['text'] = text[current['start']: next_entity['end']].strip()
                current['end'] = next_entity['end']
                current['score'] = (
                    current['score'] * current['count'] + next_entity['score']
                ) / (current['count'] + 1)
                current['count'] += 1
            else:
                current.pop('count', None)
                merged.append(current)
                current = next_entity.copy()
                current['count'] = 1
        current.pop('count', None)
        merged.append(current)
        return merged
    # def merge(self, entities, text):
    #     if not entities:
    #         return []
    #     merged = []
    #     current = entities[0].copy()
    #     current['count'] = 1

    #     # Define a set of related labels that should be merged together.
    #     date_related = {"date", "year", "month", "day of the month", "month name", "monthname", "day"}

    #     for next_entity in entities[1:]:
    #         # Only merge if both are date-related and the gap between them is small (e.g., <= 5 characters).
    #         if ((current['label'].lower() in date_related and next_entity['label'].lower() in date_related) and
    #             (next_entity['start'] - current['end'] <= 5)):
    #             current['text'] = text[current['start']: next_entity['end']].strip()
    #             current['end'] = next_entity['end']
    #             current['score'] = (
    #                 current['score'] * current['count'] + next_entity['score']
    #             ) / (current['count'] + 1)
    #             current['count'] += 1
    #         else:
    #             current.pop('count', None)
    #             merged.append(current)
    #             current = next_entity.copy()
    #             current['count'] = 1
    #     current.pop('count', None)
    #     merged.append(current)
    #     return merged

