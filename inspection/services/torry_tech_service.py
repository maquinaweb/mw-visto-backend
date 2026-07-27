import logging
import requests
from decouple import config
from rest_framework.exceptions import ValidationError

from inspection.models.torry_tech_query import TorryTechQuery

TORRY_TECH_CLIE = config("TORRY_TECH_CLIE", default="3099")
TORRY_TECH_SERIAL = config("TORRY_TECH_SERIAL", default="")
TORRY_TECH_SERIAL_CONSULTA = config("TORRY_TECH_SERIAL_CONSULTA", default="")
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
    def _execute_especial_php(cls, cons, param, cv, uf=""):
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
            f"[TorryTech] Chamando Especial.php. Param={param}, cv={cv}, uf={uf}"
        )
        try:
            response = requests.get(
                cls.get_query_url(), params=params, timeout=15
            )
            return response.json()
        except Exception as e:
            logger.exception(
                f"[TorryTech] Erro ao conectar com Especial.php: {str(e)}"
            )
            raise ValidationError(
                f"Erro ao conectar com a Torry Tech: {str(e)}"
            )

    @classmethod
    def request_query(cls, inspection, cons="83", uf=""):
        logger.info(
            f"[TorryTech] Solicitando consulta veicular. Vistoria ID: {inspection.id}, "
            f"Cons: {cons}, UF: {uf}"
        )
        vehicle = getattr(inspection, "vehicle_sga", None)
        if not vehicle:
            raise ValidationError("A vistoria não possui veículo associado.")

        plate = (vehicle.plate or "").strip().upper()
        chassi = (vehicle.chassi or "").strip().upper()

        if not plate and not chassi:
            raise ValidationError(
                "A vistoria não possui placa ou chassi cadastrado para o veículo."
            )

        # Se já existe uma consulta registrada para ESTA vistoria com o mesmo cons
        existing_query = TorryTechQuery.objects.filter(
            inspection=inspection, cons=cons
        ).first()

        if existing_query:
            if existing_query.status_consulta == "Falha":
                existing_query.delete()
            elif existing_query.id_pesquisa:
                return cls.refresh_query(existing_query)
            else:
                return existing_query

        # Tenta primeira consulta (por PLACA se existir, senão por CHASSI)
        param = "PLACA" if plate else "CHASSI"
        cv = plate if plate else chassi

        response_json = cls._execute_especial_php(cons, param, cv, uf)

        success = response_json.get("success", False)
        message = response_json.get("message", "")
        id_pesquisa = response_json.get("id_pesquisa")
        status_consulta = response_json.get("status_consulta", "Processando")
        dados_veiculo = response_json.get("dados_veiculo")
        link_impressao = response_json.get("link_impressao")

        # Se a consulta por PLACA disser que já foi realizada, mas tivermos o CHASSI disponível,
        # tentamos consultar por CHASSI para obter um id_pesquisa atualizado e ativo na API
        is_already_done = "já foi realizada" in message.lower()
        if is_already_done and param == "PLACA" and chassi:
            logger.info(
                f"[TorryTech] Consulta por PLACA informou 'já foi realizada'. Tentando via CHASSI={chassi}..."
            )
            chassi_response = cls._execute_especial_php(
                cons, "CHASSI", chassi, uf
            )
            if chassi_response.get("id_pesquisa") or chassi_response.get(
                "success"
            ):
                response_json = chassi_response
                success = response_json.get("success", False)
                message = response_json.get("message", "")
                id_pesquisa = response_json.get("id_pesquisa")
                status_consulta = response_json.get(
                    "status_consulta", "Processando"
                )
                dados_veiculo = response_json.get("dados_veiculo")
                link_impressao = response_json.get("link_impressao")

        if not success and not is_already_done and not dados_veiculo:
            logger.error(f"[TorryTech] Consulta retornou erro: {message}")
            return TorryTechQuery.objects.create(
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

        query_record = TorryTechQuery.objects.create(
            organization_id=inspection.organization_id,
            inspection=inspection,
            plate=plate,
            chassi=chassi,
            cons=cons,
            uf=uf,
            id_pesquisa=id_pesquisa,
            status_consulta=status_consulta,
            success=True
            if (success or status_consulta in ["Pronta", "Concluido"])
            else False,
            message=message,
            link_impressao=link_impressao or "",
            response_data=response_json,
        )

        if id_pesquisa:
            return cls.refresh_query(query_record)

        return query_record

    @classmethod
    def refresh_query(cls, query_record):
        if not query_record.id_pesquisa:
            return query_record

        params = {
            "clie": TORRY_TECH_CLIE,
            "serial": TORRY_TECH_SERIAL_CONSULTA,
            "id_consulta": query_record.id_pesquisa,
        }
        if TORRY_TECH_CLIE_SUB:
            params["clie_sub"] = TORRY_TECH_CLIE_SUB

        logger.info(
            f"[TorryTech] Consultando resultados via Api/Consulta para id_consulta={query_record.id_pesquisa}"
        )
        try:
            response = requests.get(
                cls.get_result_url(), params=params, timeout=15
            )
            response_json = response.json()
        except Exception as e:
            logger.exception(
                f"[TorryTech] Erro ao conectar com Api/Consulta: {str(e)}"
            )
            query_record.message = f"Erro ao atualizar dados: {str(e)}"
            query_record.save()
            return query_record

        success = response_json.get("success", False)
        status_consulta = response_json.get("status_consulta", None)
        message = response_json.get("message", query_record.message)
        link_impressao = (
            response_json.get("link_impressao")
            or query_record.link_impressao
            or ""
        )
        new_dados = response_json.get("dados_veiculo")
        new_parciais = response_json.get("parciais")

        # Preserva dados do veículo da etapa 1 caso a etapa 2 retorne dados_veiculo como array vazio
        existing_dados = {}
        if query_record.response_data and isinstance(
            query_record.response_data.get("dados_veiculo"), dict
        ):
            existing_dados = (
                query_record.response_data.get("dados_veiculo") or {}
            )

        if isinstance(new_dados, dict) and new_dados:
            merged_dados = {**existing_dados, **new_dados}
        else:
            merged_dados = existing_dados

        response_json["dados_veiculo"] = merged_dados
        response_json["link_impressao"] = link_impressao

        if success or (new_parciais and len(new_parciais) > 0):
            # Verifica se alguma parcial ainda está pendente (sem resultado preenchido)
            parciais_pending = False
            if new_parciais and isinstance(new_parciais, list):
                # Se alguma parcial ainda tiver resultado em branco, continua "Processando"
                has_empty_parcial = any(
                    not bool((p.get("Resultado") or "").strip())
                    for p in new_parciais
                )
                if has_empty_parcial:
                    parciais_pending = True

            if status_consulta == "Processando" or parciais_pending:
                final_status = "Processando"
            else:
                final_status = status_consulta or "Pronta"

            query_record.status_consulta = final_status
            query_record.message = message
            query_record.link_impressao = link_impressao
            query_record.response_data = response_json
            query_record.success = True
            query_record.save()
            logger.info(
                f"[TorryTech] Consulta {query_record.id_pesquisa} atualizada para status={query_record.status_consulta}."
            )
        else:
            if (
                "processando" in message.lower()
                or status_consulta == "Processando"
            ):
                query_record.status_consulta = "Processando"
                query_record.message = message
                query_record.response_data = response_json
            else:
                has_valid_parciais = (
                    query_record.response_data
                    and isinstance(
                        query_record.response_data.get("parciais"), list
                    )
                    and len(query_record.response_data.get("parciais")) > 0
                )
                if not has_valid_parciais:
                    query_record.status_consulta = "Falha"
                    query_record.message = message
                    query_record.response_data = response_json
                    query_record.success = False
            query_record.save()

        return query_record
