import { homedir } from "node:os";
import { join } from "node:path";

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const NOTIFICATION_SCRIPT = join(homedir(), ".agents", "hooks", "notification.sh");

export default function (pi: ExtensionAPI) {
  pi.on("agent_settled", async (_event, ctx) => {
    if (ctx.mode !== "tui") return;

    await pi.exec(
      "/usr/bin/env",
      ["AGENT_NOTIFICATION_SOURCE=pi", NOTIFICATION_SCRIPT],
      { timeout: 5000 },
    );
  });
}
