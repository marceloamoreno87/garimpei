from playwright.sync_api import BrowserContext, Page, Playwright

class Stealth:
    def __init__(
        self,
        *,
        navigator_languages_override: tuple[str, ...] = ...,
        navigator_platform: bool = ...,
        navigator_platform_override: str | None = ...,
        webgl_vendor: bool = ...,
    ) -> None: ...
    def apply_stealth_sync(self, page_or_context: BrowserContext | Page) -> None: ...
    def hook_playwright_context(self, ctx: Playwright) -> None: ...
