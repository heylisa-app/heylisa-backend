// Supabase Edge Function: hyper-action
// Receive RevenueCat webhooks and sync entitlements -> Supabase DB
// Tables updated:
// - public.users.is_pro  (RULE: true if at least one active entitlement)
// - public.lisa_user_agents.status per agent_key (active/off)
// - public.billing_events (log)
// - public.billing_state (cache)

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

const nowIso = () => new Date().toISOString();
const nowMs = () => Date.now();

const isObj = (o: any) => o && typeof o === "object" && !Array.isArray(o);

function pickEvent(payload: any) {
  return payload?.event ?? payload;
}

function pickAttrs(evt: any) {
  return evt?.attributes ?? evt;
}

function getAuthToken(req: Request) {
  const h = req.headers.get("authorization") || "";
  return h.toLowerCase().startsWith("bearer ") ? h.slice(7).trim() : h.trim();
}

function safeArray(v: any): string[] {
  if (Array.isArray(v)) return v.map(String).filter(Boolean);
  if (typeof v === "string" && v.trim()) return [v.trim()];
  return [];
}

function toIsoOrNull(v: any): string | null {
  if (!v) return null;
  try {
    return new Date(v).toISOString();
  } catch {
    return null;
  }
}

function pickProviderEventId(evt: any, attrs: any): string | null {
  const candidates = [
    evt?.id,
    evt?.event_id,
    attrs?.event_id,
    attrs?.id,
    attrs?.transaction_id,
    attrs?.original_transaction_id,
    attrs?.purchase_id,
  ]
    .map((x) => (x == null ? "" : String(x).trim()))
    .filter(Boolean);

  return candidates[0] ?? null;
}

function isUuid(v: any): boolean {
  if (typeof v !== "string") return false;
  const s = v.trim();
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(s);
}

function pickAuthUuid(evt: any, attrs: any): string {
  const candidates: string[] = [];

  // direct
  candidates.push(String(attrs?.app_user_id ?? ""));
  candidates.push(String(attrs?.original_app_user_id ?? ""));
  candidates.push(String(evt?.app_user_id ?? ""));
  candidates.push(String(evt?.original_app_user_id ?? ""));

  // transfer
  candidates.push(String(evt?.transferred_to ?? attrs?.transferred_to ?? ""));
  const tf = evt?.transferred_from ?? attrs?.transferred_from;
  if (Array.isArray(tf)) candidates.push(...tf.map((x: any) => String(x)));

  // aliases RC (souvent présent, utile en sandbox / tests)
  const aliases = evt?.aliases ?? attrs?.aliases;
  if (Array.isArray(aliases)) candidates.push(...aliases.map((x: any) => String(x)));

  for (const c of candidates) {
    const s = (c || "").trim();
    if (isUuid(s)) return s;
  }

  return "";
}

