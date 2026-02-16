import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
import Stripe from "npm:stripe@16.9.0";

type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json }
  | Json[];

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

function jsonResponse(status: number, body: Record<string, Json>) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function getStripeSecretKey() {
    return Deno.env.get("STRIPE_SECRET_KEY") || "";
  }

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return jsonResponse(405, { ok: false, error: "Method not allowed" });

  console.log("[connect-status] HIT");

  try {
    // 0) Auth
    const authHeader = req.headers.get("Authorization") || "";
    const jwt = authHeader.startsWith("Bearer ") ? authHeader.slice(7) : null;
    if (!jwt) return jsonResponse(401, { ok: false, error: "Missing Bearer token" });

    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    if (!supabaseUrl || !serviceKey) {
      return jsonResponse(500, { ok: false, error: "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY" });
    }

    const stripeSecretKey = getStripeSecretKey();
    if (!stripeSecretKey) return jsonResponse(500, { ok: false, error: "Missing STRIPE_SECRET_KEY_*" });

    const admin = createClient(supabaseUrl, serviceKey);

    // 1) Resolve auth user
    const { data: userRes, error: userErr } = await admin.auth.getUser(jwt);
    if (userErr || !userRes?.user) return jsonResponse(401, { ok: false, error: "Invalid session" });

    const authUserId = userRes.user.id;

    // 2) Get app user id
    const { data: appUser, error: appUserErr } = await admin
      .from("users")
      .select("id")
      .eq("auth_user_id", authUserId)
      .maybeSingle();

    if (appUserErr) throw appUserErr;
    if (!appUser?.id) return jsonResponse(404, { ok: false, error: "User row not found in public.users" });

    const appUserId = String(appUser.id);

    // 3) Get affiliate connect account id
    const { data: aff, error: affErr } = await admin
      .from("affiliates")
      .select("stripe_connect_account_id")
      .eq("user_id", appUserId)
      .maybeSingle();

    if (affErr) throw affErr;

    const connectAccountId = (aff?.stripe_connect_account_id || "").toString().trim();
    if (!connectAccountId) {
        return jsonResponse(200, {
            ok: true,
            has_connect_account: false,
            is_done: false,
          
            // ✅ alias pour l'app (Drawer)
            has_account: false,
            onboarding_completed: false,
          });
    }

    // 4) Fetch Stripe account live
    const stripe = new Stripe(stripeSecretKey, { apiVersion: "2024-06-20" });
    const acc = await stripe.accounts.retrieve(connectAccountId);

    const isDone =
      !!acc.details_submitted &&
      (acc.charges_enabled === true || acc.payouts_enabled === true);

    const currentlyDueCount = Array.isArray(acc.requirements?.currently_due)
      ? acc.requirements.currently_due.length
      : 0;

    console.log("[connect-status] OK", {
      connectAccountId,
      isDone,
      details_submitted: acc.details_submitted,
      charges_enabled: acc.charges_enabled,
      payouts_enabled: acc.payouts_enabled,
      currentlyDueCount,
    });

    return jsonResponse(200, {
        ok: true,
        has_connect_account: true,
        connect_account_id: connectAccountId,
        is_done: isDone,
        details_submitted: !!acc.details_submitted,
        charges_enabled: !!acc.charges_enabled,
        payouts_enabled: !!acc.payouts_enabled,
        requirements_currently_due_count: currentlyDueCount,
      
        // ✅ alias pour l'app (Drawer)
        has_account: true,
        onboarding_completed: isDone,
      });
  } catch (e: any) {
    console.log("[connect-status] error", e?.message || e);
    return jsonResponse(500, { ok: false, error: "Internal error", details: e?.message || String(e) });
  }
});