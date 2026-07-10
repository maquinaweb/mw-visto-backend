import os
import requests
import pymysql
from decouple import config

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from inspection.models import (
    InspectionType,
    InspectionTypeStep,
    InspectionMotive,
)


def get_image_content_file(filename, legacy_path=None):
    """
    Attempts to retrieve the image file from local path first.
    If not found, attempts to download it via HTTP from the legacy production domain.
    Returns a ContentFile if found, otherwise None.
    """
    if not filename:
        return None

    # Try local first
    if legacy_path:
        local_path = os.path.join(
            legacy_path, "var", "userfiles", "tipo_veiculo_img", filename
        )
        if os.path.exists(local_path):
            try:
                with open(local_path, "rb") as f:
                    return ContentFile(f.read(), name=filename)
            except Exception as e:
                print(f"Error reading local file {local_path}: {e}")

    # Fallback to web download
    url = f"https://autovisto.dnapv.com.br/var/userfiles/tipo_veiculo_img/{filename}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return ContentFile(response.content, name=filename)
        else:
            print(
                f"Failed to download image {url}: status {response.status_code}"
            )
    except Exception as e:
        print(f"Error downloading image {url}: {e}")

    return None


class Command(BaseCommand):
    help = "Migrates legacy metadata (tipovistoria to InspectionMotive, tipoveiculo to InspectionType) to the new structure."

    def add_arguments(self, parser):
        parser.add_argument(
            "--org-id",
            type=int,
            default=8,
            help="Organization ID to scope the migrated entities to.",
        )
        parser.add_argument(
            "--legacy-path",
            type=str,
            default="/home/smcodes/trabalho/autovisto-php",
            help="Local filesystem path to the legacy autovisto-php project directory.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry run mode. Shows what would be created without saving to the DB.",
        )

    def handle(self, *args, **options):
        org_id = options["org_id"]
        legacy_path = options["legacy_path"]
        dry_run = options["dry_run"]

        self.stdout.write(
            self.style.WARNING(
                f"Starting Option B metadata migration... Org ID: {org_id}, Dry Run: {dry_run}"
            )
        )

        # Connect to the legacy database
        try:
            conn = pymysql.connect(
                host=config("LEGACY_DB_HOST"),
                user=config("LEGACY_DB_USER"),
                password=config("LEGACY_DB_PASSWORD"),
                database=config("LEGACY_DB_NAME"),
                port=config("LEGACY_DB_PORT", default=3306, cast=int),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
            self.stdout.write(
                self.style.SUCCESS("Successfully connected to legacy database.")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Failed to connect to the legacy database: {e}"
                )
            )
            return

        try:
            with conn.cursor() as cursor:
                # 1. Fetch unique combinations of (tipovistoria_id, tipoveiculo_id) from the legacy vistorias table
                cursor.execute("""
                    SELECT DISTINCT tipovistoria_id, tipoveiculo_id
                    FROM gee_vistoria
                    WHERE data_exclusao IS NULL
                """)
                combinations = cursor.fetchall()
                self.stdout.write(
                    f"\nFetched {len(combinations)} active legacy templates combinations."
                )

                # Dictionary to cache resolved InspectionMotives to avoid duplicate queries
                motive_cache = {}

                for combo in combinations:
                    tv_id = combo["tipovistoria_id"]
                    tveic_id = combo["tipoveiculo_id"]

                    if not tv_id or not tveic_id:
                        continue

                    # Fetch the legacy InspectionMotive (tipovistoria)
                    cursor.execute(
                        "SELECT * FROM gee_tipovistoria WHERE id = %s", (tv_id,)
                    )
                    tv_row = cursor.fetchone()
                    if not tv_row or tv_row.get("data_exclusao"):
                        continue

                    # Fetch the legacy VehicleType (tipoveiculo)
                    cursor.execute(
                        "SELECT * FROM gee_tipoveiculo WHERE id = %s",
                        (tveic_id,),
                    )
                    tveic_row = cursor.fetchone()
                    if not tveic_row or tveic_row.get("data_exclusao"):
                        continue

                    motive_name = tv_row["nome"].strip()
                    exp_days = tv_row.get("tempo_expiracao_created_at")
                    exp_hours = tv_row.get("tempo_expiracao_started_at")
                    tv_created_at = tv_row.get("data_criacao") or timezone.now()

                    # Resolve or create InspectionMotive
                    motive_key = (motive_name, org_id)
                    if motive_key not in motive_cache:
                        existing_motive = InspectionMotive.all_objects.filter(
                            name=motive_name, organization_id=org_id
                        ).first()

                        if existing_motive:
                            motive_cache[motive_key] = existing_motive
                            # Ensure expiration configuration is updated
                            if not dry_run and (
                                existing_motive.expiration_days != exp_days
                                or existing_motive.expiration_hours != exp_hours
                            ):
                                existing_motive.expiration_days = exp_days
                                existing_motive.expiration_hours = exp_hours
                                existing_motive.save()
                        else:
                            if dry_run:
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f"  [DRY-RUN] Would create InspectionMotive '{motive_name}' (exp: {exp_days}d / {exp_hours}h)"
                                    )
                                )
                                motive_cache[motive_key] = None
                            else:
                                new_motive = InspectionMotive.objects.create(
                                    name=motive_name,
                                    description="",  # Description left empty as requested
                                    expiration_days=exp_days,
                                    expiration_hours=exp_hours,
                                    organization_id=org_id,
                                )
                                InspectionMotive.objects.filter(
                                    pk=new_motive.pk
                                ).update(created_at=tv_created_at)
                                motive_cache[motive_key] = new_motive
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f"  -> Created InspectionMotive '{motive_name}' (ID: {new_motive.id})"
                                    )
                                )

                    motive_obj = motive_cache[motive_key]

                    # Create/resolve InspectionType for the combo
                    veic_name = tveic_row["nome"].strip()
                    veic_created_at = (
                        tveic_row.get("data_criacao") or timezone.now()
                    )

                    self.stdout.write(
                        f"\nProcessing InspectionType: '{veic_name}' under motive '{motive_name}'..."
                    )

                    existing_type = InspectionType.all_objects.filter(
                        name=veic_name,
                        motive=motive_obj,
                        organization_id=org_id,
                    ).first()

                    if existing_type:
                        self.stdout.write(
                            f"  -> InspectionType '{veic_name}' for motive '{motive_name}' already exists (ID: {existing_type.id})."
                        )
                        inspection_type = existing_type
                    else:
                        if dry_run:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  [DRY-RUN] Would create InspectionType '{veic_name}' linked to motive '{motive_name}'"
                                )
                            )
                            inspection_type = None
                        else:
                            inspection_type = InspectionType.objects.create(
                                name=veic_name,
                                description="",  # Description left empty as requested
                                motive=motive_obj,
                                organization_id=org_id,
                            )
                            InspectionType.objects.filter(
                                pk=inspection_type.pk
                            ).update(created_at=veic_created_at)
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  -> Created InspectionType '{veic_name}' (ID: {inspection_type.id})"
                                )
                            )

                    # Fetch steps for this tveic_id (from gee_tipoveiculoimg)
                    cursor.execute(
                        "SELECT * FROM gee_tipoveiculoimg WHERE tipoveiculo_id = %s AND data_exclusao IS NULL ORDER BY is_sequencial, ordem",
                        (tveic_id,),
                    )
                    legacy_steps = cursor.fetchall()

                    for step_row in legacy_steps:
                        step_id = step_row["id"]
                        desc = (
                            step_row["descricao"].strip()
                            if step_row["descricao"]
                            else ""
                        )
                        filename = step_row["file"]
                        is_seq = bool(step_row.get("is_sequencial"))
                        is_anexo = bool(step_row.get("is_anexo"))
                        ordem = step_row.get("ordem") or 0
                        created_at = (
                            step_row.get("data_criacao") or timezone.now()
                        )

                        self.stdout.write(
                            f"    - Processing step: '{desc}' (Legacy ID: {step_id})"
                        )

                        if inspection_type:
                            existing_step = InspectionTypeStep.objects.filter(
                                inspection_type=inspection_type,
                                title=desc,
                            ).first()

                            if existing_step:
                                self.stdout.write(
                                    f"      -> Step '{desc}' already exists."
                                )
                            else:
                                if dry_run:
                                    self.stdout.write(
                                        f"      [DRY-RUN] Would create Step '{desc}' with file '{filename}'"
                                    )
                                else:
                                    new_step = InspectionTypeStep(
                                        inspection_type=inspection_type,
                                        title=desc,
                                        description=desc,
                                        instructions=desc,
                                        order=ordem,
                                        is_sequential=is_seq,
                                        allow_attachment=is_anexo,
                                        high_resolution="high",
                                    )

                                    if filename:
                                        self.stdout.write(
                                            f"      -> Fetching image '{filename}'..."
                                        )
                                        img_file = get_image_content_file(
                                            filename, legacy_path
                                        )
                                        if img_file:
                                            new_step.instruction_image.save(
                                                filename,
                                                img_file,
                                                save=False,
                                            )
                                            self.stdout.write(
                                                "      -> Image saved successfully."
                                            )
                                        else:
                                            self.stdout.write(
                                                self.style.WARNING(
                                                    f"      -> Warning: Image '{filename}' "
                                                    "not found locally or online."
                                                )
                                            )

                                    new_step.save()
                                    InspectionTypeStep.objects.filter(
                                        pk=new_step.pk
                                    ).update(created_at=created_at)

                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"      -> Created Step '{desc}' (ID: {new_step.id})"
                                        )
                                    )
                        else:
                            if dry_run:
                                self.stdout.write(
                                    f"      [DRY-RUN] Would process Step '{desc}' under new InspectionType"
                                )

        finally:
            conn.close()
            self.stdout.write(
                self.style.SUCCESS(
                    "\nMetadata migration completed successfully!"
                )
            )
