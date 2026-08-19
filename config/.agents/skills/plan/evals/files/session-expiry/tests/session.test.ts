import { describe, expect, it } from "vitest";
import { validateSession } from "../src/session";

const clock = { now: () => new Date("2026-08-13T12:00:00Z") };

describe("validateSession", () => {
  it("rejects an invalid signature", () => {
    expect(validateSession({ id: "session-1", expiresAt: new Date("2026-08-13T13:00:00Z"), signatureValid: false }, clock)).toEqual({ valid: false, reason: "invalid-signature" });
  });
});
