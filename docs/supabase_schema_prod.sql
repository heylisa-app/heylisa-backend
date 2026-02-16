--
-- PostgreSQL database dump
--

\restrict JkQaS6yzaoLFdoeEGvdfHsPGAigKx7tRU3D1a0Rp5xtdkzZnTrFeYf3pAbww9eo

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.7 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA public;


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- Name: agent_badge_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.agent_badge_enum AS ENUM (
    'beta',
    'live',
    'soon'
);


--
-- Name: agent_plan_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.agent_plan_enum AS ENUM (
    'included',
    'addon_3',
    'addon_6',
    'custom'
);


--
-- Name: agent_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.agent_status_enum AS ENUM (
    'off',
    'pending',
    'active',
    'error'
);


--
-- Name: automation_category_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.automation_category_enum AS ENUM (
    'personal',
    'business',
    'sales',
    'marketing',
    'ops',
    'admin',
    'finance',
    'other'
);


--
-- Name: automation_complexity_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.automation_complexity_enum AS ENUM (
    '1',
    '2',
    '3',
    '4',
    '5'
);


--
-- Name: automation_tier_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.automation_tier_enum AS ENUM (
    'standard',
    'advanced',
    'critical'
);


--
-- Name: billing_frequency_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.billing_frequency_enum AS ENUM (
    'monthly',
    'annual'
);


--
-- Name: billing_plan_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.billing_plan_enum AS ENUM (
    'starter',
    'pro',
    'business'
);


--
-- Name: budget_sensitivity_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.budget_sensitivity_enum AS ENUM (
    'low',
    'medium',
    'high'
);


--
-- Name: business_revenue_band_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.business_revenue_band_enum AS ENUM (
    '<100k',
    '100-300k',
    '300k-1M',
    '1-3M',
    '3-10M',
    '10M+'
);


--
-- Name: company_size_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.company_size_enum AS ENUM (
    'solo',
    '1-5',
    '6-10',
    '11-50',
    '51-200',
    '201-1000',
    '1000+'
);


--
-- Name: conversation_channel_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.conversation_channel_enum AS ENUM (
    'web_onboarding',
    'mobile_app',
    'web_dashboard',
    'email',
    'slack',
    'whatsapp',
    'telegram',
    'other'
);


--
-- Name: conversation_context_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.conversation_context_enum AS ENUM (
    'onboarding',
    'daily_summary',
    'project_support',
    'support_request',
    'sales_followup',
    'automation_scoping',
    'other'
);


--
-- Name: conversation_role_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.conversation_role_enum AS ENUM (
    'user',
    'assistant',
    'system'
);


--
-- Name: conversation_sender_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.conversation_sender_enum AS ENUM (
    'user',
    'lisa',
    'system',
    'human_agent'
);


--
-- Name: conversation_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.conversation_status_enum AS ENUM (
    'open',
    'snoozed',
    'closed'
);


--
-- Name: email_account_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.email_account_status_enum AS ENUM (
    'pending',
    'connected',
    'revoked',
    'error'
);


--
-- Name: email_provider_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.email_provider_enum AS ENUM (
    'google',
    'microsoft',
    'imap',
    'other'
);


--
-- Name: employment_relation_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.employment_relation_enum AS ENUM (
    'owner',
    'co-owner',
    'employee',
    'freelance',
    'advisor',
    'former-employee',
    'other'
);


--
-- Name: fact_category_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.fact_category_enum AS ENUM (
    'identity',
    'personal_profile',
    'family',
    'health',
    'preferences',
    'goals',
    'constraints',
    'context',
    'financial',
    'other'
);


--
-- Name: fact_key_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.fact_key_status_enum AS ENUM (
    'core',
    'experimental',
    'proposed',
    'deprecated'
);


--
-- Name: fact_scope_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.fact_scope_enum AS ENUM (
    'personal',
    'work',
    'both'
);


--
-- Name: fact_source_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.fact_source_type_enum AS ENUM (
    'declared',
    'observed',
    'inferred',
    'system'
);


--
-- Name: fact_value_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.fact_value_type_enum AS ENUM (
    'text',
    'number',
    'date',
    'boolean',
    'json'
);


--
-- Name: financial_data_source_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.financial_data_source_enum AS ENUM (
    'declared',
    'estimated',
    'mixed'
);


--
-- Name: financial_pressure_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.financial_pressure_enum AS ENUM (
    'relaxed',
    'comfortable',
    'tight',
    'critical'
);


--
-- Name: iap_platform; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.iap_platform AS ENUM (
    'ios',
    'android'
);


--
-- Name: income_band_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.income_band_enum AS ENUM (
    '<30k',
    '30-60k',
    '60-100k',
    '100-200k',
    '200k+'
);


--
-- Name: initial_cleaning_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.initial_cleaning_status_enum AS ENUM (
    'pending',
    'snoozed',
    'done',
    'refused'
);


--
-- Name: integration_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.integration_status_enum AS ENUM (
    'active',
    'beta',
    'deprecated',
    'disabled'
);


--
-- Name: life_dimension_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.life_dimension_enum AS ENUM (
    'health',
    'career',
    'finance',
    'relationships',
    'personal_growth',
    'leisure_stability',
    'other'
);


--
-- Name: lisa_mood_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.lisa_mood_enum AS ENUM (
    'very_low',
    'low',
    'neutral',
    'high',
    'very_high'
);


--
-- Name: lisa_task_owner_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.lisa_task_owner_enum AS ENUM (
    'lisa',
    'human_team',
    'user',
    'external_system'
);


--
-- Name: lisa_task_priority_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.lisa_task_priority_enum AS ENUM (
    'low',
    'normal',
    'high',
    'urgent'
);


--
-- Name: lisa_task_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.lisa_task_status_enum AS ENUM (
    'pending',
    'in_progress',
    'waiting_user',
    'done',
    'cancelled'
);


--
-- Name: lisa_task_trigger_source_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.lisa_task_trigger_source_enum AS ENUM (
    'lisa_chat',
    'automation',
    'system_rule',
    'rule',
    'manual'
);


--
-- Name: lisa_task_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.lisa_task_type_enum AS ENUM (
    'user_followup',
    'summary_prep',
    'fact_update',
    'automation_scoping',
    'automation_build',
    'support_request',
    'sales_opportunity',
    'other',
    'reminder',
    'memo_deletion',
    'decision_pending',
    'tools_extension'
);


--
-- Name: onboarding_stage_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.onboarding_stage_enum AS ENUM (
    'signup_only',
    'subscribed_no_oauth',
    'active',
    'churn_risk',
    'subscribed_oauth_no_first_cleaning'
);


--
-- Name: plan_recommendation_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.plan_recommendation_enum AS ENUM (
    'starter',
    'pro',
    'business'
);


--
-- Name: project_event_source_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.project_event_source_enum AS ENUM (
    'email',
    'calendar',
    'manual',
    'system',
    'slack',
    'other'
);


--
-- Name: project_event_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.project_event_type_enum AS ENUM (
    'created',
    'status_update',
    'deadline_change',
    'milestone_reached',
    'risk_flagged',
    'client_message',
    'internal_note',
    'automation_run',
    'other'
);


--
-- Name: project_priority_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.project_priority_enum AS ENUM (
    'low',
    'normal',
    'high',
    'critical'
);


--
-- Name: project_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.project_status_enum AS ENUM (
    'idea',
    'active',
    'on_hold',
    'completed',
    'dropped'
);


--
-- Name: project_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.project_type_enum AS ENUM (
    'work',
    'business',
    'personal',
    'health',
    'learning',
    'finance',
    'family',
    'legal',
    'other'
);


--
-- Name: referral_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.referral_status AS ENUM (
    'created',
    'applied',
    'consumed',
    'expired',
    'cancelled'
);


--
-- Name: service_doc_audience_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.service_doc_audience_enum AS ENUM (
    'user_facing',
    'internal_ops',
    'internal_llm'
);


--
-- Name: service_doc_category_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.service_doc_category_enum AS ENUM (
    'product',
    'pricing',
    'privacy',
    'onboarding',
    'automation_lib',
    'support',
    'internal',
    'other'
);


--
-- Name: spending_style_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.spending_style_enum AS ENUM (
    'frugal',
    'balanced',
    'premium'
);


--
-- Name: summary_detail_level_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.summary_detail_level_enum AS ENUM (
    'short',
    'normal',
    'detailed'
);


--
-- Name: triage_preset_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.triage_preset_enum AS ENUM (
    'lisa_default',
    'custom',
    'off'
);


--
-- Name: user_automation_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_automation_status_enum AS ENUM (
    'idea',
    'scoping',
    'building',
    'active',
    'paused',
    'archived'
);


--
-- Name: user_integration_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_integration_status_enum AS ENUM (
    'connected',
    'needs_attention',
    'disconnected',
    'revoked'
);


--
-- Name: user_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_status_enum AS ENUM (
    'prospect',
    'trial',
    'active',
    'new_user',
    'inactive'
);


