export interface CreatePaymentInput {
  accountId: string;
  amountCents: number;
}

export interface Payment {
  id: string;
  accountId: string;
  amountCents: number;
}

export interface PaymentService {
  create(input: CreatePaymentInput): Promise<Payment>;
}
