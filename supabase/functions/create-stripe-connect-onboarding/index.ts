// supabase/functions/create-stripe-connect-onboarding/index.ts
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

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

async function stripePost(
  path: string,
  body: URLSearchParams,
  stripeSecretKey: string
) {
  const res = await fetch(`https://api.stripe.com/v1/${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${stripeSecretKey}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });

  const json = await res.json().catch(() => ({}));
  return { res, json };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  console.log("[onboarding] HIT", {
    method: req.method,
    url: req.url,
    hasAuth: !!req.headers.get("Authorization"),
    env: Deno.env.get("SUPABASE_ENV"),
  });

  try {
    const authHeader = req.headers.get("Authorization") || "";
    const jwt = authHeader.startsWith("Bearer ") ? authHeader.slice(7) : null;
    if (!jwt) return jsonResponse(401, { ok: false, error: "Missing Bearer token" });
    console.log("[onboarding] JWT OK", { len: jwt.length });

    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    if (!supabaseUrl || !serviceKey) {
      return jsonResponse(500, { ok: false, error: "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY" });
    }

    const stripeSecretKey = getStripeSecretKey();
    if (!stripeSecretKey) {
      return jsonResponse(500, { ok: false, error: "Stripe not configured (missing STRIPE_SECRET_KEY_*)." });
    }

    const RETURN_URL = Deno.env.get("STRIPE_CONNECT_RETURN_URL") || "";
    const REFRESH_URL = Deno.env.get("STRIPE_CONNECT_REFRESH_URL") || "";
    if (!RETURN_URL || !REFRESH_URL) {
      return jsonResponse(500, { ok: false, error: "Missing STRIPE_CONNECT_RETURN_URL / STRIPE_CONNECT_REFRESH_URL" });
    }

    const admin = createClient(supabaseUrl, serviceKey);

    // 1) Auth user depuis le JWT
    const { data: userRes, error: userErr } = await admin.auth.getUser(jwt);
    if (userErr || !userRes?.user) {
      return jsonResponse(401, { ok: false, error: "Invalid session" });
    }
    const authUserId = userRes.user.id;
    console.log("[onboarding] AUTH USER", { authUserId, email: userRes.user.email ?? null });

    // 2) Charger public.users (source of truth pour country)
    const { data: appUser, error: appUserErr } = await admin
    .from("users")
    .select("id, country_code, account_email, full_name")
    .eq("auth_user_id", authUserId)
    .maybeSingle();

    if (appUserErr) throw appUserErr;
    if (!appUser?.id) {
      return jsonResponse(404, { ok: false, error: "User row not found in public.users" });
    }

    console.log("[onboarding] APP USER", {
        appUserId: appUser.id,
        country_code: appUser.country_code ?? null,
        account_email: (appUser as any).account_email ?? null,
      });

    const appUserId = appUser.id as string;
    const countryCode = (appUser.country_code || "").toString().trim().toUpperCase();

    // ✅ CRITIQUE : Stripe veut un ISO2 (FR, BE, ...)
    if (!countryCode || countryCode.length !== 2) {
      return jsonResponse(400, {
        ok: false,
        error: "Missing or invalid country_code on user (expected ISO2 like FR).",
      });
    }

    // 3) Charger/Créer la ligne affiliates
    const { data: aff, error: affErr } = await admin
    .from("affiliates")
    .select("id, stripe_connect_account_id, status, user_id")
    .eq("user_id", appUserId)
    .maybeSingle();

    if (affErr) throw affErr;

    let connectAccountId = aff?.stripe_connect_account_id as string | null;

    // 4) Si pas de Connect account, le créer en Express + country
    if (!connectAccountId) {
        const body = new URLSearchParams();
        body.set("type", "express");
        body.set("country", countryCode);
  
        // ✅ PATCH 1: 80% des affiliés = individus
        // (Stripe utilise ce champ pour orienter le parcours d'onboarding)
        body.set("business_type", "individual");
  
        if ((appUser as any).account_email) {
          body.set("email", String((appUser as any).account_email));
        }
  
        // Capabilities pour recevoir des paiements (transfers = payouts)
        body.set("capabilities[transfers][requested]", "true");

      const { res, json } = await stripePost("accounts", body, stripeSecretKey);

      if (!res.ok || !json?.id) {
        console.log("[Stripe] account create failed", { status: res.status, json });
        return jsonResponse(500, { ok: false, error: "Stripe account creation failed", details: json });
      }

      connectAccountId = String(json.id);

      if (aff?.id) {
        await admin
          .from("affiliates")
          .update({
            stripe_connect_account_id: connectAccountId,
            status: "stripe_account_created",
          })
          .eq("id", aff.id);
      } else {
        await admin.from("affiliates").insert({
            id: crypto.randomUUID(), // ✅ safe si pas de default uuid
            user_id: appUserId,
            email: String((appUser as any).account_email || userRes.user.email || ""),
            full_name: (appUser as any).full_name ?? null,
            stripe_connect_account_id: connectAccountId,
            status: "stripe_account_created",
            created_at: new Date().toISOString(),
          });
      }
    }

    // 5) Générer le lien d’onboarding
    const linkBody = new URLSearchParams();
    if (!connectAccountId) {
        return jsonResponse(500, { ok: false, error: "Missing connectAccountId after account creation." });
      }
    linkBody.set("account", connectAccountId);
    linkBody.set("type", "account_onboarding");
    linkBody.set("refresh_url", REFRESH_URL);
    linkBody.set("return_url", RETURN_URL);

    const { res: linkRes, json: linkJson } = await stripePost("account_links", linkBody, stripeSecretKey);

    if (!linkRes.ok || !linkJson?.url) {
      console.log("[Stripe] account_links failed", { status: linkRes.status, linkJson });
      return jsonResponse(500, { ok: false, error: "Stripe onboarding link creation failed", details: linkJson });
    }

    console.log("[onboarding] STRIPE LINK OK", {
        connectAccountId,
        onboarding_url: String(linkJson.url).slice(0, 60) + "...",
      });

    return jsonResponse(200, {
      ok: true,
      connect_account_id: connectAccountId,
      onboarding_url: String(linkJson.url),
      country_code: countryCode,
    });
  } catch (e: any) {
    console.log("[create-stripe-connect-onboarding] error", e);
    return jsonResponse(500, { ok: false, error: "Internal error", details: e?.message || String(e) });
  }
});