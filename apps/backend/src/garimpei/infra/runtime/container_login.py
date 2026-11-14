"""Interactive browser in a one-off container while the worker is stopped."""

import time

from garimpei.main import build_facebook_login_handler, build_facebook_profile_repository


def run_login(test_only: bool) -> int:
    if test_only:
        return _display_test()
    handler = build_facebook_login_handler()
    repository = build_facebook_profile_repository()
    print(
        "Container login ready: request login and confirm it from the integrations page.",
        flush=True,
    )
    try:
        _wait_login(handler.execute, lambda: repository.read_login().phase)
        return 0
    finally:
        handler.close()


def _wait_login(advance: "Callable[[], None]", phase: "Callable[[], str]") -> None:
    for _ in range(900):
        advance()
        if phase() == "connected":
            return
        time.sleep(1)
    raise RuntimeError("Login time limit reached; profile preserved, confirmation still required")


def _display_test() -> int:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as engine:
        browser = engine.chromium.launch(headless=False, chromium_sandbox=True)
        try:
            page = browser.new_page()
            page.set_content(
                "<title>Garimpei · teste de janela</title><h1>Janela do contêiner pronta</h1>"
            )
            page.wait_for_timeout(1500)
        finally:
            browser.close()
    print("Display and Chromium sandbox test completed.")
    return 0


from collections.abc import Callable  # noqa: E402
