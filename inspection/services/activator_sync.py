from inspection.services.automation_engine import AutomationEngine


def sync_inspection_with_activator(inspection):
    """
    Sincroniza a situação do veículo no Ativador delegando ao motor de automações.
    """
    if not inspection:
        return

    if inspection.status == "emitted":
        AutomationEngine.trigger_event("emitted", inspection)
    elif inspection.status == "approved":
        AutomationEngine.trigger_event("approved", inspection)


def sync_signature_approval_with_activator(inspection, is_approve_all=False):
    """
    Sincroniza a situação do veículo no Ativador após aprovação de assinatura.
    """
    if not inspection:
        return

    AutomationEngine.trigger_event(
        "signature_approved", inspection, is_approve_all=is_approve_all
    )
