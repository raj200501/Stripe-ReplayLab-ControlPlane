from app.services import Scenario, generate_diff, simulate_run, validate_scenario_config


def test_scenario_validation() -> None:
    errors = validate_scenario_config({"api_timeout_probability": 1.2})
    assert errors


def test_deterministic_prng() -> None:
    scenario = Scenario(id="s1", name="normal", config_json={"webhook_duplicate_probability": 0.5})
    run_a = simulate_run(scenario, 9)
    run_b = simulate_run(scenario, 9)
    assert run_a.webhooks == run_b.webhooks


def test_diagnosis_case_ordering_and_duplicates() -> None:
    baseline = simulate_run(Scenario(id="s1", name="base", config_json={}), 5)
    candidate = simulate_run(
        Scenario(
            id="s2",
            name="chaos",
            config_json={
                "webhook_out_of_order_probability": 1.0,
                "webhook_duplicate_probability": 1.0,
            },
        ),
        5,
    )
    report = generate_diff(baseline, candidate)
    hints = report["diagnosis_json"]["hints"]
    assert any("idempotent" in h for h in hints)
    assert any("order" in h for h in hints)


def test_diagnosis_case_missing_idempotency() -> None:
    baseline = simulate_run(Scenario(id="s1", name="base", config_json={}), 7)
    candidate = simulate_run(
        Scenario(id="s3", name="retry", config_json={"force_missing_idempotency": True}), 7
    )
    report = generate_diff(baseline, candidate)
    assert any("idempotency key" in h for h in report["diagnosis_json"]["hints"])