--
-- Name: apply_paywall_time_expired(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.apply_paywall_time_expired(p_trial_days integer DEFAULT 14) RETURNS TABLE(updated_count integer, updated_user_ids uuid[])
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
declare
  v_ids uuid[];
begin
  with candidates as (
    select id
    from public.users
    where coalesce(is_pro,false) = false
      and coalesce(nullif(trim(paywall_reason), ''), '') = ''
      and trial_started_at is not null
      and trial_started_at <= now() - make_interval(days => p_trial_days)
      and deleted_at is null
      and account_status = 'active'
  ),
  upd as (
    update public.users u
    set
      paywall_reason = 'time',
      paywall_at     = coalesce(u.paywall_at, now()),
      updated_at     = now()
    from candidates c
    where u.id = c.id
    returning u.id
  )
  select array_agg(id) into v_ids from upd;

  updated_user_ids := coalesce(v_ids, '{}');
  updated_count := coalesce(array_length(updated_user_ids, 1), 0);
  return;
end;
$$;


--
-- Name: cleanup_stripe_customer_outbox_done(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.cleanup_stripe_customer_outbox_done() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
begin
  -- Si le statut passe à 'done', on supprime la ligne
  if new.status = 'done' then
    delete from public.stripe_customer_outbox
    where id = new.id;
  end if;

  return null;
end;
$$;


--
-- Name: current_user_id(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.current_user_id() RETURNS uuid
    LANGUAGE sql STABLE
    AS $$
  select u.id
  from public.users u
  where u.auth_user_id = auth.uid()
  limit 1
$$;


--
-- Name: enqueue_push(uuid, text, text, text, jsonb, timestamp with time zone, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.enqueue_push(p_user_id uuid, p_kind text, p_title text, p_body text, p_data jsonb DEFAULT '{}'::jsonb, p_scheduled_at timestamp with time zone DEFAULT NULL::timestamp with time zone, p_tz text DEFAULT 'Europe/Paris'::text) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
declare
  new_id uuid;
  v_scheduled timestamptz;
begin
  if public.should_send_push(p_user_id, p_kind) is not true then
    return null;
  end if;

  -- chat = immédiat, system = repoussé si quiet hours
  if p_kind = 'system' then
    v_scheduled := public.next_allowed_push_time(coalesce(p_scheduled_at, now()), p_tz);
  else
    v_scheduled := coalesce(p_scheduled_at, now());
  end if;

  insert into public.push_outbox(user_id, kind, title, body, data, scheduled_at)
  values (p_user_id, p_kind, p_title, p_body, coalesce(p_data,'{}'::jsonb), v_scheduled)
  returning id into new_id;

  return new_id;
end;
$$;


--
-- Name: enqueue_stripe_customer_creation(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.enqueue_stripe_customer_creation() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  -- On déclenche seulement si :
  -- - on a un auth_user_id (le compte est réellement lié à Supabase Auth)
  -- - stripe_customer_id est NULL (pas déjà fait)
  if new.auth_user_id is not null
     and (new.stripe_customer_id is null or new.stripe_customer_id = '') then

    insert into public.stripe_customer_outbox (user_id, account_email, full_name, status)
    values (new.id, new.account_email, new.full_name, 'pending')
    on conflict (user_id) do nothing; -- évite doublons
  end if;

  return new;
end;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: affiliates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.affiliates (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email text NOT NULL,
    full_name text,
    stripe_customer_id text,
    stripe_connect_account_id text,
    status text DEFAULT 'active'::text NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    stripe_account_id text,
    stripe_onboarding_sent_at timestamp with time zone,
    stripe_onboarding_completed_at timestamp with time zone,
    country text,
    user_id uuid
);


--
-- Name: ensure_affiliate(uuid, text, text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.ensure_affiliate(p_user_id uuid, p_email text, p_full_name text, p_country text) RETURNS public.affiliates
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
declare
  a public.affiliates;
begin
  -- 1) Si un affiliate existe déjà avec ce user_id -> update
  select * into a from public.affiliates where user_id = p_user_id limit 1;
  if found then
    update public.affiliates
      set email = coalesce(p_email, email),
          full_name = coalesce(p_full_name, full_name),
          country = coalesce(p_country, country),
          updated_at = now()
    where user_id = p_user_id
    returning * into a;
    return a;
  end if;

  -- 2) Sinon, merge par email (affiliate web-only)
  select * into a from public.affiliates where email = p_email limit 1;
  if found then
    update public.affiliates
      set user_id = p_user_id,
          full_name = coalesce(p_full_name, full_name),
          country = coalesce(p_country, country),
          updated_at = now()
    where email = p_email
    returning * into a;
    return a;
  end if;

  -- 3) Sinon, créer un nouveau affiliate (app)
  insert into public.affiliates (user_id, email, full_name, country, status, created_at, updated_at)
  values (p_user_id, p_email, p_full_name, p_country, 'active', now(), now())
  returning * into a;

  return a;
end;
$$;


--
-- Name: ensure_user_settings_row(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.ensure_user_settings_row() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
begin
  insert into public.user_settings (user_id)
  values (new.id)
  on conflict (user_id) do nothing;

  return new;
end;
$$;


--
-- Name: fn_activate_personal_assistant_if_pro(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_activate_personal_assistant_if_pro() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
begin
  -- Only act when user IS pro
  if new.is_pro is distinct from true then
    return new;
  end if;

  -- Optional: only when is_pro just turned true
  if tg_op = 'UPDATE' and old.is_pro is distinct from true and new.is_pro = true then
    insert into public.lisa_user_agents (user_id, agent_key, status, revoked_at, updated_at)
    values (new.id, 'personal_assistant', 'active', null, now())
    on conflict (user_id, agent_key) do update
      set status     = 'active',
          revoked_at = null,
          updated_at = now();
  elsif tg_op = 'INSERT' then
    insert into public.lisa_user_agents (user_id, agent_key, status, revoked_at, updated_at)
    values (new.id, 'personal_assistant', 'active', null, now())
    on conflict (user_id, agent_key) do update
      set status     = 'active',
          revoked_at = null,
          updated_at = now();
  end if;

  return new;
end;
$$;


--
-- Name: fn_billing_events_normalize_timestamps(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_billing_events_normalize_timestamps() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  if (new.expiration_at is null)
     and (new.payload ? 'event')
     and ((new.payload->'event'->>'expiration_at_ms') is not null) then
    new.expiration_at :=
      to_timestamp( ((new.payload->'event'->>'expiration_at_ms')::bigint) / 1000.0 );
  end if;

  return new;
end;
$$;


--
-- Name: fn_billing_events_resolve_user_id(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_billing_events_resolve_user_id() RETURNS trigger
    LANGUAGE plpgsql
    AS $_$
declare
  v_auth_user_id uuid;
begin
  -- Déjà résolu ? on touche pas
  if new.user_id is not null then
    return new;
  end if;

  -- app_user_id dans payload (RevenueCat)
  if (new.payload->'event'->>'app_user_id') is not null
     and (new.payload->'event'->>'app_user_id') ~* '^[0-9a-f-]{36}$' then
    v_auth_user_id := (new.payload->'event'->>'app_user_id')::uuid;

    select u.id into new.user_id
    from public.users u
    where u.auth_user_id = v_auth_user_id
    limit 1;
  end if;

  return new;
end;
$_$;


--
-- Name: fn_pick_active_agent_status(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_pick_active_agent_status() RETURNS public.agent_status_enum
    LANGUAGE plpgsql STABLE
    AS $$
declare
  has_active boolean;
  has_on     boolean;
  has_live   boolean;
begin
  select exists(
    select 1
    from pg_type t
    join pg_enum e on e.enumtypid = t.oid
    where t.typname = 'agent_status_enum'
      and e.enumlabel = 'active'
  ) into has_active;

  if has_active then
    return 'active'::public.agent_status_enum;
  end if;

  select exists(
    select 1
    from pg_type t
    join pg_enum e on e.enumtypid = t.oid
    where t.typname = 'agent_status_enum'
      and e.enumlabel = 'on'
  ) into has_on;

  if has_on then
    return 'on'::public.agent_status_enum;
  end if;

  select exists(
    select 1
    from pg_type t
    join pg_enum e on e.enumtypid = t.oid
    where t.typname = 'agent_status_enum'
      and e.enumlabel = 'live'
  ) into has_live;

  if has_live then
    return 'live'::public.agent_status_enum;
  end if;

  -- fallback = default enum value expected in your schema
  return 'off'::public.agent_status_enum;
end;
$$;


--
-- Name: fn_recompute_user_status(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_recompute_user_status(p_user_id uuid) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare
  v_signup_source text;
  v_has_rc_events boolean;
  v_has_current boolean;
  v_current_is_trial boolean;
  v_new_status public.user_status_enum;
  v_new_is_pro boolean;
begin
  select u.signup_source
  into v_signup_source
  from public.users u
  where u.id = p_user_id;

  if not found then
    return;
  end if;

  -- A-t-on des events RevenueCat pour ce user ?
  select exists(
    select 1 from public.billing_events be
    where be.user_id = p_user_id
      and be.provider = 'revenuecat'
  ) into v_has_rc_events;

  -- A-t-on une subscription "courante" ? (expiration_at > now)
  select exists(
    select 1
    from public.billing_events be
    where be.user_id = p_user_id
      and be.provider = 'revenuecat'
      and be.expiration_at is not null
      and be.expiration_at > now()
      -- optionnel mais conseillé : ignorer les events qui ne sont pas des signaux d'accès
      and coalesce(be.event_type,'') in ('INITIAL_PURCHASE','RENEWAL','UNCANCELLATION','PRODUCT_CHANGE','TRANSFER','EXPIRATION','CANCELLATION')
  ) into v_has_current;

  -- Si on a du courant, est-ce un trial ?
  if v_has_current then
    select exists(
      select 1
      from public.billing_events be
      where be.user_id = p_user_id
        and be.provider = 'revenuecat'
        and be.expiration_at is not null
        and be.expiration_at > now()
        and (
          coalesce((be.payload->'event'->>'price')::numeric, 0) = 0
          or upper(coalesce(be.payload->'event'->>'period_type','')) = 'TRIAL'
        )
    ) into v_current_is_trial;

    if v_current_is_trial then
      v_new_status := 'trial';
      v_new_is_pro := true;
    else
      v_new_status := 'active';
      v_new_is_pro := true;
    end if;

  else
    -- pas de courant
    if v_has_rc_events then
      v_new_status := 'inactive';
      v_new_is_pro := false;
    else
      -- aucun event RC : fallback marketing
      if v_signup_source = 'web_footer_magiclink' then
        v_new_status := 'prospect';
        v_new_is_pro := false;
      else
        v_new_status := 'new_user';
        v_new_is_pro := false;
      end if;
    end if;
  end if;

  update public.users
  set
    status = v_new_status,
    is_pro = v_new_is_pro,
    updated_at = now()
  where id = p_user_id
    and (status is distinct from v_new_status or is_pro is distinct from v_new_is_pro);

end;
$$;


--
-- Name: fn_refresh_use_tu_form(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_refresh_use_tu_form(p_user_id uuid) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
declare
  v_register text;
  v_use_tu boolean;
begin
  /*
    Supporte 2 formats dans user_facts.value:
    A) scalaire jsonb: "tu"
    B) objet jsonb: {"value":"tu"} (ou {"register":"tu"})
  */
  select lower(trim(
           coalesce(
             uf.value->>'value',
             uf.value->>'register',
             trim(both '"' from uf.value::text)  -- cas scalaire "tu"
           )
         ))
  into v_register
  from public.user_facts uf
  where uf.user_id = p_user_id
    and uf.fact_key = 'preferred_language_register'
  order by coalesce(uf.updated_at, uf.created_at) desc nulls last
  limit 1;

  if v_register is null or v_register = '' then
    return;
  end if;

  if v_register = 'tu' then
    v_use_tu := true;
  elsif v_register = 'vous' then
    v_use_tu := false;
  else
    return;
  end if;

  update public.user_settings
  set use_tu_form = v_use_tu,
      updated_at = now()
  where user_id = p_user_id;
end;
$$;


--
-- Name: fn_refresh_user_agents_settings(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_refresh_user_agents_settings(p_user_id uuid) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
declare
  v_cnt int;
  v_keys_json text;
begin
  select
    count(*)::int,
    to_jsonb(array_agg(agent_key order by agent_key))::text
  into v_cnt, v_keys_json
  from public.lisa_user_agents
  where user_id = p_user_id
    and status = 'active';

  update public.user_settings
  set
    active_agents_count = coalesce(v_cnt, 0),
    included_agent_key  = coalesce(v_keys_json, '[]'),
    updated_at          = now()
  where user_id = p_user_id;
end;
$$;


--
-- Name: fn_revoke_personal_assistant_if_not_pro(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_revoke_personal_assistant_if_not_pro() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
begin
  -- Only act when user is NOT pro
  if new.is_pro = true then
    return new;
  end if;

  -- Only when is_pro just turned false
  if tg_op = 'UPDATE' and old.is_pro = true and new.is_pro = false then
    update public.lisa_user_agents
    set status     = 'off',
        revoked_at = now(),
        updated_at = now()
    where user_id = new.id
      and agent_key = 'personal_assistant';
  end if;

  return new;
end;
$$;


--
-- Name: fn_set_trial_started_at_from_billing_event(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_set_trial_started_at_from_billing_event() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
begin
  -- On ne traite que l'event RC qui correspond au démarrage de souscription (souvent début de trial)
  if new.provider = 'revenuecat' and new.event_type = 'INITIAL_PURCHASE' then

    -- Cas 1: on sait relier via auth_user_id (idéal)
    if new.auth_user_id is not null then
      update public.users u
      set trial_started_at = coalesce(u.trial_started_at, new.created_at),
          updated_at = now()
      where u.auth_user_id = new.auth_user_id
        and u.trial_started_at is null;
    end if;

    -- Cas 2 (fallback): si tu relies plutôt via app_user_id -> users.id
    if new.app_user_id is not null then
      update public.users u
      set trial_started_at = coalesce(u.trial_started_at, new.created_at),
          updated_at = now()
      where u.id = new.app_user_id
        and u.trial_started_at is null;
    end if;

  end if;

  return new;
end;
$$;


--
-- Name: fn_sync_last_active_at_from_auth(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_sync_last_active_at_from_auth() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_public_user_id uuid;
begin
  -- On ne fait rien si last_sign_in_at est NULL
  if new.last_sign_in_at is null then
    return new;
  end if;

  -- Trouver le public.users.id via auth_user_id
  select u.id into v_public_user_id
  from public.users u
  where u.auth_user_id = new.id
  limit 1;

  if v_public_user_id is null then
    return new; -- pas de user public lié (cas edge), on sort proprement
  end if;

  update public.user_settings us
  set last_active_at = new.last_sign_in_at,
      updated_at = now()
  where us.user_id = v_public_user_id;

  return new;
end;
$$;


--
-- Name: fn_trg_refresh_use_tu_form(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_trg_refresh_use_tu_form() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
begin
  -- on ne recalcul que si ça touche potentiellement le registre
  if (tg_op = 'DELETE') then
    if old.fact_key = 'preferred_language_register' then
      perform public.fn_refresh_use_tu_form(old.user_id);
    end if;
    return old;
  else
    if new.fact_key = 'preferred_language_register' then
      perform public.fn_refresh_use_tu_form(new.user_id);
    end if;
    return new;
  end if;
end;
$$;


--
-- Name: fn_trg_refresh_user_agents_settings(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_trg_refresh_user_agents_settings() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
begin
  perform public.fn_refresh_user_agents_settings(coalesce(new.user_id, old.user_id));
  return coalesce(new, old);
end;
$$;


--
-- Name: fn_users_set_signup_source_and_status(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_users_set_signup_source_and_status() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public', 'auth'
    AS $$
declare
  v_source text;
begin
  -- Rien à faire si pas de lien auth
  if new.auth_user_id is null then
    return new;
  end if;

  -- Ne jamais dégrader un user pro / trial / active
  if coalesce(new.is_pro, false) = true
     or new.status in ('trial'::public.user_status_enum, 'active'::public.user_status_enum) then
    return new;
  end if;

  -- On lit le tracking depuis auth.users
  select (u.raw_user_meta_data->>'signup_source')
    into v_source
  from auth.users u
  where u.id = new.auth_user_id;

  -- On recopie dans public.users.signup_source si vide
  if new.signup_source is null and v_source is not null and v_source <> '' then
    new.signup_source := v_source;
  end if;

  -- Status: prospect si footer détecté, sinon new_user
  if v_source = 'web_footer_magiclink' then
    new.status := 'prospect'::public.user_status_enum;
  else
    new.status := 'new_user'::public.user_status_enum;
  end if;

  return new;
end;
$$;


--
-- Name: get_user_smalltalk_stats(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_user_smalltalk_stats(p_user_id uuid) RETURNS TABLE(total_user_msgs integer, smalltalk_turns integer, smalltalk_done boolean)
    LANGUAGE sql
    AS $$
  select
    -- total de messages "user" (toutes sources confondues)
    (select count(*)::int
     from public.conversation_messages cm
     where cm.user_id = p_user_id
       and cm.sender_type = 'user'
    ) as total_user_msgs,

    -- état DB (user_settings)
    coalesce(
      (select us.intro_smalltalk_turns from public.user_settings us where us.user_id = p_user_id),
      0
    )::int as smalltalk_turns,

    coalesce(
      (select us.intro_smalltalk_done from public.user_settings us where us.user_id = p_user_id),
      false
    ) as smalltalk_done;
$$;


--
-- Name: handle_auth_user_created(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.handle_auth_user_created() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_email text;
  v_full_name text;
  v_avatar text;
  v_updated int := 0;
begin
  v_email := new.email;

  v_full_name :=
    coalesce(
      new.raw_user_meta_data->>'full_name',
      new.raw_user_meta_data->>'name',
      new.raw_user_meta_data->>'display_name',
      null
    );

  v_avatar :=
    coalesce(
      new.raw_user_meta_data->>'avatar_url',
      new.raw_user_meta_data->>'picture',
      null
    );

  insert into public.debug_auth_user_created_log(auth_user_id, email, stage, detail)
  values (new.id, v_email, 'START', 'trigger fired');

  begin
    update public.users u
    set
      auth_user_id = coalesce(u.auth_user_id, new.id),
      account_email = coalesce(u.account_email, v_email),
      full_name = coalesce(u.full_name, v_full_name),
      profile_photo_url = coalesce(u.profile_photo_url, v_avatar),
      updated_at = now()
    where
      u.auth_user_id = new.id
      or (
        u.auth_user_id is null
        and v_email is not null
        and lower(trim(u.account_email)) = lower(trim(v_email))
      );

    get diagnostics v_updated = row_count;

    insert into public.debug_auth_user_created_log(auth_user_id, email, stage, detail)
    values (new.id, v_email, 'AFTER_UPDATE', 'rows_updated=' || v_updated);

    if v_updated = 0 then
      insert into public.users (
        auth_user_id,
        account_email,
        full_name,
        profile_photo_url,
        status,
        created_at,
        updated_at
      )
      values (
        new.id,
        v_email,
        v_full_name,
        v_avatar,
        'prospect',
        now(),
        now()
      );

      insert into public.debug_auth_user_created_log(auth_user_id, email, stage, detail)
      values (new.id, v_email, 'AFTER_INSERT', 'inserted public.users');
    else
      insert into public.debug_auth_user_created_log(auth_user_id, email, stage, detail)
      values (new.id, v_email, 'SKIP_INSERT', 'user matched by update');
    end if;

  exception when others then
    insert into public.debug_auth_user_created_log(auth_user_id, email, stage, detail)
    values (new.id, v_email, 'ERROR', SQLSTATE || ' - ' || SQLERRM);
  end;

  insert into public.debug_auth_user_created_log(auth_user_id, email, stage, detail)
  values (new.id, v_email, 'END', 'done');

  return new;
end;
$$;


--
-- Name: mark_event_mentioned(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.mark_event_mentioned(event_id uuid) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  UPDATE user_key_events
  SET 
    last_mentioned_at = NOW(),
    mention_count = mention_count + 1,
    updated_at = NOW()
  WHERE id = event_id;
END;
$$;


--
-- Name: next_allowed_push_time(timestamp with time zone, text, integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.next_allowed_push_time(p_now timestamp with time zone, p_tz text DEFAULT 'Europe/Paris'::text, p_quiet_start integer DEFAULT 22, p_quiet_end integer DEFAULT 6) RETURNS timestamp with time zone
    LANGUAGE plpgsql
    AS $$
declare
  local_ts timestamp;
  local_hour int;
  next_local timestamp;
begin
  -- Convertit "now" en heure locale (timestamp sans tz)
  local_ts := (p_now at time zone p_tz);
  local_hour := extract(hour from local_ts);

  -- Si on est dans la plage de repos
  if (local_hour >= p_quiet_start) or (local_hour < p_quiet_end) then
    -- prochain 06:05 (petit offset pour éviter pile 06:00)
    if local_hour >= p_quiet_start then
      next_local := date_trunc('day', local_ts) + interval '1 day' + make_interval(hours => p_quiet_end, mins => 5);
    else
      next_local := date_trunc('day', local_ts) + make_interval(hours => p_quiet_end, mins => 5);
    end if;

    -- Reconvertit en timestamptz
    return (next_local at time zone p_tz);
  end if;

  return p_now;
end;
$$;


--
-- Name: push_outbox; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.push_outbox (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    kind text NOT NULL,
    title text NOT NULL,
    body text NOT NULL,
    data jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    sent_at timestamp with time zone,
    status text DEFAULT 'queued'::text NOT NULL,
    error text,
    scheduled_at timestamp with time zone,
    attempts integer DEFAULT 0 NOT NULL,
    sending_at timestamp with time zone,
    CONSTRAINT push_outbox_kind_check CHECK ((kind = ANY (ARRAY['chat'::text, 'system'::text]))),
    CONSTRAINT push_outbox_status_check CHECK ((status = ANY (ARRAY['queued'::text, 'sent'::text, 'failed'::text])))
);


--
-- Name: pop_push_outbox(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.pop_push_outbox(p_limit integer DEFAULT 25) RETURNS SETOF public.push_outbox
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
begin
  return query
  with picked as (
    select id
    from public.push_outbox
    where status = 'queued'
      and scheduled_at <= now()
    order by scheduled_at asc
    for update skip locked
    limit p_limit
  )
  update public.push_outbox o
  set status = 'queued', -- on laisse queued (option simple) OU tu peux mettre 'sending' si tu veux
      sending_at = now(),
      attempts = attempts + 1
  from picked
  where o.id = picked.id
  returning o.*;
end;
$$;


--
-- Name: proactive_enqueue_inactivity_events(integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.proactive_enqueue_inactivity_events(p_hours integer DEFAULT 48, p_limit integer DEFAULT 200) RETURNS integer
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_count int := 0;
begin
  with candidates as (
    select
      c.id as conversation_id,
      c.user_id,
      c.last_message_at
    from public.conversations c
    join public.users u on u.id = c.user_id
    where u.status = 'active'
      and c.last_message_at is not null
      and c.last_message_at <= now() - make_interval(hours => p_hours)
      -- évite de spammer: si on a déjà envoyé un proactif après le dernier msg, on skip
      and (c.last_proactive_message_at is null or c.last_proactive_message_at < c.last_message_at)
    order by c.last_message_at asc
    limit p_limit
  ),
  ins as (
    insert into public.proactive_events_outbox (
      event_type,
      user_id,
      conversation_id,
      payload,
      dedupe_key
    )
    select
      'INACTIVITY_48H'::text,
      user_id,
      conversation_id,
      jsonb_build_object(
        'inactivity_hours', p_hours,
        'last_message_at', last_message_at,
        'trigger_source', 'pg_cron'
      ),
      -- dédup “par conversation + last_message_at + type”
      'INACTIVITY_48H|' || conversation_id::text || '|' || to_char(last_message_at at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
    from candidates
    on conflict (dedupe_key) do nothing
    returning 1
  )
  select count(*) into v_count from ins;

  return v_count;
end;
$$;


--
-- Name: proactive_mark_ready_due_messages(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.proactive_mark_ready_due_messages(p_limit integer DEFAULT 50) RETURNS integer
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_count int := 0;
begin
  with picked as (
    select id
    from public.proactive_messages_queue
    where status = 'scheduled'
      and send_at <= now()
    order by send_at asc
    limit p_limit
    for update skip locked
  ),
  upd as (
    update public.proactive_messages_queue q
    set status = 'ready',
        updated_at = now()
    from picked
    where q.id = picked.id
      and q.status = 'scheduled'
    returning q.id
  )
  select count(*) into v_count from upd;

  return v_count;
end;
$$;


--
-- Name: propagate_affiliate_code_to_users(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.propagate_affiliate_code_to_users() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF NEW.auth_user_id IS NOT NULL AND NEW.code IS NOT NULL THEN
    UPDATE public.users
    SET affiliate_code = NEW.code
    WHERE auth_user_id = NEW.auth_user_id
      AND (affiliate_code IS NULL OR affiliate_code = '');
  END IF;

  RETURN NEW;
END;
$$;


--
-- Name: propagate_use_tu_form_from_user_facts(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.propagate_use_tu_form_from_user_facts() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
declare
  v_text text;
  v_use_tu boolean;
begin
  -- On ne traite que le fact clé qu'on veut propager
  if new.fact_key <> 'preferred_language_register' then
    return new;
  end if;

  -- Si fact désactivé, on ne propage pas (ou alors on pourrait recalculer depuis un autre fact actif)
  if coalesce(new.is_active, true) = false then
    return new;
  end if;

  -- Extraire la valeur texte depuis jsonb
  -- Cas possibles: "tu", {"value":"tu"}, etc. -> on couvre proprement
  if jsonb_typeof(new.value) = 'string' then
    v_text := trim(both '"' from new.value::text);
  elsif jsonb_typeof(new.value) = 'object' then
    v_text := coalesce(new.value->>'value', new.value->>'text', new.value->>'register', null);
  else
    v_text := null;
  end if;

  v_text := lower(coalesce(v_text, ''));

  -- Mapping
  if v_text in ('tu', 'tutoiement') then
    v_use_tu := true;
  elsif v_text in ('vous', 'vouvoiement') then
    v_use_tu := false;
  else
    -- Valeur non reconnue -> on ne touche pas
    return new;
  end if;

  -- Upsert user_settings (garantit qu'on a toujours une ligne)
  insert into public.user_settings (user_id, use_tu_form, updated_at)
  values (new.user_id, v_use_tu, now())
  on conflict (user_id)
  do update set
    use_tu_form = excluded.use_tu_form,
    updated_at  = now();

  return new;
end;
$$;


--
-- Name: refresh_user_settings_job_industry(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.refresh_user_settings_job_industry(p_user_id uuid) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
declare
  v_job_title text;
  v_industry  text;
  v_work_status text;
  v_life_stage  text;
begin
  /*
    1) Récupérer les facts "propres" si présents
  */
  select uf.value
  into v_job_title
  from public.user_facts uf
  where uf.user_id = p_user_id
    and uf.fact_key = 'job_title'
    and uf.value_type = 'text'
    and uf.value is not null
  order by uf.updated_at desc nulls last
  limit 1;

  select uf.value
  into v_industry
  from public.user_facts uf
  where uf.user_id = p_user_id
    and uf.fact_key = 'industry'
    and uf.value_type = 'text'
    and uf.value is not null
  order by uf.updated_at desc nulls last
  limit 1;

  /*
    2) Fallbacks (si job_title absent)
       - work_status (CEO/employee/freelance/other)
       - life_stage (student/employed/unemployed/entrepreneur/retired/other)
  */
  if v_job_title is null then
    select uf.value
    into v_work_status
    from public.user_facts uf
    where uf.user_id = p_user_id
      and uf.fact_key = 'work_status'
      and uf.value_type = 'text'
      and uf.value is not null
    order by uf.updated_at desc nulls last
    limit 1;

    if v_work_status is not null then
      v_job_title :=
        case lower(v_work_status)
          when 'ceo' then 'Chef d''entreprise'
          when 'founder' then 'Chef d''entreprise'
          when 'entrepreneur' then 'Entrepreneur'
          when 'employee' then 'Salarié'
          when 'freelance' then 'Freelance'
          when 'other' then null
          else v_work_status
        end case;
    end if;
  end if;

  if v_job_title is null then
    select uf.value
    into v_life_stage
    from public.user_facts uf
    where uf.user_id = p_user_id
      and uf.fact_key = 'life_stage'
      and uf.value_type = 'text'
      and uf.value is not null
    order by uf.updated_at desc nulls last
    limit 1;

    if v_life_stage is not null then
      v_job_title :=
        case lower(v_life_stage)
          when 'student' then 'Étudiant'
          when 'employed' then 'Salarié'
          when 'unemployed' then 'Sans emploi'
          when 'entrepreneur' then 'Entrepreneur'
          when 'retired' then 'Retraité'
          when 'other' then null
          else v_life_stage
        end case;
    end if;
  end if;

  /*
    3) Update user_settings (on met à jour seulement si ça change)
  */
  update public.user_settings us
  set
    job_title  = v_job_title,
    industry   = v_industry,
    updated_at = now()
  where us.user_id = p_user_id
    and (
      us.job_title is distinct from v_job_title
      or us.industry is distinct from v_industry
    );

end;
$$;


--
-- Name: run_paywall_engagement(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.run_paywall_engagement() RETURNS integer
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$declare
  updated_users integer := 0;
begin
  with eligible_users as (
    select
      u.id,
      u.trial_started_at
    from public.users u
    where
      coalesce(u.is_pro, false) = false
      and (u.paywall_reason is null or btrim(u.paywall_reason) = '')
      and u.paywall_at is null
      and u.trial_started_at <= now() - interval '24 hours'
  ),

  msg_metrics as (
    select
      eu.id as user_id,

      max(cm.sent_at) filter (where cm.sender_type = 'user') as last_user_message_at,

      count(*) filter (
        where cm.sender_type = 'user'
          and cm.sent_at >= now() - interval '7 days'
      ) as user_msgs_7d,

      count(distinct date_trunc('day', cm.sent_at)) filter (
        where cm.sender_type = 'user'
          and cm.sent_at >= now() - interval '7 days'
      ) as active_days_7d

    from eligible_users eu
    left join public.conversations c
      on c.user_id = eu.id
    left join public.conversation_messages cm
      on cm.conversation_id = c.id
    group by eu.id
  ),

  concierge_metrics as (
    select
      eu.id as user_id,
      (
        select count(*)
        from public.lisa_concierge_suggestions lcs
        where lcs.user_id = eu.id
          and coalesce(lcs.suggested_at, lcs.created_at) >= now() - interval '30 days'
      ) as concierge_suggestions_30d
    from eligible_users eu
  ),

  merged as (
    select
      m.user_id,
      m.last_user_message_at,
      coalesce(m.user_msgs_7d, 0) as user_msgs_7d,
      coalesce(m.active_days_7d, 0) as active_days_7d,
      coalesce(c.concierge_suggestions_30d, 0) as concierge_suggestions_30d
    from msg_metrics m
    join concierge_metrics c on c.user_id = m.user_id
  ),

  scored as (
    select
      *,
      (
        case
          when user_msgs_7d >= 40 then 55
          when user_msgs_7d >= 20 then 40
          else 0
        end
        +
        case
          when active_days_7d >= 4 then 30
          when active_days_7d >= 3 then 20
          else 0
        end
        +
        case
          when concierge_suggestions_30d >= 1 then 30
          else 0
        end
      )::numeric as engagement_score
    from merged
  ),

  upsert_settings as (
    insert into public.user_settings as us (
      user_id,
      engagement_score,
      chat_turns_7d,
      active_days_7d,
      concierge_requests_30d,
      last_message_at,
      engagement_last_calculated_at,
      updated_at
    )
    select
      s.user_id,
      s.engagement_score,
      s.user_msgs_7d,
      s.active_days_7d,
      s.concierge_suggestions_30d,
      s.last_user_message_at,
      now(),
      now()
    from scored s
    on conflict (user_id) do update set
      engagement_score = excluded.engagement_score,
      chat_turns_7d = excluded.chat_turns_7d,
      active_days_7d = excluded.active_days_7d,
      concierge_requests_30d = excluded.concierge_requests_30d,
      last_message_at = excluded.last_message_at,
      engagement_last_calculated_at = excluded.engagement_last_calculated_at,
      updated_at = excluded.updated_at
    returning user_id
  ),

  candidates as (
    select eu.id
    from eligible_users eu
    join public.user_settings us on us.user_id = eu.id
    where
      us.last_message_at >= now() - interval '48 hours'
      and us.engagement_score >= 75
  )

  update public.users u
    set paywall_reason = 'engagement',
        paywall_at     = now(),
        updated_at     = now()
  where u.id in (select id from candidates);

  get diagnostics updated_users = row_count;
  return updated_users;
end;$$;


--
-- Name: run_paywall_time_expired(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.run_paywall_time_expired(p_days integer DEFAULT 14) RETURNS jsonb
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
declare
  v_updated int := 0;
begin
  update public.users u
  set
    paywall_reason = 'time',
    paywall_at     = coalesce(u.paywall_at, now()),
    updated_at     = now()
  where
    coalesce(u.is_pro, false) = false
    and (u.paywall_reason is null or btrim(u.paywall_reason) = '')
    and u.trial_started_at is not null
    and u.trial_started_at <= now() - make_interval(days => p_days);

  get diagnostics v_updated = row_count;

  return jsonb_build_object(
    'ok', true,
    'reason', 'time',
    'days', p_days,
    'updated', v_updated,
    'ran_at', now()
  );
end;
$$;


--
-- Name: save_welcome_message(uuid, text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.save_welcome_message(p_conversation_id uuid, p_content text, p_first_name text DEFAULT NULL::text) RETURNS TABLE(id uuid, sent_at timestamp with time zone)
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_user_id uuid;
  v_dedupe_key text;
  v_content text;
begin
  -- 1) resolve public.users.id from auth.uid()
  select u.id into v_user_id
  from public.users u
  where u.auth_user_id = auth.uid()
    and u.deleted_at is null
  limit 1;

  if v_user_id is null then
    raise exception 'no_public_user_for_auth_uid';
  end if;

  -- 2) ensure conversation belongs to this user
  if not exists (
    select 1
    from public.conversations c
    where c.id = p_conversation_id
      and c.user_id = v_user_id
  ) then
    raise exception 'conversation_not_owned_by_user';
  end if;

  -- 3) stable dedupe key
  v_dedupe_key := 'sys:welcome:' || p_conversation_id::text;

  -- 4) content
  v_content := coalesce(nullif(trim(p_content), ''), 'Bienvenue 👋');

  -- 5) insert as assistant (bypass RLS via security definer)
  insert into public.conversation_messages (
    conversation_id,
    user_id,
    sender_type,
    role,
    content,
    metadata,
    dedupe_key
  )
  values (
    p_conversation_id,
    v_user_id,
    'lisa',
    'assistant',
    v_content,
    jsonb_build_object(
      'event_type','chat',
      'kind','welcome',
      'first_name', p_first_name
    ),
    v_dedupe_key
  )
  on conflict (dedupe_key)
  do update set
    content  = excluded.content,
    metadata = excluded.metadata
  returning conversation_messages.id, conversation_messages.sent_at
  into id, sent_at;

  return;
end;
$$;


--
-- Name: set_automation_templates_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_automation_templates_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  new.updated_at = now();
  return new;
end;
$$;


--
-- Name: set_plan_automation_pricing_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_plan_automation_pricing_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  new.updated_at = now();
  return new;
end;
$$;


--
-- Name: set_proactive_messages_queue_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_proactive_messages_queue_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  new.updated_at = now();
  return new;
end;
$$;


--
-- Name: set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  new.updated_at = now();
  return new;
end;
$$;


--
-- Name: set_user_automations_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_user_automations_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  new.updated_at = now();
  return new;
end;
$$;


--
-- Name: should_send_push(uuid, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.should_send_push(p_user_id uuid, p_kind text) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
declare
  has_any_active boolean;
  has_active_chat boolean;
begin
  -- devices actifs (app au premier plan)
  select exists(
    select 1 from public.push_devices
    where user_id = p_user_id
      and is_app_active = true
  ) into has_any_active;

  -- device actif SUR le chat
  select exists(
    select 1 from public.push_devices
    where user_id = p_user_id
      and is_app_active = true
      and active_screen = 'chat'
  ) into has_active_chat;

  if p_kind = 'chat' then
    return not has_active_chat;   -- si user est déjà sur le chat => pas de push
  end if;

  if p_kind = 'system' then
    return not has_any_active;    -- si app active => pas de push (option “safe”)
  end if;

  return false;
end;
$$;


--
-- Name: sync_user_settings_last_message_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.sync_user_settings_last_message_at() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
begin
  if new.user_id is null then
    return new;
  end if;

  update public.user_settings
  set last_message_at = new.last_message_at,
      updated_at = now()
  where user_id = new.user_id;

  return new;
end;
$$;


--
-- Name: tg_set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.tg_set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  new.updated_at = now();
  return new;
end;
$$;


--
-- Name: track_doc_usage(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.track_doc_usage(doc_id uuid) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  UPDATE lisa_service_docs
  SET 
    usage_count = usage_count + 1,
    last_used_at = NOW()
  WHERE id = doc_id;
END;
$$;


--
-- Name: trg_billing_events_recompute_user_status(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trg_billing_events_recompute_user_status() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  if new.user_id is not null and new.provider = 'revenuecat' then
    perform public.fn_recompute_user_status(new.user_id);
  end if;
  return new;
end;
$$;


--
-- Name: trg_conversation_message_enqueue_push(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trg_conversation_message_enqueue_push() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
declare
  v_user_id uuid;
  v_is_welcome boolean;
begin
  -- on ne push que sur messages Lisa
  if new.sender_type <> 'lisa' then
    return new;
  end if;

  -- option : ignorer le welcome
  v_is_welcome := coalesce((new.metadata->>'kind') = 'welcome', false);
  if v_is_welcome then
    return new;
  end if;

  -- user_id (public.users.id) : direct sinon via conversations.user_id
  v_user_id := new.user_id;
  if v_user_id is null then
    select c.user_id into v_user_id
    from public.conversations c
    where c.id = new.conversation_id;
  end if;

  if v_user_id is null then
    return new;
  end if;

  -- ✅ NOTIF STANDARD
  -- title = "Lisa"
  -- body  = extrait 160 chars
  perform public.enqueue_push(
    p_user_id      => v_user_id,
    p_kind         => 'chat',
    p_title        => 'Lisa',
    p_body         => left(coalesce(new.content,''), 160),
    p_data         => jsonb_build_object(
                      'type','chat',
                      'conversation_id', new.conversation_id,
                      'message_id', new.id
                    ),
    p_scheduled_at => now(),
    p_tz           => 'Europe/Paris'
  );

  return new;
end;
$$;


--
-- Name: trg_outbox_on_lisa_tech_issue(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trg_outbox_on_lisa_tech_issue() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_fallback text := 'Je rencontre un petit souci technique. Réessaie dans un instant.';
  v_dedupe text;
begin
  -- On ne réagit qu'aux messages assistant/Lisa
  if (new.role = 'assistant'::public.conversation_role_enum)
     and (new.sender_type = 'lisa'::public.conversation_sender_enum)
     and (new.content = v_fallback) then

    -- Dédoublonnage strict : 1 event par message
    v_dedupe := 'TECH_ISSUE|' || new.id::text;

    insert into public.proactive_events_outbox (
      event_type,
      user_id,
      conversation_id,
      payload,
      dedupe_key
    )
    values (
      'TECH_ISSUE',
      coalesce(new.user_id, (select c.user_id from public.conversations c where c.id = new.conversation_id)),
      new.conversation_id,
      jsonb_build_object(
        'message_id', new.id,
        'fallback', v_fallback,
        'content', new.content,
        'sent_at', new.sent_at
      ),
      v_dedupe
    )
    on conflict (dedupe_key) do nothing;
  end if;

  return new;
end;
$$;


--
-- Name: trg_outbox_on_task_created(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trg_outbox_on_task_created() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_dedupe text;
begin
  -- Dédoublonnage strict : 1 event par task_id
  v_dedupe := 'TASK_CREATED|' || new.id::text;

  insert into public.proactive_events_outbox (
    event_type,
    user_id,
    conversation_id,
    payload,
    dedupe_key
  )
  values (
    'TASK_CREATED',
    new.user_id,
    new.conversation_id,
    jsonb_build_object(
      'task_id', new.id,
      'task_type', new.task_type,
      'status', new.status,
      'priority', new.priority,
      'title', new.title,
      'description', new.description,
      'due_at', new.due_at,
      'created_at', new.created_at,
      'source_reference', new.source_reference,
      'trigger_source', new.trigger_source
    ),
    v_dedupe
  )
  on conflict (dedupe_key) do nothing;

  return new;
end;
$$;


--
-- Name: trg_refresh_user_settings_job_industry(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trg_refresh_user_settings_job_industry() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
begin
  perform public.refresh_user_settings_job_industry(coalesce(new.user_id, old.user_id));
  return coalesce(new, old);
end;
$$;


--
-- Name: trg_users_recompute_status(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trg_users_recompute_status() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  perform public.fn_recompute_user_status(new.id);
  return new;
end;
$$;


--
-- Name: update_intro_smalltalk_state(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_intro_smalltalk_state() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
declare
  v_user_id uuid;
begin
  -- 1) On ne compte que les messages émis par le user
  if new.sender_type <> 'user' then
    return new;
  end if;

  -- 2) user_id direct si présent sur conversation_messages
  v_user_id := new.user_id;

  -- 3) fallback : si user_id null, on le récupère via conversations
  if v_user_id is null then
    select c.user_id
      into v_user_id
    from public.conversations c
    where c.id = new.conversation_id;

    if v_user_id is null then
      return new;
    end if;
  end if;

  -- 4) Ensure user_settings row
  insert into public.user_settings (user_id)
  values (v_user_id)
  on conflict (user_id) do nothing;

  -- 5) Increment uniquement si pas déjà done
  update public.user_settings us
  set
    intro_smalltalk_turns = us.intro_smalltalk_turns + 1,
    intro_smalltalk_done  = case
      when (us.intro_smalltalk_turns + 1) >= 8 then true
      else us.intro_smalltalk_done
    end,
    updated_at = now()
  where us.user_id = v_user_id
    and us.intro_smalltalk_done = false;

  return new;
end;
$$;


--
-- Name: update_lisa_service_docs_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_lisa_service_docs_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;


--
-- Name: update_profiling_completion(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_profiling_completion() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  total_core_facts INT;
  user_core_facts_count INT;
  completion_pct NUMERIC;
  new_level TEXT;
BEGIN
  -- Compter le nombre total de facts "core" dans fact_key_registry
  SELECT COUNT(*) INTO total_core_facts
  FROM fact_key_registry
  WHERE status = 'core';
  
  -- Compter combien de facts core le user a renseignés
  SELECT COUNT(DISTINCT fact_key) INTO user_core_facts_count
  FROM user_facts
  WHERE user_id = NEW.user_id
    AND fact_key IN (
      SELECT fact_key FROM fact_key_registry WHERE status = 'core'
    );
  
  -- Calculer le %
  completion_pct := (user_core_facts_count::NUMERIC / total_core_facts::NUMERIC) * 100;
  
  -- Déterminer le niveau
  IF completion_pct < 25 THEN
    new_level := 'max';
  ELSIF completion_pct < 50 THEN
    new_level := 'high';
  ELSIF completion_pct < 75 THEN
    new_level := 'medium';
  ELSE
    new_level := 'baseline';
  END IF;
  
  -- Mettre à jour user_settings
  UPDATE user_settings
  SET 
    profiling_facts_count = user_core_facts_count,
    profiling_facts_total = total_core_facts,
    profiling_completion_pct = completion_pct,
    profiling_level = new_level,
    profiling_completed = (completion_pct >= 75)
  WHERE user_id = NEW.user_id;
  
  RETURN NEW;
END;
$$;


--
-- Name: update_timestamp(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  new.updated_at = now();
  return new;
end;
$$;


--
-- Name: update_user_key_events_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_user_key_events_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;


--
-- Name: upsert_push_device_safe(text, text, text, boolean, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.upsert_push_device_safe(p_device_id text, p_expo_push_token text, p_platform text, p_is_app_active boolean, p_active_screen text) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_user_id uuid;
  v_existing_id uuid;
  v_existing_device_id text;
  v_id uuid;
begin
  -- 1) Récupère le public.users.id du user authentifié
  select u.id into v_user_id
  from public.users u
  where u.auth_user_id = auth.uid()
  limit 1;

  if v_user_id is null then
    raise exception 'no_public_user_for_auth_uid';
  end if;

  -- 2) Si le token existe déjà, on check device_id (anti-hijack)
  select id, device_id
  into v_existing_id, v_existing_device_id
  from public.push_devices
  where expo_push_token = p_expo_push_token
  limit 1;

  if v_existing_id is not null
     and v_existing_device_id is not null
     and v_existing_device_id <> p_device_id then

    -- Autoriser le "rebinding" UNIQUEMENT si le token change de user
    -- (ex: même téléphone, compte A -> compte B, device_id local régénéré)
    if exists (
      select 1
      from public.push_devices
      where expo_push_token = p_expo_push_token
        and user_id <> v_user_id
      limit 1
    ) then
      -- OK: on autorise
      null;
    else
      -- Même user + device_id différent => suspect => on bloque
      raise exception 'token_already_bound_to_another_device';
    end if;
  end if;

  -- 3) Upsert
  insert into public.push_devices (
    user_id,
    device_id,
    expo_push_token,
    platform,
    is_app_active,
    active_screen,
    last_seen_at
  )
  values (
    v_user_id,
    p_device_id,
    p_expo_push_token,
    p_platform,
    p_is_app_active,
    p_active_screen,
    now()
  )
  on conflict (expo_push_token)
  do update set
    user_id       = excluded.user_id,
    device_id     = excluded.device_id,
    platform      = excluded.platform,
    is_app_active = excluded.is_app_active,
    active_screen = excluded.active_screen,
    last_seen_at  = excluded.last_seen_at
  returning id into v_id;

  return v_id;
end;
$$;


--
-- Name: user_is_on_chat(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.user_is_on_chat(p_user_id uuid) RETURNS boolean
    LANGUAGE sql STABLE
    AS $$
  select exists (
    select 1
    from public.push_devices d
    where d.user_id = p_user_id
      and d.is_app_active = true
      and d.active_screen = 'chat'
      and d.last_seen_at > (now() - interval '2 minutes')
  );
$$;


--
-- Name: affiliate_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.affiliate_codes (
    user_id uuid NOT NULL,
    code text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    id uuid DEFAULT gen_random_uuid(),
    share_url text,
    country_code text
);


--
-- Name: affiliate_commissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.affiliate_commissions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    affiliate_id uuid NOT NULL,
    affiliate_promo_code_id uuid NOT NULL,
    stripe_invoice_id text NOT NULL,
    stripe_subscription_id text,
    stripe_customer_id text,
    stripe_charge_id text,
    amount_excl_tax_cents integer NOT NULL,
    commission_rate numeric(5,2) NOT NULL,
    commission_cents integer NOT NULL,
    currency text DEFAULT 'eur'::text NOT NULL,
    period_start timestamp with time zone,
    period_end timestamp with time zone,
    status text DEFAULT 'pending'::text NOT NULL,
    payout_batch_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: automation_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.automation_templates (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    slug text NOT NULL,
    label text NOT NULL,
    category public.automation_category_enum DEFAULT 'other'::public.automation_category_enum NOT NULL,
    description_short text NOT NULL,
    description_full text,
    complexity_level public.automation_complexity_enum DEFAULT '2'::public.automation_complexity_enum NOT NULL,
    recommended_plan public.plan_recommendation_enum DEFAULT 'pro'::public.plan_recommendation_enum NOT NULL,
    required_connectors jsonb DEFAULT '[]'::jsonb,
    default_triggers jsonb DEFAULT '{}'::jsonb,
    default_actions jsonb DEFAULT '{}'::jsonb,
    default_roi_estimate jsonb DEFAULT '{}'::jsonb,
    tags text[] DEFAULT ARRAY[]::text[],
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    tier public.automation_tier_enum DEFAULT 'standard'::public.automation_tier_enum NOT NULL
);


--
-- Name: billing_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.billing_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    source text NOT NULL,
    provider text NOT NULL,
    provider_event_id text,
    event_type text,
    auth_user_id uuid,
    app_user_id text,
    user_id uuid,
    entitlement_ids text[],
    expiration_at timestamp with time zone,
    payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    processed_at timestamp with time zone,
    process_status text DEFAULT 'received'::text NOT NULL,
    process_error text,
    payload_sha256 text,
    mode text
);


--
-- Name: billing_state; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.billing_state (
    user_id uuid NOT NULL,
    auth_user_id uuid,
    is_pro boolean DEFAULT false NOT NULL,
    has_core boolean DEFAULT false NOT NULL,
    active_entitlements text[] DEFAULT '{}'::text[] NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: companies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.companies (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    legal_name text,
    slug text,
    website text,
    country_code character(2),
    main_city text,
    size public.company_size_enum,
    industry text,
    source text,
    external_ref text,
    notes jsonb DEFAULT '{}'::jsonb,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: conversation_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversation_messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    conversation_id uuid NOT NULL,
    user_id uuid,
    sender_type public.conversation_sender_enum DEFAULT 'user'::public.conversation_sender_enum NOT NULL,
    role public.conversation_role_enum DEFAULT 'user'::public.conversation_role_enum NOT NULL,
    content text NOT NULL,
    content_tokens integer,
    sent_at timestamp with time zone DEFAULT now() NOT NULL,
    channel_message_id text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    sender text,
    visitor_id uuid,
    dedupe_key text NOT NULL
);


--
-- Name: conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    channel public.conversation_channel_enum DEFAULT 'web_onboarding'::public.conversation_channel_enum NOT NULL,
    context public.conversation_context_enum DEFAULT 'other'::public.conversation_context_enum NOT NULL,
    status public.conversation_status_enum DEFAULT 'open'::public.conversation_status_enum NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    last_message_at timestamp with time zone DEFAULT now() NOT NULL,
    last_summary text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    visitor_id uuid,
    meta jsonb DEFAULT '{}'::jsonb,
    last_proactive_message_at timestamp with time zone
);


--
-- Name: debug_auth_user_created_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.debug_auth_user_created_log (
    id bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    auth_user_id uuid,
    email text,
    stage text NOT NULL,
    detail text
);


--
-- Name: debug_auth_user_created_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.debug_auth_user_created_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: debug_auth_user_created_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.debug_auth_user_created_log_id_seq OWNED BY public.debug_auth_user_created_log.id;


--
-- Name: email_accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.email_accounts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    provider public.email_provider_enum DEFAULT 'google'::public.email_provider_enum NOT NULL,
    email text NOT NULL,
    is_primary boolean DEFAULT false NOT NULL,
    status public.email_account_status_enum DEFAULT 'pending'::public.email_account_status_enum NOT NULL,
    provider_user_id text,
    scopes text[],
    last_sync_at timestamp with time zone,
    last_sync_status text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    access_token text,
    refresh_token text,
    token_type text,
    expires_at timestamp with time zone,
    id_token text,
    sync_cursor text
);


--
-- Name: fact_key_registry; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fact_key_registry (
    fact_key text NOT NULL,
    status public.fact_key_status_enum DEFAULT 'proposed'::public.fact_key_status_enum NOT NULL,
    category_default public.fact_category_enum DEFAULT 'other'::public.fact_category_enum NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    used_count integer DEFAULT 0 NOT NULL,
    last_used_at timestamp with time zone
);


--
-- Name: fact_profile_mappings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fact_profile_mappings (
    id bigint NOT NULL,
    fact_key text NOT NULL,
    target_table text NOT NULL,
    target_column text NOT NULL,
    sync_direction text DEFAULT 'facts->user'::text NOT NULL,
    priority integer DEFAULT 10 NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


--
-- Name: fact_profile_mappings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.fact_profile_mappings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: fact_profile_mappings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.fact_profile_mappings_id_seq OWNED BY public.fact_profile_mappings.id;


--
-- Name: gmail_watch_subscriptions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.gmail_watch_subscriptions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    account_email text NOT NULL,
    channel_id text NOT NULL,
    resource_id text NOT NULL,
    history_id text NOT NULL,
    expiration timestamp with time zone NOT NULL,
    last_renewed_at timestamp with time zone DEFAULT now() NOT NULL,
    status text DEFAULT 'active'::text NOT NULL,
    last_error text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: heylisa_post_checkout_contexts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.heylisa_post_checkout_contexts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id text NOT NULL,
    visitor_id text,
    user_id uuid NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone
);


--
-- Name: iap_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.iap_transactions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    platform public.iap_platform NOT NULL,
    product_id text NOT NULL,
    purchased_at timestamp with time zone DEFAULT now() NOT NULL,
    transaction_id text,
    original_transaction_id text,
    is_refund boolean DEFAULT false NOT NULL,
    raw jsonb
);


--
-- Name: lisa_agent_integrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lisa_agent_integrations (
    agent_key text NOT NULL,
    integration_key text NOT NULL,
    required boolean DEFAULT true NOT NULL,
    notes text DEFAULT ''::text NOT NULL
);


--
-- Name: lisa_agents_catalog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lisa_agents_catalog (
    agent_key text NOT NULL,
    title text NOT NULL,
    lisa_instructions_short text DEFAULT ''::text NOT NULL,
    lisa_playbook text DEFAULT ''::text NOT NULL,
    requires_subscription boolean DEFAULT false NOT NULL,
    requires_integrations text[] DEFAULT '{}'::text[] NOT NULL,
    executable_actions text[] DEFAULT '{}'::text[] NOT NULL,
    status text DEFAULT 'live'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: lisa_brains; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lisa_brains (
    id text NOT NULL,
    description text,
    lisa_brain_prompt text NOT NULL
);


--
-- Name: lisa_concierge_suggestions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lisa_concierge_suggestions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    suggestion_type text NOT NULL,
    title text NOT NULL,
    description text,
    url text,
    location_city text,
    location_address text,
    suggested_at timestamp with time zone DEFAULT now(),
    suggested_for_date date,
    expires_at date,
    status text DEFAULT 'suggested'::text,
    user_feedback text,
    feedback_at timestamp with time zone,
    source text DEFAULT 'lisa_proactive'::text,
    search_query text,
    context_tags text[],
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: lisa_dashboard_weekly_kpis; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lisa_dashboard_weekly_kpis (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    email_account_id uuid,
    week_start date NOT NULL,
    time_saved_minutes integer DEFAULT 0 NOT NULL,
    life_health_energy numeric(4,1) NOT NULL,
    life_finance_stability numeric(4,1) NOT NULL,
    life_relations_social numeric(4,1) NOT NULL,
    life_career_impact numeric(4,1) NOT NULL,
    life_personal_development numeric(4,1) NOT NULL,
    life_balance_serenity numeric(4,1) NOT NULL,
    life_global_average numeric(4,1) NOT NULL,
    life_summary text,
    week_end date,
    week_key text,
    window_label text,
    year_month text
);


--
-- Name: lisa_integrations_catalog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lisa_integrations_catalog (
    id text DEFAULT gen_random_uuid() NOT NULL,
    provider text NOT NULL,
    name text NOT NULL,
    category text NOT NULL,
    description text,
    status public.integration_status_enum DEFAULT 'active'::public.integration_status_enum NOT NULL,
    docs_url text,
    icon_url text,
    default_scopes jsonb,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    integration_key text
);


--
-- Name: lisa_priority_emails; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lisa_priority_emails (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    gmail_id text NOT NULL,
    thread_id text NOT NULL,
    subject text NOT NULL,
    from_email text NOT NULL,
    to_emails text,
    cc_emails text,
    date_received timestamp with time zone NOT NULL,
    is_unread boolean DEFAULT true NOT NULL,
    in_inbox boolean DEFAULT true NOT NULL,
    labels text[] DEFAULT '{}'::text[] NOT NULL,
    snippet text,
    body_full text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    processed_at timestamp with time zone
);


--
-- Name: lisa_service_docs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lisa_service_docs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    chunk_title text NOT NULL,
    chunk_content text NOT NULL,
    tags text[] NOT NULL,
    order_key text DEFAULT '1.0'::text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    doc_scope text,
    rubrique_title text
);


--
-- Name: lisa_tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lisa_tasks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    project_id uuid,
    conversation_id uuid,
    task_type public.lisa_task_type_enum NOT NULL,
    owner_type public.lisa_task_owner_enum DEFAULT 'lisa'::public.lisa_task_owner_enum NOT NULL,
    status public.lisa_task_status_enum DEFAULT 'pending'::public.lisa_task_status_enum NOT NULL,
    priority public.lisa_task_priority_enum DEFAULT 'normal'::public.lisa_task_priority_enum NOT NULL,
    title text NOT NULL,
    description text,
    trigger_source public.lisa_task_trigger_source_enum DEFAULT 'lisa_chat'::public.lisa_task_trigger_source_enum,
    source_reference text,
    due_at timestamp with time zone,
    completed_at timestamp with time zone,
    llm_payload jsonb DEFAULT '{}'::jsonb,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    dedupe_key text,
    project_client_ref text
);


--
-- Name: lisa_user_agent_settings_gmail; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lisa_user_agent_settings_gmail (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    agent_id uuid NOT NULL,
    oauth_connected boolean DEFAULT false NOT NULL,
    oauth_connected_at timestamp with time zone,
    gmail_email text,
    granted_scopes text[] DEFAULT '{}'::text[],
    last_sync_at timestamp with time zone,
    last_watch_setup_at timestamp with time zone,
    watch_expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: lisa_user_agents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lisa_user_agents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    agent_key text NOT NULL,
    status public.agent_status_enum DEFAULT 'off'::public.agent_status_enum NOT NULL,
    config jsonb,
    revoked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.lisa_user_agents REPLICA IDENTITY FULL;


--
-- Name: lisa_user_integrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lisa_user_integrations (
    user_id uuid NOT NULL,
    integration_key text NOT NULL,
    status text DEFAULT 'disconnected'::text NOT NULL,
    connected_at timestamp with time zone,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: lisa_user_monthly_memory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lisa_user_monthly_memory (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    year_month character(7) NOT NULL,
    summary_text text NOT NULL,
    dominant_mood public.lisa_mood_enum,
    key_events jsonb,
    tags jsonb,
    generated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    month_key text
);


--
-- Name: plan_automation_pricing; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plan_automation_pricing (
    plan_code public.plan_recommendation_enum NOT NULL,
    automations_allowed boolean DEFAULT false NOT NULL,
    included_standard integer DEFAULT 0 NOT NULL,
    included_advanced integer DEFAULT 0 NOT NULL,
    included_critical integer DEFAULT 0 NOT NULL,
    price_standard_eur numeric(10,2) DEFAULT 0 NOT NULL,
    price_advanced_eur numeric(10,2) DEFAULT 0 NOT NULL,
    price_critical_eur numeric(10,2) DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: proactive_events_outbox; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.proactive_events_outbox (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    event_type text NOT NULL,
    user_id uuid NOT NULL,
    conversation_id uuid,
    payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    dedupe_key text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    processed_at timestamp with time zone,
    CONSTRAINT proactive_events_outbox_event_type_check CHECK ((event_type = ANY (ARRAY['TECH_ISSUE'::text, 'TASK_CREATED'::text, 'INACTIVITY_48H'::text])))
);


--
-- Name: proactive_messages_queue; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.proactive_messages_queue (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    send_at timestamp with time zone NOT NULL,
    status text DEFAULT 'scheduled'::text NOT NULL,
    content text NOT NULL,
    dedupe_key text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    event_type text,
    CONSTRAINT proactive_messages_queue_status_check CHECK ((status = ANY (ARRAY['scheduled'::text, 'ready'::text, 'sent'::text, 'canceled'::text])))
);


--
-- Name: project_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid,
    user_id uuid NOT NULL,
    source text NOT NULL,
    event_type public.project_event_type_enum DEFAULT 'other'::public.project_event_type_enum NOT NULL,
    title text NOT NULL,
    description text,
    event_ts timestamp with time zone DEFAULT now() NOT NULL,
    importance smallint DEFAULT 5 NOT NULL,
    related_email_provider text,
    related_email_id text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    fingerprint text,
    project_client_ref text
);


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projects (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name text NOT NULL,
    description text,
    project_type public.project_type_enum DEFAULT 'other'::public.project_type_enum NOT NULL,
    status public.project_status_enum DEFAULT 'active'::public.project_status_enum NOT NULL,
    priority public.project_priority_enum DEFAULT 'normal'::public.project_priority_enum NOT NULL,
    impact_life smallint,
    impact_business smallint,
    urgency_score smallint,
    energy_required smallint,
    start_date date,
    target_end_date date,
    main_company_id uuid,
    tags text[],
    suggested_actions jsonb,
    life_dimension public.life_dimension_enum DEFAULT 'other'::public.life_dimension_enum NOT NULL,
    parent_project_id uuid,
    next_action text,
    next_follow_up_at timestamp with time zone,
    last_event_at timestamp with time zone,
    cadence jsonb,
    details jsonb,
    client_ref text
);


--
-- Name: push_devices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.push_devices (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    expo_push_token text NOT NULL,
    platform text NOT NULL,
    is_app_active boolean DEFAULT false NOT NULL,
    active_screen text,
    last_seen_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    device_id text,
    CONSTRAINT push_devices_platform_check CHECK ((platform = ANY (ARRAY['ios'::text, 'android'::text])))
);


--
-- Name: referrals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.referrals (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    code text NOT NULL,
    referrer_user_id uuid NOT NULL,
    referred_user_id uuid NOT NULL,
    status public.referral_status DEFAULT 'created'::public.referral_status NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    applied_at timestamp with time zone,
    consumed_at timestamp with time zone,
    expires_at timestamp with time zone,
    first_purchase_only boolean DEFAULT true NOT NULL,
    eligible_product_id text DEFAULT 'com.neatikai.heylisa.pro.monthly_discount'::text NOT NULL,
    platform text,
    transaction_id text,
    original_transaction_id text,
    referrer_user_id_l2 uuid,
    referrer_user_id_l3 uuid
);


--
-- Name: user_activities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_activities (
    user_id uuid NOT NULL,
    main_activity text,
    main_activity_confidence smallint DEFAULT 0 NOT NULL,
    main_activity_reason text,
    secondary_activities jsonb DEFAULT '[]'::jsonb NOT NULL,
    last_observed_at timestamp with time zone,
    source text DEFAULT 'conversation'::text NOT NULL,
    source_conversation_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: user_automations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_automations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    project_id uuid,
    template_id uuid,
    status public.user_automation_status_enum DEFAULT 'idea'::public.user_automation_status_enum NOT NULL,
    title text NOT NULL,
    description text,
    config jsonb DEFAULT '{}'::jsonb,
    impact_estimate jsonb DEFAULT '{}'::jsonb,
    metrics jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: user_companies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_companies (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    company_id uuid NOT NULL,
    relation public.employment_relation_enum DEFAULT 'employee'::public.employment_relation_enum NOT NULL,
    title text,
    department text,
    seniority_level text,
    is_primary boolean DEFAULT false,
    started_at date,
    ended_at date,
    notes jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: user_daily_life_signals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_daily_life_signals (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    day_key text NOT NULL,
    window_start timestamp with time zone NOT NULL,
    window_end timestamp with time zone NOT NULL,
    life_radar_signals jsonb,
    source_stats jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: user_facts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_facts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid NOT NULL,
    fact_key text NOT NULL,
    category public.fact_category_enum DEFAULT 'other'::public.fact_category_enum NOT NULL,
    scope public.fact_scope_enum DEFAULT 'personal'::public.fact_scope_enum NOT NULL,
    value_type public.fact_value_type_enum DEFAULT 'text'::public.fact_value_type_enum NOT NULL,
    value jsonb DEFAULT '{}'::jsonb,
    source_type public.fact_source_type_enum DEFAULT 'declared'::public.fact_source_type_enum NOT NULL,
    source_ref text,
    confidence numeric(3,2) DEFAULT 0.80 NOT NULL,
    is_estimated boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    notes text,
    last_seen_at timestamp with time zone,
    mention_count integer DEFAULT 0 NOT NULL,
    updated_by text,
    deactivated_at timestamp with time zone
);


--
-- Name: user_financial_profile; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_financial_profile (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    data_source public.financial_data_source_enum DEFAULT 'estimated'::public.financial_data_source_enum NOT NULL,
    confidence_score numeric DEFAULT 0.3 NOT NULL,
    personal_income_band public.income_band_enum,
    financial_pressure public.financial_pressure_enum,
    spending_style public.spending_style_enum,
    main_currency text,
    business_revenue_band public.business_revenue_band_enum,
    budget_sensitivity public.budget_sensitivity_enum,
    max_monthly_tools_budget numeric,
    financial_goals text
);


--
-- Name: user_key_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_key_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    event_type text NOT NULL,
    title text NOT NULL,
    description text,
    event_date date NOT NULL,
    is_recurring boolean DEFAULT false,
    recurrence_pattern text,
    importance_level text DEFAULT 'medium'::text,
    related_people text[],
    related_project_id uuid,
    reminder_days_before integer[] DEFAULT ARRAY[7, 3, 1],
    last_mentioned_at timestamp with time zone,
    source text DEFAULT 'user_input'::text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    mention_count integer DEFAULT 0,
    source_reference text
);


--
-- Name: user_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_settings (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    job_title text,
    industry text,
    last_active_at timestamp with time zone,
    profiling_completed boolean DEFAULT false,
    profiling_facts_count integer DEFAULT 0,
    profiling_facts_total integer DEFAULT 0,
    profiling_completion_pct numeric(5,2) DEFAULT 0.00,
    use_tu_form boolean DEFAULT false,
    intro_smalltalk_turns integer DEFAULT 0 NOT NULL,
    intro_smalltalk_done boolean DEFAULT false NOT NULL,
    chat_turns_7d integer DEFAULT 0 NOT NULL,
    active_days_7d integer DEFAULT 0 NOT NULL,
    last_message_at timestamp with time zone,
    active_agents_count integer DEFAULT 0 NOT NULL,
    included_agent_key text,
    locale_main text DEFAULT 'fr-FR'::text NOT NULL,
    timezone text DEFAULT 'UTC'::text NOT NULL,
    country_code text
);

ALTER TABLE ONLY public.user_settings REPLICA IDENTITY FULL;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    account_email text,
    status public.user_status_enum DEFAULT 'prospect'::public.user_status_enum NOT NULL,
    stripe_customer_id text,
    first_name text,
    last_name text,
    full_name text,
    primary_company_id uuid,
    profile_photo_url text,
    deleted_at timestamp with time zone,
    auth_user_id uuid,
    deletion_reason text,
    country_code text,
    affiliate_code text,
    affiliate_link text,
    trial_started_at timestamp with time zone,
    is_pro boolean DEFAULT false,
    pro_started_at timestamp with time zone,
    referrer_applied_at timestamp with time zone,
    signup_source text
);


--
-- Name: debug_auth_user_created_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.debug_auth_user_created_log ALTER COLUMN id SET DEFAULT nextval('public.debug_auth_user_created_log_id_seq'::regclass);


--
-- Name: fact_profile_mappings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_profile_mappings ALTER COLUMN id SET DEFAULT nextval('public.fact_profile_mappings_id_seq'::regclass);


--
-- Name: affiliate_codes affiliate_codes_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliate_codes
    ADD CONSTRAINT affiliate_codes_code_key UNIQUE (code);


--
-- Name: affiliate_codes affiliate_codes_code_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliate_codes
    ADD CONSTRAINT affiliate_codes_code_unique UNIQUE (code);


--
-- Name: affiliate_codes affiliate_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliate_codes
    ADD CONSTRAINT affiliate_codes_pkey PRIMARY KEY (user_id);


--
-- Name: affiliate_codes affiliate_codes_user_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliate_codes
    ADD CONSTRAINT affiliate_codes_user_unique UNIQUE (user_id);


--
-- Name: affiliate_commissions affiliate_commissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliate_commissions
    ADD CONSTRAINT affiliate_commissions_pkey PRIMARY KEY (id);


--
-- Name: affiliates affiliates_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliates
    ADD CONSTRAINT affiliates_email_key UNIQUE (email);


--
-- Name: affiliates affiliates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliates
    ADD CONSTRAINT affiliates_pkey PRIMARY KEY (id);


--
-- Name: automation_templates automation_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.automation_templates
    ADD CONSTRAINT automation_templates_pkey PRIMARY KEY (id);


--
-- Name: automation_templates automation_templates_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.automation_templates
    ADD CONSTRAINT automation_templates_slug_key UNIQUE (slug);


--
-- Name: billing_events billing_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_events
    ADD CONSTRAINT billing_events_pkey PRIMARY KEY (id);


--
-- Name: billing_state billing_state_auth_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_state
    ADD CONSTRAINT billing_state_auth_user_id_key UNIQUE (auth_user_id);


--
-- Name: billing_state billing_state_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_state
    ADD CONSTRAINT billing_state_pkey PRIMARY KEY (user_id);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: conversation_messages conversation_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_user_id_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_id_unique UNIQUE (user_id);


--
-- Name: debug_auth_user_created_log debug_auth_user_created_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.debug_auth_user_created_log
    ADD CONSTRAINT debug_auth_user_created_log_pkey PRIMARY KEY (id);


--
-- Name: email_accounts email_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_accounts
    ADD CONSTRAINT email_accounts_pkey PRIMARY KEY (id);


--
-- Name: fact_key_registry fact_key_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_key_registry
    ADD CONSTRAINT fact_key_registry_pkey PRIMARY KEY (fact_key);


--
-- Name: fact_profile_mappings fact_profile_mappings_fact_key_target_table_target_column_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_profile_mappings
    ADD CONSTRAINT fact_profile_mappings_fact_key_target_table_target_column_key UNIQUE (fact_key, target_table, target_column);


--
-- Name: fact_profile_mappings fact_profile_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_profile_mappings
    ADD CONSTRAINT fact_profile_mappings_pkey PRIMARY KEY (id);


--
-- Name: gmail_watch_subscriptions gmail_watch_sub_unique_user_email; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gmail_watch_subscriptions
    ADD CONSTRAINT gmail_watch_sub_unique_user_email UNIQUE (user_id, account_email);


--
-- Name: gmail_watch_subscriptions gmail_watch_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gmail_watch_subscriptions
    ADD CONSTRAINT gmail_watch_subscriptions_pkey PRIMARY KEY (id);


--
-- Name: heylisa_post_checkout_contexts heylisa_post_checkout_contexts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.heylisa_post_checkout_contexts
    ADD CONSTRAINT heylisa_post_checkout_contexts_pkey PRIMARY KEY (id);


--
-- Name: heylisa_post_checkout_contexts heylisa_post_checkout_contexts_session_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.heylisa_post_checkout_contexts
    ADD CONSTRAINT heylisa_post_checkout_contexts_session_id_key UNIQUE (session_id);


--
-- Name: iap_transactions iap_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.iap_transactions
    ADD CONSTRAINT iap_transactions_pkey PRIMARY KEY (id);


--
-- Name: lisa_agent_integrations lisa_agent_integrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_agent_integrations
    ADD CONSTRAINT lisa_agent_integrations_pkey PRIMARY KEY (agent_key, integration_key);


--
-- Name: lisa_agents_catalog lisa_agents_catalog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_agents_catalog
    ADD CONSTRAINT lisa_agents_catalog_pkey PRIMARY KEY (agent_key);


--
-- Name: lisa_brains lisa_brains_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_brains
    ADD CONSTRAINT lisa_brains_pkey PRIMARY KEY (id);


--
-- Name: lisa_concierge_suggestions lisa_concierge_suggestions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_concierge_suggestions
    ADD CONSTRAINT lisa_concierge_suggestions_pkey PRIMARY KEY (id);


--
-- Name: lisa_dashboard_weekly_kpis lisa_dashboard_weekly_kpis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_dashboard_weekly_kpis
    ADD CONSTRAINT lisa_dashboard_weekly_kpis_pkey PRIMARY KEY (id);


--
-- Name: lisa_dashboard_weekly_kpis lisa_dashboard_weekly_kpis_uid_week_key_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_dashboard_weekly_kpis
    ADD CONSTRAINT lisa_dashboard_weekly_kpis_uid_week_key_unique UNIQUE (user_id, week_key);


--
-- Name: lisa_integrations_catalog lisa_integrations_catalog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_integrations_catalog
    ADD CONSTRAINT lisa_integrations_catalog_pkey PRIMARY KEY (id);


--
-- Name: lisa_priority_emails lisa_priority_emails_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_priority_emails
    ADD CONSTRAINT lisa_priority_emails_pkey PRIMARY KEY (id);


--
-- Name: lisa_service_docs lisa_service_docs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_service_docs
    ADD CONSTRAINT lisa_service_docs_pkey PRIMARY KEY (id);


--
-- Name: lisa_tasks lisa_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_tasks
    ADD CONSTRAINT lisa_tasks_pkey PRIMARY KEY (id);


--
-- Name: lisa_tasks lisa_tasks_user_id_dedupe_key_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_tasks
    ADD CONSTRAINT lisa_tasks_user_id_dedupe_key_uniq UNIQUE (user_id, dedupe_key);


--
-- Name: lisa_user_agent_settings_gmail lisa_user_agent_settings_gmail_agent_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_user_agent_settings_gmail
    ADD CONSTRAINT lisa_user_agent_settings_gmail_agent_id_key UNIQUE (agent_id);


--
-- Name: lisa_user_agent_settings_gmail lisa_user_agent_settings_gmail_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_user_agent_settings_gmail
    ADD CONSTRAINT lisa_user_agent_settings_gmail_pkey PRIMARY KEY (id);


--
-- Name: lisa_user_agents lisa_user_agents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_user_agents
    ADD CONSTRAINT lisa_user_agents_pkey PRIMARY KEY (id);


--
-- Name: lisa_user_agents lisa_user_agents_user_agent_key_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_user_agents
    ADD CONSTRAINT lisa_user_agents_user_agent_key_unique UNIQUE (user_id, agent_key);


--
-- Name: lisa_user_integrations lisa_user_integrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_user_integrations
    ADD CONSTRAINT lisa_user_integrations_pkey PRIMARY KEY (user_id, integration_key);


--
-- Name: lisa_user_monthly_memory lisa_user_monthly_memory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_user_monthly_memory
    ADD CONSTRAINT lisa_user_monthly_memory_pkey PRIMARY KEY (id);


--
-- Name: lisa_user_monthly_memory lisa_user_monthly_memory_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_user_monthly_memory
    ADD CONSTRAINT lisa_user_monthly_memory_unique UNIQUE (user_id, month_key);


--
-- Name: lisa_user_monthly_memory lisa_user_monthly_memory_user_month_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_user_monthly_memory
    ADD CONSTRAINT lisa_user_monthly_memory_user_month_uniq UNIQUE (user_id, year_month);


--
-- Name: plan_automation_pricing plan_automation_pricing_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_automation_pricing
    ADD CONSTRAINT plan_automation_pricing_pkey PRIMARY KEY (plan_code);


--
-- Name: proactive_events_outbox proactive_events_outbox_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.proactive_events_outbox
    ADD CONSTRAINT proactive_events_outbox_pkey PRIMARY KEY (id);


--
-- Name: proactive_messages_queue proactive_messages_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.proactive_messages_queue
    ADD CONSTRAINT proactive_messages_queue_pkey PRIMARY KEY (id);


--
-- Name: project_events project_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_events
    ADD CONSTRAINT project_events_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: push_devices push_devices_expo_push_token_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.push_devices
    ADD CONSTRAINT push_devices_expo_push_token_unique UNIQUE (expo_push_token);


--
-- Name: push_devices push_devices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.push_devices
    ADD CONSTRAINT push_devices_pkey PRIMARY KEY (id);


--
-- Name: push_outbox push_outbox_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.push_outbox
    ADD CONSTRAINT push_outbox_pkey PRIMARY KEY (id);


--
-- Name: referrals referrals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_pkey PRIMARY KEY (id);


--
-- Name: user_activities user_activities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_activities
    ADD CONSTRAINT user_activities_pkey PRIMARY KEY (user_id);


--
-- Name: user_activities user_activities_user_id_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_activities
    ADD CONSTRAINT user_activities_user_id_unique UNIQUE (user_id);


--
-- Name: user_automations user_automations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_automations
    ADD CONSTRAINT user_automations_pkey PRIMARY KEY (id);


--
-- Name: user_companies user_companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_companies
    ADD CONSTRAINT user_companies_pkey PRIMARY KEY (id);


--
-- Name: user_daily_life_signals user_daily_life_signals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_daily_life_signals
    ADD CONSTRAINT user_daily_life_signals_pkey PRIMARY KEY (id);


--
-- Name: user_daily_life_signals user_daily_life_signals_user_day_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_daily_life_signals
    ADD CONSTRAINT user_daily_life_signals_user_day_unique UNIQUE (user_id, day_key);


--
-- Name: user_facts user_facts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_facts
    ADD CONSTRAINT user_facts_pkey PRIMARY KEY (id);


--
-- Name: user_facts user_facts_user_factkey_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_facts
    ADD CONSTRAINT user_facts_user_factkey_uniq UNIQUE (user_id, fact_key);


--
-- Name: user_facts user_facts_user_id_fact_key_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_facts
    ADD CONSTRAINT user_facts_user_id_fact_key_unique UNIQUE (user_id, fact_key);


--
-- Name: user_financial_profile user_financial_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_financial_profile
    ADD CONSTRAINT user_financial_profile_pkey PRIMARY KEY (id);


--
-- Name: user_financial_profile user_financial_profile_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_financial_profile
    ADD CONSTRAINT user_financial_profile_user_id_key UNIQUE (user_id);


--
-- Name: user_key_events user_key_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_key_events
    ADD CONSTRAINT user_key_events_pkey PRIMARY KEY (id);


--
-- Name: user_settings user_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_pkey PRIMARY KEY (id);


--
-- Name: user_settings user_settings_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_user_id_key UNIQUE (user_id);


--
-- Name: users users_account_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_account_email_key UNIQUE (account_email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: affiliate_codes_code_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX affiliate_codes_code_idx ON public.affiliate_codes USING btree (code);


--
-- Name: affiliates_email_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX affiliates_email_unique ON public.affiliates USING btree (email);


--
-- Name: affiliates_user_id_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX affiliates_user_id_unique ON public.affiliates USING btree (user_id) WHERE (user_id IS NOT NULL);


--
-- Name: billing_events_auth_user_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX billing_events_auth_user_id_idx ON public.billing_events USING btree (auth_user_id);


--
-- Name: billing_events_created_at_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX billing_events_created_at_idx ON public.billing_events USING btree (created_at DESC);


--
-- Name: billing_events_payload_sha256_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX billing_events_payload_sha256_idx ON public.billing_events USING btree (payload_sha256);


--
-- Name: billing_events_provider_dedup; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX billing_events_provider_dedup ON public.billing_events USING btree (provider, provider_event_id) WHERE (provider_event_id IS NOT NULL);


--
-- Name: billing_events_user_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX billing_events_user_id_idx ON public.billing_events USING btree (user_id);


--
-- Name: billing_state_is_pro_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX billing_state_is_pro_idx ON public.billing_state USING btree (is_pro);


--
-- Name: companies_slug_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX companies_slug_key ON public.companies USING btree (slug);


--
-- Name: conversation_messages_dedupe_key_uniq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX conversation_messages_dedupe_key_uniq ON public.conversation_messages USING btree (dedupe_key);


--
-- Name: conversation_messages_unique_dedupe; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX conversation_messages_unique_dedupe ON public.conversation_messages USING btree (conversation_id, dedupe_key);


--
-- Name: conversation_messages_user_dedupe_uq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX conversation_messages_user_dedupe_uq ON public.conversation_messages USING btree (user_id, dedupe_key);


--
-- Name: email_accounts_primary_unique_per_user; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX email_accounts_primary_unique_per_user ON public.email_accounts USING btree (user_id) WHERE (is_primary = true);


--
-- Name: email_accounts_user_email_uniq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX email_accounts_user_email_uniq ON public.email_accounts USING btree (user_id, email);


--
-- Name: email_accounts_user_provider_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX email_accounts_user_provider_unique ON public.email_accounts USING btree (user_id, provider);


--
-- Name: fact_key_registry_status_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX fact_key_registry_status_idx ON public.fact_key_registry USING btree (status);


--
-- Name: gmail_watch_subscriptions_exp_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX gmail_watch_subscriptions_exp_idx ON public.gmail_watch_subscriptions USING btree (expiration);


--
-- Name: gmail_watch_subscriptions_user_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX gmail_watch_subscriptions_user_idx ON public.gmail_watch_subscriptions USING btree (user_id);


--
-- Name: iap_tx_product_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX iap_tx_product_idx ON public.iap_transactions USING btree (product_id);


--
-- Name: iap_tx_user_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX iap_tx_user_idx ON public.iap_transactions USING btree (user_id, purchased_at DESC);


--
-- Name: idx_affiliate_codes_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_affiliate_codes_code ON public.affiliate_codes USING btree (code);


--
-- Name: idx_affiliate_codes_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_affiliate_codes_user_id ON public.affiliate_codes USING btree (user_id);


--
-- Name: idx_concierge_suggestions_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_concierge_suggestions_date ON public.lisa_concierge_suggestions USING btree (suggested_for_date);


--
-- Name: idx_concierge_suggestions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_concierge_suggestions_status ON public.lisa_concierge_suggestions USING btree (status);


--
-- Name: idx_concierge_suggestions_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_concierge_suggestions_type ON public.lisa_concierge_suggestions USING btree (suggestion_type);


--
-- Name: idx_concierge_suggestions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_concierge_suggestions_user_id ON public.lisa_concierge_suggestions USING btree (user_id);


--
-- Name: idx_conv_messages_conv_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conv_messages_conv_ts ON public.conversation_messages USING btree (conversation_id, sent_at);


--
-- Name: idx_conv_messages_conversation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conv_messages_conversation_id ON public.conversation_messages USING btree (conversation_id);


--
-- Name: idx_conv_messages_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conv_messages_user_id ON public.conversation_messages USING btree (user_id);


--
-- Name: idx_conv_messages_user_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conv_messages_user_ts ON public.conversation_messages USING btree (user_id, sent_at DESC);


--
-- Name: idx_conv_messages_visitor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conv_messages_visitor_id ON public.conversation_messages USING btree (visitor_id);


--
-- Name: idx_conversation_messages_conv_sentat; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversation_messages_conv_sentat ON public.conversation_messages USING btree (conversation_id, sent_at DESC);


--
-- Name: idx_conversations_channel; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_channel ON public.conversations USING btree (channel);


--
-- Name: idx_conversations_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_status ON public.conversations USING btree (status, last_message_at DESC);


--
-- Name: idx_conversations_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_user ON public.conversations USING btree (user_id, started_at DESC);


--
-- Name: idx_conversations_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_user_id ON public.conversations USING btree (user_id);


--
-- Name: idx_conversations_visitor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_visitor_id ON public.conversations USING btree (visitor_id);


--
-- Name: idx_gmail_settings_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gmail_settings_user ON public.lisa_user_agent_settings_gmail USING btree (user_id);


--
-- Name: idx_hl_post_checkout_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hl_post_checkout_session ON public.heylisa_post_checkout_contexts USING btree (session_id);


--
-- Name: idx_hl_post_checkout_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hl_post_checkout_user ON public.heylisa_post_checkout_contexts USING btree (user_id);


--
-- Name: idx_lisa_agents_catalog_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lisa_agents_catalog_status ON public.lisa_agents_catalog USING btree (status);


--
-- Name: idx_lisa_integrations_catalog_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lisa_integrations_catalog_category ON public.lisa_integrations_catalog USING btree (category);


--
-- Name: idx_lisa_service_docs_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lisa_service_docs_scope ON public.lisa_service_docs USING btree (doc_scope);


--
-- Name: idx_lisa_tasks_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lisa_tasks_owner ON public.lisa_tasks USING btree (owner_type);


--
-- Name: idx_lisa_tasks_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lisa_tasks_project ON public.lisa_tasks USING btree (project_id);


--
-- Name: idx_lisa_tasks_status_due; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lisa_tasks_status_due ON public.lisa_tasks USING btree (status, due_at);


--
-- Name: idx_lisa_tasks_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lisa_tasks_user ON public.lisa_tasks USING btree (user_id);


--
-- Name: idx_lisa_user_agents_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lisa_user_agents_key ON public.lisa_user_agents USING btree (agent_key);


--
-- Name: idx_lisa_user_agents_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lisa_user_agents_status ON public.lisa_user_agents USING btree (status);


--
-- Name: idx_lisa_user_agents_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lisa_user_agents_user ON public.lisa_user_agents USING btree (user_id);


--
-- Name: idx_lisa_user_integrations_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lisa_user_integrations_user ON public.lisa_user_integrations USING btree (user_id);


--
-- Name: idx_project_events_project_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_events_project_ts ON public.project_events USING btree (project_id, event_ts DESC);


--
-- Name: idx_project_events_user_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_events_user_ts ON public.project_events USING btree (user_id, event_ts DESC);


--
-- Name: idx_projects_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_parent ON public.projects USING btree (parent_project_id);


--
-- Name: idx_projects_user_dimension; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_user_dimension ON public.projects USING btree (user_id, life_dimension);


--
-- Name: idx_projects_user_next_follow_up; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_user_next_follow_up ON public.projects USING btree (user_id, next_follow_up_at);


--
-- Name: idx_service_docs_content_fts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_service_docs_content_fts ON public.lisa_service_docs USING gin (to_tsvector('french'::regconfig, ((chunk_title || ' '::text) || chunk_content)));


--
-- Name: idx_service_docs_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_service_docs_tags ON public.lisa_service_docs USING gin (tags);


--
-- Name: idx_user_activities_last_observed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_activities_last_observed_at ON public.user_activities USING btree (last_observed_at DESC);


--
-- Name: idx_user_automations_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_automations_status ON public.user_automations USING btree (status);


--
-- Name: idx_user_automations_template; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_automations_template ON public.user_automations USING btree (template_id);


--
-- Name: idx_user_automations_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_automations_user ON public.user_automations USING btree (user_id);


--
-- Name: idx_user_key_events_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_key_events_date ON public.user_key_events USING btree (event_date);


--
-- Name: idx_user_key_events_last_mentioned; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_key_events_last_mentioned ON public.user_key_events USING btree (last_mentioned_at);


--
-- Name: idx_user_key_events_proactive; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_key_events_proactive ON public.user_key_events USING btree (user_id, event_date, last_mentioned_at, importance_level);


--
-- Name: idx_user_key_events_upcoming; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_key_events_upcoming ON public.user_key_events USING btree (user_id, event_date);


--
-- Name: idx_user_key_events_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_key_events_user_id ON public.user_key_events USING btree (user_id);


--
-- Name: idx_user_settings_last_active_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_settings_last_active_at ON public.user_settings USING btree (last_active_at);


--
-- Name: ix_user_facts_fact_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_facts_fact_key ON public.user_facts USING btree (fact_key);


--
-- Name: ix_user_facts_user_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_facts_user_active ON public.user_facts USING btree (user_id, is_active);


--
-- Name: lisa_integrations_catalog_category_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX lisa_integrations_catalog_category_idx ON public.lisa_integrations_catalog USING btree (category);


--
-- Name: lisa_integrations_catalog_provider_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX lisa_integrations_catalog_provider_idx ON public.lisa_integrations_catalog USING btree (provider);


--
-- Name: lisa_integrations_catalog_status_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX lisa_integrations_catalog_status_idx ON public.lisa_integrations_catalog USING btree (status);


--
-- Name: lisa_priority_emails_unprocessed_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX lisa_priority_emails_unprocessed_idx ON public.lisa_priority_emails USING btree (user_id, date_received) WHERE (processed_at IS NULL);


--
-- Name: lisa_priority_emails_user_mail_uidx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX lisa_priority_emails_user_mail_uidx ON public.lisa_priority_emails USING btree (user_id, gmail_id);


--
-- Name: lisa_tasks_clientref_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX lisa_tasks_clientref_idx ON public.lisa_tasks USING btree (user_id, project_client_ref) WHERE (project_id IS NULL);


--
-- Name: lisa_tasks_conversation_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX lisa_tasks_conversation_idx ON public.lisa_tasks USING btree (conversation_id);


--
-- Name: lisa_tasks_status_due_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX lisa_tasks_status_due_idx ON public.lisa_tasks USING btree (status, due_at);


--
-- Name: lisa_tasks_user_dedupe_key_uq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX lisa_tasks_user_dedupe_key_uq ON public.lisa_tasks USING btree (user_id, dedupe_key);


--
-- Name: lisa_tasks_user_dedupe_key_ux; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX lisa_tasks_user_dedupe_key_ux ON public.lisa_tasks USING btree (user_id, dedupe_key) WHERE (dedupe_key IS NOT NULL);


--
-- Name: lisa_tasks_user_due_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX lisa_tasks_user_due_idx ON public.lisa_tasks USING btree (user_id, status, due_at);


--
-- Name: lisa_user_monthly_memory_month_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX lisa_user_monthly_memory_month_idx ON public.lisa_user_monthly_memory USING btree (year_month);


--
-- Name: lisa_user_monthly_memory_user_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX lisa_user_monthly_memory_user_idx ON public.lisa_user_monthly_memory USING btree (user_id);


--
-- Name: lisa_weekly_kpis_user_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX lisa_weekly_kpis_user_week_idx ON public.lisa_dashboard_weekly_kpis USING btree (user_id, week_start);


--
-- Name: proactive_events_outbox_dedupe_key_uidx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX proactive_events_outbox_dedupe_key_uidx ON public.proactive_events_outbox USING btree (dedupe_key);


--
-- Name: proactive_events_outbox_dedupe_key_ux; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX proactive_events_outbox_dedupe_key_ux ON public.proactive_events_outbox USING btree (dedupe_key);


--
-- Name: proactive_events_outbox_unprocessed_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX proactive_events_outbox_unprocessed_idx ON public.proactive_events_outbox USING btree (created_at) WHERE (processed_at IS NULL);


--
-- Name: proactive_messages_queue_dedupe_key_ux; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX proactive_messages_queue_dedupe_key_ux ON public.proactive_messages_queue USING btree (dedupe_key);


--
-- Name: proactive_messages_queue_due_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX proactive_messages_queue_due_idx ON public.proactive_messages_queue USING btree (send_at) WHERE (status = 'scheduled'::text);


--
-- Name: proactive_messages_queue_user_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX proactive_messages_queue_user_idx ON public.proactive_messages_queue USING btree (user_id);


--
-- Name: project_events_clientref_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX project_events_clientref_idx ON public.project_events USING btree (user_id, project_client_ref) WHERE (project_id IS NULL);


--
-- Name: projects_user_client_ref_uq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX projects_user_client_ref_uq ON public.projects USING btree (user_id, client_ref);


--
-- Name: projects_user_client_ref_ux; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX projects_user_client_ref_ux ON public.projects USING btree (user_id, client_ref) WHERE (client_ref IS NOT NULL);


--
-- Name: push_devices_expo_push_token_uq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX push_devices_expo_push_token_uq ON public.push_devices USING btree (expo_push_token) WHERE (expo_push_token IS NOT NULL);


--
-- Name: push_devices_token_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX push_devices_token_idx ON public.push_devices USING btree (expo_push_token);


--
-- Name: push_devices_user_device_uniq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX push_devices_user_device_uniq ON public.push_devices USING btree (user_id, device_id);


--
-- Name: push_devices_user_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX push_devices_user_idx ON public.push_devices USING btree (user_id);


--
-- Name: push_outbox_status_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX push_outbox_status_idx ON public.push_outbox USING btree (status, scheduled_at);


--
-- Name: push_outbox_user_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX push_outbox_user_idx ON public.push_outbox USING btree (user_id, created_at DESC);


--
-- Name: push_outbox_user_status_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX push_outbox_user_status_idx ON public.push_outbox USING btree (user_id, status, created_at);


--
-- Name: referrals_code_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX referrals_code_idx ON public.referrals USING btree (code);


--
-- Name: referrals_referred_unique_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX referrals_referred_unique_idx ON public.referrals USING btree (referred_user_id);


--
-- Name: referrals_referrer_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX referrals_referrer_idx ON public.referrals USING btree (referrer_user_id);


--
-- Name: referrals_referrer_l2_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX referrals_referrer_l2_idx ON public.referrals USING btree (referrer_user_id_l2);


--
-- Name: referrals_referrer_l3_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX referrals_referrer_l3_idx ON public.referrals USING btree (referrer_user_id_l3);


--
-- Name: uq_lisa_integrations_catalog_integration_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_lisa_integrations_catalog_integration_key ON public.lisa_integrations_catalog USING btree (integration_key);


--
-- Name: user_activities_user_uq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX user_activities_user_uq ON public.user_activities USING btree (user_id);


--
-- Name: user_companies_company_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_companies_company_idx ON public.user_companies USING btree (company_id);


--
-- Name: user_companies_user_company_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX user_companies_user_company_unique ON public.user_companies USING btree (user_id, company_id, relation) WHERE (ended_at IS NULL);


--
-- Name: user_facts_user_category_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_facts_user_category_idx ON public.user_facts USING btree (user_id, category);


--
-- Name: user_facts_user_id_fact_key_uq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX user_facts_user_id_fact_key_uq ON public.user_facts USING btree (user_id, fact_key);


--
-- Name: user_facts_user_key_active_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_facts_user_key_active_idx ON public.user_facts USING btree (user_id, fact_key, is_active);


--
-- Name: user_facts_value_json_gin_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_facts_value_json_gin_idx ON public.user_facts USING gin (value);


--
-- Name: users_affiliate_code_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX users_affiliate_code_key ON public.users USING btree (affiliate_code) WHERE (affiliate_code IS NOT NULL);


--
-- Name: users_auth_user_id_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX users_auth_user_id_key ON public.users USING btree (auth_user_id) WHERE (auth_user_id IS NOT NULL);


--
-- Name: users_auth_user_id_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX users_auth_user_id_unique ON public.users USING btree (auth_user_id);


--
-- Name: users_deleted_at_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX users_deleted_at_idx ON public.users USING btree (deleted_at);


--
-- Name: lisa_user_agents addon_event; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER addon_event AFTER INSERT OR UPDATE ON public.lisa_user_agents FOR EACH ROW EXECUTE FUNCTION supabase_functions.http_request('https://neatik-ai.app.n8n.cloud/webhook/addon/router', 'POST', '{"Content-type":"application/json","x-addon-secret":"sk_addon_router_9f3cA2bE7KxLQmW4R8HjD6ZP0yNVa5S1T"}', '{}', '5000');


--
-- Name: conversation_messages conversation_messages_enqueue_push; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER conversation_messages_enqueue_push AFTER INSERT ON public.conversation_messages FOR EACH ROW EXECUTE FUNCTION public.trg_conversation_message_enqueue_push();


--
-- Name: users new_prospect_email_chat; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER new_prospect_email_chat AFTER INSERT ON public.users FOR EACH ROW EXECUTE FUNCTION supabase_functions.http_request('https://neatik-ai.app.n8n.cloud/webhook/new-email-chat-request', 'POST', '{"Content-type":"application/json"}', '{}', '5000');


--
-- Name: conversation_messages outbox_on_lisa_tech_issue; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER outbox_on_lisa_tech_issue AFTER INSERT ON public.conversation_messages FOR EACH ROW EXECUTE FUNCTION public.trg_outbox_on_lisa_tech_issue();


--
-- Name: lisa_tasks outbox_on_task_created; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER outbox_on_task_created AFTER INSERT ON public.lisa_tasks FOR EACH ROW EXECUTE FUNCTION public.trg_outbox_on_task_created();


--
-- Name: proactive_events_outbox proactive_messages; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER proactive_messages AFTER INSERT ON public.proactive_events_outbox FOR EACH ROW EXECUTE FUNCTION supabase_functions.http_request('https://neatik-ai.app.n8n.cloud/webhook/proactif/message', 'POST', '{"Content-type":"application/json"}', '{}', '5000');


--
-- Name: proactive_messages_queue send_proactive_messages; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER send_proactive_messages AFTER UPDATE ON public.proactive_messages_queue FOR EACH ROW EXECUTE FUNCTION supabase_functions.http_request('https://neatik-ai.app.n8n.cloud/webhook/send/proactive/messages', 'POST', '{"Content-type":"application/json"}', '{}', '5000');


--
-- Name: affiliate_codes set_updated_at_affiliate_codes; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER set_updated_at_affiliate_codes BEFORE UPDATE ON public.affiliate_codes FOR EACH ROW EXECUTE FUNCTION public.tg_set_updated_at();


--
-- Name: lisa_user_integrations tool_event; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER tool_event AFTER UPDATE ON public.lisa_user_integrations FOR EACH ROW EXECUTE FUNCTION supabase_functions.http_request('https://neatik-ai.app.n8n.cloud/webhook/addon/router', 'POST', '{"Content-type":"application/json"}', '{}', '5000');


--
-- Name: users trg_activate_personal_assistant_if_pro; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_activate_personal_assistant_if_pro AFTER UPDATE OF is_pro ON public.users FOR EACH ROW WHEN (((new.is_pro = true) AND (old.is_pro IS DISTINCT FROM new.is_pro))) EXECUTE FUNCTION public.fn_activate_personal_assistant_if_pro();


--
-- Name: automation_templates trg_automation_templates_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_automation_templates_updated_at BEFORE UPDATE ON public.automation_templates FOR EACH ROW EXECUTE FUNCTION public.set_automation_templates_updated_at();


--
-- Name: billing_events trg_billing_events_normalize_timestamps; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_billing_events_normalize_timestamps BEFORE INSERT OR UPDATE OF payload ON public.billing_events FOR EACH ROW EXECUTE FUNCTION public.fn_billing_events_normalize_timestamps();


--
-- Name: billing_events trg_billing_events_recompute_user_status; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_billing_events_recompute_user_status AFTER INSERT OR UPDATE OF expiration_at, event_type, payload, user_id ON public.billing_events FOR EACH ROW EXECUTE FUNCTION public.trg_billing_events_recompute_user_status();


--
-- Name: billing_events trg_billing_events_recompute_user_status_ins; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_billing_events_recompute_user_status_ins AFTER INSERT ON public.billing_events FOR EACH ROW EXECUTE FUNCTION public.trg_billing_events_recompute_user_status();


--
-- Name: billing_events trg_billing_events_resolve_user_id; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_billing_events_resolve_user_id BEFORE INSERT ON public.billing_events FOR EACH ROW EXECUTE FUNCTION public.fn_billing_events_resolve_user_id();


--
-- Name: users trg_ensure_user_settings_row; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_ensure_user_settings_row AFTER INSERT ON public.users FOR EACH ROW EXECUTE FUNCTION public.ensure_user_settings_row();


--
-- Name: lisa_user_agent_settings_gmail trg_gmail_settings_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_gmail_settings_updated_at BEFORE UPDATE ON public.lisa_user_agent_settings_gmail FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: lisa_user_agents trg_lisa_user_agents_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_lisa_user_agents_updated_at BEFORE UPDATE ON public.lisa_user_agents FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: plan_automation_pricing trg_plan_automation_pricing_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_plan_automation_pricing_updated_at BEFORE UPDATE ON public.plan_automation_pricing FOR EACH ROW EXECUTE FUNCTION public.set_plan_automation_pricing_updated_at();


--
-- Name: user_facts trg_propagate_use_tu_form_from_user_facts; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_propagate_use_tu_form_from_user_facts AFTER INSERT OR UPDATE OF value, is_active, fact_key ON public.user_facts FOR EACH ROW EXECUTE FUNCTION public.propagate_use_tu_form_from_user_facts();


--
-- Name: push_devices trg_push_devices_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_push_devices_updated_at BEFORE UPDATE ON public.push_devices FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: user_facts trg_refresh_use_tu_form; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_refresh_use_tu_form AFTER INSERT OR DELETE OR UPDATE ON public.user_facts FOR EACH ROW EXECUTE FUNCTION public.fn_trg_refresh_use_tu_form();


--
-- Name: lisa_user_agents trg_refresh_user_agents_settings; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_refresh_user_agents_settings AFTER INSERT OR DELETE OR UPDATE ON public.lisa_user_agents FOR EACH ROW EXECUTE FUNCTION public.fn_trg_refresh_user_agents_settings();


--
-- Name: users trg_revoke_personal_assistant_if_not_pro; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_revoke_personal_assistant_if_not_pro AFTER UPDATE OF is_pro ON public.users FOR EACH ROW WHEN (((new.is_pro = false) AND (old.is_pro IS DISTINCT FROM new.is_pro))) EXECUTE FUNCTION public.fn_revoke_personal_assistant_if_not_pro();


--
-- Name: lisa_service_docs trg_service_docs_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_service_docs_updated_at BEFORE UPDATE ON public.lisa_service_docs FOR EACH ROW EXECUTE FUNCTION public.update_lisa_service_docs_updated_at();


--
-- Name: proactive_messages_queue trg_set_proactive_messages_queue_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_set_proactive_messages_queue_updated_at BEFORE UPDATE ON public.proactive_messages_queue FOR EACH ROW EXECUTE FUNCTION public.set_proactive_messages_queue_updated_at();


--
-- Name: billing_events trg_set_trial_started_at_from_billing_event; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_set_trial_started_at_from_billing_event AFTER INSERT ON public.billing_events FOR EACH ROW EXECUTE FUNCTION public.fn_set_trial_started_at_from_billing_event();


--
-- Name: conversations trg_sync_user_settings_last_message_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_sync_user_settings_last_message_at AFTER UPDATE OF last_message_at ON public.conversations FOR EACH ROW WHEN ((new.last_message_at IS DISTINCT FROM old.last_message_at)) EXECUTE FUNCTION public.sync_user_settings_last_message_at();


--
-- Name: conversation_messages trg_update_intro_smalltalk; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_update_intro_smalltalk AFTER INSERT ON public.conversation_messages FOR EACH ROW EXECUTE FUNCTION public.update_intro_smalltalk_state();


--
-- Name: user_facts trg_update_profiling_on_fact_change; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_update_profiling_on_fact_change AFTER INSERT OR DELETE OR UPDATE ON public.user_facts FOR EACH ROW EXECUTE FUNCTION public.update_profiling_completion();


--
-- Name: user_activities trg_user_activities_set_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_user_activities_set_updated_at BEFORE UPDATE ON public.user_activities FOR EACH ROW EXECUTE FUNCTION public.tg_set_updated_at();


--
-- Name: user_automations trg_user_automations_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_user_automations_updated_at BEFORE UPDATE ON public.user_automations FOR EACH ROW EXECUTE FUNCTION public.set_user_automations_updated_at();


--
-- Name: user_facts trg_user_facts_refresh_user_settings_job_industry; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_user_facts_refresh_user_settings_job_industry AFTER INSERT OR DELETE OR UPDATE ON public.user_facts FOR EACH ROW EXECUTE FUNCTION public.trg_refresh_user_settings_job_industry();


--
-- Name: user_key_events trg_user_key_events_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_user_key_events_updated_at BEFORE UPDATE ON public.user_key_events FOR EACH ROW EXECUTE FUNCTION public.update_user_key_events_updated_at();


--
-- Name: users trg_users_enqueue_stripe_customer_ins; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_users_enqueue_stripe_customer_ins AFTER INSERT ON public.users FOR EACH ROW EXECUTE FUNCTION public.enqueue_stripe_customer_creation();

ALTER TABLE public.users DISABLE TRIGGER trg_users_enqueue_stripe_customer_ins;


--
-- Name: users trg_users_enqueue_stripe_customer_upd; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_users_enqueue_stripe_customer_upd AFTER UPDATE OF auth_user_id ON public.users FOR EACH ROW EXECUTE FUNCTION public.enqueue_stripe_customer_creation();

ALTER TABLE public.users DISABLE TRIGGER trg_users_enqueue_stripe_customer_upd;


--
-- Name: users trg_users_recompute_status; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_users_recompute_status AFTER INSERT OR UPDATE OF signup_source ON public.users FOR EACH ROW EXECUTE FUNCTION public.trg_users_recompute_status();


--
-- Name: users trg_users_recompute_status_ins; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_users_recompute_status_ins AFTER INSERT ON public.users FOR EACH ROW EXECUTE FUNCTION public.trg_users_recompute_status();


--
-- Name: users trg_users_set_signup_source_ins; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_users_set_signup_source_ins BEFORE INSERT ON public.users FOR EACH ROW EXECUTE FUNCTION public.fn_users_set_signup_source_and_status();


--
-- Name: users trg_users_set_signup_source_upd_auth; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_users_set_signup_source_upd_auth BEFORE UPDATE OF auth_user_id ON public.users FOR EACH ROW WHEN (((new.auth_user_id IS NOT NULL) AND (new.auth_user_id IS DISTINCT FROM old.auth_user_id))) EXECUTE FUNCTION public.fn_users_set_signup_source_and_status();


--
-- Name: users update_users_timestamp; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_users_timestamp BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();


--
-- Name: affiliate_codes affiliate_codes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliate_codes
    ADD CONSTRAINT affiliate_codes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: affiliate_commissions affiliate_commissions_affiliate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliate_commissions
    ADD CONSTRAINT affiliate_commissions_affiliate_id_fkey FOREIGN KEY (affiliate_id) REFERENCES public.affiliates(id) ON DELETE CASCADE;


--
-- Name: conversation_messages conversation_messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: conversation_messages conversation_messages_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: conversations conversations_user_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_fk FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: conversations conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: email_accounts email_accounts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_accounts
    ADD CONSTRAINT email_accounts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: fact_profile_mappings fact_profile_mappings_fact_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_profile_mappings
    ADD CONSTRAINT fact_profile_mappings_fact_key_fkey FOREIGN KEY (fact_key) REFERENCES public.fact_key_registry(fact_key) ON DELETE CASCADE;


--
-- Name: gmail_watch_subscriptions gmail_watch_subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gmail_watch_subscriptions
    ADD CONSTRAINT gmail_watch_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: heylisa_post_checkout_contexts heylisa_post_checkout_contexts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.heylisa_post_checkout_contexts
    ADD CONSTRAINT heylisa_post_checkout_contexts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: iap_transactions iap_transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.iap_transactions
    ADD CONSTRAINT iap_transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: lisa_agent_integrations lisa_agent_integrations_agent_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_agent_integrations
    ADD CONSTRAINT lisa_agent_integrations_agent_key_fkey FOREIGN KEY (agent_key) REFERENCES public.lisa_agents_catalog(agent_key) ON DELETE CASCADE;


--
-- Name: lisa_agent_integrations lisa_agent_integrations_integration_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_agent_integrations
    ADD CONSTRAINT lisa_agent_integrations_integration_key_fkey FOREIGN KEY (integration_key) REFERENCES public.lisa_integrations_catalog(integration_key) ON DELETE RESTRICT;


--
-- Name: lisa_concierge_suggestions lisa_concierge_suggestions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_concierge_suggestions
    ADD CONSTRAINT lisa_concierge_suggestions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: lisa_tasks lisa_tasks_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_tasks
    ADD CONSTRAINT lisa_tasks_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: lisa_tasks lisa_tasks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_tasks
    ADD CONSTRAINT lisa_tasks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: lisa_user_agent_settings_gmail lisa_user_agent_settings_gmail_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_user_agent_settings_gmail
    ADD CONSTRAINT lisa_user_agent_settings_gmail_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.lisa_user_agents(id) ON DELETE CASCADE;


--
-- Name: lisa_user_agent_settings_gmail lisa_user_agent_settings_gmail_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_user_agent_settings_gmail
    ADD CONSTRAINT lisa_user_agent_settings_gmail_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: lisa_user_agents lisa_user_agents_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_user_agents
    ADD CONSTRAINT lisa_user_agents_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: lisa_user_integrations lisa_user_integrations_integration_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lisa_user_integrations
    ADD CONSTRAINT lisa_user_integrations_integration_key_fkey FOREIGN KEY (integration_key) REFERENCES public.lisa_integrations_catalog(integration_key) ON DELETE RESTRICT;


--
-- Name: conversation_messages messages_conversation_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT messages_conversation_fk FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: project_events project_events_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_events
    ADD CONSTRAINT project_events_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_events project_events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_events
    ADD CONSTRAINT project_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: projects projects_main_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_main_company_id_fkey FOREIGN KEY (main_company_id) REFERENCES public.companies(id) ON DELETE SET NULL;


--
-- Name: projects projects_parent_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_parent_project_id_fkey FOREIGN KEY (parent_project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: projects projects_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: push_devices push_devices_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.push_devices
    ADD CONSTRAINT push_devices_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: push_outbox push_outbox_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.push_outbox
    ADD CONSTRAINT push_outbox_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: referrals referrals_referred_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_referred_user_id_fkey FOREIGN KEY (referred_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: referrals referrals_referrer_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_referrer_user_id_fkey FOREIGN KEY (referrer_user_id) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: referrals referrals_referrer_user_id_l2_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_referrer_user_id_l2_fkey FOREIGN KEY (referrer_user_id_l2) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: referrals referrals_referrer_user_id_l3_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_referrer_user_id_l3_fkey FOREIGN KEY (referrer_user_id_l3) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: user_activities user_activities_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_activities
    ADD CONSTRAINT user_activities_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_automations user_automations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_automations
    ADD CONSTRAINT user_automations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: user_automations user_automations_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_automations
    ADD CONSTRAINT user_automations_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.automation_templates(id) ON DELETE SET NULL;


--
-- Name: user_automations user_automations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_automations
    ADD CONSTRAINT user_automations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_companies user_companies_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_companies
    ADD CONSTRAINT user_companies_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: user_companies user_companies_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_companies
    ADD CONSTRAINT user_companies_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_daily_life_signals user_daily_life_signals_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_daily_life_signals
    ADD CONSTRAINT user_daily_life_signals_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_facts user_facts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_facts
    ADD CONSTRAINT user_facts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_financial_profile user_financial_profile_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_financial_profile
    ADD CONSTRAINT user_financial_profile_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_key_events user_key_events_related_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_key_events
    ADD CONSTRAINT user_key_events_related_project_id_fkey FOREIGN KEY (related_project_id) REFERENCES public.projects(id);


--
-- Name: user_key_events user_key_events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_key_events
    ADD CONSTRAINT user_key_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_settings user_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: users users_auth_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_auth_user_id_fkey FOREIGN KEY (auth_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: users users_primary_company_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_primary_company_fk FOREIGN KEY (primary_company_id) REFERENCES public.companies(id) ON DELETE SET NULL;


--
-- Name: lisa_user_agents Agents: read own rows; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Agents: read own rows" ON public.lisa_user_agents FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agents.user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: user_activities User can insert own activity; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "User can insert own activity" ON public.user_activities FOR INSERT WITH CHECK ((auth.uid() = user_id));


--
-- Name: user_activities User can read own activity; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "User can read own activity" ON public.user_activities FOR SELECT USING ((auth.uid() = user_id));


--
-- Name: user_activities User can update own activity; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "User can update own activity" ON public.user_activities FOR UPDATE USING ((auth.uid() = user_id)) WITH CHECK ((auth.uid() = user_id));


--
-- Name: lisa_dashboard_weekly_kpis Users can read their own lisa dashboard kpis; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can read their own lisa dashboard kpis" ON public.lisa_dashboard_weekly_kpis FOR SELECT TO authenticated USING ((user_id = ( SELECT u.id
   FROM public.users u
  WHERE (u.auth_user_id = auth.uid())
 LIMIT 1)));


--
-- Name: affiliate_codes; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.affiliate_codes ENABLE ROW LEVEL SECURITY;

--
-- Name: affiliate_codes affiliate_codes_select_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY affiliate_codes_select_own ON public.affiliate_codes FOR SELECT TO authenticated USING ((user_id = auth.uid()));


--
-- Name: affiliate_commissions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.affiliate_commissions ENABLE ROW LEVEL SECURITY;

--
-- Name: affiliate_commissions affiliate_commissions_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY affiliate_commissions_service_full ON public.affiliate_commissions TO service_role USING (true) WITH CHECK (true);


--
-- Name: affiliates; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.affiliates ENABLE ROW LEVEL SECURITY;

--
-- Name: affiliates affiliates_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY affiliates_service_full ON public.affiliates TO service_role USING (true) WITH CHECK (true);


--
-- Name: affiliates affiliates_user_can_select_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY affiliates_user_can_select_own ON public.affiliates FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = affiliates.user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: automation_templates; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.automation_templates ENABLE ROW LEVEL SECURITY;

--
-- Name: automation_templates automation_templates_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY automation_templates_service_full ON public.automation_templates TO service_role USING (true) WITH CHECK (true);


--
-- Name: billing_events; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.billing_events ENABLE ROW LEVEL SECURITY;

--
-- Name: billing_state; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.billing_state ENABLE ROW LEVEL SECURITY;

--
-- Name: conversation_messages cm_delete_none; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY cm_delete_none ON public.conversation_messages FOR DELETE TO authenticated USING (false);


--
-- Name: conversation_messages cm_insert_user_only; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY cm_insert_user_only ON public.conversation_messages FOR INSERT TO authenticated WITH CHECK (((sender_type = 'user'::public.conversation_sender_enum) AND (EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = conversation_messages.user_id) AND (u.auth_user_id = auth.uid()) AND (u.deleted_at IS NULL)))) AND (EXISTS ( SELECT 1
   FROM public.conversations c
  WHERE ((c.id = conversation_messages.conversation_id) AND (c.user_id = conversation_messages.user_id))))));


--
-- Name: conversation_messages cm_select_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY cm_select_own ON public.conversation_messages FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.conversations c
     JOIN public.users u ON ((u.id = c.user_id)))
  WHERE ((c.id = conversation_messages.conversation_id) AND (u.auth_user_id = auth.uid()) AND (u.deleted_at IS NULL)))));


--
-- Name: conversation_messages cm_update_none; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY cm_update_none ON public.conversation_messages FOR UPDATE TO authenticated USING (false);


--
-- Name: companies; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;

--
-- Name: companies companies_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY companies_service_full ON public.companies TO service_role USING (true) WITH CHECK (true);


--
-- Name: conversation_messages; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.conversation_messages ENABLE ROW LEVEL SECURITY;

--
-- Name: conversation_messages conversation_messages_service_role_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY conversation_messages_service_role_full ON public.conversation_messages TO service_role USING (true) WITH CHECK (true);


--
-- Name: conversations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

--
-- Name: conversations conversations_delete_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY conversations_delete_own ON public.conversations FOR DELETE USING ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = conversations.user_id) AND (u.auth_user_id = auth.uid()) AND (u.deleted_at IS NULL)))));


--
-- Name: conversations conversations_front_read_only; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY conversations_front_read_only ON public.conversations FOR SELECT USING ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));


--
-- Name: conversations conversations_insert_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY conversations_insert_own ON public.conversations FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = conversations.user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: conversations conversations_select_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY conversations_select_own ON public.conversations FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = conversations.user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: conversations conversations_service_full_access; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY conversations_service_full_access ON public.conversations USING ((auth.role() = 'service_role'::text)) WITH CHECK ((auth.role() = 'service_role'::text));


--
-- Name: conversations conversations_update_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY conversations_update_own ON public.conversations FOR UPDATE USING ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = conversations.user_id) AND (u.auth_user_id = auth.uid()))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = conversations.user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: debug_auth_user_created_log; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.debug_auth_user_created_log ENABLE ROW LEVEL SECURITY;

--
-- Name: email_accounts; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.email_accounts ENABLE ROW LEVEL SECURITY;

--
-- Name: email_accounts email_accounts_front_read; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY email_accounts_front_read ON public.email_accounts FOR SELECT TO authenticated, anon USING ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));


--
-- Name: email_accounts email_accounts_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY email_accounts_service_full ON public.email_accounts TO service_role USING (true) WITH CHECK (true);


--
-- Name: fact_key_registry; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.fact_key_registry ENABLE ROW LEVEL SECURITY;

--
-- Name: fact_key_registry fact_key_registry_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY fact_key_registry_service_full ON public.fact_key_registry TO service_role USING (true) WITH CHECK (true);


--
-- Name: fact_profile_mappings; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.fact_profile_mappings ENABLE ROW LEVEL SECURITY;

--
-- Name: fact_profile_mappings fact_profile_mappings_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY fact_profile_mappings_service_full ON public.fact_profile_mappings TO service_role USING (true) WITH CHECK (true);


--
-- Name: lisa_user_agent_settings_gmail gmail_settings_insert_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY gmail_settings_insert_own ON public.lisa_user_agent_settings_gmail FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agent_settings_gmail.user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: lisa_user_agent_settings_gmail gmail_settings_select_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY gmail_settings_select_own ON public.lisa_user_agent_settings_gmail FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agent_settings_gmail.user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: lisa_user_agent_settings_gmail gmail_settings_update_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY gmail_settings_update_own ON public.lisa_user_agent_settings_gmail FOR UPDATE USING ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agent_settings_gmail.user_id) AND (u.auth_user_id = auth.uid()))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agent_settings_gmail.user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: gmail_watch_subscriptions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.gmail_watch_subscriptions ENABLE ROW LEVEL SECURITY;

--
-- Name: gmail_watch_subscriptions gmail_watch_subscriptions_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY gmail_watch_subscriptions_service_full ON public.gmail_watch_subscriptions TO service_role USING (true) WITH CHECK (true);


--
-- Name: heylisa_post_checkout_contexts; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.heylisa_post_checkout_contexts ENABLE ROW LEVEL SECURITY;

--
-- Name: heylisa_post_checkout_contexts heylisa_post_checkout_contexts_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY heylisa_post_checkout_contexts_service_full ON public.heylisa_post_checkout_contexts TO service_role USING (true) WITH CHECK (true);


--
-- Name: iap_transactions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.iap_transactions ENABLE ROW LEVEL SECURITY;

--
-- Name: iap_transactions iap_tx_select_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY iap_tx_select_own ON public.iap_transactions FOR SELECT TO authenticated USING ((user_id = auth.uid()));


--
-- Name: lisa_agent_integrations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lisa_agent_integrations ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_agents_catalog; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lisa_agents_catalog ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_brains; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lisa_brains ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_brains lisa_brains_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY lisa_brains_service_full ON public.lisa_brains TO service_role USING (true) WITH CHECK (true);


--
-- Name: lisa_concierge_suggestions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lisa_concierge_suggestions ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_concierge_suggestions lisa_concierge_suggestions_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY lisa_concierge_suggestions_service_full ON public.lisa_concierge_suggestions TO service_role USING (true) WITH CHECK (true);


--
-- Name: lisa_dashboard_weekly_kpis; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lisa_dashboard_weekly_kpis ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_integrations_catalog; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lisa_integrations_catalog ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_integrations_catalog lisa_integrations_catalog_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY lisa_integrations_catalog_service_full ON public.lisa_integrations_catalog TO service_role USING (true) WITH CHECK (true);


--
-- Name: lisa_priority_emails; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lisa_priority_emails ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_priority_emails lisa_priority_emails_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY lisa_priority_emails_service_full ON public.lisa_priority_emails TO service_role USING (true) WITH CHECK (true);


--
-- Name: lisa_service_docs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lisa_service_docs ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_service_docs lisa_service_docs_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY lisa_service_docs_service_full ON public.lisa_service_docs TO service_role USING (true) WITH CHECK (true);


--
-- Name: lisa_tasks; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lisa_tasks ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_tasks lisa_tasks_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY lisa_tasks_service_full ON public.lisa_tasks TO service_role USING (true) WITH CHECK (true);


--
-- Name: lisa_user_agent_settings_gmail; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lisa_user_agent_settings_gmail ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_user_agents; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lisa_user_agents ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_user_agents lisa_user_agents_insert_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY lisa_user_agents_insert_own ON public.lisa_user_agents FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agents.user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: lisa_user_agents lisa_user_agents_select_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY lisa_user_agents_select_own ON public.lisa_user_agents FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agents.user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: lisa_user_agents lisa_user_agents_update_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY lisa_user_agents_update_own ON public.lisa_user_agents FOR UPDATE USING ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agents.user_id) AND (u.auth_user_id = auth.uid()))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agents.user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: lisa_user_integrations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lisa_user_integrations ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_user_monthly_memory; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lisa_user_monthly_memory ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_user_monthly_memory lisa_user_monthly_memory_front_read; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY lisa_user_monthly_memory_front_read ON public.lisa_user_monthly_memory FOR SELECT TO authenticated, anon USING ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));


--
-- Name: lisa_user_monthly_memory lisa_user_monthly_memory_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY lisa_user_monthly_memory_service_full ON public.lisa_user_monthly_memory TO service_role USING (true) WITH CHECK (true);


--
-- Name: plan_automation_pricing; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.plan_automation_pricing ENABLE ROW LEVEL SECURITY;

--
-- Name: plan_automation_pricing plan_automation_pricing_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY plan_automation_pricing_service_full ON public.plan_automation_pricing TO service_role USING (true) WITH CHECK (true);


--
-- Name: proactive_events_outbox; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.proactive_events_outbox ENABLE ROW LEVEL SECURITY;

--
-- Name: proactive_messages_queue; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.proactive_messages_queue ENABLE ROW LEVEL SECURITY;

--
-- Name: project_events; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.project_events ENABLE ROW LEVEL SECURITY;

--
-- Name: project_events project_events_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY project_events_service_full ON public.project_events TO service_role USING (true) WITH CHECK (true);


--
-- Name: projects; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

--
-- Name: projects projects_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY projects_service_full ON public.projects TO service_role USING (true) WITH CHECK (true);


--
-- Name: users public_can_select_users_for_now; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY public_can_select_users_for_now ON public.users FOR SELECT USING (true);


--
-- Name: push_devices; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.push_devices ENABLE ROW LEVEL SECURITY;

--
-- Name: push_devices push_devices_insert_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY push_devices_insert_own ON public.push_devices FOR INSERT TO authenticated WITH CHECK ((user_id = public.current_user_id()));


--
-- Name: push_devices push_devices_select_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY push_devices_select_own ON public.push_devices FOR SELECT USING ((user_id IN ( SELECT users.id
   FROM public.users
  WHERE (users.auth_user_id = auth.uid()))));


--
-- Name: push_devices push_devices_update_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY push_devices_update_own ON public.push_devices FOR UPDATE USING ((user_id IN ( SELECT users.id
   FROM public.users
  WHERE (users.auth_user_id = auth.uid())))) WITH CHECK ((user_id IN ( SELECT users.id
   FROM public.users
  WHERE (users.auth_user_id = auth.uid()))));


--
-- Name: push_devices push_devices_upsert_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY push_devices_upsert_own ON public.push_devices FOR INSERT WITH CHECK ((user_id IN ( SELECT users.id
   FROM public.users
  WHERE (users.auth_user_id = auth.uid()))));


--
-- Name: push_outbox; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.push_outbox ENABLE ROW LEVEL SECURITY;

--
-- Name: lisa_user_agents realtime_select_own_agents; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY realtime_select_own_agents ON public.lisa_user_agents FOR SELECT USING ((user_id IN ( SELECT users.id
   FROM public.users
  WHERE (users.auth_user_id = auth.uid()))));


--
-- Name: referrals; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.referrals ENABLE ROW LEVEL SECURITY;

--
-- Name: referrals referrals_insert_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY referrals_insert_own ON public.referrals FOR INSERT WITH CHECK ((referred_user_id = auth.uid()));


--
-- Name: referrals referrals_select_involved; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY referrals_select_involved ON public.referrals FOR SELECT TO authenticated USING (((referrer_user_id = auth.uid()) OR (referred_user_id = auth.uid())));


--
-- Name: referrals referrals_select_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY referrals_select_own ON public.referrals FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = referrals.referred_user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: lisa_user_integrations select own integrations; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "select own integrations" ON public.lisa_user_integrations FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_integrations.user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: users service_can_manage_users; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY service_can_manage_users ON public.users TO service_role USING (true) WITH CHECK (true);


--
-- Name: lisa_user_integrations update own integrations; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "update own integrations" ON public.lisa_user_integrations FOR UPDATE TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_integrations.user_id) AND (u.auth_user_id = auth.uid()))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_integrations.user_id) AND (u.auth_user_id = auth.uid())))));


