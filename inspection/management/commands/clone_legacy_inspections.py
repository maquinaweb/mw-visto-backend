import os
import requests
import pymysql

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile

from inspection.models import (
    Inspection,
    InspectionStep,
    InspectionType,
    InspectionTypeStep,
    InspectionMotive,
    Inspector,
)
from message.models import Contact
from sga.models.vehicle_sga import VehicleSGA


class Command(BaseCommand):
    help = "Clones real inspections from the legacy PHP MySQL database into Django and uploads images to S3."

    def add_arguments(self, parser):
        parser.add_argument(
            "--org-id",
            type=int,
            default=8,
            help="Organization ID to scope the cloned entities to.",
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
            help="Dry run mode. Shows what would be created without saving to the DB or uploading to S3.",
        )
        parser.add_argument(
            "--status",
            type=str,
            default="Aprovada",
            choices=[
                "Aprovada",
                "Reprovada",
                "Realizada",
                "Pendente",
                "Iniciada",
            ],
            help="Legacy inspection status to filter by.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Limit of inspections to clone.",
        )
        parser.add_argument(
            "--use-legacy-dates",
            action="store_true",
            help="Keep original legacy timestamps for inspections and steps instead of using current time.",
        )

    def handle(self, *args, **options):
        org_id = options["org_id"]
        legacy_path = options["legacy_path"]
        dry_run = options["dry_run"]
        status_arg = options["status"]
        limit = options["limit"]
        use_legacy_dates = options["use_legacy_dates"]

        self.stdout.write(
            self.style.WARNING(
                f"Starting legacy inspection cloning... Org ID: {org_id}, Status: {status_arg}, Limit: {limit}, Use Legacy Dates: {use_legacy_dates}, Dry Run: {dry_run}"
            )
        )

        # Connect to the legacy database
        try:
            conn = pymysql.connect(
                host="mysql.clube.autos",
                user="clube03",
                password="3zy9b4he9RNKc",
                database="clube03",
                port=3306,
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
                # Query legacy inspections that have at least one active image
                query = """
                    SELECT v.*, vt.nome as motive_name, tv.nome as type_name
                    FROM gee_vistoria v
                    LEFT JOIN gee_tipovistoria vt ON v.tipovistoria_id = vt.id
                    LEFT JOIN gee_tipoveiculo tv ON v.tipoveiculo_id = tv.id
                    WHERE v.status = %s
                      AND v.data_exclusao IS NULL
                      AND (SELECT COUNT(*) FROM gee_imagem i WHERE i.vistoria_id = v.id AND i.data_exclusao IS NULL) > 0
                    ORDER BY v.data_criacao DESC
                    LIMIT %s
                """
                cursor.execute(query, (status_arg, limit))
                legacy_inspections = cursor.fetchall()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Fetched {len(legacy_inspections)} eligible inspections from legacy database."
                    )
                )

                if len(legacy_inspections) == 0:
                    self.stdout.write(
                        self.style.WARNING(
                            "No legacy inspections found matching criteria."
                        )
                    )
                    return

                # Process fetched inspections
                for idx, v_row in enumerate(legacy_inspections):
                    legacy_id = v_row["id"]
                    created_at = (
                        v_row.get("data_criacao")
                        if use_legacy_dates and v_row.get("data_criacao")
                        else timezone.now()
                    )
                    updated_at = (
                        v_row.get("data_finalizacao")
                        if use_legacy_dates and v_row.get("data_finalizacao")
                        else timezone.now()
                    )
                    usuario = v_row.get("usuario") or "consultor"

                    # 1. Map target status
                    if status_arg == "Aprovada":
                        target_status = (
                            Inspection.Status.PERFORMED
                            if idx < limit // 2
                            else Inspection.Status.APPROVED
                        )
                    elif status_arg == "Reprovada":
                        target_status = Inspection.Status.REJECTED
                    elif status_arg == "Realizada":
                        target_status = Inspection.Status.PERFORMED
                    else:
                        target_status = Inspection.Status.EMITTED

                    # 2. Get Vehicle details
                    cursor.execute(
                        "SELECT * FROM gee_veiculo WHERE id = %s",
                        (v_row["veiculo_id"],),
                    )
                    veic_row = cursor.fetchone()
                    plate = veic_row["placa"] if veic_row else "AAA0000"
                    chassi = veic_row["chassi"] if veic_row else ""
                    codigo_veiculo = (
                        veic_row.get("codigo_veiculo") if veic_row else None
                    )

                    # 3. Get Client details
                    client_row = None
                    if veic_row and veic_row.get("cliente_id"):
                        cursor.execute(
                            "SELECT * FROM gee_cliente WHERE id = %s",
                            (veic_row["cliente_id"],),
                        )
                        client_row = cursor.fetchone()

                    client_name = (
                        client_row["nome"] if client_row else "Cliente Antigo"
                    )
                    client_cpf = client_row["cpf"] if client_row else ""
                    client_email = (
                        client_row["email"]
                        if client_row
                        else f"{usuario.lower()}@autovisto.com.br"
                    )
                    client_phone = client_row["celular"] if client_row else ""

                    # 4. Resolve InspectionType and InspectionMotive
                    type_name = v_row.get("type_name") or "Carro"
                    motive_name = v_row.get("motive_name") or "Vistoria"

                    self.stdout.write(
                        self.style.WARNING(
                            f"\n[{idx + 1}/{len(legacy_inspections)}] Processing Legacy ID: {legacy_id} (Plate: {plate}) -> Target Status: {target_status}"
                        )
                    )

                    if dry_run:
                        self.stdout.write(
                            f"  [DRY-RUN] Would map to Type: '{type_name}', Motive: '{motive_name}'"
                        )
                        self.stdout.write(
                            f"  [DRY-RUN] Would create Contact: '{client_name}' ({client_email})"
                        )
                        self.stdout.write(
                            f"  [DRY-RUN] Would create Inspection: 'Vistoria {legacy_id} - Placa {plate}'"
                        )
                        self.stdout.write(
                            f"  [DRY-RUN] Would create VehicleSGA: plate='{plate}', chassi='{chassi}'"
                        )
                    else:
                        # Find or create InspectionType
                        type_obj = InspectionType.objects.filter(
                            organization_id=org_id, name=type_name
                        ).first()
                        if not type_obj:
                            type_obj = InspectionType.objects.filter(
                                name=type_name
                            ).first()
                        if not type_obj:
                            type_obj = InspectionType.objects.create(
                                name=type_name, organization_id=org_id
                            )

                        # Find or create InspectionMotive
                        motive_obj = InspectionMotive.objects.filter(
                            organization_id=org_id, name=motive_name
                        ).first()
                        if not motive_obj:
                            motive_obj = InspectionMotive.objects.filter(
                                name=motive_name
                            ).first()
                        if not motive_obj:
                            motive_obj = InspectionMotive.objects.create(
                                name=motive_name, organization_id=org_id
                            )

                        # Find or create Contact
                        contact = Contact.objects.filter(
                            organization_id=org_id, email=client_email
                        ).first()
                        if not contact and client_cpf:
                            contact = Contact.objects.filter(
                                organization_id=org_id, document=client_cpf
                            ).first()
                        if not contact:
                            contact = Contact.objects.create(
                                organization_id=org_id,
                                name=client_name,
                                email=client_email,
                                phone=client_phone,
                                document=client_cpf,
                            )

                        # Create Inspection
                        new_inspection = Inspection.objects.create(
                            organization_id=org_id,
                            status=target_status,
                            inspection_type=type_obj,
                            motive=motive_obj,
                            title=f"Vistoria {legacy_id} - Placa {plate}",
                            description=f"Clonada do antigo backend em PHP. ID Legado: {legacy_id}",
                        )
                        # Set original timestamps
                        Inspection.objects.filter(pk=new_inspection.pk).update(
                            created_at=created_at, updated_at=updated_at
                        )

                        # Create VehicleSGA
                        VehicleSGA.objects.create(
                            organization_id=org_id,
                            inspection=new_inspection,
                            plate=plate,
                            chassi=chassi,
                            codigo_veiculo=str(codigo_veiculo)
                            if codigo_veiculo
                            else None,
                        )

                        # Create Inspector
                        Inspector.objects.create(
                            organization_id=org_id,
                            inspection=new_inspection,
                            contact=contact,
                            user_id=None,
                        )

                    # 5. Fetch and map images for this inspection
                    cursor.execute(
                        """
                        SELECT i.*, step.descricao as step_desc
                        FROM gee_imagem i
                        LEFT JOIN gee_tipoveiculoimg step ON i.tipoveiculoimg_id = step.id
                        WHERE i.vistoria_id = %s
                          AND i.data_exclusao IS NULL
                        ORDER BY i.ordem, i.data
                    """,
                        (legacy_id,),
                    )
                    images = cursor.fetchall()
                    self.stdout.write(
                        f"  Found {len(images)} images associated."
                    )

                    for img_row in images:
                        filename = img_row["imagem"]
                        step_desc = (
                            img_row.get("step_desc")
                            or img_row.get("descricao")
                            or "Foto"
                        )
                        lat = (
                            float(img_row["latitude"])
                            if img_row["latitude"] is not None
                            else None
                        )
                        lng = (
                            float(img_row["longitude"])
                            if img_row["longitude"] is not None
                            else None
                        )
                        img_created = (
                            (img_row.get("data") or img_row.get("data_criacao"))
                            if use_legacy_dates
                            else created_at
                        )
                        ordem = img_row.get("ordem") or 0
                        rejeitada = bool(img_row.get("rejeitada"))

                        self.stdout.write(
                            f"    - Step: '{step_desc}' -> File: '{filename}'"
                        )

                        if dry_run:
                            self.stdout.write(
                                f"      [DRY-RUN] Would import image '{filename}' to step '{step_desc}' at ({lat}, {lng})"
                            )
                        else:
                            # Try to locate the matching InspectionTypeStep
                            all_type_steps = list(
                                InspectionTypeStep.objects.filter(
                                    inspection_type=type_obj
                                )
                            )
                            type_step = None
                            # 1. Try exact match (case-insensitive)
                            for ts in all_type_steps:
                                if (
                                    ts.title.strip().lower()
                                    == step_desc.strip().lower()
                                ):
                                    type_step = ts
                                    break
                            # 2. Try substring match (if one title contains the other)
                            if not type_step:
                                for ts in all_type_steps:
                                    t1 = ts.title.strip().lower()
                                    t2 = step_desc.strip().lower()
                                    if t1 in t2 or t2 in t1:
                                        type_step = ts
                                        break
                            # 3. Create step on the fly if still not found
                            if not type_step:
                                current_count = len(all_type_steps)
                                type_step = InspectionTypeStep.objects.create(
                                    inspection_type=type_obj,
                                    title=step_desc,
                                    order=current_count + 1,
                                )

                            # Load file content
                            img_content = None

                            # Try local filesystem first
                            local_path = os.path.join(
                                legacy_path, "var", "vistoria_imgs", filename
                            )
                            if os.path.exists(local_path):
                                try:
                                    with open(local_path, "rb") as f:
                                        img_content = ContentFile(
                                            f.read(), name=filename
                                        )
                                        self.stdout.write(
                                            "      (Loaded from local file)"
                                        )
                                except Exception as e:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f"      Failed to read local file: {e}"
                                        )
                                    )

                            # Fallback: download from CloudFront CDN
                            if not img_content:
                                url = f"https://d3jljvnn7x2x26.cloudfront.net/media/{filename}"
                                try:
                                    r = requests.get(url, timeout=15)
                                    if r.status_code == 200:
                                        img_content = ContentFile(
                                            r.content, name=filename
                                        )
                                        self.stdout.write(
                                            "      (Downloaded from CloudFront CDN)"
                                        )
                                    else:
                                        self.stdout.write(
                                            self.style.WARNING(
                                                f"      CDN returned status {r.status_code}"
                                            )
                                        )
                                except Exception as e:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f"      CDN download error: {e}"
                                        )
                                    )

                            if img_content:
                                status_step = (
                                    "rejected" if rejeitada else "realized"
                                )

                                # Create InspectionStep
                                new_step = InspectionStep.objects.create(
                                    inspection=new_inspection,
                                    type_step=type_step,
                                    status=status_step,
                                    order=ordem,
                                    latitude=lat,
                                    longitude=lng,
                                )
                                # Save the file (which uploads it to AWS S3 automatically)
                                new_step.file.save(
                                    filename, img_content, save=False
                                )
                                new_step.save()

                                # Update created_at and updated_at timestamps
                                InspectionStep.objects.filter(
                                    pk=new_step.pk
                                ).update(
                                    created_at=img_created,
                                    updated_at=img_created,
                                )
                            else:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f"      Could not retrieve image content for '{filename}'"
                                    )
                                )

        finally:
            conn.close()
            self.stdout.write(
                self.style.SUCCESS("\nLegacy inspection cloning completed!")
            )
