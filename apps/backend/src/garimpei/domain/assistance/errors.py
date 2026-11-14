class AssistanceError(Exception):
    def __init__(self, code: str, status: int = 422) -> None:
        self.code, self.status = code, status
        self.message = {
            "revision_conflict": "A observação mudou. Recarregue antes de pedir outra análise.",
            "command_conflict": "Este comando já foi usado com outros dados. Recarregue e tente novamente.",
            "not_found": "Oferta ou recorte não encontrado.",
            "invalid_input": "Entrada inválida: informe finalidade, revisão positiva e UUID do comando.",
            "insufficient_input": "Não há evidência utilizável para esta finalidade.",
            "snapshot_changed": "O acompanhamento mudou. Reabra o recorte antes de explicar.",
        }.get(code, "Não foi possível concluir a análise. Tente novamente.")
        super().__init__(code)
