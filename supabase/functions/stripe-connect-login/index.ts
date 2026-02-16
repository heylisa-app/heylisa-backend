// supabase/functions/stripe-connect-login/index.ts
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

function json(status: number, body: Record<string, any>) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function getStripeKey() {
    return Deno.env.get("STRIPE_SECRET_KEY") || "";
  }

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });

  try {
    const authHeader = req.headers.get("Authorization") ?? "";
    const jwt = authHeader.startsWith("Bearer ") ? authHeader.slice(7) : null;
    if (!jwt) return json(401, { ok: false, error: "Missing JWT" });

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    const stripeKey = getStripeKey();
    if (!stripeKey) return json(500, { ok: false, error: "Stripe not configured" });

    // 1) Auth user
    const { data: auth, error: authErr } = await supabase.auth.getUser(jwt);
    if (authErr || !auth?.user) {
      return json(401, { ok: false, error: "Invalid session" });
    }

    // 2) Récupérer affiliate
// 2) Get app user id (public.users.id)
const { data: appUser, error: appUserErr } = await supabase
  .from("users")
  .select("id")
  .eq("auth_user_id", auth.user.id)
  .maybeSingle();

if (appUserErr || !appUser?.id) {
  return json(404, { ok: false, error: "User row not found in public.users" });
}

// 3) Récupérer affiliate (affiliates.user_id = public.users.id)
const { data: affiliate, error } = await supabase
  .from("affiliates")
  .select("stripe_connect_account_id")
  .eq("user_id", String(appUser.id))
  .maybeSingle();

if (error || !affiliate?.stripe_connect_account_id) {
  return json(404, { ok: false, error: "Stripe account not found" });
}

    // 3) Créer login link Stripe Express
    const res = await fetch(
      `https://api.stripe.com/v1/accounts/${affiliate.stripe_connect_account_id}/login_links`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${stripeKey}`,
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }
    );

    const data = await res.json();
    if (!res.ok || !data?.url) {
      return json(500, { ok: false, error: "Stripe login link failed", details: data });
    }

    return json(200, {
      ok: true,
      url: data.url,
    });
  } catch (e: any) {
    return json(500, { ok: false, error: e.message });
  }
});