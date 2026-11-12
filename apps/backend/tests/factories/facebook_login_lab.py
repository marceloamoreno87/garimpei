"""Own temporary UI environment; only synthetic login data, never Facebook."""

import json
import tempfile
from pathlib import Path

from tests.factories.facebook_login import FacebookLoginSite, serve_facebook_login
from tests.factories.integration import integration_scenario
from tests.integration.test_collection import completed, configure


def main() -> None:
    site = FacebookLoginSite()
    with tempfile.TemporaryDirectory(prefix="garimpei-f11-") as directory:
        with (
            serve_facebook_login(site) as origin,
            integration_scenario(Path(directory)) as (instance, source, clock, state, credentials),
        ):
            with instance.private_file.open("a") as output:
                output.write(f"GARIMPEI_FACEBOOK_BROWSER_FIXTURE_URL={origin}\n")
            configure(instance)
            completed(instance, 1)
            metadata = {
                "url": f"http://127.0.0.1:{instance.config.web_port}",
                "environment_id": instance.config.environment_id,
            }
            target = instance.root / ".runtime/f11/lab.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(metadata))
            print(json.dumps(metadata), flush=True)
            while True:
                action = json.loads(input())["action"]
                if action == "quit":
                    break
                if action == "authorized":
                    site.authorized = True
                if action == "expire":
                    source.mode = "access"
                    clock.advance(61)
                print(json.dumps({"action": action}), flush=True)


if __name__ == "__main__":
    main()
