import re

from django.http import HttpRequest

from garimpei.domain.monitoring.errors import MonitoringError
from garimpei.usecase.monitoring.save_step_usecase import StepInput


def parse_input(request: HttpRequest, step: str) -> StepInput:
    raw_revision = request.POST.get("revision", "")
    if not re.fullmatch(r"[0-9]{1,18}", raw_revision):
        raise MonitoringError("Revisão inválida. Recarregue o formulário.", "revision")
    products = list(request.POST.getlist("product_names[]"))
    intent = request.POST.get("intent", "")
    if re.fullmatch(r"remove:[0-9]{1,9}", intent):
        index = int(intent.split(":")[1])
        products = [value for position, value in enumerate(products) if position != index]
    new_product = request.POST.get("new_product", "")
    if new_product.strip() or request.POST.get("intent") == "add":
        products.append(new_product)
    return StepInput(
        step=step,
        revision=int(raw_revision),
        cep=request.POST.get("cep", ""),
        shipping_estimate=request.POST.get("shipping_estimate", ""),
        resale_fee_percent=request.POST.get("resale_fee_percent", ""),
        category_ids=tuple(request.POST.getlist("category_ids[]")),
        product_names=tuple(products),
    )