--
-- Name: user_activities; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_activities ENABLE ROW LEVEL SECURITY;

--
-- Name: user_automations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_automations ENABLE ROW LEVEL SECURITY;

--
-- Name: user_automations user_automations_front_read; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_automations_front_read ON public.user_automations FOR SELECT TO authenticated, anon USING ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));


--
-- Name: user_automations user_automations_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_automations_service_full ON public.user_automations TO service_role USING (true) WITH CHECK (true);


--
-- Name: user_companies; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_companies ENABLE ROW LEVEL SECURITY;

--
-- Name: user_companies user_companies_front_read; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_companies_front_read ON public.user_companies FOR SELECT TO authenticated, anon USING ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));


--
-- Name: user_companies user_companies_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_companies_service_full ON public.user_companies TO service_role USING (true) WITH CHECK (true);


--
-- Name: user_daily_life_signals; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_daily_life_signals ENABLE ROW LEVEL SECURITY;

--
-- Name: user_daily_life_signals user_daily_life_signals_front_read; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_daily_life_signals_front_read ON public.user_daily_life_signals FOR SELECT TO authenticated, anon USING ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));


--
-- Name: user_daily_life_signals user_daily_life_signals_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_daily_life_signals_service_full ON public.user_daily_life_signals TO service_role USING (true) WITH CHECK (true);


