import logging
import random
import time
import requests
from decouple import config

from core.observability.tasks import tracked_task
from inspection.models.step import InspectionStep
from inspection.services import get_step_image_base64

logger = logging.getLogger("observability")


@tracked_task
def analyze_steps_task(inspection_id: int):
    """
    Triggers separate parallel tasks for each completed step in an inspection.
    """
    logger.info(
        f"Triggering step analysis tasks for inspection {inspection_id}"
    )

    steps = InspectionStep.objects.filter(
        inspection_id=inspection_id,
        status__in=["realized", "approved", "rejected"],
    ).exclude(file="")

    if not steps.exists():
        logger.warning(
            f"No steps with files found for inspection {inspection_id}"
        )
        return

    for step in steps:
        # Trigger the Zappa asynchronous task for this single step.
        # This will run each task in parallel on separate Lambda instances.
        analyze_single_step_task(step.id)

    logger.info(
        f"AI analysis trigger complete for inspection {inspection_id}. "
        f"Spawned {steps.count()} parallel task(s)."
    )


@tracked_task
def analyze_single_step_task(step_id: int):
    """
    Asynchronously analyzes the image for a single step
    using Cerebras Gemma-4-31b multimodal model and writes an evaluation description.
    """
    try:
        step = InspectionStep.objects.select_related("type_step").get(
            id=step_id
        )
    except InspectionStep.DoesNotExist:
        logger.error(f"Step {step_id} not found.")
        return

    if not step.file:
        logger.warning(f"Step {step_id} has no file to analyze.")
        return

    api_key = config("CEREBRAS_API_KEY", default=None)
    if not api_key:
        logger.error("Cerebras API key CEREBRAS_API_KEY not configured in env.")
        return

    logger.info(f"Analyzing step {step.id} (Order: {step.order})...")

    try:
        # Get image base64 representation via step_image service (downloading and converting WebP as needed)
        base64_image = get_step_image_base64(step)
        mime_type = "image/jpeg"

        step_title = (
            step.type_step.title if step.type_step else "Passo de Vistoria"
        )
        step_instructions = (
            step.type_step.instructions if step.type_step else ""
        )

        prompt = (
            f"Você é um vistoriador veicular especialista e detalhista.\n"
            f"Analise a imagem fornecida para a etapa '{step_title}'.\n"
            f"Diretrizes desta etapa:\n{step_instructions}\n\n"
            "Sua principal tarefa é identificar possíveis avarias, danos, riscos, amassados, trincas, peças quebradas "
            "ou qualquer anomalia visível no veículo nesta imagem. "
            "Descreva de forma concisa e direta (em até 3 frases) o que está visível, detalhando qualquer avaria encontrada "
            "e avaliando se a etapa foi cumprida corretamente. Se não houver avarias, informe que o componente está em bom estado aparente. "
            "Importante: Responda diretamente com o texto da análise técnica, sem saudações, introduções ou formatação markdown."
        )

        payload = {
            "model": "gemma-4-31b",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            "temperature": 0.2,
            "max_tokens": 300,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Call Cerebras OpenAI compatible completions endpoint with retry on 429
        max_retries = 5
        retry_delay = 2.0  # seconds
        response = None

        for attempt in range(max_retries):
            response = requests.post(
                "https://api.cerebras.ai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=45,
            )

            if response.status_code == 200:
                break
            elif response.status_code == 429:
                jitter = random.uniform(0.5, 1.5)
                sleep_time = retry_delay * (2**attempt) * jitter
                logger.warning(
                    f"Cerebras API rate limited (429) for step {step.id}. "
                    f"Retrying in {sleep_time:.2f} seconds (Attempt {attempt + 1}/{max_retries})..."
                )
                time.sleep(sleep_time)
            else:
                break

        if response and response.status_code == 200:
            result = response.json()
            ai_description = result["choices"][0]["message"]["content"].strip()
            step.description = ai_description
            step.save(update_fields=["description"])
            logger.info(f"Successfully analyzed step {step.id}.")
        else:
            status_code = response.status_code if response else "No Response"
            response_text = response.text if response else ""
            logger.error(
                f"Cerebras API returned status {status_code} for step {step.id}: {response_text}"
            )

    except Exception as e:
        logger.exception(f"Error analyzing step {step.id}: {e}")
