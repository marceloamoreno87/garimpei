from django.conf import settings
from django.urls import path
from django.views.static import serve

from garimpei.infra.http.health_handler import health, ready
from garimpei.infra.http.inference.routes import inference_view
from garimpei.infra.http.integration.routes import integration_view
from garimpei.infra.http.listing.routes import condition_view
from garimpei.infra.http.media.routes import media_view
from garimpei.infra.http.monitoring.routes import monitoring_view
from garimpei.infra.http.navigation.routes import navigation_view
from garimpei.infra.http.operations.routes import operations_view
from garimpei.infra.http.robot.routes import robot_view
from garimpei.infra.http.valuation.routes import identity_view

urlpatterns = [
    path("acompanhamento/robo/", robot_view, name="robot-status"),
    path("acompanhamento/robo/ligar/", robot_view, {"action": "enable"}, name="robot-enable"),
    path("acompanhamento/robo/desligar/", robot_view, {"action": "disable"}, name="robot-disable"),
    path("ofertas/<uuid:identity>/identidade/", identity_view, name="identity-edit"),
    path("acompanhamento/estado/", operations_view, name="operations-status"),
    path(
        "acompanhamento/etapas/<str:stage>/retomar/",
        operations_view,
        {"action": "resume"},
        name="operations-resume",
    ),
    path(
        "acompanhamento/backups/", operations_view, {"action": "backups"}, name="operations-backups"
    ),
    path(
        "acompanhamento/backups/<uuid:identity>/exportar/",
        operations_view,
        {"action": "export"},
        name="operations-export",
    ),
    path(
        "acompanhamento/exportacoes/<uuid:identity>/arquivo/",
        operations_view,
        {"action": "download"},
        name="operations-download",
    ),
    path(
        "ofertas/<uuid:identity>/imagens/<uuid:version>/<str:variant>/",
        media_view,
        name="media-file",
    ),
    path("ofertas/<uuid:identity>/imagens/reprocessar/", media_view, name="media-recovery"),
    path("acompanhamento/navegacao/", navigation_view, name="navigation-status"),
    path(
        "acompanhamento/navegacao/retomar/",
        navigation_view,
        {"action": "resume"},
        name="navigation-resume",
    ),
    path("sugestoes/", navigation_view, {"action": "suggestions"}, name="navigation-suggestions"),
    path("integracoes/ia/", inference_view, name="inference-status"),
    path("integracoes/ia/pausar/", inference_view, {"action": "pause"}, name="inference-pause"),
    path("integracoes/ia/retomar/", inference_view, {"action": "resume"}, name="inference-resume"),
    path(
        "integracoes/facebook/status/",
        integration_view,
        {"action": "facebook-status"},
        name="integration-facebook-status",
    ),
    path("integracoes/", integration_view, name="integration-settings"),
    path(
        "integracoes/whatsapp/status/",
        integration_view,
        {"action": "status"},
        name="integration-status",
    ),
    path("integracoes/whatsapp/qr/", integration_view, {"action": "qr"}, name="integration-qr"),
    path(
        "ofertas/atualizacoes/", condition_view, {"action": "updates"}, name="exploration-updates"
    ),
    path("ofertas/", condition_view, name="condition-list"),
    path("ofertas/<uuid:identity>/", condition_view, name="condition-detail"),
    path(
        "ofertas/<uuid:identity>/condicao/",
        condition_view,
        {"action": "classify"},
        name="condition-classify",
    ),
    path("health", health),
    path("health/ready", ready),
    path("", monitoring_view, name="monitoring-root"),
    path(
        "configuracao/concluir/",
        monitoring_view,
        {"action": "concluir"},
        name="monitoring-complete",
    ),
    path("configuracao/<str:step>/", monitoring_view, {"action": "etapa"}, name="monitoring-step"),
    path("configuracoes/", monitoring_view, {"action": "editar"}, name="monitoring-edit"),
    path(
        "acompanhamento/", monitoring_view, {"action": "acompanhamento"}, name="monitoring-tracking"
    ),
    # The product is served only on loopback; ship its packaged, public assets with Django.
    path("static/<path:path>", serve, {"document_root": settings.STATICFILES_DIRS[0]}),
]