--
-- Name: user_facts; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_facts ENABLE ROW LEVEL SECURITY;

--
-- Name: user_facts user_facts_front_read; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_facts_front_read ON public.user_facts FOR SELECT TO authenticated, anon USING ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));


--
-- Name: user_facts user_facts_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_facts_service_full ON public.user_facts TO service_role USING (true) WITH CHECK (true);


--
-- Name: user_financial_profile; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_financial_profile ENABLE ROW LEVEL SECURITY;

--
-- Name: user_financial_profile user_financial_profile_front_read; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_financial_profile_front_read ON public.user_financial_profile FOR SELECT TO authenticated, anon USING ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));


--
-- Name: user_financial_profile user_financial_profile_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_financial_profile_service_full ON public.user_financial_profile TO service_role USING (true) WITH CHECK (true);


--
-- Name: user_key_events; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_key_events ENABLE ROW LEVEL SECURITY;

--
-- Name: user_key_events user_key_events_front_read; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_key_events_front_read ON public.user_key_events FOR SELECT TO authenticated, anon USING ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));


--
-- Name: user_key_events user_key_events_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_key_events_service_full ON public.user_key_events TO service_role USING (true) WITH CHECK (true);


--
-- Name: user_settings; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;

--
-- Name: user_settings user_settings_front_read; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_settings_front_read ON public.user_settings FOR SELECT TO authenticated, anon USING ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));


