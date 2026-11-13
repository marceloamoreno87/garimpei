import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from playwright.sync_api import Error as BrowserError
from playwright.sync_api import Page, sync_playwright

from garimpei.domain.listing.listing import Evidence
from garimpei.domain.robot.ports import RobotAdmission
from garimpei.domain.valuation.identity import identify
from garimpei.domain.valuation.ports import NewSourceFailure
from garimpei.domain.valuation.values import NewQuote
from garimpei.infra.gateway.robot.admission import robot_operation
from garimpei.infra.repository.valuation.mapper import decode_quote, mapping, records


class RetailNewSource:
    def __init__(
        self,
        catalog: Path,
        fixture_url: str | None,
        timeout: int = 30,
        *,
        robot: RobotAdmission | None = None,
    ) -> None:
        self._catalog, self._fixture, self._timeout = catalog, fixture_url, timeout
        self._robot = robot

    def offers(self, product: str, now: datetime) -> tuple[NewQuote, ...]:
        if self._fixture is not None:
            return self._fixture_offers(product)
        catalog = mapping(json.loads(self._catalog.read_text()))
        urls = catalog.get(product)
        if not isinstance(urls, list):
            return ()
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix="retail-new") as executor:
            return executor.submit(self._browse, tuple(str(url) for url in urls), now).result()

    def _fixture_offers(self, product: str) -> tuple[NewQuote, ...]:
        try:
            with (
                robot_operation(self._robot, "retail_new", "fixture:" + product),
                urlopen(
                    str(self._fixture) + "/new?" + urlencode({"product": product}),
                    timeout=self._timeout,
                ) as response,
            ):
                payload = mapping(json.load(response))
            return tuple(decode_quote(row) for row in records(payload["offers"]))
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError, InvalidOperation):
            raise NewSourceFailure("new_source_unavailable") from None

    def _browse(self, urls: tuple[str, ...], now: datetime) -> tuple[NewQuote, ...]:
        # The public document is read in a separate thread, outside Django transactions.
        try:
            with (
                sync_playwright() as engine,
                closing(engine.chromium.launch(headless=True)) as browser,
            ):
                return self._read_pages(browser.new_page(locale="pt-BR"), urls, now)
        except (BrowserError, ValueError, KeyError, InvalidOperation):
            raise NewSourceFailure("new_source_unavailable") from None

    def _read_pages(
        self, page: "Page", urls: tuple[str, ...], now: datetime
    ) -> tuple[NewQuote, ...]:
        quotes: list[NewQuote] = []
        for url in urls:
            quote = self._read_quote(page, url, now)
            if quote is not None:
                quotes.append(quote)
            page.wait_for_timeout(2000)
        return tuple(quotes)

    def _read_quote(self, page: Page, url: str, now: datetime) -> NewQuote | None:
        with robot_operation(self._robot, "retail_new", "navigate:" + url):
            response = page.goto(url, timeout=self._timeout * 1000, wait_until="domcontentloaded")
            if response is None or not response.ok:
                raise NewSourceFailure("new_source_unavailable")
            # Select the product only; never recommendations, sessions or tracking payloads.
            raw = page.evaluate("""() => {
                const node=document.getElementById('__NEXT_DATA__');
                if(!node) return null;
                const p=JSON.parse(node.textContent).props.pageProps.product;
                const ld=Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
                  .map(node=>JSON.parse(node.textContent)).find(row=>row['@type']==='Product');
                return {id:p.id,title:p.title,available:p.available,prices:p.prices,
                        currency:ld?.offers?.priceCurrency,stock:ld?.offers?.availability};
            }""")
            row = mapping(raw)
            quote = self._quote(row, url, now)
            return quote

    @staticmethod
    def _quote(row: dict[str, object], url: str, now: datetime) -> NewQuote | None:
        title = str(row["title"])
        if any(
            word in title.casefold()
            for word in ("usado", "recondicionado", "open box", "kit ", "lote ")
        ):
            return None
        key = identify(Evidence(title=title))
        if (
            key is None
            or row["available"] is not True
            or row.get("currency") != "BRL"
            or row.get("stock") != "https://schema.org/InStock"
        ):
            return None
        price = Decimal(str(mapping(row["prices"])["priceWithDiscount"]))
        return NewQuote(key, "KaBuM!", str(row["id"]), title, url, price, now)
