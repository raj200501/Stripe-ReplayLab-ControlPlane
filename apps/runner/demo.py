import argparse
import time

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--loops", type=int, default=4)
    args = parser.parse_args()

    scenarios = [
        ("Normal", {"webhook_out_of_order_probability": 0.0, "webhook_duplicate_probability": 0.0}),
        ("OutOfOrder", {"webhook_out_of_order_probability": 1.0, "webhook_duplicate_probability": 0.0}),
        ("Duplicate", {"webhook_out_of_order_probability": 0.0, "webhook_duplicate_probability": 1.0}),
        ("Flaky", {"api_500_probability": 0.4}),
    ]

    with httpx.Client(timeout=5.0) as client:
        for i in range(args.loops):
            name, config = scenarios[i % len(scenarios)]
            scenario = client.post(
                f"{args.api}/api/scenarios",
                json={"name": f"{name}-{i}", "description": "demo", "version": 1, "config_json": config},
            ).json()
            run = client.post(f"{args.api}/api/scenarios/{scenario['id']}/run", json={"seed": args.seed + i}).json()
            print(f"[{i+1}/{args.loops}] {name} run={run['id']} status={run['status']}")
            time.sleep(0.2)


if __name__ == "__main__":
    main()
