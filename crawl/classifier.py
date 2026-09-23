"""VLM image classification module with prompt construction and mock support."""

import json
import logging
from typing import Any

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


def build_classification_prompt(crop: str, classes: list[str], context: str) -> str:
    """Construct an expert agricultural classification prompt in English.

    Args:
        crop: Crop name ('rice' or 'coffee').
        classes: List of valid class labels.
        context: Text context surrounding the image on the web page.

    Returns:
        Formatted prompt string.
    """
    category_list = ", ".join(classes)
    return (
        f"You are an agricultural expert specialising in {crop} plants. "
        f'Look at this image and the surrounding context from an agricultural source: "{context}".\n'
        f"Determine if this is a valid close-up of a {crop} plant or leaf. "
        f"If it is, classify it strictly as ONE of these categories: {category_list}.\n"
        f'Respond ONLY with a JSON object in this format: {{"prediction": "LabelName"}}. '
        f'If it is not a valid image of a {crop} plant, respond with {{"prediction": "Invalid"}}.'
    )


async def classify_image(
    crop: str,
    classes: list[str],
    base64_image: str,
    context: str,
    client: AsyncOpenAI | None = None,
    mock: bool = False,
) -> str:
    """Classify an image using a Vision-Language Model or deterministic mock.

    Args:
        crop: Crop name.
        classes: Allowed classes for classification.
        base64_image: Data URL base64 image string.
        context: Context text extracted alongside the image.
        client: AsyncOpenAI client instance.
        mock: If True, returns deterministic mock response without network call.

    Returns:
        Predicted disease label string.
    """
    if mock or client is None:
        return classes[0] if classes else "Healthy"

    prompt_text = build_classification_prompt(crop, classes, context)
    try:
        response = await client.chat.completions.create(
            model="local-vlm",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": base64_image}},
                    ],
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = response.choices[0].message.content or "{}"
        prediction_data = json.loads(content)
        return prediction_data.get("prediction", "Unknown")
    except Exception as e:
        logger.error(f"Error classifying image: {e}")
        return f"Error: {e}"


async def classify_task(
    task_data: dict[str, Any],
    ai_client: AsyncOpenAI | None,
    crop: str,
    classes: list[str],
    semaphore,
    final_file,
    file_lock,
    mock: bool = False,
) -> None:
    """Classify a single task and write output to final JSONL file."""
    async with semaphore:
        try:
            prediction = await classify_image(
                crop=crop,
                classes=classes,
                base64_image=task_data.get("base64", ""),
                context=task_data.get("context", ""),
                client=ai_client,
                mock=mock,
            )

            if not prediction.startswith("Error:"):
                annotation_entry = {
                    "data": {
                        "image": task_data["image_path"],
                        "source_url": task_data.get("source_url", ""),
                        "context_text": task_data.get("context", ""),
                        "crop": crop,
                    },
                    "predictions": [
                        {
                            "model_version": "vlm-prelabel",
                            "result": [
                                {
                                    "from_name": "choice",
                                    "to_name": "image",
                                    "type": "choices",
                                    "value": {"choices": [prediction]},
                                }
                            ],
                        }
                    ],
                }
                async with file_lock:
                    with open(final_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(annotation_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Error in classify_task: {e}")
