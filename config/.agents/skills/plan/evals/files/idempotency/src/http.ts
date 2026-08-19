import type { PaymentService } from "./payments";

export function createPaymentHandler(service: PaymentService) {
  return async function handle(request: Request): Promise<Response> {
    const body = await request.json();
    const payment = await service.create(body);
    return Response.json(payment, { status: 201 });
  };
}
