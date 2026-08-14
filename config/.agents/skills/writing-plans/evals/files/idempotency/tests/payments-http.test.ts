import { describe, expect, it, vi } from "vitest";
import { createPaymentHandler } from "../src/http";

describe("POST /payments", () => {
  it("creates a payment", async () => {
    const service = { create: vi.fn().mockResolvedValue({ id: "payment-1", accountId: "account-1", amountCents: 1200 }) };
    const handler = createPaymentHandler(service);
    const response = await handler(new Request("https://example.test/payments", { method: "POST", body: JSON.stringify({ accountId: "account-1", amountCents: 1200 }) }));
    expect(response.status).toBe(201);
  });
});
