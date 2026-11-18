from operator import index


def _score(entity):
    return entity.get("score", 1.0)


def _overlap_priority(entity):
    return (
        -_score(entity),
        entity["start"] - entity["end"],
        entity["label"],
        entity["start"],
    )


def _merge_overlaps(entities, text):
    winner = entities[0]
    start, end = winner["start"], winner["end"]
    for entity in entities[1:]:
        if entity["start"] >= end:
            yield {**winner, "start": start, "end": end, "text": text[start:end]}
            winner = entity
            start, end = entity["start"], entity["end"]
        else:
            end = max(end, entity["end"])
            if _overlap_priority(entity) < _overlap_priority(winner):
                winner = entity

    yield {**winner, "start": start, "end": end, "text": text[start:end]}


class EntityMerger:
    """Normalize overlapping predictions into non-overlapping spans.

    Each group of overlapping predictions covers the union of its original
    spans. It takes its label, score, and other metadata from the prediction
    with the highest confidence. Ties favor longer spans, then alphabetical
    label order, then earlier starts. Neighboring groups with the same label
    and at most one character between them are combined and their scores
    averaged.
    """

    def merge(self, entities, text):
        """Return new entity dictionaries in original text order.

        Start and end are integer character offsets, and end is exclusive.
        Raise ValueError if an entity is empty or outside the original text.
        """
        ordered = []
        for entity in entities:
            try:
                start, end = index(entity["start"]), index(entity["end"])
            except (KeyError, TypeError) as exc:
                raise ValueError(
                    "Entity span requires integer start and end offsets"
                ) from exc
            if not 0 <= start < end <= len(text):
                raise ValueError(
                    f"Entity span ({start}, {end}) is outside non-empty bounds"
                )
            ordered.append({**entity, "start": start, "end": end})

        if not ordered:
            return []
        ordered.sort(key=lambda entity: entity["start"])

        merged = []
        count = 0
        for entity in _merge_overlaps(ordered, text):
            if (
                merged
                and entity["label"] == merged[-1]["label"]
                and entity["start"] - merged[-1]["end"] <= 1
            ):
                previous = merged[-1]
                previous["score"] = (_score(previous) * count + _score(entity)) / (
                    count + 1
                )
                previous["end"] = entity["end"]
                previous["text"] = text[previous["start"] : previous["end"]]
                count += 1
            else:
                merged.append(entity)
                count = 1

        return merged
