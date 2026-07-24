import logging
from core.services.activator.activator import ActivatorEndPoints
from inspection.models.automation_rule import AutomationRule

logger = logging.getLogger(__name__)


class AutomationEngine:
    """
    Motor central de automações por Organização.
    Avalia regras configuráveis e executa ações de acordo com o provedor (ex: Ativador).
    """

    @classmethod
    def trigger_event(cls, event: str, inspection, **kwargs):
        if not inspection:
            return

        vehicle = getattr(inspection, "vehicle_sga", None)
        if not vehicle or not vehicle.codigo_veiculo:
            logger.info(
                f"[AutomationEngine] Vistoria {inspection.hash} ({event}) ignorada: Sem veículo cadastrado."
            )
            return

        codigo_veiculo = str(vehicle.codigo_veiculo)
        org_id = getattr(inspection, "organization_id", None)

        # 1. Buscar regras ativas da organização para o evento disparado
        rules_qs = AutomationRule.objects.filter(
            is_active=True,
            event=event,
        )
        if org_id:
            rules_qs = rules_qs.filter(organization_id=org_id)

        matching_rules = []
        for rule in rules_qs:
            # Filtro por tipo de vistoria
            if (
                rule.inspection_type_id
                and getattr(inspection, "type_id", None)
                != rule.inspection_type_id
            ):
                continue
            # Filtro por motivo da vistoria
            if (
                rule.inspection_motive_id
                and getattr(inspection, "motive_id", None)
                != rule.inspection_motive_id
            ):
                continue
            matching_rules.append(rule)

        if not matching_rules:
            logger.info(
                f"[AutomationEngine] Nenhuma regra configurada para o evento '{event}' na org {org_id}."
            )
            return

        # 2. Executa as regras encontradas de acordo com o provedor
        activator = (
            ActivatorEndPoints(org_id) if org_id else ActivatorEndPoints()
        )
        for rule in matching_rules:
            if rule.provider == AutomationRule.Provider.ATIVADOR:
                obs = (
                    rule.observation_template.format(hash=inspection.hash)
                    if rule.observation_template
                    else f"Automação '{rule.name}' executada (Vistoria: {inspection.hash})"
                )
                cls._execute_change_situation(
                    activator,
                    codigo_veiculo,
                    rule.target_situation_code,
                    obs,
                    rule_name=rule.name,
                )

    @classmethod
    def _execute_change_situation(
        cls, activator, codigo_veiculo, target_situation, obs, rule_name="Regra"
    ):
        try:
            res = activator.vehicle.change_situation(
                codigo_veiculo=codigo_veiculo,
                codigo_situacao=target_situation,
                observacao=obs,
            )
            status_code = res.status_code if res else "Sem resposta"
            if res and res.status_code >= 400:
                err_text = res.text or ""
                if "já está" in err_text.lower() or "transição não autorizada" in err_text.lower():
                    logger.info(
                        f"[AutomationEngine] [{rule_name}] Veículo {codigo_veiculo} já na situação {target_situation} ou transição redundante: {err_text}"
                    )
                    return res
                error_msg = f"[AutomationEngine] [{rule_name}] Erro ao alterar situação do veículo {codigo_veiculo} para {target_situation}: HTTP {status_code} - {err_text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            logger.info(
                f"[AutomationEngine] [{rule_name}] Veículo {codigo_veiculo} -> Situação {target_situation} (HTTP {status_code})"
            )
            return res
        except Exception as e:
            logger.error(
                f"[AutomationEngine] [{rule_name}] Erro ao alterar situação do veículo {codigo_veiculo} para {target_situation}: {e}"
            )
            raise
