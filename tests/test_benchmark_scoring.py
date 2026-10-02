from benchmarks.compare_presidio import score


def test_exact_matching_penalizes_boundary_and_label_errors():
    gold = {(0, 0, 5, "person"), (0, 10, 15, "location")}
    predicted = {(0, 0, 5, "person"), (0, 10, 14, "location"), (0, 10, 15, "person")}
    result = score(gold, predicted)
    assert (result["tp"], result["fp"], result["fn"]) == (1, 2, 1)
    assert result["precision"] == 1 / 3
    assert result["recall"] == 1 / 2


def test_no_predictions_and_negative_documents():
    assert score({(0, 0, 5, "person")}, set())["f4"] == 0
    assert score(set(), {(0, 0, 5, "person")})["fp"] == 1