--
-- Name: user_settings user_settings_insert_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_settings_insert_own ON public.user_settings FOR INSERT TO authenticated WITH CHECK ((user_id = ( SELECT u.id
   FROM public.users u
  WHERE (u.auth_user_id = auth.uid())
 LIMIT 1)));


--
-- Name: user_settings user_settings_select_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_settings_select_own ON public.user_settings FOR SELECT TO authenticated USING ((user_id = ( SELECT u.id
   FROM public.users u
  WHERE (u.auth_user_id = auth.uid())
 LIMIT 1)));


--
-- Name: user_settings user_settings_service_full; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_settings_service_full ON public.user_settings TO service_role USING (true) WITH CHECK (true);


--
-- Name: user_settings user_settings_update_own; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_settings_update_own ON public.user_settings FOR UPDATE TO authenticated USING ((user_id = ( SELECT u.id
   FROM public.users u
  WHERE (u.auth_user_id = auth.uid())
 LIMIT 1))) WITH CHECK ((user_id = ( SELECT u.id
   FROM public.users u
  WHERE (u.auth_user_id = auth.uid())
 LIMIT 1)));


--
-- Name: users; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

--
-- Name: users users_can_update_self; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY users_can_update_self ON public.users FOR UPDATE TO authenticated USING ((auth_user_id = auth.uid())) WITH CHECK ((auth_user_id = auth.uid()));


--
-- PostgreSQL database dump complete
--

\unrestrict JkQaS6yzaoLFdoeEGvdfHsPGAigKx7tRU3D1a0Rp5xtdkzZnTrFeYf3pAbww9eo

