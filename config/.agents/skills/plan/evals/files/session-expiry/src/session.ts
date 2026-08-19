export interface Clock {
  now(): Date;
}

export interface Session {
  id: string;
  expiresAt: Date;
  signatureValid: boolean;
}

export type SessionValidation =
  | { valid: true }
  | { valid: false; reason: "invalid-signature" | "expired" };

export function validateSession(
  session: Session,
  _clock: Clock,
): SessionValidation {
  if (!session.signatureValid) {
    return { valid: false, reason: "invalid-signature" };
  }
  return { valid: true };
}
