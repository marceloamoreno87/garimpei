from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from garimpei.domain.inference.errors import InferenceError
from garimpei.usecase.inference.pause_inference_usecase import PauseInferenceUseCase
from garimpei.usecase.inference.read_status_usecase import ReadStatusUseCase
from garimpei.usecase.inference.resume_inference_usecase import ResumeInferenceUseCase

MESSAGES = {
    "artifact_missing": (
        "Artefatos locais ainda não preparados",
        "Prepare os artefatos aprovados antes de iniciar a análise.",
    ),
    "artifact_incomplete": (
        "Preparo local incompleto",
        "Confira o manifesto e conclua o preparo dos artefatos.",
    ),
    "service_unavailable": (
        "Serviço local indisponível",
        "Confira o serviço de IA neste computador e tente novamente.",
    ),
    "model_missing": (
        "Modelo ainda não preparado",
        "Prepare os pesos locais antes de iniciar a análise.",
    ),
    "model_corrupt": (
        "Pesos do modelo inválidos",
        "Confira a integridade dos artefatos no preparo local.",
    ),
    "artifact_mismatch": (
        "Versão do modelo diferente da preparada",
        "Confira os artefatos fixados antes de retomar.",
    ),
    "gpu_unavailable": (
        "Aguardando a GPU",
        "A GPU está indisponível ou reservada por outra instância.",
    ),
    "gpu_degraded": (
        "Aceleração incompleta",
        "A análise foi suspensa. Confira a disponibilidade de memória da GPU.",
    ),
    "out_of_memory": (
        "Memória da GPU insuficiente",
        "Libere memória em outros programas e retome quando possível.",
    ),
    "timeout": (
        "A análise excedeu o prazo",
        "O encerramento da chamada será conferido antes de uma nova tentativa.",
    ),
    "execution_unknown": (
        "Conferindo a chamada anterior",
        "Novas análises aguardam a confirmação do encerramento anterior.",
    ),
    "invalid_output": (
        "Resposta do modelo recusada",
        "A resposta não passou pela validação. O resultado anterior foi conservado.",
    ),
    "context_unverified": (
        "Material não cabe no perfil verificado",
        "Confira o tamanho e a cobertura do material antes de tentar novamente.",
    ),
    "capacity_limit": (
        "Limite de armazenamento ou entrada atingido",
        "Confira o espaço disponível e os limites do material.",
    ),
    "idle_unloaded": (
        "Modelo descarregado por inatividade",
        "Os pesos e os resultados foram conservados. Novo trabalho poderá carregar o modelo.",
    ),
    "unload_failed": (
        "Não foi possível confirmar o descarregamento",
        "A memória ainda não foi confirmada como liberada. Confira o serviço local.",
    ),
    "ready": ("IA disponível", "Novas análises válidas são processadas automaticamente."),
    "running": ("Analisando localmente", "O material está sendo examinado neste computador."),
    "paused": (
        "IA pausada pelo usuário",
        "A fila e os resultados foram conservados. Retome quando quiser.",
    ),
}


class InferenceHandler:
    def __init__(
        self, read: ReadStatusUseCase, pause: PauseInferenceUseCase, resume: ResumeInferenceUseCase
    ) -> None:
        self._read, self._pause, self._resume = read, pause, resume

    def handle(self, request: HttpRequest, action: str) -> HttpResponse:
        if action == "page" and request.method == "GET":
            status = self._read.execute()
            uncertain = status.reason in {"execution_unknown", "timeout"}
            state = status.reason
            if status.paused and not uncertain:
                state = "draining" if status.active else "paused"
            title, next_action = MESSAGES.get(
                state,
                (
                    "Concluindo a chamada em curso",
                    "A pausa já está confirmada. Nenhuma nova parte será iniciada.",
                ),
            )
            return render(
                request,
                "inference/status.html",
                {
                    "integration_page": True,
                    "status": status,
                    "state_title": title,
                    "next_action": next_action,
                    "execution_uncertain": uncertain,
                },
            )
        if action not in {"pause", "resume"} or request.method != "POST":
            return HttpResponse(
                status=405, headers={"Allow": "GET" if action == "page" else "POST"}
            )
        raw = request.POST.get("revision", "")
        if not raw.isdecimal() or len(raw) > 16 or int(raw) < 1:
            raise InferenceError("invalid_control_revision")
        command = self._pause if action == "pause" else self._resume
        command.execute(int(raw))
        return HttpResponse(status=303, headers={"Location": "/integracoes/ia/"})
