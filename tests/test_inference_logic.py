import numpy as np
import pytest

from backend.app.services.inference import InferenceService


@pytest.fixture
def inference_service(monkeypatch):
    import pathlib

    import onnxruntime

    # Mock Path.exists to return True for the expected ONNX model paths
    original_exists = pathlib.Path.exists

    def mock_exists(self):
        if self.name in ("yolo26_rice_quantized.onnx", "yolo26_coffee_quantized.onnx"):
            return True
        return original_exists(self)

    monkeypatch.setattr(pathlib.Path, "exists", mock_exists)

    # Mock onnxruntime.InferenceSession
    class MockInferenceSession:
        def __init__(self, model_path, providers=None):
            self.model_path = model_path
            self.providers = providers

        def get_inputs(self):
            class MockInput:
                def __init__(self, name):
                    self.name = name

            return [MockInput("images")]

        def run(self, output_names, input_feed, run_options=None):
            return [np.zeros((1, 300, 38), dtype=np.float32)]

    monkeypatch.setattr(onnxruntime, "InferenceSession", MockInferenceSession)

    class_names = InferenceService.load_class_names("models/class_names.json")
    return InferenceService("models/yolo26_rice_quantized.onnx", class_names)


def test_inference_service_loads_models(inference_service):
    assert inference_service.has_both is True
    assert len(inference_service.rice_class_names) == 4
    assert len(inference_service.coffee_class_names) == 4


def test_onnx_shape_parsing_logic(inference_service):
    # Case 1: End-to-end model with 38 columns (e.g. [1, 300, 38])
    # The parsing should treat col 4 as conf and col 5 as class_id
    mock_e2e_output = np.zeros((1, 300, 38), dtype=np.float32)
    # Detection 1: conf 0.85, class 1
    mock_e2e_output[0, 0, 4] = 0.85
    mock_e2e_output[0, 0, 5] = 1.0
    # Detection 2: conf 0.95, class 2
    mock_e2e_output[0, 1, 4] = 0.95
    mock_e2e_output[0, 1, 5] = 2.0

    scores = inference_service._class_scores_from_output_for_classes(mock_e2e_output, 4)
    assert np.allclose(scores, [0.0, 0.85, 0.95, 0.0])

    # Case 2: Standard YOLOv8 model with 8 columns (e.g. [1, 8, 8400] transposed to [1, 8400, 8])
    # The parsing should NOT execute the end-to-end path. It should just take max along axis 0
    # for class scores at columns 4, 5, 6, 7.
    mock_std_output = np.zeros((1, 8400, 8), dtype=np.float32)
    # Box 1: class 0 score 0.70, class 1 score 0.20, class 2 score 0.10, class 3 score 0.05
    mock_std_output[0, 0, 4:] = [0.70, 0.20, 0.10, 0.05]
    # Box 2: class 0 score 0.10, class 1 score 0.90, class 2 score 0.05, class 3 score 0.02
    mock_std_output[0, 1, 4:] = [0.10, 0.90, 0.05, 0.02]

    scores_std = inference_service._class_scores_from_output_for_classes(mock_std_output, 4)
    assert np.allclose(scores_std, [0.70, 0.90, 0.10, 0.05])


def test_crop_routing_by_filename(inference_service):
    # Dummy leaf image (1x1 black image converted to bytes)
    import io

    from PIL import Image

    img = Image.new("RGB", (100, 100), color="green")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    image_bytes = img_byte_arr.getvalue()

    # Case 1: Filename implies coffee crop -> should route to coffee model classes
    coffee_preds = inference_service.predict(image_bytes, filename="my-coffee-leaf.jpg")
    # All predicted classes should belong to coffee_class_names
    for label, _ in coffee_preds:
        assert label in inference_service.coffee_class_names

    # Case 2: Filename implies rice crop -> should route to rice model classes
    rice_preds = inference_service.predict(image_bytes, filename="lalua-disease.jpg")
    for label, _ in rice_preds:
        assert label in inference_service.rice_class_names


def test_crop_routing_by_explicit_parameter(inference_service):
    import io

    from PIL import Image

    img = Image.new("RGB", (100, 100), color="green")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    image_bytes = img_byte_arr.getvalue()

    # Even if filename is None or says "rice", explicit crop="coffee" should route to coffee
    preds = inference_service.predict(image_bytes, filename="rice.jpg", crop="coffee")
    for label, _ in preds:
        assert label in inference_service.coffee_class_names

    preds_rice = inference_service.predict(image_bytes, filename="coffee.jpg", crop="rice")
    for label, _ in preds_rice:
        assert label in inference_service.rice_class_names


def test_raw_probabilities_not_deflated_by_softmax(inference_service):
    import io

    from PIL import Image

    img = Image.new("RGB", (100, 100), color="green")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    image_bytes = img_byte_arr.getvalue()

    # Predict using coffee crop to check outputs
    preds = inference_service.predict(image_bytes, crop="coffee")
    # Since it's a dummy green image, scores will be low or 0.0,
    # but the highest score should NOT be capped under 0.475 if a real detection existed.
    # Let's mock coffee_session.run to return a high confidence detection
    original_run = inference_service.coffee_session.run

    # We want to mock outputs to return one box with 0.95 confidence for Rust (class 3)
    mock_outputs = [np.zeros((1, 300, 38), dtype=np.float32)]
    mock_outputs[0][0, 0, 4] = 0.95
    mock_outputs[0][0, 0, 5] = 3.0  # Rust

    inference_service.coffee_session.run = lambda *args, **kwargs: mock_outputs

    try:
        preds = inference_service.predict(image_bytes, crop="coffee")
        # Top prediction should be Rust with confidence exactly 0.95
        assert preds[0][0] == "Rust"
        assert abs(preds[0][1] - 0.95) < 1e-5
    finally:
        inference_service.coffee_session.run = original_run


def test_real_quantized_model_inference():
    """Verify real quantized ONNX model loads and runs inference without mocks."""
    import io
    from pathlib import Path

    from PIL import Image

    model_path = Path("models/yolo26_quantized.onnx")
    class_names_path = Path("models/class_names.json")
    if not model_path.exists() or not class_names_path.exists():
        pytest.skip("Quantized model or class names file not found")

    class_names = InferenceService.load_class_names(str(class_names_path))
    service = InferenceService(str(model_path), class_names, input_size=1024)

    # Create a test leaf image
    img = Image.new("RGB", (256, 256), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    preds = service.predict(image_bytes)
    assert isinstance(preds, list)
    assert len(preds) > 0
    for label, conf in preds:
        assert label in class_names
        assert 0.0 <= conf <= 1.0
