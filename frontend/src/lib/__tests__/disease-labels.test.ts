import { describe, expect, it } from "vitest";
import { getDiseaseDisplayName } from "../disease-labels";

describe("getDiseaseDisplayName", () => {
  it("localizes supported model labels and never returns an unknown raw label", () => {
    expect(getDiseaseDisplayName("BrownSpot")).toBe("Brown Spot");
    expect(getDiseaseDisplayName("internal_label")).toBe("Unknown Disease");
  });
});
