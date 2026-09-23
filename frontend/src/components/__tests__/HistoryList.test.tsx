import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { HistoryItem } from "../../lib/api";
import { fetchHistory } from "../../lib/api";
import HistoryList from "../HistoryList";
import { LanguageProvider } from "../../lib/i18n";

vi.mock("../../lib/api", () => ({
  fetchHistory: vi.fn(),
}));

const mockFetchHistory = vi.mocked(fetchHistory);

function makeItem(index: number): HistoryItem {
  return {
    id: `prediction-${index}`,
    image_id: `image-${index}`,
    predicted_label: `Disease ${index}`,
    confidence: 0.8,
    top_k: [],
    created_at: "2026-07-15T08:00:00Z",
  };
}

describe("HistoryList pagination", () => {
  beforeEach(() => {
    mockFetchHistory.mockReset();
    mockFetchHistory.mockImplementation(async (_token, page = 1) => {
      const start = (page - 1) * 5 + 1;
      const end = Math.min(start + 4, 11);
      return {
        items: Array.from({ length: end - start + 1 }, (_, index) => makeItem(start + index)),
        total: 11,
        page,
        page_size: 5,
      };
    });
  });

  it("navigates deterministically across three pages for eleven records in Vietnamese by default", async () => {
    const user = userEvent.setup();

    render(<HistoryList token="demo-token" onLoginPrompt={vi.fn()} onStartDiagnosis={vi.fn()} />);

    expect(await screen.findByText("Disease 1")).toBeVisible();
    expect(screen.getByText("Trang 1 / 3")).toBeVisible();
    expect(screen.getByRole("button", { name: "Trang trước" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Trang 2" }));
    expect(await screen.findByText("Disease 6")).toBeVisible();
    expect(screen.getByText("Trang 2 / 3")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Trang sau" }));
    expect(await screen.findByText("Disease 11")).toBeVisible();
    expect(screen.getByText("Trang 3 / 3")).toBeVisible();
    expect(screen.getByRole("button", { name: "Trang sau" })).toBeDisabled();

    await waitFor(() => {
      expect(mockFetchHistory).toHaveBeenNthCalledWith(3, "demo-token", 3, 5);
    });
  });

  it("supports English pagination when LanguageProvider specifies English", async () => {
    const user = userEvent.setup();

    render(
      <LanguageProvider defaultLang="en">
        <HistoryList token="demo-token" onLoginPrompt={vi.fn()} onStartDiagnosis={vi.fn()} />
      </LanguageProvider>
    );

    expect(await screen.findByText("Disease 1")).toBeVisible();
    expect(screen.getByText("Page 1 of 3")).toBeVisible();
    expect(screen.getByRole("button", { name: "Previous page" })).toBeDisabled();
  });
});
