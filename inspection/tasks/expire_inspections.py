import logging
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from core.observability.tasks import tracked_task
from inspection.models import Inspection, InspectionMotive

logger = logging.getLogger("observability")


@tracked_task
def expire_inspections_task(*args, **kwargs):
    """
    Recurring task to check and mark expired inspections.
    Filters inspections with status EMITTED or VIEWED whose calculated
    expiration time based on their InspectionMotive has passed.
    """
    logger.info("Starting inspection expiration task...")
    now = timezone.now()

    # Get motives configured with positive expiration days or hours
    motives = InspectionMotive.objects.filter(
        Q(expiration_days__gt=0) | Q(expiration_hours__gt=0)
    )

    if not motives.exists():
        logger.info("No inspection motives with expiration parameters found.")
        return 0

    # Build database-level Q filter for inspections per motive cutoff
    q_filter = Q()
    for motive in motives:
        days = motive.expiration_days or 0
        hours = motive.expiration_hours or 0
        cutoff = now - timedelta(days=days, hours=hours)
        q_filter |= Q(motive=motive, created_at__lte=cutoff)

    # Query active unfulfilled inspections (EMITTED or VIEWED) matching expiration criteria
    inspections_to_expire = Inspection.objects.filter(
        status__in=[Inspection.Status.EMITTED, Inspection.Status.VIEWED]
    ).filter(q_filter)

    count = inspections_to_expire.update(status=Inspection.Status.EXPIRED)

    logger.info(
        f"Inspection expiration task finished. Updated {count} inspection(s) to EXPIRED status."
    )
    return count
