from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

import pytest

from garimpei.domain.listing.condition import automatic_condition
from garimpei.domain.listing.coverage import Coverage
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.listing.scope import Scope
from garimpei.domain.monitoring.configuration import MonitoringConfiguration
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot
from garimpei.domain.valuation.identity import identify
from garimpei.domain.valuation.profit import compose_profit
from tests.unit.test_profit import NOW, inputs


def test_one_search_per_interest_without_logistics() -> None:
    scope = Scope.from_snapshot(
        MonitoringSnapshot(
            configured=True,
            configuration_id=uuid4(),
            revision=1,
            cep="01001000",
            category_ids=("cameras",),
            product_names=("iPhone 13",),
        )
    )
    assert scope is not None
    assert len(scope.searches) == 2
    assert {query.term for query in scope.searches} == {"cameras", "iPhone 13"}
    assert {query.modality for query in scope.searches} == {"marketplace"}


def test_potential_profit_requires_no_logistics_or_freight() -> None:
    value = inputs(applicable_freight=None)
    value = replace(
        value,
        coverage=Coverage("unknown", "unknown", None, "unknown", "unknown"),
        configuration=replace(value.configuration, shipping_estimate=None),
    )
    result = compose_profit(value, NOW)
    assert result.profit.value == Decimal("512.50")
    assert result.profit.state == "estimado"
    assert result.freight.value is None
    assert "freight" in " ".join(result.excluded_costs)


def test_configuration_can_be_completed_without_shipping() -> None:
    value = MonitoringConfiguration.create().save_region("01001000", 0)
    value = value.save_costs("", "12.50", value.revision)
    assert value.next_step == "interesses" and value.shipping_estimate is None


@pytest.mark.parametrize(
    "title,identity",
    [
        ("iPhone 11 128GB", "apple:iphone11:standard:128gb"),
        ("iPhone 13 Pro 1TB", "apple:iphone13:pro:1tb"),
        ("iPhone 14 Plus 256GB", "apple:iphone14:plus:256gb"),
        ("iPhone 16 Pro Max 512GB", "apple:iphone16:promax:512gb"),
        ("Xbox Series S 512GB", "microsoft:xboxseriess:standard:512gb"),
        ("Xbox Series X 1TB com leitor", "microsoft:xboxseriesx:disc:1tb"),
        ("Nintendo Switch OLED 64GB", "nintendo:switch:oled:64gb"),
        ("Nintendo Switch Lite 32GB", "nintendo:switch:lite:32gb"),
        ("iPhone 13 64GB", None),
        ("iPhone 12 Pro 64GB", None),
        ("iPhone 14 mini 128GB", None),
        ("iPhone 16 Pro 128GB e iPhone 15 128GB", None),
        ("Capa para iPhone 13 128GB", None),
        ("Xbox Series S 2TB", None),
        ("Nintendo Switch OLED 32GB", None),
    ],
)
def test_more_electronics_keep_exact_variant_identity(title: str, identity: str | None) -> None:
    assert identify(Evidence(title=title)) == identity


@pytest.mark.parametrize(
    "description,condition",
    [
        ("Funcionando perfeitamente, acompanha caixa e carregador.", "good"),
        ("Aparelho testado e funcionando normalmente, com marcas de uso.", "good"),
        ("Funciona perfeitamente, mas não liga sem o carregador.", "defect"),
        ("Não está funcionando perfeitamente, precisa de reparo.", "defect"),
        ("Funciona perfeitamente? Não testei.", "uncertain"),
        ("Controle funcionando perfeitamente, console não testado.", "uncertain"),
        ("Usado em bom estado.", "uncertain"),
    ],
)
def test_condition_uses_explicit_evidence_in_natural_description(
    description: str, condition: str
) -> None:
    assert automatic_condition(Evidence(description=description)).condition == condition


def test_discovery_requires_source_publication_after_start_and_verified_detail() -> None:
    from datetime import timedelta

    from garimpei.domain.listing.discovery import publication_is_new

    evidence = Evidence(
        title="iPhone 13 128GB", price=Decimal("1000"), published_at=NOW, source_available=True
    )
    started = NOW - timedelta(hours=1)
    assert publication_is_new(evidence, started, NOW)
    for alternative in (
        replace(evidence, published_at=started),
        replace(evidence, published_at=NOW + timedelta(seconds=1)),
        replace(evidence, published_at=None),
        replace(evidence, source_available=None),
        replace(evidence, price=None),
    ):
        assert not publication_is_new(alternative, started, NOW)


