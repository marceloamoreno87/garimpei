FACEBOOK_MESSAGES = {
    "browser_requested": (
        "Abrindo o navegador do Facebook",
        "Aguarde a janela própria do Garimpei neste computador. A coleta está pausada.",
    ),
    "browser_waiting": (
        "Conclua o login na janela do Facebook",
        "Entre na sua conta, resolva as confirmações e volte para clicar em Já entrei, verificar acesso. A coleta está pausada.",
    ),
    "browser_verifying": (
        "Verificando acesso ao Marketplace",
        "Aguarde a confirmação antes de retomar a coleta.",
    ),
    "browser_failed": (
        "Não foi possível abrir a janela",
        "Tente abrir novamente. Mantenha a sessão gráfica deste computador disponível.",
    ),
    "browser_interrupted": (
        "A conexão foi interrompida",
        "Abra novamente o navegador do Facebook para concluir a conexão. Seus dados anteriores foram preservados.",
    ),
    "browser_challenge": (
        "O Facebook precisa da sua confirmação",
        "A coleta foi pausada. Abra o navegador, confira o acesso e confirme a conexão novamente.",
    ),
    "missing": (
        "Conecte o Facebook",
        "Abra o navegador do Garimpei e entre na sua conta para permitir a coleta.",
    ),
    "missing_file": (
        "Renove a sessão do Facebook",
        "Os dados de acesso não estão disponíveis. Adicione os cookies novamente.",
    ),
    "expired": (
        "A sessão do Facebook expirou",
        "Adicione novos cookies para continuar a coleta.",
    ),
    "challenge": (
        "Verifique sua sessão do Facebook",
        "Confirme o acesso no Facebook e depois adicione novos cookies para retomar a coleta.",
    ),
    "pending": (
        "Sessão aguardando verificação",
        "Os cookies foram salvos. A próxima coleta verificará o acesso.",
    ),
}


def facebook_context(phase: str, *, detail: bool = False) -> dict[str, object]:
    notice = FACEBOOK_MESSAGES.get(phase)
    if detail and phase == "connected":
        notice = ("Sessão verificada", "Sua sessão foi verificada.")
    return {
        "facebook_notice": notice,
        "facebook_phase": phase,
        "facebook_detail": detail,
        "facebook_waiting": phase == "browser_waiting",
        "facebook_busy": phase in {"browser_requested", "browser_waiting", "browser_verifying"},
    }
