// supabase/functions/push-dispatcher/index.ts

// 🔴 IMPORTANT : ce fichier est exécuté par Deno (Supabase Edge)
// Il est NORMAL que Cursor/TS de l’app mobile affiche des warnings

import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

type OutboxRow = {
  id: string;
  user_id: string;
  kind: "chat" | "system";
  title: string | null;
  body: string;
  data: Record<string, unknown>;
  attempts: number;
};

const EXPO_PUSH_URL =
  Deno.env.get("EXPO_PUSH_URL") ||
  "https://exp.host/--/api/v2/push/send";

serve(async (_req: Request) => {
  const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
  const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

  const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
    auth: { persistSession: false },
  });

  const log = (...args: any[]) =>
    console.log("[push-dispatcher]", ...args);

  try {
    // 1️⃣ Pop des jobs
    const { data: jobs, error } = await supabase.rpc(
      "pop_push_outbox",
      { p_limit: 25 }
    );
    if (error) throw error;

    const rows = (jobs ?? []) as OutboxRow[];
    if (rows.length === 0) {
      return new Response(
        JSON.stringify({ ok: true, picked: 0 }),
        { status: 200 }
      );
    }

    log("picked", rows.length);

    // 2️⃣ Re-check règles + tokens
    const toSend: Array<{ outbox: OutboxRow; tokens: string[] }> = [];

    for (const r of rows) {
      const { data: canSend } = await supabase.rpc(
        "should_send_push",
        { p_user_id: r.user_id, p_kind: r.kind }
      );

      if (!canSend) {
        await supabase
          .from("push_outbox")
          .update({
            status: "sent",
            error: "skipped_presence_rule",
            sent_at: new Date().toISOString(),
          })
          .eq("id", r.id);
        continue;
      }

      const { data: devices } = await supabase
        .from("push_devices")
        .select("expo_push_token")
        .eq("user_id", r.user_id);

      const tokens =
        (devices ?? [])
          .map((d: any) => d.expo_push_token)
          .filter(
            (t: any) =>
              typeof t === "string" &&
              t.startsWith("ExponentPushToken")
          );

      if (tokens.length === 0) {
        await supabase
          .from("push_outbox")
          .update({ status: "failed", error: "no_tokens" })
          .eq("id", r.id);
        continue;
      }

      toSend.push({ outbox: r, tokens });
    }

    if (toSend.length === 0) {
      return new Response(
        JSON.stringify({ ok: true, ready: 0 }),
        { status: 200 }
      );
    }

    // 3️⃣ Payload Expo
    const messages = toSend.flatMap(({ outbox, tokens }) =>
      tokens.map((token) => ({
        to: token,
        sound: "default",
        title: outbox.title ?? "HeyLisa",
        body: outbox.body,
        data: {
          ...(outbox.data ?? {}),
          outbox_id: outbox.id,
          kind: outbox.kind,
        },
      }))
    );

    // 4️⃣ Envoi
    const resp = await fetch(EXPO_PUSH_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(messages),
    });

    if (!resp.ok) {
      await supabase
        .from("push_outbox")
        .update({ status: "failed", error: `expo_${resp.status}` })
        .in(
          "id",
          toSend.map((p) => p.outbox.id)
        );

      return new Response(
        JSON.stringify({ ok: false, status: resp.status }),
        { status: 200 }
      );
    }

    // 5️⃣ Mark sent
    await supabase
      .from("push_outbox")
      .update({
        status: "sent",
        sent_at: new Date().toISOString(),
        error: null,
      })
      .in(
        "id",
        toSend.map((p) => p.outbox.id)
      );

    return new Response(
      JSON.stringify({ ok: true, sent: toSend.length }),
      { status: 200 }
    );
  } catch (e: any) {
    console.error("[push-dispatcher] fatal", e);
    return new Response(
      JSON.stringify({ ok: false, error: String(e) }),
      { status: 200 }
    );
  }
});