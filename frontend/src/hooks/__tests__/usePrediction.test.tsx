import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { predictImage } from "../../lib/api";
import { usePrediction } from "../usePrediction";

vi.mock("../../lib/api", () => ({
  predictImage: vi.fn(),
}));

const mockPredictImage = vi.mocked(predictImage);

describe("usePrediction", () => {
  beforeEach(() => {
    mockPredictImage.mockReset();
  });

  it("clears the selected file and previous result when a new diagnosis starts", async () => {
    const file = new File(["leaf"], "leaf.png", { type: "image/png" });
    mockPredictImage.mockResolvedValueOnce({
      prediction: "Healthy",
      confidence: 0.98,
      top_k: [],
    });

    const { result } = renderHook(() => usePrediction());

    act(() => {
      result.current.handleFileSelect(file, null);
    });
    await act(async () => {
      await result.current.handleSubmit("demo-token");
    });

    expect(result.current.selectedFile).toBe(file);
    expect(result.current.prediction?.prediction).toBe("Healthy");

    act(() => {
      result.current.handleReset();
    });

    expect(result.current.selectedFile).toBeNull();
    expect(result.current.prediction).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isSubmitting).toBe(false);
  });
});
