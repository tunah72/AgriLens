import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import Sidebar from "../Sidebar";
import { LanguageProvider } from "../../lib/i18n";

describe("Sidebar", () => {
  it("runs the dedicated new-diagnosis action and prevents it while prediction is running (Vietnamese by default)", async () => {
    const user = userEvent.setup();
    const onNewDiagnosis = vi.fn();
    const onTabChange = vi.fn();

    const { rerender } = render(
      <Sidebar
        activeTab="history"
        onTabChange={onTabChange}
        onNewDiagnosis={onNewDiagnosis}
        user={null}
        isLoading={false}
        isPredictionSubmitting={false}
        logout={vi.fn()}
        onLoginClick={vi.fn()}
      />,
    );

    await user.click(screen.getByTitle("Chẩn đoán mới"));
    expect(onNewDiagnosis).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole("button", { name: "Chẩn đoán" }));
    expect(onNewDiagnosis).toHaveBeenCalledTimes(2);
    expect(onTabChange).not.toHaveBeenCalled();

    rerender(
      <Sidebar
        activeTab="history"
        onTabChange={onTabChange}
        onNewDiagnosis={onNewDiagnosis}
        user={null}
        isLoading={false}
        isPredictionSubmitting
        logout={vi.fn()}
        onLoginClick={vi.fn()}
      />,
    );

    expect(screen.getByTitle("Chẩn đoán mới")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Chẩn đoán" })).toBeDisabled();
  });

  it("supports English labels when LanguageProvider is set to English", async () => {
    const user = userEvent.setup();
    const onNewDiagnosis = vi.fn();

    render(
      <LanguageProvider defaultLang="en">
        <Sidebar
          activeTab="history"
          onTabChange={vi.fn()}
          onNewDiagnosis={onNewDiagnosis}
          user={null}
          isLoading={false}
          isPredictionSubmitting={false}
          logout={vi.fn()}
          onLoginClick={vi.fn()}
        />
      </LanguageProvider>
    );

    await user.click(screen.getByTitle("New diagnosis"));
    expect(onNewDiagnosis).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole("button", { name: "Diagnosis" }));
    expect(onNewDiagnosis).toHaveBeenCalledTimes(2);
  });

  it("keeps the mobile authentication affordance in a loading state during session restoration", () => {
    render(
      <Sidebar
        activeTab="diagnosis"
        onTabChange={vi.fn()}
        onNewDiagnosis={vi.fn()}
        user={null}
        isLoading
        isPredictionSubmitting={false}
        logout={vi.fn()}
        onLoginClick={vi.fn()}
      />,
    );

    expect(screen.getAllByRole("status", { name: "Đang tải trạng thái tài khoản" })).toHaveLength(2);
    expect(screen.queryByRole("button", { name: "Đăng nhập" })).not.toBeInTheDocument();
  });
});
