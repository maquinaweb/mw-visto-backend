import logging
import requests
from rest_framework.exceptions import ValidationError
from decouple import config

from inspection.models.torry_tech_query import TorryTechQuery

TORRY_TECH_CLIE = config("TORRY_TECH_CLIE", default="3099")
TORRY_TECH_SERIAL = config(
    "TORRY_TECH_SERIAL", default="4w88FbEQhphhx7cXKRSwN8HTgkGWVw"
)
TORRY_TECH_CLIE_SUB = config("TORRY_TECH_CLIE_SUB", default="")

logger = logging.getLogger("observability")


class TorryTechService:
    @staticmethod
    def get_query_url():
        return "https://mobilytech.torrytech.com.br/webservice/tpEspecial/Especial.php"

    @staticmethod
    def get_result_url():
        return "https://mobilytech.torrytech.com.br/Api/Consulta"

    @classmethod
    def request_query(cls, inspection, cons="83", uf=""):
        logger.info(
            f"[TorryTech] Iniciando requisição de consulta. Vistoria ID: {inspection.id}, "
            f"Cons: {cons}, UF informada: {uf}"
        )
        vehicle = getattr(inspection, "vehicle_sga", None)
        if not vehicle:
            logger.warning(
                f"[TorryTech] Falha: Vistoria {inspection.id} não possui veículo associado."
            )
            raise ValidationError("A vistoria não possui veículo associado.")

        plate = (vehicle.plate or "").strip().upper()
        chassi = (vehicle.chassi or "").strip().upper()

        if not plate and not chassi:
            logger.warning(
                f"[TorryTech] Falha: Vistoria {inspection.id} não possui placa ou chassi cadastrado."
            )
            raise ValidationError(
                "A vistoria não possui placa ou chassi cadastrado para o veículo."
            )

        # Check if there is already a completed query for this plate or chassi in the database
        cached_query = None
        if plate:
            cached_query = TorryTechQuery.objects.filter(
                plate=plate, cons=cons, status_consulta="Pronta", success=True
            ).first()
        if not cached_query and chassi:
            cached_query = TorryTechQuery.objects.filter(
                chassi=chassi, cons=cons, status_consulta="Pronta", success=True
            ).first()

        # If cached query is found, create a new record for this inspection copying the data
        if cached_query:
            logger.info(
                f"[TorryTech] Cache Hit: Encontrada consulta anterior id={cached_query.id} para "
                f"placa={plate}/chassi={chassi}. Clonando resultados."
            )
            new_query = TorryTechQuery.objects.create(
                organization_id=inspection.organization_id,
                inspection=inspection,
                plate=plate or cached_query.plate,
                chassi=chassi or cached_query.chassi,
                cons=cons,
                uf=uf or cached_query.uf,
                id_pesquisa=cached_query.id_pesquisa,
                status_consulta="Pronta",
                success=True,
                message="Dados recuperados do cache (pesquisa anterior)",
                response_data=cached_query.response_data,
                link_impressao=cached_query.link_impressao,
            )
            return new_query

        # Clean up failed queries so they can be retried
        TorryTechQuery.objects.filter(
            inspection=inspection, cons=cons, status_consulta="Falha"
        ).delete()

        # Otherwise, check if there's an ongoing (processing) query for this inspection
        existing_query = TorryTechQuery.objects.filter(
            inspection=inspection, cons=cons
        ).first()

        if existing_query:
            logger.info(
                f"[TorryTech] Consulta já existente para a vistoria {inspection.id} e cons {cons}. "
                f"Status: {existing_query.status_consulta}"
            )
            if (
                existing_query.status_consulta == "Processando"
                and existing_query.id_pesquisa
            ):
                logger.info(
                    f"[TorryTech] Consulta em processamento (ID: {existing_query.id_pesquisa}). "
                    f"Iniciando atualização de status..."
                )
                return cls.refresh_query(existing_query)
            return existing_query

        # Create new query record and execute
        param = "PLACA" if plate else "CHASSI"
        cv = plate if plate else chassi

        params = {
            "clie": TORRY_TECH_CLIE,
            "serial": TORRY_TECH_SERIAL,
            "cons": cons,
            "param": param,
            "cv": cv,
        }
        if TORRY_TECH_CLIE_SUB:
            params["clie_sub"] = TORRY_TECH_CLIE_SUB
        if uf:
            params["uf"] = uf

        logger.info(
            f"[TorryTech] Chamando API Especial.php. Param={param}, cv={cv}, uf={uf}"
        )
        try:
            response = requests.get(
                cls.get_query_url(), params=params, timeout=15
            )
            response_json = response.json()
        except Exception as e:
            logger.exception(
                f"[TorryTech] Falha ao conectar com a API Torry Tech Especial.php: {str(e)}"
            )
            raise ValidationError(
                f"Erro ao conectar com a Torry Tech: {str(e)}"
            )

        success = response_json.get("success", False)
        message = response_json.get("message", "")
        id_pesquisa = response_json.get("id_pesquisa")
        status_consulta = response_json.get("status_consulta", "Processando")

        logger.info(
            f"[TorryTech] Resposta da API Especial.php: success={success}, message='{message}', "
            f"id_pesquisa={id_pesquisa}, status_consulta={status_consulta}"
        )

        # Check for already performed query message
        is_already_done = "já foi realizada" in message.lower()

        if not success and not is_already_done:
            logger.error(f"[TorryTech] Consulta retornou erro: {message}")
            query_record = TorryTechQuery.objects.create(
                organization_id=inspection.organization_id,
                inspection=inspection,
                plate=plate,
                chassi=chassi,
                cons=cons,
                uf=uf,
                id_pesquisa=id_pesquisa,
                status_consulta="Falha",
                success=False,
                message=message,
                response_data=response_json,
            )
            return query_record

        # If success, or already done, we create/save the query record and try to fetch results
        query_record = TorryTechQuery.objects.create(
            organization_id=inspection.organization_id,
            inspection=inspection,
            plate=plate,
            chassi=chassi,
            cons=cons,
            uf=uf,
            id_pesquisa=id_pesquisa,
            status_consulta=status_consulta,
            success=True if success else False,
            message=message,
            response_data=response_json,
        )

        if id_pesquisa:
            logger.info(
                f"[TorryTech] Cadastro realizado com sucesso na Torry Tech. "
                f"Consultando resultados imediatos para id_pesquisa={id_pesquisa}..."
            )
            return cls.refresh_query(query_record)

        return query_record

    @classmethod
    def refresh_query(cls, query_record):
        if not query_record.id_pesquisa:
            logger.warning(
                f"[TorryTech] Falha ao tentar atualizar status da consulta {query_record.id}: "
                f"id_pesquisa está ausente."
            )
            return query_record

        params = {
            "clie": TORRY_TECH_CLIE,
            "serial": TORRY_TECH_SERIAL,
            "id_consulta": query_record.id_pesquisa,
        }

        logger.info(
            f"[TorryTech] Chamando API de Consulta para id_consulta={query_record.id_pesquisa}"
        )
        try:
            response = requests.get(
                cls.get_result_url(), params=params, timeout=15
            )
            response_json = response.json()
        except Exception as e:
            logger.exception(
                f"[TorryTech] Erro ao conectar com API de Consulta para id_consulta={query_record.id_pesquisa}: {str(e)}"
            )
            query_record.message = f"Erro ao atualizar dados: {str(e)}"
            query_record.save()
            return query_record

        success = response_json.get("success", False)
        status_consulta = response_json.get(
            "status_consulta", query_record.status_consulta
        )
        message = response_json.get("message", query_record.message)
        link_impressao = response_json.get(
            "link_impressao", query_record.link_impressao
        )

        logger.info(
            f"[TorryTech] Resposta da API de Consulta: success={success}, status_consulta={status_consulta}, "
            f"message='{message}'"
        )

        if success:
            query_record.status_consulta = status_consulta
            query_record.message = message
            query_record.link_impressao = link_impressao
            query_record.response_data = response_json
            query_record.success = True
            query_record.save()
            logger.info(
                f"[TorryTech] Consulta {query_record.id_pesquisa} atualizada com sucesso para status={status_consulta}."
            )
        else:
            if (
                "processando" in message.lower()
                or status_consulta == "Processando"
            ):
                query_record.status_consulta = "Processando"
            else:
                query_record.status_consulta = "Falha"
                logger.error(
                    f"[TorryTech] Consulta {query_record.id_pesquisa} falhou durante atualização: {message}"
                )
            query_record.message = message
            query_record.response_data = response_json
            query_record.save()

        return query_record
