// supabase/functions/create-affiliate-link/index.ts
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
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

function jsonResponse(status: number, body: Record<string, Json>) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function makeCode(len = 10) {
  // Code lisible, sans caractères ambigus (0/O, 1/I, etc.)
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  const bytes = new Uint8Array(len);
  crypto.getRandomValues(bytes);
  let out = "";
  for (let i = 0; i < len; i++) out += alphabet[bytes[i] % alphabet.length];
  return out;
}

function isProductionEnv() {
  const v = (Deno.env.get("SUPABASE_ENV") || "").toLowerCase();
  return v === "production" || v === "prod";
}

async function createBranchLink(params: {
  code: string;
  referrerUserId: string;
  countryCode?: string | null;
}) {
  // ✅ Force PROD (LIVE) — no bullshit
const branchKey = Deno.env.get("BRANCH_KEY");
const branchDomain = Deno.env.get("BRANCH_DOMAIN");

  if (!branchKey || !branchDomain) {
    return { ok: false as const, url: null, reason: "missing_branch_env" };
  }

  // Branch attend le domain sans https://
  const domain = branchDomain;


  const payload = {
    branch_key: branchKey,
    domain, // ✅ force ton domaine (heylisa.app.link / heylisa.test-app.link)
    data: {
      aff: params.code, // ✅ clé unique partout
      referrer_user_id: params.referrerUserId,
      country_code: params.countryCode ?? null,
      $marketing_title: "HeyLisa affiliate",
      $marketing_channel: "app",
      $marketing_feature: "referral",
      $marketing_campaign: "mlm",
    },
  };

  const res = await fetch("https://api2.branch.io/v1/url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const json = await res.json().catch(() => ({}));

  if (!res.ok || !json?.url) {
    console.log("[Branch] create url failed", { status: res.status, json });
    return { ok: false as const, url: null, reason: `http_${res.status}` };
  }

  return { ok: true as const, url: String(json.url), reason: "ok" };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const authHeader = req.headers.get("Authorization") || "";
    const jwt = authHeader.startsWith("Bearer ") ? authHeader.slice(7) : null;

    if (!jwt) {
      return jsonResponse(401, { error: "Missing Bearer token" });
    }

    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

    if (!supabaseUrl || !serviceKey) {
      return jsonResponse(500, {
        ok: false,
        error: "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY",
      });
    }

    const admin = createClient(supabaseUrl, serviceKey);

    // 1) Auth: récupérer l'user depuis le JWT
    const { data: userRes, error: userErr } = await admin.auth.getUser(jwt);
    if (userErr || !userRes?.user) {
      return jsonResponse(401, { error: "Invalid session" });
    }
    const authUserId = userRes.user.id;

    // 2) Récupérer la ligne public.users associée
    const { data: appUser, error: appUserErr } = await admin
      .from("users")
      .select("id, country_code")
      .eq("auth_user_id", authUserId)
      .maybeSingle();

    if (appUserErr) throw appUserErr;
    if (!appUser?.id) {
      return jsonResponse(404, {
        error: "User row not found in public.users (auth_user_id missing)",
      });
    }

    const appUserId = appUser.id;
    const countryCode = (appUser.country_code || null) as string | null;

    // 3) Check existing affiliate code
    const { data: existing, error: existingErr } = await admin
      .from("affiliate_codes")
      .select("id, code, share_url")
      .eq("user_id", appUserId)
      .maybeSingle();

    if (existingErr) throw existingErr;

    if (existing?.code) {
      // si share_url existe => renvoyer direct
      if (existing.share_url) {
        return jsonResponse(200, {
          already_affiliate: true,
          link: { code: existing.code, url: existing.share_url },
        });
      }

      // sinon => créer Branch + update (0 fallback)
      const br = await createBranchLink({
        code: existing.code,
        referrerUserId: appUserId,
        countryCode,
      });

      if (!br.ok || !br.url) {
        return jsonResponse(500, {
          error: "Branch link creation failed",
          reason: br.reason,
        });
      }

      await admin
        .from("affiliate_codes")
        .update({ share_url: br.url })
        .eq("id", existing.id);

      return jsonResponse(200, {
        already_affiliate: true,
        link: { code: existing.code, url: br.url },
      });
    }

    // 4) Générer un code + Branch + upsert (retry collisions)
    let code = "";
    let shareUrl = "";
    const maxTries = 8;

    for (let attempt = 1; attempt <= maxTries; attempt++) {
      code = `HL${makeCode(8)}`;

      const br = await createBranchLink({
        code,
        referrerUserId: appUserId,
        countryCode,
      });

      // 0 fallback : si Branch fail => erreur directe
      if (!br.ok || !br.url) {
        return jsonResponse(500, {
          error: "Branch link creation failed",
          reason: br.reason,
        });
      }

      shareUrl = br.url;

      const { error: upsertErr } = await admin
        .from("affiliate_codes")
        .upsert(
          {
            user_id: appUserId,
            code,
            share_url: shareUrl,
            country_code: countryCode,
            is_active: true,
          },
          { onConflict: "user_id" }
        );

      if (!upsertErr) break;

      // collision code unique ? => retry
      const msg = String((upsertErr as any)?.message || "").toLowerCase();
      const isUniqueCollision =
        msg.includes("duplicate") ||
        msg.includes("unique") ||
        msg.includes("affiliate_codes_code_unique");

      if (attempt < maxTries && isUniqueCollision) continue;
      throw upsertErr;
    }

    return jsonResponse(200, {
      already_affiliate: false,
      link: { code, url: shareUrl },
    });
  } catch (e: any) {
    console.log("[create-affiliate-link] error", e);
    return jsonResponse(500, {
      error: "Internal error",
      details: e?.message || String(e),
    });
  }
});