async function sha256Hex(input: string): Promise<string> {
  const data = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function computeProviderEventId(evt: any, attrs: any, payload: any): Promise<string> {
  const existing = pickProviderEventId(evt, attrs);
  if (existing) return existing;

  // fallback stable: hash du payload complet
  const raw = JSON.stringify(payload ?? {});
  const h = await sha256Hex(raw);

  // format lisible
  return `payload_sha256:${h}`;
}

// ---- CONFIG ----

// RevenueCat entitlements identifiers -> internal agent_key mapping
const ENTITLEMENT_TO_AGENT_KEY: Record<string, string> = {
  airbnb_assistant: "airbnb_assistant",
  medical_assistant: "medical_assistant",
  executive_assistant: "executive_assistant",
  ultimate_assistant: "ultimate_assistant",
};

// “core” identifiers (optional). Keep as-is.
const CORE_ENTITLEMENT_IDS = new Set(["HeyLisa Pro", "heylisa_pro", "pro"]);

// MODE detection
// - DELTA (activate-only): purchase / renewal / uncancel / transfer / product change…
// - FULL SYNC: cancellation / expiration / billing issue / pause / revoke…
// NOTE: RC event types vary; we match by keywords to be resilient.
function inferMode(typeRaw: string) {
  const t = (typeRaw || "").toLowerCase();

  const fullSyncHints = [
    "cancel",
    "cancellation",
    "expired",
    "expiration",
    "billing_issue",
    "billing issue",
    "pause",
    "revok",
    "refund",
    "unsubscribe",
    "transfer",
  ];
  
  const deltaHints = [
    "purchase",
    "initial_purchase",
    "renewal",
    "non_renewing_purchase",
    "uncancel",
    "reinstall",
    "product_change",
    "downgrade",
    "upgrade",
  ];

  if (fullSyncHints.some((k) => t.includes(k))) return "FULL_SYNC";
  if (deltaHints.some((k) => t.includes(k))) return "DELTA";

  // Default: DELTA (safe = never turns off other entitlements)
  return "DELTA";
}

// RevenueCat REST API fetch (global truth)
async function fetchRcCustomerInfo(appUserId: string) {
  const secret = Deno.env.get("RC_REST_SECRET") || "";
  if (!secret) {
    throw new Error("missing_RC_REST_SECRET");
  }

  const url = `https://api.revenuecat.com/v1/subscribers/${encodeURIComponent(
    appUserId
  )}`;

  const res = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${secret}`,
      "Content-Type": "application/json",
    },
  });

  const text = await res.text().catch(() => "");
  let data: any = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }

  if (!res.ok) {
    const msg = data?.message || data?.error || text || `http_${res.status}`;
    throw new Error(`rc_fetch_failed:${res.status}:${msg}`);
  }

  return data;
}

// Extract active entitlement keys from RC subscriber payload
function extractActiveEntitlementsFromRc(rc: any): string[] {
  const entObj = rc?.subscriber?.entitlements;
  if (!isObj(entObj)) return [];

  const active: string[] = [];
  const now = nowMs();

  for (const [key, ent] of Object.entries(entObj)) {
    const e: any = ent;
    // RevenueCat entitlements often provide expires_date (string or null for lifetime)
    const expires = e?.expires_date ?? e?.expiresDate ?? null;

    if (!expires) {
      // Lifetime / non-expiring => active
      active.push(String(key));
      continue;
    }

    const expMs = new Date(expires as any).getTime();
    if (Number.isFinite(expMs) && expMs > now) {
      active.push(String(key));
    }
  }

  return active;
}

Deno.serve(async (req) => {
  const startedAt = Date.now();

  const debug: any = {
    at: nowIso(),
    step: "start",
    warnings: [] as string[],
  };

  try {
    if (req.method !== "POST") {
      return json(405, { ok: false, error: "method_not_allowed" });
    }

    // --- Auth: RevenueCat -> Edge Function secret ---
    const expected = Deno.env.get("RC_WEBHOOK_SECRET") || "";
    const got = getAuthToken(req);

    if (!expected) {
      console.log("[RC] missing RC_WEBHOOK_SECRET in Supabase Secrets");
      return json(500, { ok: false, error: "server_not_configured" });
    }
    if (!got || got !== expected) {
      console.log("[RC] unauthorized", { hasToken: !!got });
      return json(401, { ok: false, error: "unauthorized" });
    }

    const payload = await req.json().catch(() => null);
    if (!payload) return json(400, { ok: false, error: "invalid_json" });

    const evt = pickEvent(payload);
    const attrs = pickAttrs(evt);

    const type = String(evt?.type ?? attrs?.type ?? "UNKNOWN");
    const mode = inferMode(type);

    const auth_uid = pickAuthUuid(evt, attrs);

    const entitlement_ids_from_event = safeArray(attrs?.entitlement_ids);
    const expiration_at_raw = attrs?.expiration_at ?? null;
    const expiration_at = toIsoOrNull(expiration_at_raw);

    const provider_event_id = await computeProviderEventId(evt, attrs, payload);
    const provider = "revenuecat";
    const dedupe_key = `${provider}:${provider_event_id}`;

    debug.step = "parsed";
    debug.type = type;
    debug.mode = mode;
    debug.auth_uid = auth_uid ? auth_uid.slice(0, 8) + "…" : null;
    debug.entitlement_ids_from_event = entitlement_ids_from_event;
    debug.provider_event_id = provider_event_id;

    console.log("[RC] event received", {
      at: nowIso(),
      type,
      mode,
      auth_uid: auth_uid ? auth_uid.slice(0, 8) + "…" : null,
      entitlement_ids_from_event,
      expiration_at,
      provider_event_id,
    });

    if (!auth_uid) {
      // Ici: event RC sans uuid (test webhooks, sandbox noise, edge cases)
      return json(200, { ok: true, skipped: "missing_or_invalid_auth_uid", debug });
    }

    // --- Supabase admin client (service role) ---
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";

    if (!serviceKey) {
      console.log("[RC] missing SUPABASE_SERVICE_ROLE_KEY in Supabase Secrets");
      return json(500, { ok: false, error: "missing_service_role_key" });
    }

    const sb = createClient(supabaseUrl, serviceKey, {
      auth: { persistSession: false },
    });

// 0) Log into billing_events (best effort) — robust dedupe
// 0) Log into billing_events (best effort) — dedupe via unique(provider, provider_event_id)
try {
  const ins = {
    source: "rc_webhook",
    provider,                 // <= "revenuecat"
    provider_event_id,
    dedupe_key,               // <= NEW
    event_type: type,
    auth_user_id: auth_uid,
    app_user_id: auth_uid,
    entitlement_ids: entitlement_ids_from_event,
    expiration_at,
    payload,
    mode,
    created_at: nowIso(),
  };

  const { error: logErr } = await sb
  .from("billing_events")
  .upsert(ins, { onConflict: "dedupe_key" });

  if (logErr) {
    debug.warnings.push(`billing_events_write_failed: ${logErr.message}`);
    console.log("[RC] billing_events write warning", { logErr });
  } else {
    debug.logged = true;
  }

  if (logErr) {
    debug.warnings.push(`billing_events_write_failed: ${logErr.message}`);
    console.log("[RC] billing_events write warning", { logErr });
  } else {
    debug.logged = true;
  }
} catch (e) {
  debug.warnings.push(`billing_events_write_exception: ${String((e as any)?.message ?? e)}`);
}

    // 1) Resolve public.users row by auth_user_id
    debug.step = "resolve_user";

    const { data: userRow, error: userErr } = await sb
      .from("users")
      .select("id, auth_user_id, is_pro, pro_started_at")
      .eq("auth_user_id", auth_uid)
      .maybeSingle();

    if (userErr) {
      console.log("[RC] users lookup error", { userErr });
      return json(200, { ok: true, skipped: "users_lookup_error", debug });
    }
    if (!userRow) {
      console.log("[RC] user not found in public.users", { auth_uid });
      return json(200, { ok: true, skipped: "user_not_found", debug });
    }

    const user_id = userRow.id as string;
    debug.user_id = user_id;

    // 2) Determine “truth” of active entitlements depending on mode
    debug.step = "compute_truth";

    let active_entitlement_ids: string[] = [];
    let truth_source: "event_delta" | "rc_customerinfo" = "event_delta";

    if (mode === "FULL_SYNC") {
      // fetch global truth from RevenueCat
      truth_source = "rc_customerinfo";
      const rc = await fetchRcCustomerInfo(auth_uid);
      active_entitlement_ids = extractActiveEntitlementsFromRc(rc);

      debug.rc_active_entitlements = active_entitlement_ids;
    } else {
      // DELTA mode: use only entitlements present in event payload as "to activate"
      active_entitlement_ids = entitlement_ids_from_event;
    }

    debug.truth_source = truth_source;
    debug.active_entitlement_ids = active_entitlement_ids;

    // 3) Compute is_pro (RULE: at least one active entitlement)
    // FULL_SYNC uses global truth; DELTA can only turn it ON (safe)
    const isProTruth = (mode === "FULL_SYNC")
      ? active_entitlement_ids.length > 0
      : (userRow.is_pro === true || active_entitlement_ids.length > 0);

    // core flag (optional, keep)
    const hasCoreTruth = (mode === "FULL_SYNC")
      ? active_entitlement_ids.some((e) => CORE_ENTITLEMENT_IDS.has(e))
      : (active_entitlement_ids.some((e) => CORE_ENTITLEMENT_IDS.has(e)) || false);

    debug.isProTruth = isProTruth;
    debug.hasCoreTruth = hasCoreTruth;

    // 4) Update public.users.is_pro (+ pro_started_at)
    debug.step = "update_users";

    if (userRow.is_pro !== isProTruth) {
      const updatePayload: any = {
        is_pro: isProTruth,
        paywall_reason: isProTruth ? null : "expired_or_cancelled",
      };

      if (isProTruth && !userRow.pro_started_at) updatePayload.pro_started_at = nowIso();

      const { error: upErr } = await sb
        .from("users")
        .update(updatePayload)
        .eq("id", user_id);

      if (upErr) {
        debug.warnings.push(`users_update_failed: ${upErr.message}`);
        console.log("[RC] users update error", { upErr });
      } else {
        debug.users_updated = true;
        console.log("[RC] users updated", { user_id, is_pro: isProTruth });
      }
    } else {
      console.log("[RC] users unchanged", { user_id, is_pro: isProTruth });
    }

    // 6) Update lisa_user_agents statuses
    debug.step = "update_agents";

    const agentKeys = Object.values(ENTITLEMENT_TO_AGENT_KEY);

    const { data: existingAgents, error: agErr } = await sb
      .from("lisa_user_agents")
      .select("id, agent_key, status")
      .eq("user_id", user_id)
      .in("agent_key", agentKeys);

    if (agErr) {
      console.log("[RC] lisa_user_agents lookup error", { agErr });
      return json(200, { ok: true, skipped: "agents_lookup_error", debug });
    }

    // Build desired states depending on mode:
    // - FULL_SYNC: set each mapped agent to active/off based on global truth
    // - DELTA: only set "active" for entitlements present in the event; never set "off" here
    const desiredByAgent: Record<string, "active" | "off" | "unchanged"> = {};
    for (const [entId, agentKey] of Object.entries(ENTITLEMENT_TO_AGENT_KEY)) {
      if (mode === "FULL_SYNC") {
        desiredByAgent[agentKey] = active_entitlement_ids.includes(entId) ? "active" : "off";
      } else {
        // DELTA
        desiredByAgent[agentKey] = active_entitlement_ids.includes(entId) ? "active" : "unchanged";
      }
    }

    debug.desiredByAgent = desiredByAgent;

    const updates: Array<{ id: string; status: "active" | "off" }> = [];

    for (const row of existingAgents ?? []) {
      const agentKey = String(row.agent_key);
      const desired = desiredByAgent[agentKey] ?? "unchanged";

      if (desired === "unchanged") continue;
      if (String(row.status) !== desired) {
        updates.push({ id: row.id as string, status: desired });
      }
    }

    let updatedAgents = 0;
    for (const u of updates) {
      const { error: uErr } = await sb
        .from("lisa_user_agents")
        .update({ status: u.status })
        .eq("id", u.id);

      if (uErr) {
        debug.warnings.push(`agent_update_failed(${u.id}): ${uErr.message}`);
        console.log("[RC] agent update error", { id: u.id, uErr });
      } else {
        updatedAgents++;
        console.log("[RC] agent updated", { id: u.id, status: u.status });
      }
    }

    // 7) Mark billing_events processed (best effort)
    debug.step = "mark_processed";
    try {
      if (provider_event_id) {
        await sb
          .from("billing_events")
          .update({
            processed_at: nowIso(),
            process_status: "processed",
            process_error: null,
            user_id,
          })
          .eq("provider", "revenuecat")
          .eq("provider_event_id", provider_event_id);
      }
    } catch (_e) {
      debug.warnings.push("billing_events_mark_processed_exception");
    }

    const ms = Date.now() - startedAt;
    debug.step = "done";
    debug.ms = ms;
    debug.updatedAgents = updatedAgents;

    console.log("[RC] done", {
      ms,
      user_id,
      mode,
      truth_source,
      isProTruth,
      updatedAgents,
    });

    return json(200, {
      ok: true,
      type,
      mode,
      truth_source,
      auth_uid,
      user_id,
      isPro: isProTruth,
      hasCore: hasCoreTruth,
      entitlement_ids_from_event,
      active_entitlement_ids,
      desiredByAgent,
      updatedAgents,
      ms,
      debug,
    });
  } catch (e) {
    console.log("[RC] fatal", { message: String((e as any)?.message ?? e) });
    return json(200, { ok: true, skipped: "fatal_caught" });
  }
});