@pytest.mark.parametrize(
    "title,description,identity",
    [
        ("Canon EOS T5i somente corpo", "Funcionando perfeitamente.", "canon:eos:t5i:body"),
        ("Nikon D5300 somente corpo", "Funcionando perfeitamente.", "nikon:d:d5300:body"),
        ("Sony a6400 somente corpo", "Funcionando perfeitamente.", "sony:alpha:a6400:body"),
        ("Canon EOS T5i com lente 18-55mm", "Funcionando perfeitamente.", None),
        ("Lente para Canon EOS T5i", "Somente corpo, funcionando perfeitamente.", None),
        ("Nikon D5300 D5600 somente corpo", "Funcionando perfeitamente.", None),
        (
            "RTX 3060 12GB",
            "Placa de vídeo usada funcionando perfeitamente.",
            "nvidia:rtx:3060:12gb",
        ),
        ("RTX 3060 Ti 8GB GDDR6", "Funcionando perfeitamente.", "nvidia:rtx:3060ti:8gb:gddr6"),
        ("RTX 4060 Ti 16GB", "Funcionando perfeitamente.", "nvidia:rtx:4060ti:16gb"),
        ("RTX 4070 Ti Super 16GB", "Funcionando perfeitamente.", "nvidia:rtx:4070tisuper:16gb"),
        ("RTX 4070 12GB", "Funcionando perfeitamente.", None),
        ("RTX 3060 Ti 8GB", "Funcionando perfeitamente.", None),
        ("RTX 3060 16GB", "Funcionando perfeitamente.", None),
        ("Notebook RTX 3060 12GB", "Funcionando perfeitamente.", None),
        ("Suporte RTX 3060 12GB", "Funcionando perfeitamente.", None),
        ("RTX 3060 12GB ou RTX 4060 8GB", "Funcionando perfeitamente.", None),
    ],
)
def test_camera_bodies_and_graphics_cards_do_not_mix_kits_or_variants(
    title: str, description: str, identity: str | None
) -> None:
    assert identify(Evidence(title=title, description=description)) == identity


def test_missing_comparables_wait_before_becoming_a_terminal_exclusion() -> None:
    from datetime import timedelta

    from garimpei.domain.alert.eligibility import pricing_decision

    assert pricing_decision("amostra_insuficiente", NOW, NOW) == ("waiting", "amostra_insuficiente")
    assert pricing_decision("amostra_insuficiente", NOW, NOW + timedelta(hours=48)) == (
        "excluded",
        "reference_wait_expired",
    )
    assert pricing_decision("produto_indeterminado", NOW, NOW) == (
        "excluded",
        "produto_indeterminado",
    )


@pytest.mark.parametrize(
    "description",
    [
        "Entrada de R$ 1.500,00 e parcelas a combinar. Funcionando perfeitamente.",
        "10x de R$ 1.500,00 no cartão. Funcionando perfeitamente.",
        "Somente troca por outro aparelho. Funcionando perfeitamente.",
    ],
)
def test_partial_prices_and_trade_only_offers_do_not_fabricate_profit(description: str) -> None:
    value = inputs()
    value = replace(
        value,
        observation=replace(
            value.observation, evidence=replace(value.observation.evidence, description=description)
        ),
    )
    result = compose_profit(value, NOW)
    assert result.purchase.value == Decimal("1500")
    assert result.profit.value is None


def test_frozen_legacy_profit_is_not_relabelled_as_before_freight() -> None:
    from garimpei.domain.alert.alert import AlertMessage
    from garimpei.domain.alert.eligibility import message_text

    value = AlertMessage(
        uuid4(),
        "discovered",
        "iPhone 13",
        "Marketplace",
        Decimal("1000"),
        None,
        Decimal("200"),
        NOW,
        "https://www.facebook.com/marketplace/item/1/",
    )
    assert "Lucro potencial antes de frete/transporte" in message_text(value)
    old = replace(value, profit_policy="profit-brl-v1")
    assert "regra anterior" in message_text(old)
    assert "antes de frete/transporte" not in message_text(old)


@pytest.mark.parametrize(
    "title,identity",
    [
        ("Smart TV Samsung UN50AU7700GXZD", "samsung:tv:un50au7700gxzd"),
        ("Smart TV Samsung UN55CU7700GXZD", "samsung:tv:un55cu7700gxzd"),
        ("Smart TV LG 55UR8750PSA.BWZ", "lg:tv:55ur8750psa.bwz"),
        ("Samsung UN55AU7700", None),
        ("LG 55UR8750PSA", None),
        ("Placa para TV Samsung UN55AU7700GXZD", None),
        ("Samsung UN50AU7700GXZD ou UN55AU7700GXZD", None),
        ("Sony WH-1000XM4", "sony:headphone:wh1000xm4"),
        ("Sony WH1000XM5", "sony:headphone:wh1000xm5"),
        ("JBL Tune 510BT", "jbl:headphone:tune510bt"),
        ("JBL Tune 520BT", "jbl:headphone:tune520bt"),
        ("JBL Tune 720BT", "jbl:headphone:tune720bt"),
        ("Almofadas para Sony WH-1000XM4", None),
        ("Sony WH-1000XM4 réplica", None),
        ("Sony WH-1000XM4 e WH-1000XM5", None),
        ("Sony WF-1000XM4", None),
    ],
)
def test_tv_skus_and_headphone_models_keep_distinct_variants(
    title: str, identity: str | None
) -> None:
    assert identify(Evidence(title=title)) == identity


@pytest.mark.parametrize("title", ["Samsung UN55AU7700GXZD", "Sony WH-1000XM4", "JBL Tune 520BT"])
def test_new_category_models_require_and_use_five_exact_comparables(title: str) -> None:
    from garimpei.domain.valuation.policy import estimate
    from garimpei.domain.valuation.values import Comparable
    from tests.unit.test_valuation import sample

    def model(price: str) -> Comparable:
        row = sample(price)
        return replace(row, title=title, evidence=replace(row.evidence, title=title))

    target = model("1500")
    references = tuple(model(str(price)) for price in (2100, 2200, 2300, 2400, 2500))
    assert estimate(target, references, NOW).price == Decimal("2300.00")
    assert estimate(target, references[:4], NOW).reason == "amostra_insuficiente"
