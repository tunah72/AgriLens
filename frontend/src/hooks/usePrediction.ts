import { useState } from "react";
import { predictImage, PredictionResponse } from "../lib/api";

export function usePrediction() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFileSelect = (file: File | null, validationError: string | null) => {
    setSelectedFile(file);
    setError(validationError);
    setPrediction(null); // Clear previous results
  };

  const handleSubmit = async (token?: string) => {
    if (!selectedFile) {
      setError("Please select or capture a leaf photo before submitting.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setPrediction(null);

    try {
      const result = await predictImage(selectedFile, token);
      setPrediction(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred during diagnosis.");
      // Note: we preserve the selectedFile state here so the user doesn't have to re-select it
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPrediction(null);
    setError(null);
    setIsSubmitting(false);
  };

  return {
    selectedFile,
    prediction,
    error,
    isSubmitting,
    handleFileSelect,
    handleSubmit,
    handleReset,
  };
}
