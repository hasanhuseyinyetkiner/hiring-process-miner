from scripts.robustness_experiment import PLANTED, run_one


def test_robustness_experiment_is_repeatable_and_uses_app_card() -> None:
    first = run_one(0, 0)
    assert first == run_one(0, 0)
    assert first["selected"] == PLANTED
    assert first["planted_frequency"] >= 30
    assert first["eligible_edges"] > 1
    assert run_one(0, 72) == run_one(0, 72)
