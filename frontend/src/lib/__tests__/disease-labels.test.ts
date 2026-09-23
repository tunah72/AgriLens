import { describe, expect, it } from "vitest";
import { getDiseaseDisplayName } from "../disease-labels";

describe("getDiseaseDisplayName", () => {
  it("localizes supported model labels in Vietnamese by default", () => {
    expect(getDiseaseDisplayName("BrownSpot")).toBe("Bệnh đốm nâu hại lúa");
    expect(getDiseaseDisplayName("internal_label")).toBe("Bệnh chưa xác định");
  });

  it("localizes supported model labels in English when requested", () => {
    expect(getDiseaseDisplayName("BrownSpot", "en")).toBe("Brown Spot");
    expect(getDiseaseDisplayName("internal_label", "en")).toBe("Unknown Disease");
  });
});
