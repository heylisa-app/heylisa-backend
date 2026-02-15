// supabase/functions/apply-referral-link/index.ts
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const ok = (body: any, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...corsHeaders, "Content-Type": "application/json" } });

const bad = (message: string, status = 400, extra: any = {}) =>
  ok({ ok: false, message, ...extra }, status);

const CODE_RE = /^[A-Za-z0-9_-]{4,64}$/;
const MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000; // 30 jours
const branchDomain = Deno.env.get("BRANCH_DOMAIN") || "";

function extractAffCode(raw: string): string | null {
  const s = (raw || "").trim();
  if (!s) return null;

  if (CODE_RE.test(s) && !s.includes("http")) return s;

  try {
    const url = new URL(s.startsWith("http") ? s : `https://${s}`);
    const aff = url.searchParams.get("aff");
    if (aff && CODE_RE.test(aff.trim())) return aff.trim();
  } catch (_) {}

  const m = s.match(/[?&]aff=([A-Za-z0-9_-]{4,64})/i);
  if (m?.[1] && CODE_RE.test(m[1])) return m[1];

  return null;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return ok({ ok: true }, 200);

  try {
    const payload = await req.json().catch(() => ({}));
    const { referrer_code, referrer_link, clicked_at } = payload ?? {};

    const code = extractAffCode(referrer_code || referrer_link || "");
    if (!code) return bad("Lien/code invalide.");

    // ✅ Fenêtre 30 jours (si clicked_at fourni)
    if (clicked_at) {
      const ts = new Date(clicked_at).getTime();
      if (!Number.isFinite(ts)) return bad("clicked_at invalide.");
      const age = Date.now() - ts;
      if (age > MAX_AGE_MS) {
        return bad("Attribution expirée (30 jours).", 410);
      }
    }

    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const anonKey = Deno.env.get("SUPABASE_ANON_KEY")!;
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const jwt = req.headers.get("Authorization")?.replace("Bearer ", "") || "";

    // 1) Client user-scoped (pour lire auth)
    const supaUser = createClient(supabaseUrl, anonKey, {
      global: { headers: { Authorization: `Bearer ${jwt}` } },
    });

    const { data: userData, error: userErr } = await supaUser.auth.getUser();
    if (userErr || !userData?.user) return bad("Session invalide. Reconnecte-toi.", 401);

    const authUserId = userData.user.id;

    // 2) Service client (bypass RLS)
    const supa = createClient(supabaseUrl, serviceKey);

    console.log("[apply-referral] authUserId:", authUserId, "code:", code);

    // 3) Map auth.user.id -> public.users.id (LA règle d’or)
    const { data: appUser, error: appUserErr } = await supa
      .from("users")
      .select("id")
      .eq("auth_user_id", authUserId)
      .maybeSingle();

    if (appUserErr) return bad("Erreur DB (users).", 500, { details: appUserErr.message });
    if (!appUser?.id) return bad("User row not found in public.users.", 404);

    const referredUserId = String(appUser.id); // ✅ public.users.id

    // 4) Si déjà attribué -> no-op
    const { data: existingRef, error: exErr } = await supa
      .from("referrals")
      .select("id, code, applied_at, created_at")
      .eq("referred_user_id", referredUserId)
      .maybeSingle();

    if (exErr) return bad("Erreur DB (referrals).", 500, { details: exErr.message });

    if (existingRef?.id) {
      console.log("[apply-referral] already_applied", existingRef.code);
      return ok({
        ok: true,
        already_applied: true,
        referrer_code: existingRef.code,
        applied_at: existingRef.applied_at,
      });
    }

    // 5) Resolve code -> referrer (public.users.id)
    const { data: aff, error: affErr } = await supa
      .from("affiliate_codes")
      .select("user_id, code, is_active, share_url, created_at")
      .eq("code", code)
      .eq("is_active", true)
      .order("created_at", { ascending: false })
      .limit(1)
      .maybeSingle();

    if (affErr) return bad("Erreur DB (affiliate_codes).", 500, { details: affErr.message });
    if (!aff?.user_id) return bad("Ce code n’existe pas (ou n’est plus actif).");

    const referrerL1 = String(aff.user_id);

    // 6) Anti auto-parrainage (même namespace)
    if (referrerL1 === referredUserId) return bad("Tu ne peux pas utiliser ton propre lien 😄");

    // 7) Construire L2 / L3 via la chaîne de parrainage existante
    //    L2 = parrain du L1 (si L1 a lui-même été parrainé)
    const { data: l1Ref, error: l1Err } = await supa
      .from("referrals")
      .select("referrer_user_id")
      .eq("referred_user_id", referrerL1)
      .maybeSingle();

    if (l1Err) return bad("Erreur DB (referrals L2).", 500, { details: l1Err.message });

    const referrerL2 = l1Ref?.referrer_user_id ? String(l1Ref.referrer_user_id) : null;

    // L3 = parrain du L2 (si existe)
    let referrerL3: string | null = null;
    if (referrerL2) {
      const { data: l2Ref, error: l2Err } = await supa
        .from("referrals")
        .select("referrer_user_id")
        .eq("referred_user_id", referrerL2)
        .maybeSingle();

      if (l2Err) return bad("Erreur DB (referrals L3).", 500, { details: l2Err.message });
      referrerL3 = l2Ref?.referrer_user_id ? String(l2Ref.referrer_user_id) : null;
    }

    console.log("[apply-referral] chain", { referrerL1, referrerL2, referrerL3 });

    const finalLink =
    (typeof referrer_link === "string" && referrer_link.trim()) ||
    aff.share_url ||
    (branchDomain ? `https://${branchDomain}/${code}` : null);

    const nowIso = new Date().toISOString();
    const expiresIso = new Date(Date.now() + MAX_AGE_MS).toISOString();

    // 8) Insert source of truth
    const { error: insErr } = await supa.from("referrals").insert({
      code,
      referrer_user_id: referrerL1,
      referrer_user_id_l2: referrerL2,
      referrer_user_id_l3: referrerL3,
      referred_user_id: referredUserId,
      status: "applied",
      applied_at: nowIso,
      created_at: nowIso,
      expires_at: expiresIso,
    });

    if (insErr) {
      if ((insErr as any)?.code === "23505") {
        return ok({ ok: true, already_applied: true, referrer_code: code });
      }
      return bad("Impossible d’appliquer le parrainage.", 500, { details: insErr.message });
    }

    // 9) Cache (si tu veux le garder) dans public.users (toujours user.id)
    await supa
      .from("users")
      .update({
        referrer_code: code,
        referrer_link: finalLink,
        referrer_applied_at: nowIso,
      })
      .eq("id", referredUserId);

    return ok({
      ok: true,
      referrer_code: code,
      referrer_link: finalLink,
      applied_at: nowIso,
      expires_at: expiresIso,
      levels: {
        l1: referrerL1,
        l2: referrerL2,
        l3: referrerL3,
      },
    });
  } catch (e: any) {
    console.log("[apply-referral] error", e?.message || e);
    return bad("Erreur serveur.", 500, { details: e?.message || String(e) });
  }
});