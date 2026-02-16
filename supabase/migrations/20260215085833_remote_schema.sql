create extension if not exists "pg_cron" with schema "pg_catalog";

create type "public"."agent_badge_enum" as enum ('beta', 'live', 'soon');

create type "public"."agent_plan_enum" as enum ('included', 'addon_3', 'addon_6', 'custom');

create type "public"."agent_status_enum" as enum ('off', 'pending', 'active', 'error');

create type "public"."automation_category_enum" as enum ('personal', 'business', 'sales', 'marketing', 'ops', 'admin', 'finance', 'other');

create type "public"."automation_complexity_enum" as enum ('1', '2', '3', '4', '5');

create type "public"."automation_tier_enum" as enum ('standard', 'advanced', 'critical');

create type "public"."billing_frequency_enum" as enum ('monthly', 'annual');

create type "public"."billing_plan_enum" as enum ('starter', 'pro', 'business');

create type "public"."budget_sensitivity_enum" as enum ('low', 'medium', 'high');

create type "public"."business_revenue_band_enum" as enum ('<100k', '100-300k', '300k-1M', '1-3M', '3-10M', '10M+');

create type "public"."company_size_enum" as enum ('solo', '1-5', '6-10', '11-50', '51-200', '201-1000', '1000+');

create type "public"."conversation_channel_enum" as enum ('web_onboarding', 'mobile_app', 'web_dashboard', 'email', 'slack', 'whatsapp', 'telegram', 'other');

create type "public"."conversation_context_enum" as enum ('onboarding', 'daily_summary', 'project_support', 'support_request', 'sales_followup', 'automation_scoping', 'other');

create type "public"."conversation_role_enum" as enum ('user', 'assistant', 'system');

create type "public"."conversation_sender_enum" as enum ('user', 'lisa', 'system', 'human_agent');

create type "public"."conversation_status_enum" as enum ('open', 'snoozed', 'closed');

create type "public"."email_account_status_enum" as enum ('pending', 'connected', 'revoked', 'error');

create type "public"."email_provider_enum" as enum ('google', 'microsoft', 'imap', 'other');

create type "public"."employment_relation_enum" as enum ('owner', 'co-owner', 'employee', 'freelance', 'advisor', 'former-employee', 'other');

create type "public"."fact_category_enum" as enum ('identity', 'personal_profile', 'family', 'health', 'preferences', 'goals', 'constraints', 'context', 'financial', 'other');

create type "public"."fact_key_status_enum" as enum ('core', 'experimental', 'proposed', 'deprecated');

create type "public"."fact_scope_enum" as enum ('personal', 'work', 'both');

create type "public"."fact_source_type_enum" as enum ('declared', 'observed', 'inferred', 'system');

create type "public"."fact_value_type_enum" as enum ('text', 'number', 'date', 'boolean', 'json');

create type "public"."financial_data_source_enum" as enum ('declared', 'estimated', 'mixed');

create type "public"."financial_pressure_enum" as enum ('relaxed', 'comfortable', 'tight', 'critical');

create type "public"."iap_platform" as enum ('ios', 'android');

create type "public"."income_band_enum" as enum ('<30k', '30-60k', '60-100k', '100-200k', '200k+');

create type "public"."initial_cleaning_status_enum" as enum ('pending', 'snoozed', 'done', 'refused');

create type "public"."integration_status_enum" as enum ('active', 'beta', 'deprecated', 'disabled');

create type "public"."life_dimension_enum" as enum ('health', 'career', 'finance', 'relationships', 'personal_growth', 'leisure_stability', 'other');

create type "public"."lisa_mood_enum" as enum ('very_low', 'low', 'neutral', 'high', 'very_high');

create type "public"."lisa_task_owner_enum" as enum ('lisa', 'human_team', 'user', 'external_system');

create type "public"."lisa_task_priority_enum" as enum ('low', 'normal', 'high', 'urgent');

create type "public"."lisa_task_status_enum" as enum ('pending', 'in_progress', 'waiting_user', 'done', 'cancelled');

create type "public"."lisa_task_trigger_source_enum" as enum ('lisa_chat', 'automation', 'system_rule', 'rule', 'manual');

create type "public"."lisa_task_type_enum" as enum ('user_followup', 'summary_prep', 'fact_update', 'automation_scoping', 'automation_build', 'support_request', 'sales_opportunity', 'other', 'reminder', 'memo_deletion', 'decision_pending', 'tools_extension');

create type "public"."onboarding_stage_enum" as enum ('signup_only', 'subscribed_no_oauth', 'active', 'churn_risk', 'subscribed_oauth_no_first_cleaning');

create type "public"."plan_recommendation_enum" as enum ('starter', 'pro', 'business');

create type "public"."project_event_source_enum" as enum ('email', 'calendar', 'manual', 'system', 'slack', 'other');

create type "public"."project_event_type_enum" as enum ('created', 'status_update', 'deadline_change', 'milestone_reached', 'risk_flagged', 'client_message', 'internal_note', 'automation_run', 'other');

create type "public"."project_priority_enum" as enum ('low', 'normal', 'high', 'critical');

create type "public"."project_status_enum" as enum ('idea', 'active', 'on_hold', 'completed', 'dropped');

create type "public"."project_type_enum" as enum ('work', 'business', 'personal', 'health', 'learning', 'finance', 'family', 'legal', 'other');

create type "public"."referral_status" as enum ('created', 'applied', 'consumed', 'expired', 'cancelled');

create type "public"."service_doc_audience_enum" as enum ('user_facing', 'internal_ops', 'internal_llm');

create type "public"."service_doc_category_enum" as enum ('product', 'pricing', 'privacy', 'onboarding', 'automation_lib', 'support', 'internal', 'other');

create type "public"."spending_style_enum" as enum ('frugal', 'balanced', 'premium');

create type "public"."summary_detail_level_enum" as enum ('short', 'normal', 'detailed');

create type "public"."triage_preset_enum" as enum ('lisa_default', 'custom', 'off');

create type "public"."user_automation_status_enum" as enum ('idea', 'scoping', 'building', 'active', 'paused', 'archived');

create type "public"."user_integration_status_enum" as enum ('connected', 'needs_attention', 'disconnected', 'revoked');

create type "public"."user_status_enum" as enum ('prospect', 'trial', 'active', 'new_user', 'inactive');

create sequence "public"."debug_auth_user_created_log_id_seq";

create sequence "public"."fact_profile_mappings_id_seq";


  create table "public"."affiliate_codes" (
    "user_id" uuid not null,
    "code" text not null,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "is_active" boolean not null default true,
    "id" uuid default gen_random_uuid(),
    "share_url" text,
    "country_code" text
      );


alter table "public"."affiliate_codes" enable row level security;


  create table "public"."affiliate_commissions" (
    "id" uuid not null default gen_random_uuid(),
    "affiliate_id" uuid not null,
    "affiliate_promo_code_id" uuid not null,
    "stripe_invoice_id" text not null,
    "stripe_subscription_id" text,
    "stripe_customer_id" text,
    "stripe_charge_id" text,
    "amount_excl_tax_cents" integer not null,
    "commission_rate" numeric(5,2) not null,
    "commission_cents" integer not null,
    "currency" text not null default 'eur'::text,
    "period_start" timestamp with time zone,
    "period_end" timestamp with time zone,
    "status" text not null default 'pending'::text,
    "payout_batch_id" uuid,
    "created_at" timestamp with time zone not null default now()
      );


alter table "public"."affiliate_commissions" enable row level security;


  create table "public"."affiliates" (
    "id" uuid not null default gen_random_uuid(),
    "email" text not null,
    "full_name" text,
    "stripe_customer_id" text,
    "stripe_connect_account_id" text,
    "status" text not null default 'active'::text,
    "notes" text,
    "created_at" timestamp with time zone not null default now(),
    "stripe_account_id" text,
    "stripe_onboarding_sent_at" timestamp with time zone,
    "stripe_onboarding_completed_at" timestamp with time zone,
    "country" text,
    "user_id" uuid
      );


alter table "public"."affiliates" enable row level security;


  create table "public"."app_config" (
    "key" text not null,
    "value" text not null,
    "updated_at" timestamp with time zone not null default now()
      );


alter table "public"."app_config" enable row level security;


  create table "public"."automation_templates" (
    "id" uuid not null default gen_random_uuid(),
    "slug" text not null,
    "label" text not null,
    "category" public.automation_category_enum not null default 'other'::public.automation_category_enum,
    "description_short" text not null,
    "description_full" text,
    "complexity_level" public.automation_complexity_enum not null default '2'::public.automation_complexity_enum,
    "recommended_plan" public.plan_recommendation_enum not null default 'pro'::public.plan_recommendation_enum,
    "required_connectors" jsonb default '[]'::jsonb,
    "default_triggers" jsonb default '{}'::jsonb,
    "default_actions" jsonb default '{}'::jsonb,
    "default_roi_estimate" jsonb default '{}'::jsonb,
    "tags" text[] default ARRAY[]::text[],
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "tier" public.automation_tier_enum not null default 'standard'::public.automation_tier_enum
      );


alter table "public"."automation_templates" enable row level security;


  create table "public"."billing_events" (
    "id" uuid not null default gen_random_uuid(),
    "created_at" timestamp with time zone not null default now(),
    "source" text not null,
    "provider" text not null,
    "provider_event_id" text,
    "event_type" text,
    "auth_user_id" uuid,
    "app_user_id" text,
    "user_id" uuid,
    "entitlement_ids" text[],
    "expiration_at" timestamp with time zone,
    "payload" jsonb not null default '{}'::jsonb,
    "processed_at" timestamp with time zone,
    "process_status" text not null default 'received'::text,
    "process_error" text,
    "payload_sha256" text,
    "mode" text,
    "dedupe_key" text
      );


alter table "public"."billing_events" enable row level security;


  create table "public"."companies" (
    "id" uuid not null default gen_random_uuid(),
    "name" text not null,
    "legal_name" text,
    "slug" text,
    "website" text,
    "country_code" character(2),
    "main_city" text,
    "size" public.company_size_enum,
    "industry" text,
    "source" text,
    "external_ref" text,
    "notes" jsonb default '{}'::jsonb,
    "is_active" boolean default true,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."companies" enable row level security;


  create table "public"."conversation_messages" (
    "id" uuid not null default gen_random_uuid(),
    "conversation_id" uuid not null,
    "user_id" uuid,
    "sender_type" public.conversation_sender_enum not null default 'user'::public.conversation_sender_enum,
    "role" public.conversation_role_enum not null default 'user'::public.conversation_role_enum,
    "content" text not null,
    "content_tokens" integer,
    "sent_at" timestamp with time zone not null default now(),
    "channel_message_id" text,
    "metadata" jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "sender" text,
    "visitor_id" uuid,
    "dedupe_key" text not null
      );


alter table "public"."conversation_messages" enable row level security;


  create table "public"."conversations" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "channel" public.conversation_channel_enum not null default 'web_onboarding'::public.conversation_channel_enum,
    "context" public.conversation_context_enum not null default 'other'::public.conversation_context_enum,
    "status" public.conversation_status_enum not null default 'open'::public.conversation_status_enum,
    "started_at" timestamp with time zone not null default now(),
    "last_message_at" timestamp with time zone not null default now(),
    "last_summary" text,
    "metadata" jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "visitor_id" uuid,
    "meta" jsonb default '{}'::jsonb,
    "last_proactive_message_at" timestamp with time zone
      );


alter table "public"."conversations" enable row level security;


  create table "public"."debug_auth_user_created_log" (
    "id" bigint not null default nextval('public.debug_auth_user_created_log_id_seq'::regclass),
    "created_at" timestamp with time zone not null default now(),
    "auth_user_id" uuid,
    "email" text,
    "stage" text not null,
    "detail" text
      );


alter table "public"."debug_auth_user_created_log" enable row level security;


  create table "public"."email_accounts" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "provider" public.email_provider_enum not null default 'google'::public.email_provider_enum,
    "email" text not null,
    "is_primary" boolean not null default false,
    "status" public.email_account_status_enum not null default 'pending'::public.email_account_status_enum,
    "provider_user_id" text,
    "scopes" text[],
    "last_sync_at" timestamp with time zone,
    "last_sync_status" text,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "access_token" text,
    "refresh_token" text,
    "token_type" text,
    "expires_at" timestamp with time zone,
    "id_token" text,
    "sync_cursor" text
      );


alter table "public"."email_accounts" enable row level security;


  create table "public"."fact_key_registry" (
    "fact_key" text not null,
    "status" public.fact_key_status_enum not null default 'proposed'::public.fact_key_status_enum,
    "category_default" public.fact_category_enum not null default 'other'::public.fact_category_enum,
    "description" text,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "used_count" integer not null default 0,
    "last_used_at" timestamp with time zone
      );


alter table "public"."fact_key_registry" enable row level security;


  create table "public"."fact_profile_mappings" (
    "id" bigint not null default nextval('public.fact_profile_mappings_id_seq'::regclass),
    "fact_key" text not null,
    "target_table" text not null,
    "target_column" text not null,
    "sync_direction" text not null default 'facts->user'::text,
    "priority" integer not null default 10,
    "is_active" boolean not null default true
      );


alter table "public"."fact_profile_mappings" enable row level security;


  create table "public"."gmail_watch_subscriptions" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "account_email" text not null,
    "channel_id" text not null,
    "resource_id" text not null,
    "history_id" text not null,
    "expiration" timestamp with time zone not null,
    "last_renewed_at" timestamp with time zone not null default now(),
    "status" text not null default 'active'::text,
    "last_error" text,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now()
      );


alter table "public"."gmail_watch_subscriptions" enable row level security;


  create table "public"."heylisa_post_checkout_contexts" (
    "id" uuid not null default gen_random_uuid(),
    "session_id" text not null,
    "visitor_id" text,
    "user_id" uuid not null,
    "payload" jsonb not null,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone
      );


alter table "public"."heylisa_post_checkout_contexts" enable row level security;


  create table "public"."lisa_actions_catalog" (
    "action_key" text not null,
    "title" text not null,
    "category" text not null default 'general'::text,
    "description" text,
    "required_integrations" text[] not null default '{}'::text[],
    "docs_scope" text,
    "status" text not null default 'active'::text,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now()
      );


alter table "public"."lisa_actions_catalog" enable row level security;


  create table "public"."lisa_agent_integrations" (
    "agent_key" text not null,
    "integration_key" text not null,
    "required" boolean not null default true,
    "notes" text not null default ''::text
      );


alter table "public"."lisa_agent_integrations" enable row level security;


  create table "public"."lisa_agents_catalog" (
    "agent_key" text not null,
    "title" text not null,
    "lisa_instructions_short" text not null default ''::text,
    "lisa_playbook" text not null default ''::text,
    "requires_subscription" boolean not null default false,
    "requires_integrations" text[] not null default '{}'::text[],
    "executable_actions" text[] not null default '{}'::text[],
    "status" text not null default 'live'::text,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now()
      );


alter table "public"."lisa_agents_catalog" enable row level security;


  create table "public"."lisa_brains" (
    "id" text not null,
    "description" text,
    "lisa_brain_prompt" text not null
      );


alter table "public"."lisa_brains" enable row level security;


  create table "public"."lisa_concierge_suggestions" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "suggestion_type" text not null,
    "title" text not null,
    "description" text,
    "url" text,
    "location_city" text,
    "location_address" text,
    "suggested_at" timestamp with time zone default now(),
    "suggested_for_date" date,
    "expires_at" date,
    "status" text default 'suggested'::text,
    "user_feedback" text,
    "feedback_at" timestamp with time zone,
    "source" text default 'lisa_proactive'::text,
    "search_query" text,
    "context_tags" text[],
    "metadata" jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );


alter table "public"."lisa_concierge_suggestions" enable row level security;


  create table "public"."lisa_dashboard_weekly_kpis" (
    "id" uuid not null default gen_random_uuid(),
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "user_id" uuid not null,
    "email_account_id" uuid,
    "week_start" date not null,
    "time_saved_minutes" integer not null default 0,
    "life_health_energy" numeric(4,1) not null,
    "life_finance_stability" numeric(4,1) not null,
    "life_relations_social" numeric(4,1) not null,
    "life_career_impact" numeric(4,1) not null,
    "life_personal_development" numeric(4,1) not null,
    "life_balance_serenity" numeric(4,1) not null,
    "life_global_average" numeric(4,1) not null,
    "life_summary" text,
    "week_end" date,
    "week_key" text,
    "window_label" text,
    "year_month" text
      );


alter table "public"."lisa_dashboard_weekly_kpis" enable row level security;


  create table "public"."lisa_integrations_catalog" (
    "id" text not null default gen_random_uuid(),
    "provider" text not null,
    "name" text not null,
    "category" text not null,
    "description" text,
    "status" public.integration_status_enum not null default 'active'::public.integration_status_enum,
    "docs_url" text,
    "icon_url" text,
    "default_scopes" jsonb,
    "metadata" jsonb,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "integration_key" text
      );


alter table "public"."lisa_integrations_catalog" enable row level security;


  create table "public"."lisa_priority_emails" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "gmail_id" text not null,
    "thread_id" text not null,
    "subject" text not null,
    "from_email" text not null,
    "to_emails" text,
    "cc_emails" text,
    "date_received" timestamp with time zone not null,
    "is_unread" boolean not null default true,
    "in_inbox" boolean not null default true,
    "labels" text[] not null default '{}'::text[],
    "snippet" text,
    "body_full" text,
    "created_at" timestamp with time zone not null default now(),
    "processed_at" timestamp with time zone
      );


alter table "public"."lisa_priority_emails" enable row level security;


  create table "public"."lisa_service_docs" (
    "id" uuid not null default gen_random_uuid(),
    "chunk_title" text not null,
    "chunk_content" text not null,
    "tags" text[] not null,
    "order_key" text default '1.0'::text,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "doc_scope" text,
    "rubrique_title" text
      );


alter table "public"."lisa_service_docs" enable row level security;


  create table "public"."lisa_tasks" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "project_id" uuid,
    "conversation_id" uuid,
    "task_type" public.lisa_task_type_enum not null,
    "owner_type" public.lisa_task_owner_enum not null default 'lisa'::public.lisa_task_owner_enum,
    "status" public.lisa_task_status_enum not null default 'pending'::public.lisa_task_status_enum,
    "priority" public.lisa_task_priority_enum not null default 'normal'::public.lisa_task_priority_enum,
    "title" text not null,
    "description" text,
    "trigger_source" public.lisa_task_trigger_source_enum default 'lisa_chat'::public.lisa_task_trigger_source_enum,
    "source_reference" text,
    "due_at" timestamp with time zone,
    "completed_at" timestamp with time zone,
    "llm_payload" jsonb default '{}'::jsonb,
    "metadata" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "dedupe_key" text,
    "project_client_ref" text
      );


alter table "public"."lisa_tasks" enable row level security;


  create table "public"."lisa_user_agent_settings_gmail" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "agent_id" uuid not null,
    "oauth_connected" boolean not null default false,
    "oauth_connected_at" timestamp with time zone,
    "gmail_email" text,
    "granted_scopes" text[] default '{}'::text[],
    "last_sync_at" timestamp with time zone,
    "last_watch_setup_at" timestamp with time zone,
    "watch_expires_at" timestamp with time zone,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now()
      );


alter table "public"."lisa_user_agent_settings_gmail" enable row level security;


  create table "public"."lisa_user_agents" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "agent_key" text not null,
    "status" public.agent_status_enum not null default 'off'::public.agent_status_enum,
    "config" jsonb,
    "revoked_at" timestamp with time zone,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "onboarding_status" text
      );


alter table "public"."lisa_user_agents" enable row level security;


  create table "public"."lisa_user_integrations" (
    "user_id" uuid not null,
    "integration_key" text not null,
    "status" text not null default 'disconnected'::text,
    "connected_at" timestamp with time zone,
    "metadata" jsonb not null default '{}'::jsonb,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now()
      );


alter table "public"."lisa_user_integrations" enable row level security;


  create table "public"."lisa_user_monthly_memory" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "year_month" character(7) not null,
    "summary_text" text not null,
    "dominant_mood" public.lisa_mood_enum,
    "key_events" jsonb,
    "tags" jsonb,
    "generated_at" timestamp with time zone not null default now(),
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "month_key" text
      );


alter table "public"."lisa_user_monthly_memory" enable row level security;


  create table "public"."proactive_events_outbox" (
    "id" uuid not null default gen_random_uuid(),
    "event_type" text not null,
    "user_id" uuid not null,
    "conversation_id" uuid,
    "payload" jsonb not null default '{}'::jsonb,
    "dedupe_key" text not null,
    "created_at" timestamp with time zone not null default now(),
    "processed_at" timestamp with time zone
      );


alter table "public"."proactive_events_outbox" enable row level security;


  create table "public"."proactive_messages_queue" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "send_at" timestamp with time zone not null,
    "status" text not null default 'scheduled'::text,
    "content" text not null,
    "dedupe_key" text not null,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "event_type" text
      );


alter table "public"."proactive_messages_queue" enable row level security;


  create table "public"."project_events" (
    "id" uuid not null default gen_random_uuid(),
    "project_id" uuid,
    "user_id" uuid not null,
    "source" text not null,
    "event_type" public.project_event_type_enum not null default 'other'::public.project_event_type_enum,
    "title" text not null,
    "description" text,
    "event_ts" timestamp with time zone not null default now(),
    "importance" smallint not null default 5,
    "related_email_provider" text,
    "related_email_id" text,
    "metadata" jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "fingerprint" text,
    "project_client_ref" text
      );


alter table "public"."project_events" enable row level security;


  create table "public"."projects" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "name" text not null,
    "description" text,
    "project_type" public.project_type_enum not null default 'other'::public.project_type_enum,
    "status" public.project_status_enum not null default 'active'::public.project_status_enum,
    "priority" public.project_priority_enum not null default 'normal'::public.project_priority_enum,
    "impact_life" smallint,
    "impact_business" smallint,
    "urgency_score" smallint,
    "energy_required" smallint,
    "start_date" date,
    "target_end_date" date,
    "main_company_id" uuid,
    "tags" text[],
    "suggested_actions" jsonb,
    "life_dimension" public.life_dimension_enum not null default 'other'::public.life_dimension_enum,
    "parent_project_id" uuid,
    "next_action" text,
    "next_follow_up_at" timestamp with time zone,
    "last_event_at" timestamp with time zone,
    "cadence" jsonb,
    "details" jsonb,
    "client_ref" text
      );


alter table "public"."projects" enable row level security;


  create table "public"."push_devices" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "expo_push_token" text not null,
    "platform" text not null,
    "is_app_active" boolean not null default false,
    "active_screen" text,
    "last_seen_at" timestamp with time zone not null default now(),
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "device_id" text
      );


alter table "public"."push_devices" enable row level security;


  create table "public"."push_outbox" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "kind" text not null,
    "title" text not null,
    "body" text not null,
    "data" jsonb not null default '{}'::jsonb,
    "created_at" timestamp with time zone not null default now(),
    "sent_at" timestamp with time zone,
    "status" text not null default 'queued'::text,
    "error" text,
    "scheduled_at" timestamp with time zone,
    "attempts" integer not null default 0,
    "sending_at" timestamp with time zone
      );


alter table "public"."push_outbox" enable row level security;


  create table "public"."referrals" (
    "id" uuid not null default gen_random_uuid(),
    "code" text not null,
    "referrer_user_id" uuid not null,
    "referred_user_id" uuid not null,
    "status" public.referral_status not null default 'created'::public.referral_status,
    "created_at" timestamp with time zone not null default now(),
    "applied_at" timestamp with time zone,
    "consumed_at" timestamp with time zone,
    "expires_at" timestamp with time zone,
    "first_purchase_only" boolean not null default true,
    "eligible_product_id" text not null default 'com.neatikai.heylisa.pro.monthly_discount'::text,
    "platform" text,
    "transaction_id" text,
    "original_transaction_id" text,
    "referrer_user_id_l2" uuid,
    "referrer_user_id_l3" uuid
      );


alter table "public"."referrals" enable row level security;


  create table "public"."user_activities" (
    "user_id" uuid not null,
    "main_activity" text,
    "main_activity_confidence" smallint not null default 0,
    "main_activity_reason" text,
    "secondary_activities" jsonb not null default '[]'::jsonb,
    "last_observed_at" timestamp with time zone,
    "source" text not null default 'conversation'::text,
    "source_conversation_id" uuid,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now()
      );


alter table "public"."user_activities" enable row level security;


  create table "public"."user_automations" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "project_id" uuid,
    "template_id" uuid,
    "status" public.user_automation_status_enum not null default 'idea'::public.user_automation_status_enum,
    "title" text not null,
    "description" text,
    "config" jsonb default '{}'::jsonb,
    "impact_estimate" jsonb default '{}'::jsonb,
    "metrics" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now()
      );


alter table "public"."user_automations" enable row level security;


  create table "public"."user_companies" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "company_id" uuid not null,
    "relation" public.employment_relation_enum not null default 'employee'::public.employment_relation_enum,
    "title" text,
    "department" text,
    "seniority_level" text,
    "is_primary" boolean default false,
    "started_at" date,
    "ended_at" date,
    "notes" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now()
      );


alter table "public"."user_companies" enable row level security;


  create table "public"."user_daily_life_signals" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "day_key" text not null,
    "window_start" timestamp with time zone not null,
    "window_end" timestamp with time zone not null,
    "life_radar_signals" jsonb,
    "source_stats" jsonb,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now()
      );


alter table "public"."user_daily_life_signals" enable row level security;


  create table "public"."user_facts" (
    "id" uuid not null default gen_random_uuid(),
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "user_id" uuid not null,
    "fact_key" text not null,
    "category" public.fact_category_enum not null default 'other'::public.fact_category_enum,
    "scope" public.fact_scope_enum not null default 'personal'::public.fact_scope_enum,
    "value_type" public.fact_value_type_enum not null default 'text'::public.fact_value_type_enum,
    "value" jsonb default '{}'::jsonb,
    "source_type" public.fact_source_type_enum not null default 'declared'::public.fact_source_type_enum,
    "source_ref" text,
    "confidence" numeric(3,2) not null default 0.80,
    "is_estimated" boolean not null default false,
    "is_active" boolean not null default true,
    "notes" text,
    "last_seen_at" timestamp with time zone,
    "mention_count" integer not null default 0,
    "updated_by" text,
    "deactivated_at" timestamp with time zone
      );


alter table "public"."user_facts" enable row level security;


  create table "public"."user_financial_profile" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "data_source" public.financial_data_source_enum not null default 'estimated'::public.financial_data_source_enum,
    "confidence_score" numeric not null default 0.3,
    "personal_income_band" public.income_band_enum,
    "financial_pressure" public.financial_pressure_enum,
    "spending_style" public.spending_style_enum,
    "main_currency" text,
    "business_revenue_band" public.business_revenue_band_enum,
    "budget_sensitivity" public.budget_sensitivity_enum,
    "max_monthly_tools_budget" numeric,
    "financial_goals" text
      );


alter table "public"."user_financial_profile" enable row level security;


  create table "public"."user_key_events" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "event_type" text not null,
    "title" text not null,
    "description" text,
    "event_date" date not null,
    "is_recurring" boolean default false,
    "recurrence_pattern" text,
    "importance_level" text default 'medium'::text,
    "related_people" text[],
    "related_project_id" uuid,
    "reminder_days_before" integer[] default ARRAY[7, 3, 1],
    "last_mentioned_at" timestamp with time zone,
    "source" text default 'user_input'::text,
    "metadata" jsonb,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "mention_count" integer default 0,
    "source_reference" text
      );


alter table "public"."user_key_events" enable row level security;


  create table "public"."user_settings" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "created_at" timestamp with time zone not null default now(),
    "updated_at" timestamp with time zone not null default now(),
    "job_title" text,
    "industry" text,
    "last_active_at" timestamp with time zone,
    "profiling_completed" boolean default false,
    "profiling_facts_count" integer default 0,
    "profiling_facts_total" integer default 0,
    "profiling_completion_pct" numeric(5,2) default 0.00,
    "use_tu_form" boolean,
    "intro_smalltalk_turns" integer not null default 0,
    "intro_smalltalk_done" boolean not null default false,
    "chat_turns_7d" integer not null default 0,
    "active_days_7d" integer not null default 0,
    "last_message_at" timestamp with time zone,
    "active_agents_count" integer not null default 0,
    "included_agent_key" text,
    "locale_main" text not null default 'fr-FR'::text,
    "timezone" text not null default 'UTC'::text,
    "country_code" text,
    "free_quota_limit" integer not null default 8,
    "free_quota_used" integer not null default 0,
    "main_city" text,
    "main_activity" text,
    "profiling_level" text,
    "discovery_status" text default 'pending'::text,
    "discovery_completed_at" timestamp with time zone
      );


alter table "public"."user_settings" enable row level security;


  create table "public"."userfacts_daily_queue" (
    "id" uuid not null default gen_random_uuid(),
    "public_user_id" uuid not null,
    "conversation_id" uuid not null,
    "target_day" date not null,
    "status" text not null default 'pending'::text,
    "enqueued_at" timestamp with time zone not null default now(),
    "processed_at" timestamp with time zone,
    "dedupe_key" text not null,
    "debug" jsonb
      );


alter table "public"."userfacts_daily_queue" enable row level security;


  create table "public"."users" (
    "id" uuid not null default gen_random_uuid(),
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now(),
    "account_email" text,
    "status" public.user_status_enum not null default 'prospect'::public.user_status_enum,
    "stripe_customer_id" text,
    "first_name" text,
    "last_name" text,
    "full_name" text,
    "primary_company_id" uuid,
    "profile_photo_url" text,
    "deleted_at" timestamp with time zone,
    "auth_user_id" uuid,
    "deletion_reason" text,
    "country_code" text,
    "affiliate_code" text,
    "affiliate_link" text,
    "trial_started_at" timestamp with time zone,
    "is_pro" boolean default false,
    "pro_started_at" timestamp with time zone,
    "referrer_applied_at" timestamp with time zone,
    "signup_source" text,
    "paywall_reason" text
      );


alter table "public"."users" enable row level security;

alter sequence "public"."debug_auth_user_created_log_id_seq" owned by "public"."debug_auth_user_created_log"."id";

alter sequence "public"."fact_profile_mappings_id_seq" owned by "public"."fact_profile_mappings"."id";

CREATE INDEX affiliate_codes_code_idx ON public.affiliate_codes USING btree (code);

CREATE UNIQUE INDEX affiliate_codes_code_key ON public.affiliate_codes USING btree (code);

CREATE UNIQUE INDEX affiliate_codes_code_unique ON public.affiliate_codes USING btree (code);

CREATE UNIQUE INDEX affiliate_codes_pkey ON public.affiliate_codes USING btree (user_id);

CREATE UNIQUE INDEX affiliate_codes_user_unique ON public.affiliate_codes USING btree (user_id);

CREATE UNIQUE INDEX affiliate_commissions_pkey ON public.affiliate_commissions USING btree (id);

CREATE UNIQUE INDEX affiliates_email_key ON public.affiliates USING btree (email);

CREATE UNIQUE INDEX affiliates_email_unique ON public.affiliates USING btree (email);

CREATE UNIQUE INDEX affiliates_pkey ON public.affiliates USING btree (id);

CREATE UNIQUE INDEX affiliates_user_id_unique ON public.affiliates USING btree (user_id) WHERE (user_id IS NOT NULL);

CREATE UNIQUE INDEX app_config_pkey ON public.app_config USING btree (key);

CREATE UNIQUE INDEX automation_templates_pkey ON public.automation_templates USING btree (id);

CREATE UNIQUE INDEX automation_templates_slug_key ON public.automation_templates USING btree (slug);

CREATE INDEX billing_events_auth_user_id_idx ON public.billing_events USING btree (auth_user_id);

CREATE INDEX billing_events_created_at_idx ON public.billing_events USING btree (created_at DESC);

CREATE UNIQUE INDEX billing_events_dedupe_key_uq ON public.billing_events USING btree (dedupe_key);

CREATE INDEX billing_events_payload_sha256_idx ON public.billing_events USING btree (payload_sha256);

CREATE UNIQUE INDEX billing_events_pkey ON public.billing_events USING btree (id);

CREATE UNIQUE INDEX billing_events_provider_dedup ON public.billing_events USING btree (provider, provider_event_id) WHERE (provider_event_id IS NOT NULL);

CREATE INDEX billing_events_user_id_idx ON public.billing_events USING btree (user_id);

CREATE UNIQUE INDEX companies_pkey ON public.companies USING btree (id);

CREATE UNIQUE INDEX companies_slug_key ON public.companies USING btree (slug);

CREATE UNIQUE INDEX conversation_messages_dedupe_key_uniq ON public.conversation_messages USING btree (dedupe_key);

CREATE UNIQUE INDEX conversation_messages_pkey ON public.conversation_messages USING btree (id);

CREATE UNIQUE INDEX conversation_messages_unique_dedupe ON public.conversation_messages USING btree (conversation_id, dedupe_key);

CREATE UNIQUE INDEX conversation_messages_user_dedupe_uq ON public.conversation_messages USING btree (user_id, dedupe_key);

CREATE UNIQUE INDEX conversations_pkey ON public.conversations USING btree (id);

CREATE UNIQUE INDEX conversations_user_id_unique ON public.conversations USING btree (user_id);

CREATE UNIQUE INDEX debug_auth_user_created_log_pkey ON public.debug_auth_user_created_log USING btree (id);

CREATE UNIQUE INDEX email_accounts_pkey ON public.email_accounts USING btree (id);

CREATE UNIQUE INDEX email_accounts_primary_unique_per_user ON public.email_accounts USING btree (user_id) WHERE (is_primary = true);

CREATE UNIQUE INDEX email_accounts_user_email_uniq ON public.email_accounts USING btree (user_id, email);

CREATE UNIQUE INDEX email_accounts_user_provider_unique ON public.email_accounts USING btree (user_id, provider);

CREATE UNIQUE INDEX fact_key_registry_pkey ON public.fact_key_registry USING btree (fact_key);

CREATE INDEX fact_key_registry_status_idx ON public.fact_key_registry USING btree (status);

CREATE UNIQUE INDEX fact_profile_mappings_fact_key_target_table_target_column_key ON public.fact_profile_mappings USING btree (fact_key, target_table, target_column);

CREATE UNIQUE INDEX fact_profile_mappings_pkey ON public.fact_profile_mappings USING btree (id);

CREATE UNIQUE INDEX gmail_watch_sub_unique_user_email ON public.gmail_watch_subscriptions USING btree (user_id, account_email);

CREATE INDEX gmail_watch_subscriptions_exp_idx ON public.gmail_watch_subscriptions USING btree (expiration);

CREATE UNIQUE INDEX gmail_watch_subscriptions_pkey ON public.gmail_watch_subscriptions USING btree (id);

CREATE INDEX gmail_watch_subscriptions_user_idx ON public.gmail_watch_subscriptions USING btree (user_id);

CREATE UNIQUE INDEX heylisa_post_checkout_contexts_pkey ON public.heylisa_post_checkout_contexts USING btree (id);

CREATE UNIQUE INDEX heylisa_post_checkout_contexts_session_id_key ON public.heylisa_post_checkout_contexts USING btree (session_id);

CREATE INDEX idx_affiliate_codes_code ON public.affiliate_codes USING btree (code);

CREATE INDEX idx_affiliate_codes_user_id ON public.affiliate_codes USING btree (user_id);

CREATE INDEX idx_concierge_suggestions_date ON public.lisa_concierge_suggestions USING btree (suggested_for_date);

CREATE INDEX idx_concierge_suggestions_status ON public.lisa_concierge_suggestions USING btree (status);

CREATE INDEX idx_concierge_suggestions_type ON public.lisa_concierge_suggestions USING btree (suggestion_type);

CREATE INDEX idx_concierge_suggestions_user_id ON public.lisa_concierge_suggestions USING btree (user_id);

CREATE INDEX idx_conv_messages_conv_ts ON public.conversation_messages USING btree (conversation_id, sent_at);

CREATE INDEX idx_conv_messages_conversation_id ON public.conversation_messages USING btree (conversation_id);

CREATE INDEX idx_conv_messages_user_id ON public.conversation_messages USING btree (user_id);

CREATE INDEX idx_conv_messages_user_ts ON public.conversation_messages USING btree (user_id, sent_at DESC);

CREATE INDEX idx_conv_messages_visitor_id ON public.conversation_messages USING btree (visitor_id);

CREATE INDEX idx_conversation_messages_conv_sentat ON public.conversation_messages USING btree (conversation_id, sent_at DESC);

CREATE INDEX idx_conversations_channel ON public.conversations USING btree (channel);

CREATE INDEX idx_conversations_status ON public.conversations USING btree (status, last_message_at DESC);

CREATE INDEX idx_conversations_user ON public.conversations USING btree (user_id, started_at DESC);

CREATE INDEX idx_conversations_user_id ON public.conversations USING btree (user_id);

CREATE INDEX idx_conversations_visitor_id ON public.conversations USING btree (visitor_id);

CREATE INDEX idx_gmail_settings_user ON public.lisa_user_agent_settings_gmail USING btree (user_id);

CREATE INDEX idx_hl_post_checkout_session ON public.heylisa_post_checkout_contexts USING btree (session_id);

CREATE INDEX idx_hl_post_checkout_user ON public.heylisa_post_checkout_contexts USING btree (user_id);

CREATE INDEX idx_lisa_actions_catalog_category ON public.lisa_actions_catalog USING btree (category);

CREATE INDEX idx_lisa_actions_catalog_status ON public.lisa_actions_catalog USING btree (status);

CREATE INDEX idx_lisa_agents_catalog_status ON public.lisa_agents_catalog USING btree (status);

CREATE INDEX idx_lisa_integrations_catalog_category ON public.lisa_integrations_catalog USING btree (category);

CREATE INDEX idx_lisa_service_docs_scope ON public.lisa_service_docs USING btree (doc_scope);

CREATE INDEX idx_lisa_tasks_owner ON public.lisa_tasks USING btree (owner_type);

CREATE INDEX idx_lisa_tasks_project ON public.lisa_tasks USING btree (project_id);

CREATE INDEX idx_lisa_tasks_status_due ON public.lisa_tasks USING btree (status, due_at);

CREATE INDEX idx_lisa_tasks_user ON public.lisa_tasks USING btree (user_id);

CREATE INDEX idx_lisa_user_agents_key ON public.lisa_user_agents USING btree (agent_key);

CREATE INDEX idx_lisa_user_agents_onboarding_status ON public.lisa_user_agents USING btree (user_id, onboarding_status);

CREATE INDEX idx_lisa_user_agents_status ON public.lisa_user_agents USING btree (status);

CREATE INDEX idx_lisa_user_agents_user ON public.lisa_user_agents USING btree (user_id);

CREATE INDEX idx_lisa_user_integrations_user ON public.lisa_user_integrations USING btree (user_id);

CREATE INDEX idx_project_events_project_ts ON public.project_events USING btree (project_id, event_ts DESC);

CREATE INDEX idx_project_events_user_ts ON public.project_events USING btree (user_id, event_ts DESC);

CREATE INDEX idx_projects_parent ON public.projects USING btree (parent_project_id);

CREATE INDEX idx_projects_user_dimension ON public.projects USING btree (user_id, life_dimension);

CREATE INDEX idx_projects_user_next_follow_up ON public.projects USING btree (user_id, next_follow_up_at);

CREATE INDEX idx_service_docs_content_fts ON public.lisa_service_docs USING gin (to_tsvector('french'::regconfig, ((chunk_title || ' '::text) || chunk_content)));

CREATE INDEX idx_service_docs_tags ON public.lisa_service_docs USING gin (tags);

CREATE INDEX idx_user_activities_last_observed_at ON public.user_activities USING btree (last_observed_at DESC);

CREATE INDEX idx_user_automations_status ON public.user_automations USING btree (status);

CREATE INDEX idx_user_automations_template ON public.user_automations USING btree (template_id);

CREATE INDEX idx_user_automations_user ON public.user_automations USING btree (user_id);

CREATE INDEX idx_user_key_events_date ON public.user_key_events USING btree (event_date);

CREATE INDEX idx_user_key_events_last_mentioned ON public.user_key_events USING btree (last_mentioned_at);

CREATE INDEX idx_user_key_events_proactive ON public.user_key_events USING btree (user_id, event_date, last_mentioned_at, importance_level);

CREATE INDEX idx_user_key_events_upcoming ON public.user_key_events USING btree (user_id, event_date);

CREATE INDEX idx_user_key_events_user_id ON public.user_key_events USING btree (user_id);

CREATE INDEX idx_user_settings_last_active_at ON public.user_settings USING btree (last_active_at);

CREATE INDEX ix_user_facts_fact_key ON public.user_facts USING btree (fact_key);

CREATE INDEX ix_user_facts_user_active ON public.user_facts USING btree (user_id, is_active);

CREATE INDEX ix_userfacts_daily_queue_pending ON public.userfacts_daily_queue USING btree (status, target_day);

CREATE UNIQUE INDEX lisa_actions_catalog_pkey ON public.lisa_actions_catalog USING btree (action_key);

CREATE UNIQUE INDEX lisa_agent_integrations_pkey ON public.lisa_agent_integrations USING btree (agent_key, integration_key);

CREATE UNIQUE INDEX lisa_agents_catalog_pkey ON public.lisa_agents_catalog USING btree (agent_key);

CREATE UNIQUE INDEX lisa_brains_pkey ON public.lisa_brains USING btree (id);

CREATE UNIQUE INDEX lisa_concierge_suggestions_pkey ON public.lisa_concierge_suggestions USING btree (id);

CREATE UNIQUE INDEX lisa_dashboard_weekly_kpis_pkey ON public.lisa_dashboard_weekly_kpis USING btree (id);

CREATE UNIQUE INDEX lisa_dashboard_weekly_kpis_uid_week_key_unique ON public.lisa_dashboard_weekly_kpis USING btree (user_id, week_key);

CREATE INDEX lisa_integrations_catalog_category_idx ON public.lisa_integrations_catalog USING btree (category);

CREATE UNIQUE INDEX lisa_integrations_catalog_pkey ON public.lisa_integrations_catalog USING btree (id);

CREATE INDEX lisa_integrations_catalog_provider_idx ON public.lisa_integrations_catalog USING btree (provider);

CREATE INDEX lisa_integrations_catalog_status_idx ON public.lisa_integrations_catalog USING btree (status);

CREATE UNIQUE INDEX lisa_priority_emails_pkey ON public.lisa_priority_emails USING btree (id);

CREATE INDEX lisa_priority_emails_unprocessed_idx ON public.lisa_priority_emails USING btree (user_id, date_received) WHERE (processed_at IS NULL);

CREATE UNIQUE INDEX lisa_priority_emails_user_mail_uidx ON public.lisa_priority_emails USING btree (user_id, gmail_id);

CREATE UNIQUE INDEX lisa_service_docs_pkey ON public.lisa_service_docs USING btree (id);

CREATE INDEX lisa_tasks_clientref_idx ON public.lisa_tasks USING btree (user_id, project_client_ref) WHERE (project_id IS NULL);

CREATE INDEX lisa_tasks_conversation_idx ON public.lisa_tasks USING btree (conversation_id);

CREATE UNIQUE INDEX lisa_tasks_pkey ON public.lisa_tasks USING btree (id);

CREATE INDEX lisa_tasks_status_due_idx ON public.lisa_tasks USING btree (status, due_at);

CREATE UNIQUE INDEX lisa_tasks_user_dedupe_key_uq ON public.lisa_tasks USING btree (user_id, dedupe_key);

CREATE UNIQUE INDEX lisa_tasks_user_dedupe_key_ux ON public.lisa_tasks USING btree (user_id, dedupe_key) WHERE (dedupe_key IS NOT NULL);

CREATE INDEX lisa_tasks_user_due_idx ON public.lisa_tasks USING btree (user_id, status, due_at);

CREATE UNIQUE INDEX lisa_tasks_user_id_dedupe_key_uniq ON public.lisa_tasks USING btree (user_id, dedupe_key);

CREATE UNIQUE INDEX lisa_user_agent_settings_gmail_agent_id_key ON public.lisa_user_agent_settings_gmail USING btree (agent_id);

CREATE UNIQUE INDEX lisa_user_agent_settings_gmail_pkey ON public.lisa_user_agent_settings_gmail USING btree (id);

CREATE UNIQUE INDEX lisa_user_agents_pkey ON public.lisa_user_agents USING btree (id);

CREATE UNIQUE INDEX lisa_user_agents_user_agent_key_unique ON public.lisa_user_agents USING btree (user_id, agent_key);

CREATE UNIQUE INDEX lisa_user_integrations_pkey ON public.lisa_user_integrations USING btree (user_id, integration_key);

CREATE INDEX lisa_user_monthly_memory_month_idx ON public.lisa_user_monthly_memory USING btree (year_month);

CREATE UNIQUE INDEX lisa_user_monthly_memory_pkey ON public.lisa_user_monthly_memory USING btree (id);

CREATE UNIQUE INDEX lisa_user_monthly_memory_unique ON public.lisa_user_monthly_memory USING btree (user_id, month_key);

CREATE INDEX lisa_user_monthly_memory_user_idx ON public.lisa_user_monthly_memory USING btree (user_id);

CREATE UNIQUE INDEX lisa_user_monthly_memory_user_month_uniq ON public.lisa_user_monthly_memory USING btree (user_id, year_month);

CREATE INDEX lisa_weekly_kpis_user_week_idx ON public.lisa_dashboard_weekly_kpis USING btree (user_id, week_start);

CREATE UNIQUE INDEX proactive_events_outbox_dedupe_key_uidx ON public.proactive_events_outbox USING btree (dedupe_key);

CREATE UNIQUE INDEX proactive_events_outbox_dedupe_key_ux ON public.proactive_events_outbox USING btree (dedupe_key);

CREATE UNIQUE INDEX proactive_events_outbox_pkey ON public.proactive_events_outbox USING btree (id);

CREATE INDEX proactive_events_outbox_unprocessed_idx ON public.proactive_events_outbox USING btree (created_at) WHERE (processed_at IS NULL);

CREATE UNIQUE INDEX proactive_messages_queue_dedupe_key_ux ON public.proactive_messages_queue USING btree (dedupe_key);

CREATE INDEX proactive_messages_queue_due_idx ON public.proactive_messages_queue USING btree (send_at) WHERE (status = 'scheduled'::text);

CREATE UNIQUE INDEX proactive_messages_queue_pkey ON public.proactive_messages_queue USING btree (id);

CREATE INDEX proactive_messages_queue_user_idx ON public.proactive_messages_queue USING btree (user_id);

CREATE INDEX project_events_clientref_idx ON public.project_events USING btree (user_id, project_client_ref) WHERE (project_id IS NULL);

CREATE UNIQUE INDEX project_events_pkey ON public.project_events USING btree (id);

CREATE UNIQUE INDEX projects_pkey ON public.projects USING btree (id);

CREATE UNIQUE INDEX projects_user_client_ref_uq ON public.projects USING btree (user_id, client_ref);

CREATE UNIQUE INDEX projects_user_client_ref_ux ON public.projects USING btree (user_id, client_ref) WHERE (client_ref IS NOT NULL);

CREATE UNIQUE INDEX push_devices_expo_push_token_unique ON public.push_devices USING btree (expo_push_token);

CREATE UNIQUE INDEX push_devices_expo_push_token_uq ON public.push_devices USING btree (expo_push_token) WHERE (expo_push_token IS NOT NULL);

CREATE UNIQUE INDEX push_devices_pkey ON public.push_devices USING btree (id);

CREATE INDEX push_devices_token_idx ON public.push_devices USING btree (expo_push_token);

CREATE UNIQUE INDEX push_devices_user_device_uniq ON public.push_devices USING btree (user_id, device_id);

CREATE INDEX push_devices_user_idx ON public.push_devices USING btree (user_id);

CREATE UNIQUE INDEX push_outbox_pkey ON public.push_outbox USING btree (id);

CREATE INDEX push_outbox_status_idx ON public.push_outbox USING btree (status, scheduled_at);

CREATE INDEX push_outbox_user_idx ON public.push_outbox USING btree (user_id, created_at DESC);

CREATE INDEX push_outbox_user_status_idx ON public.push_outbox USING btree (user_id, status, created_at);

CREATE INDEX referrals_code_idx ON public.referrals USING btree (code);

CREATE UNIQUE INDEX referrals_pkey ON public.referrals USING btree (id);

CREATE UNIQUE INDEX referrals_referred_unique_idx ON public.referrals USING btree (referred_user_id);

CREATE INDEX referrals_referrer_idx ON public.referrals USING btree (referrer_user_id);

CREATE INDEX referrals_referrer_l2_idx ON public.referrals USING btree (referrer_user_id_l2);

CREATE INDEX referrals_referrer_l3_idx ON public.referrals USING btree (referrer_user_id_l3);

CREATE UNIQUE INDEX uq_lisa_integrations_catalog_integration_key ON public.lisa_integrations_catalog USING btree (integration_key);

CREATE UNIQUE INDEX user_activities_pkey ON public.user_activities USING btree (user_id);

CREATE UNIQUE INDEX user_activities_user_id_unique ON public.user_activities USING btree (user_id);

CREATE UNIQUE INDEX user_activities_user_uq ON public.user_activities USING btree (user_id);

CREATE UNIQUE INDEX user_automations_pkey ON public.user_automations USING btree (id);

CREATE INDEX user_companies_company_idx ON public.user_companies USING btree (company_id);

CREATE UNIQUE INDEX user_companies_pkey ON public.user_companies USING btree (id);

CREATE UNIQUE INDEX user_companies_user_company_unique ON public.user_companies USING btree (user_id, company_id, relation) WHERE (ended_at IS NULL);

CREATE UNIQUE INDEX user_daily_life_signals_pkey ON public.user_daily_life_signals USING btree (id);

CREATE UNIQUE INDEX user_daily_life_signals_user_day_unique ON public.user_daily_life_signals USING btree (user_id, day_key);

CREATE UNIQUE INDEX user_facts_pkey ON public.user_facts USING btree (id);

CREATE INDEX user_facts_user_category_idx ON public.user_facts USING btree (user_id, category);

CREATE UNIQUE INDEX user_facts_user_factkey_uniq ON public.user_facts USING btree (user_id, fact_key);

CREATE UNIQUE INDEX user_facts_user_id_fact_key_unique ON public.user_facts USING btree (user_id, fact_key);

CREATE UNIQUE INDEX user_facts_user_id_fact_key_uq ON public.user_facts USING btree (user_id, fact_key);

CREATE INDEX user_facts_user_key_active_idx ON public.user_facts USING btree (user_id, fact_key, is_active);

CREATE INDEX user_facts_value_json_gin_idx ON public.user_facts USING gin (value);

CREATE UNIQUE INDEX user_financial_profile_pkey ON public.user_financial_profile USING btree (id);

CREATE UNIQUE INDEX user_financial_profile_user_id_key ON public.user_financial_profile USING btree (user_id);

CREATE UNIQUE INDEX user_key_events_pkey ON public.user_key_events USING btree (id);

CREATE UNIQUE INDEX user_settings_pkey ON public.user_settings USING btree (id);

CREATE UNIQUE INDEX user_settings_user_id_key ON public.user_settings USING btree (user_id);

CREATE UNIQUE INDEX userfacts_daily_queue_pkey ON public.userfacts_daily_queue USING btree (id);

CREATE UNIQUE INDEX users_account_email_key ON public.users USING btree (account_email);

CREATE UNIQUE INDEX users_affiliate_code_key ON public.users USING btree (affiliate_code) WHERE (affiliate_code IS NOT NULL);

CREATE UNIQUE INDEX users_auth_user_id_key ON public.users USING btree (auth_user_id) WHERE (auth_user_id IS NOT NULL);

CREATE UNIQUE INDEX users_auth_user_id_unique ON public.users USING btree (auth_user_id);

CREATE INDEX users_deleted_at_idx ON public.users USING btree (deleted_at);

CREATE UNIQUE INDEX users_pkey ON public.users USING btree (id);

CREATE UNIQUE INDEX ux_userfacts_daily_queue_dedupe ON public.userfacts_daily_queue USING btree (dedupe_key);

alter table "public"."affiliate_codes" add constraint "affiliate_codes_pkey" PRIMARY KEY using index "affiliate_codes_pkey";

alter table "public"."affiliate_commissions" add constraint "affiliate_commissions_pkey" PRIMARY KEY using index "affiliate_commissions_pkey";

alter table "public"."affiliates" add constraint "affiliates_pkey" PRIMARY KEY using index "affiliates_pkey";

alter table "public"."app_config" add constraint "app_config_pkey" PRIMARY KEY using index "app_config_pkey";

alter table "public"."automation_templates" add constraint "automation_templates_pkey" PRIMARY KEY using index "automation_templates_pkey";

alter table "public"."billing_events" add constraint "billing_events_pkey" PRIMARY KEY using index "billing_events_pkey";

alter table "public"."companies" add constraint "companies_pkey" PRIMARY KEY using index "companies_pkey";

alter table "public"."conversation_messages" add constraint "conversation_messages_pkey" PRIMARY KEY using index "conversation_messages_pkey";

alter table "public"."conversations" add constraint "conversations_pkey" PRIMARY KEY using index "conversations_pkey";

alter table "public"."debug_auth_user_created_log" add constraint "debug_auth_user_created_log_pkey" PRIMARY KEY using index "debug_auth_user_created_log_pkey";

alter table "public"."email_accounts" add constraint "email_accounts_pkey" PRIMARY KEY using index "email_accounts_pkey";

alter table "public"."fact_key_registry" add constraint "fact_key_registry_pkey" PRIMARY KEY using index "fact_key_registry_pkey";

alter table "public"."fact_profile_mappings" add constraint "fact_profile_mappings_pkey" PRIMARY KEY using index "fact_profile_mappings_pkey";

alter table "public"."gmail_watch_subscriptions" add constraint "gmail_watch_subscriptions_pkey" PRIMARY KEY using index "gmail_watch_subscriptions_pkey";

alter table "public"."heylisa_post_checkout_contexts" add constraint "heylisa_post_checkout_contexts_pkey" PRIMARY KEY using index "heylisa_post_checkout_contexts_pkey";

alter table "public"."lisa_actions_catalog" add constraint "lisa_actions_catalog_pkey" PRIMARY KEY using index "lisa_actions_catalog_pkey";

alter table "public"."lisa_agent_integrations" add constraint "lisa_agent_integrations_pkey" PRIMARY KEY using index "lisa_agent_integrations_pkey";

alter table "public"."lisa_agents_catalog" add constraint "lisa_agents_catalog_pkey" PRIMARY KEY using index "lisa_agents_catalog_pkey";

alter table "public"."lisa_brains" add constraint "lisa_brains_pkey" PRIMARY KEY using index "lisa_brains_pkey";

alter table "public"."lisa_concierge_suggestions" add constraint "lisa_concierge_suggestions_pkey" PRIMARY KEY using index "lisa_concierge_suggestions_pkey";

alter table "public"."lisa_dashboard_weekly_kpis" add constraint "lisa_dashboard_weekly_kpis_pkey" PRIMARY KEY using index "lisa_dashboard_weekly_kpis_pkey";

alter table "public"."lisa_integrations_catalog" add constraint "lisa_integrations_catalog_pkey" PRIMARY KEY using index "lisa_integrations_catalog_pkey";

alter table "public"."lisa_priority_emails" add constraint "lisa_priority_emails_pkey" PRIMARY KEY using index "lisa_priority_emails_pkey";

alter table "public"."lisa_service_docs" add constraint "lisa_service_docs_pkey" PRIMARY KEY using index "lisa_service_docs_pkey";

alter table "public"."lisa_tasks" add constraint "lisa_tasks_pkey" PRIMARY KEY using index "lisa_tasks_pkey";

alter table "public"."lisa_user_agent_settings_gmail" add constraint "lisa_user_agent_settings_gmail_pkey" PRIMARY KEY using index "lisa_user_agent_settings_gmail_pkey";

alter table "public"."lisa_user_agents" add constraint "lisa_user_agents_pkey" PRIMARY KEY using index "lisa_user_agents_pkey";

alter table "public"."lisa_user_integrations" add constraint "lisa_user_integrations_pkey" PRIMARY KEY using index "lisa_user_integrations_pkey";

alter table "public"."lisa_user_monthly_memory" add constraint "lisa_user_monthly_memory_pkey" PRIMARY KEY using index "lisa_user_monthly_memory_pkey";

alter table "public"."proactive_events_outbox" add constraint "proactive_events_outbox_pkey" PRIMARY KEY using index "proactive_events_outbox_pkey";

alter table "public"."proactive_messages_queue" add constraint "proactive_messages_queue_pkey" PRIMARY KEY using index "proactive_messages_queue_pkey";

alter table "public"."project_events" add constraint "project_events_pkey" PRIMARY KEY using index "project_events_pkey";

alter table "public"."projects" add constraint "projects_pkey" PRIMARY KEY using index "projects_pkey";

alter table "public"."push_devices" add constraint "push_devices_pkey" PRIMARY KEY using index "push_devices_pkey";

alter table "public"."push_outbox" add constraint "push_outbox_pkey" PRIMARY KEY using index "push_outbox_pkey";

alter table "public"."referrals" add constraint "referrals_pkey" PRIMARY KEY using index "referrals_pkey";

alter table "public"."user_activities" add constraint "user_activities_pkey" PRIMARY KEY using index "user_activities_pkey";

alter table "public"."user_automations" add constraint "user_automations_pkey" PRIMARY KEY using index "user_automations_pkey";

alter table "public"."user_companies" add constraint "user_companies_pkey" PRIMARY KEY using index "user_companies_pkey";

alter table "public"."user_daily_life_signals" add constraint "user_daily_life_signals_pkey" PRIMARY KEY using index "user_daily_life_signals_pkey";

alter table "public"."user_facts" add constraint "user_facts_pkey" PRIMARY KEY using index "user_facts_pkey";

alter table "public"."user_financial_profile" add constraint "user_financial_profile_pkey" PRIMARY KEY using index "user_financial_profile_pkey";

alter table "public"."user_key_events" add constraint "user_key_events_pkey" PRIMARY KEY using index "user_key_events_pkey";

alter table "public"."user_settings" add constraint "user_settings_pkey" PRIMARY KEY using index "user_settings_pkey";

alter table "public"."userfacts_daily_queue" add constraint "userfacts_daily_queue_pkey" PRIMARY KEY using index "userfacts_daily_queue_pkey";

alter table "public"."users" add constraint "users_pkey" PRIMARY KEY using index "users_pkey";

alter table "public"."affiliate_codes" add constraint "affiliate_codes_code_key" UNIQUE using index "affiliate_codes_code_key";

alter table "public"."affiliate_codes" add constraint "affiliate_codes_code_unique" UNIQUE using index "affiliate_codes_code_unique";

alter table "public"."affiliate_codes" add constraint "affiliate_codes_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."affiliate_codes" validate constraint "affiliate_codes_user_id_fkey";

alter table "public"."affiliate_codes" add constraint "affiliate_codes_user_unique" UNIQUE using index "affiliate_codes_user_unique";

alter table "public"."affiliate_commissions" add constraint "affiliate_commissions_affiliate_id_fkey" FOREIGN KEY (affiliate_id) REFERENCES public.affiliates(id) ON DELETE CASCADE not valid;

alter table "public"."affiliate_commissions" validate constraint "affiliate_commissions_affiliate_id_fkey";

alter table "public"."affiliates" add constraint "affiliates_email_key" UNIQUE using index "affiliates_email_key";

alter table "public"."automation_templates" add constraint "automation_templates_slug_key" UNIQUE using index "automation_templates_slug_key";

alter table "public"."billing_events" add constraint "billing_events_dedupe_key_uq" UNIQUE using index "billing_events_dedupe_key_uq";

alter table "public"."conversation_messages" add constraint "conversation_messages_conversation_id_fkey" FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE not valid;

alter table "public"."conversation_messages" validate constraint "conversation_messages_conversation_id_fkey";

alter table "public"."conversation_messages" add constraint "conversation_messages_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."conversation_messages" validate constraint "conversation_messages_user_id_fkey";

alter table "public"."conversation_messages" add constraint "messages_conversation_fk" FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE not valid;

alter table "public"."conversation_messages" validate constraint "messages_conversation_fk";

alter table "public"."conversations" add constraint "conversations_user_fk" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."conversations" validate constraint "conversations_user_fk";

alter table "public"."conversations" add constraint "conversations_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."conversations" validate constraint "conversations_user_id_fkey";

alter table "public"."conversations" add constraint "conversations_user_id_unique" UNIQUE using index "conversations_user_id_unique";

alter table "public"."email_accounts" add constraint "email_accounts_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."email_accounts" validate constraint "email_accounts_user_id_fkey";

alter table "public"."fact_profile_mappings" add constraint "fact_profile_mappings_fact_key_fkey" FOREIGN KEY (fact_key) REFERENCES public.fact_key_registry(fact_key) ON DELETE CASCADE not valid;

alter table "public"."fact_profile_mappings" validate constraint "fact_profile_mappings_fact_key_fkey";

alter table "public"."fact_profile_mappings" add constraint "fact_profile_mappings_fact_key_target_table_target_column_key" UNIQUE using index "fact_profile_mappings_fact_key_target_table_target_column_key";

alter table "public"."gmail_watch_subscriptions" add constraint "gmail_watch_sub_unique_user_email" UNIQUE using index "gmail_watch_sub_unique_user_email";

alter table "public"."gmail_watch_subscriptions" add constraint "gmail_watch_subscriptions_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."gmail_watch_subscriptions" validate constraint "gmail_watch_subscriptions_user_id_fkey";

alter table "public"."heylisa_post_checkout_contexts" add constraint "heylisa_post_checkout_contexts_session_id_key" UNIQUE using index "heylisa_post_checkout_contexts_session_id_key";

alter table "public"."heylisa_post_checkout_contexts" add constraint "heylisa_post_checkout_contexts_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."heylisa_post_checkout_contexts" validate constraint "heylisa_post_checkout_contexts_user_id_fkey";

alter table "public"."lisa_actions_catalog" add constraint "lisa_actions_catalog_status_check" CHECK ((status = ANY (ARRAY['active'::text, 'disabled'::text]))) not valid;

alter table "public"."lisa_actions_catalog" validate constraint "lisa_actions_catalog_status_check";

alter table "public"."lisa_agent_integrations" add constraint "lisa_agent_integrations_agent_key_fkey" FOREIGN KEY (agent_key) REFERENCES public.lisa_agents_catalog(agent_key) ON DELETE CASCADE not valid;

alter table "public"."lisa_agent_integrations" validate constraint "lisa_agent_integrations_agent_key_fkey";

alter table "public"."lisa_agent_integrations" add constraint "lisa_agent_integrations_integration_key_fkey" FOREIGN KEY (integration_key) REFERENCES public.lisa_integrations_catalog(integration_key) ON DELETE RESTRICT not valid;

alter table "public"."lisa_agent_integrations" validate constraint "lisa_agent_integrations_integration_key_fkey";

alter table "public"."lisa_concierge_suggestions" add constraint "lisa_concierge_suggestions_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."lisa_concierge_suggestions" validate constraint "lisa_concierge_suggestions_user_id_fkey";

alter table "public"."lisa_dashboard_weekly_kpis" add constraint "lisa_dashboard_weekly_kpis_uid_week_key_unique" UNIQUE using index "lisa_dashboard_weekly_kpis_uid_week_key_unique";

alter table "public"."lisa_tasks" add constraint "lisa_tasks_project_id_fkey" FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL not valid;

alter table "public"."lisa_tasks" validate constraint "lisa_tasks_project_id_fkey";

alter table "public"."lisa_tasks" add constraint "lisa_tasks_user_id_dedupe_key_uniq" UNIQUE using index "lisa_tasks_user_id_dedupe_key_uniq";

alter table "public"."lisa_tasks" add constraint "lisa_tasks_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."lisa_tasks" validate constraint "lisa_tasks_user_id_fkey";

alter table "public"."lisa_user_agent_settings_gmail" add constraint "lisa_user_agent_settings_gmail_agent_id_fkey" FOREIGN KEY (agent_id) REFERENCES public.lisa_user_agents(id) ON DELETE CASCADE not valid;

alter table "public"."lisa_user_agent_settings_gmail" validate constraint "lisa_user_agent_settings_gmail_agent_id_fkey";

alter table "public"."lisa_user_agent_settings_gmail" add constraint "lisa_user_agent_settings_gmail_agent_id_key" UNIQUE using index "lisa_user_agent_settings_gmail_agent_id_key";

alter table "public"."lisa_user_agent_settings_gmail" add constraint "lisa_user_agent_settings_gmail_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."lisa_user_agent_settings_gmail" validate constraint "lisa_user_agent_settings_gmail_user_id_fkey";

alter table "public"."lisa_user_agents" add constraint "lisa_user_agents_onboarding_status_check" CHECK (((onboarding_status IS NULL) OR (onboarding_status = ANY (ARRAY['pending'::text, 'started'::text, 'complete'::text, 'aborted'::text])))) not valid;

alter table "public"."lisa_user_agents" validate constraint "lisa_user_agents_onboarding_status_check";

alter table "public"."lisa_user_agents" add constraint "lisa_user_agents_user_agent_key_unique" UNIQUE using index "lisa_user_agents_user_agent_key_unique";

alter table "public"."lisa_user_agents" add constraint "lisa_user_agents_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."lisa_user_agents" validate constraint "lisa_user_agents_user_id_fkey";

alter table "public"."lisa_user_integrations" add constraint "lisa_user_integrations_integration_key_fkey" FOREIGN KEY (integration_key) REFERENCES public.lisa_integrations_catalog(integration_key) ON DELETE RESTRICT not valid;

alter table "public"."lisa_user_integrations" validate constraint "lisa_user_integrations_integration_key_fkey";

alter table "public"."lisa_user_monthly_memory" add constraint "lisa_user_monthly_memory_unique" UNIQUE using index "lisa_user_monthly_memory_unique";

alter table "public"."lisa_user_monthly_memory" add constraint "lisa_user_monthly_memory_user_month_uniq" UNIQUE using index "lisa_user_monthly_memory_user_month_uniq";

alter table "public"."proactive_events_outbox" add constraint "proactive_events_outbox_event_type_check" CHECK ((event_type = ANY (ARRAY['TECH_ISSUE'::text, 'TASK_CREATED'::text, 'INACTIVITY_48H'::text]))) not valid;

alter table "public"."proactive_events_outbox" validate constraint "proactive_events_outbox_event_type_check";

alter table "public"."proactive_messages_queue" add constraint "proactive_messages_queue_status_check" CHECK ((status = ANY (ARRAY['scheduled'::text, 'ready'::text, 'sent'::text, 'canceled'::text]))) not valid;

alter table "public"."proactive_messages_queue" validate constraint "proactive_messages_queue_status_check";

alter table "public"."project_events" add constraint "project_events_project_id_fkey" FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE not valid;

alter table "public"."project_events" validate constraint "project_events_project_id_fkey";

alter table "public"."project_events" add constraint "project_events_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."project_events" validate constraint "project_events_user_id_fkey";

alter table "public"."projects" add constraint "projects_main_company_id_fkey" FOREIGN KEY (main_company_id) REFERENCES public.companies(id) ON DELETE SET NULL not valid;

alter table "public"."projects" validate constraint "projects_main_company_id_fkey";

alter table "public"."projects" add constraint "projects_parent_project_id_fkey" FOREIGN KEY (parent_project_id) REFERENCES public.projects(id) ON DELETE SET NULL not valid;

alter table "public"."projects" validate constraint "projects_parent_project_id_fkey";

alter table "public"."projects" add constraint "projects_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."projects" validate constraint "projects_user_id_fkey";

alter table "public"."push_devices" add constraint "push_devices_expo_push_token_unique" UNIQUE using index "push_devices_expo_push_token_unique";

alter table "public"."push_devices" add constraint "push_devices_platform_check" CHECK ((platform = ANY (ARRAY['ios'::text, 'android'::text]))) not valid;

alter table "public"."push_devices" validate constraint "push_devices_platform_check";

alter table "public"."push_devices" add constraint "push_devices_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."push_devices" validate constraint "push_devices_user_id_fkey";

alter table "public"."push_outbox" add constraint "push_outbox_kind_check" CHECK ((kind = ANY (ARRAY['chat'::text, 'system'::text]))) not valid;

alter table "public"."push_outbox" validate constraint "push_outbox_kind_check";

alter table "public"."push_outbox" add constraint "push_outbox_status_check" CHECK ((status = ANY (ARRAY['queued'::text, 'sent'::text, 'failed'::text]))) not valid;

alter table "public"."push_outbox" validate constraint "push_outbox_status_check";

alter table "public"."push_outbox" add constraint "push_outbox_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."push_outbox" validate constraint "push_outbox_user_id_fkey";

alter table "public"."referrals" add constraint "referrals_referred_user_id_fkey" FOREIGN KEY (referred_user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."referrals" validate constraint "referrals_referred_user_id_fkey";

alter table "public"."referrals" add constraint "referrals_referrer_user_id_fkey" FOREIGN KEY (referrer_user_id) REFERENCES public.users(id) ON DELETE RESTRICT not valid;

alter table "public"."referrals" validate constraint "referrals_referrer_user_id_fkey";

alter table "public"."referrals" add constraint "referrals_referrer_user_id_l2_fkey" FOREIGN KEY (referrer_user_id_l2) REFERENCES public.users(id) ON DELETE RESTRICT not valid;

alter table "public"."referrals" validate constraint "referrals_referrer_user_id_l2_fkey";

alter table "public"."referrals" add constraint "referrals_referrer_user_id_l3_fkey" FOREIGN KEY (referrer_user_id_l3) REFERENCES public.users(id) ON DELETE RESTRICT not valid;

alter table "public"."referrals" validate constraint "referrals_referrer_user_id_l3_fkey";

alter table "public"."user_activities" add constraint "user_activities_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."user_activities" validate constraint "user_activities_user_id_fkey";

alter table "public"."user_activities" add constraint "user_activities_user_id_unique" UNIQUE using index "user_activities_user_id_unique";

alter table "public"."user_automations" add constraint "user_automations_project_id_fkey" FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL not valid;

alter table "public"."user_automations" validate constraint "user_automations_project_id_fkey";

alter table "public"."user_automations" add constraint "user_automations_template_id_fkey" FOREIGN KEY (template_id) REFERENCES public.automation_templates(id) ON DELETE SET NULL not valid;

alter table "public"."user_automations" validate constraint "user_automations_template_id_fkey";

alter table "public"."user_automations" add constraint "user_automations_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."user_automations" validate constraint "user_automations_user_id_fkey";

alter table "public"."user_companies" add constraint "user_companies_company_id_fkey" FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE not valid;

alter table "public"."user_companies" validate constraint "user_companies_company_id_fkey";

alter table "public"."user_companies" add constraint "user_companies_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."user_companies" validate constraint "user_companies_user_id_fkey";

alter table "public"."user_daily_life_signals" add constraint "user_daily_life_signals_user_day_unique" UNIQUE using index "user_daily_life_signals_user_day_unique";

alter table "public"."user_daily_life_signals" add constraint "user_daily_life_signals_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."user_daily_life_signals" validate constraint "user_daily_life_signals_user_id_fkey";

alter table "public"."user_facts" add constraint "user_facts_user_factkey_uniq" UNIQUE using index "user_facts_user_factkey_uniq";

alter table "public"."user_facts" add constraint "user_facts_user_id_fact_key_unique" UNIQUE using index "user_facts_user_id_fact_key_unique";

alter table "public"."user_facts" add constraint "user_facts_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."user_facts" validate constraint "user_facts_user_id_fkey";

alter table "public"."user_financial_profile" add constraint "user_financial_profile_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."user_financial_profile" validate constraint "user_financial_profile_user_id_fkey";

alter table "public"."user_financial_profile" add constraint "user_financial_profile_user_id_key" UNIQUE using index "user_financial_profile_user_id_key";

alter table "public"."user_key_events" add constraint "user_key_events_related_project_id_fkey" FOREIGN KEY (related_project_id) REFERENCES public.projects(id) not valid;

alter table "public"."user_key_events" validate constraint "user_key_events_related_project_id_fkey";

alter table "public"."user_key_events" add constraint "user_key_events_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."user_key_events" validate constraint "user_key_events_user_id_fkey";

alter table "public"."user_settings" add constraint "user_settings_user_id_fkey" FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE not valid;

alter table "public"."user_settings" validate constraint "user_settings_user_id_fkey";

alter table "public"."user_settings" add constraint "user_settings_user_id_key" UNIQUE using index "user_settings_user_id_key";

alter table "public"."users" add constraint "users_account_email_key" UNIQUE using index "users_account_email_key";

alter table "public"."users" add constraint "users_auth_user_id_fkey" FOREIGN KEY (auth_user_id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."users" validate constraint "users_auth_user_id_fkey";

alter table "public"."users" add constraint "users_primary_company_fk" FOREIGN KEY (primary_company_id) REFERENCES public.companies(id) ON DELETE SET NULL not valid;

alter table "public"."users" validate constraint "users_primary_company_fk";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.apply_paywall_time_expired(p_trial_days integer DEFAULT 14)
 RETURNS TABLE(updated_count integer, updated_user_ids uuid[])
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.call_n8n_webhook(p_path text, p_payload jsonb, p_timeout_ms integer DEFAULT 5000)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  url text;
  headers jsonb;
  params jsonb;
  _request_id bigint;
begin
  url := public.n8n_webhook_url(p_path);

  headers := jsonb_build_object('Content-Type', 'application/json');
  params := '{}'::jsonb;

  -- Fire-and-forget via pg_net (async)
  _request_id := net.http_post(
    url,
    coalesce(p_payload, '{}'::jsonb),
    params,
    headers,
    p_timeout_ms
  );

exception when others then
  -- NE BLOQUE JAMAIS la transaction appelante (achat)
  raise notice 'call_n8n_webhook failed: %', sqlerrm;
  return;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.cleanup_stripe_customer_outbox_done()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
begin
  -- Si le statut passe à 'done', on supprime la ligne
  if new.status = 'done' then
    delete from public.stripe_customer_outbox
    where id = new.id;
  end if;

  return null;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.cron_push_dispatcher()
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
declare
  v_url text;
  v_timeout int;
begin
  v_url := public.get_app_config('push_dispatcher_url', null);
  if v_url is null or length(v_url) = 0 then
    raise exception 'push_dispatcher_url missing in app_config';
  end if;

  v_timeout := coalesce(nullif(public.get_app_config('push_dispatcher_timeout_ms',''), '')::int, 1000);

  perform net.http_post(
    url := v_url,
    headers := jsonb_build_object(),
    timeout_milliseconds := v_timeout
  );
end;
$function$
;

CREATE OR REPLACE FUNCTION public.current_user_id()
 RETURNS uuid
 LANGUAGE sql
 STABLE
AS $function$
  select u.id
  from public.users u
  where u.auth_user_id = auth.uid()
  limit 1
$function$
;

CREATE OR REPLACE FUNCTION public.enqueue_push(p_user_id uuid, p_kind text, p_title text, p_body text, p_data jsonb DEFAULT '{}'::jsonb, p_scheduled_at timestamp with time zone DEFAULT NULL::timestamp with time zone, p_tz text DEFAULT 'Europe/Paris'::text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.enqueue_stripe_customer_creation()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.ensure_affiliate(p_user_id uuid, p_email text, p_full_name text, p_country text)
 RETURNS public.affiliates
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.ensure_user_settings_row()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
begin
  insert into public.user_settings (user_id)
  values (new.id)
  on conflict (user_id) do nothing;

  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.fn_activate_personal_assistant_if_pro()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.fn_billing_events_normalize_timestamps()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  if (new.expiration_at is null)
     and (new.payload ? 'event')
     and ((new.payload->'event'->>'expiration_at_ms') is not null) then
    new.expiration_at :=
      to_timestamp( ((new.payload->'event'->>'expiration_at_ms')::bigint) / 1000.0 );
  end if;

  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.fn_billing_events_resolve_user_id()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.fn_pick_active_agent_status()
 RETURNS public.agent_status_enum
 LANGUAGE plpgsql
 STABLE
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.fn_propagate_core_user_facts(p_user_id uuid)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
declare
  v_first_name     text;
  v_full_name      text;
  v_last_name      text;

  v_main_city      text;
  v_locale_main    text;
  v_timezone       text;
  v_country_code   text;

  v_main_activity  text;
  v_act_conf       numeric;
  v_act_notes      text;
  v_act_updated_at timestamptz;

  v_act_conf_si    smallint;
begin
  if p_user_id is null then
    return;
  end if;

  -- Ensure user_settings row exists
  insert into public.user_settings (user_id)
  values (p_user_id)
  on conflict (user_id) do nothing;

  /* ---------------------------
     NAMES (first_name, full_name)
     --------------------------- */

  -- first_name: priorités -> core.preferred_name, first_name
  select
    (
      select
        nullif(
          trim(
            case
              when jsonb_typeof(uf.value) = 'string' then trim(both '"' from uf.value::text)
              when jsonb_typeof(uf.value) = 'object' then coalesce(uf.value->>'value', uf.value->>'text', uf.value->>'name', uf.value->>'first_name')
              else null
            end
          ),
          ''
        )
      from public.user_facts uf
      where uf.user_id = p_user_id
        and uf.is_active = true
        and uf.fact_key in ('core.preferred_name','first_name')
      order by coalesce(uf.updated_at, uf.created_at) desc
      limit 1
    )
  into v_first_name;

  -- full_name: core.full_name, full_name
  select
    (
      select
        nullif(
          trim(
            case
              when jsonb_typeof(uf.value) = 'string' then trim(both '"' from uf.value::text)
              when jsonb_typeof(uf.value) = 'object' then coalesce(uf.value->>'value', uf.value->>'text', uf.value->>'name', uf.value->>'full_name')
              else null
            end
          ),
          ''
        )
      from public.user_facts uf
      where uf.user_id = p_user_id
        and uf.is_active = true
        and uf.fact_key in ('core.full_name','full_name')
      order by coalesce(uf.updated_at, uf.created_at) desc
      limit 1
    )
  into v_full_name;

  -- best-effort last_name: si full_name contient 2 mots, on prend le dernier
  if v_full_name is not null and position(' ' in v_full_name) > 0 then
    v_last_name := nullif(regardless_split_part(v_full_name, ' ', array_length(regexp_split_to_array(v_full_name, '\s+'), 1)), '');
  else
    v_last_name := null;
  end if;

  -- Update users (uniquement si valeurs non vides)
  if v_first_name is not null then
    update public.users
    set first_name = v_first_name
    where id = p_user_id
      and (first_name is null or first_name = '' or first_name is distinct from v_first_name);
  end if;

  if v_full_name is not null then
    update public.users
    set full_name = v_full_name
    where id = p_user_id
      and (full_name is null or full_name = '' or full_name is distinct from v_full_name);
  end if;

  if v_last_name is not null then
    update public.users
    set last_name = v_last_name
    where id = p_user_id
      and (last_name is null or last_name = '' or last_name is distinct from v_last_name);
  end if;

  /* ---------------------------
     Other core fields
     --------------------------- */

  -- main_city
  select
    (
      select
        case
          when jsonb_typeof(uf.value) = 'string' then trim(both '"' from uf.value::text)
          when jsonb_typeof(uf.value) = 'object' then coalesce(uf.value->>'value', uf.value->>'text', uf.value->>'city')
          else null
        end
      from public.user_facts uf
      where uf.user_id = p_user_id
        and uf.is_active = true
        and uf.fact_key in ('context.primary_city','main_city','city_main')
      order by coalesce(uf.updated_at, uf.created_at) desc
      limit 1
    )
  into v_main_city;

  -- locale_main
  select
    (
      select
        case
          when jsonb_typeof(uf.value) = 'string' then trim(both '"' from uf.value::text)
          when jsonb_typeof(uf.value) = 'object' then coalesce(uf.value->>'value', uf.value->>'text', uf.value->>'locale')
          else null
        end
      from public.user_facts uf
      where uf.user_id = p_user_id
        and uf.is_active = true
        and uf.fact_key in ('locale_main','identity.locale_main')
      order by coalesce(uf.updated_at, uf.created_at) desc
      limit 1
    )
  into v_locale_main;

  -- timezone
  select
    (
      select
        case
          when jsonb_typeof(uf.value) = 'string' then trim(both '"' from uf.value::text)
          when jsonb_typeof(uf.value) = 'object' then coalesce(uf.value->>'value', uf.value->>'text', uf.value->>'timezone')
          else null
        end
      from public.user_facts uf
      where uf.user_id = p_user_id
        and uf.is_active = true
        and uf.fact_key in ('timezone','context.timezone')
      order by coalesce(uf.updated_at, uf.created_at) desc
      limit 1
    )
  into v_timezone;

  -- country_code
  select
    (
      select
        upper(
          case
            when jsonb_typeof(uf.value) = 'string' then trim(both '"' from uf.value::text)
            when jsonb_typeof(uf.value) = 'object' then coalesce(uf.value->>'value', uf.value->>'text', uf.value->>'country_code')
            else null
          end
        )
      from public.user_facts uf
      where uf.user_id = p_user_id
        and uf.is_active = true
        and uf.fact_key in ('country_code','context.country_code')
      order by coalesce(uf.updated_at, uf.created_at) desc
      limit 1
    )
  into v_country_code;

  -- main_activity (+ metadata for user_activities)
  select
    (
      select
        case
          when jsonb_typeof(uf.value) = 'string' then trim(both '"' from uf.value::text)
          when jsonb_typeof(uf.value) = 'object' then coalesce(uf.value->>'value', uf.value->>'text', uf.value->>'activity')
          else null
        end
      from public.user_facts uf
      where uf.user_id = p_user_id
        and uf.is_active = true
        and uf.fact_key in ('main_activity','work.main_activity')
      order by coalesce(uf.updated_at, uf.created_at) desc
      limit 1
    ),
    (
      select uf.confidence
      from public.user_facts uf
      where uf.user_id = p_user_id
        and uf.is_active = true
        and uf.fact_key in ('main_activity','work.main_activity')
      order by coalesce(uf.updated_at, uf.created_at) desc
      limit 1
    ),
    (
      select uf.notes
      from public.user_facts uf
      where uf.user_id = p_user_id
        and uf.is_active = true
        and uf.fact_key in ('main_activity','work.main_activity')
      order by coalesce(uf.updated_at, uf.created_at) desc
      limit 1
    ),
    (
      select coalesce(uf.updated_at, uf.created_at)
      from public.user_facts uf
      where uf.user_id = p_user_id
        and uf.is_active = true
        and uf.fact_key in ('main_activity','work.main_activity')
      order by coalesce(uf.updated_at, uf.created_at) desc
      limit 1
    )
  into v_main_activity, v_act_conf, v_act_notes, v_act_updated_at;

  -- Apply to user_settings
  if v_main_city is not null and v_main_city <> '' then
    update public.user_settings
    set main_city = v_main_city, updated_at = now()
    where user_id = p_user_id
      and main_city is distinct from v_main_city;
  end if;

  if v_locale_main is not null and v_locale_main <> '' then
    update public.user_settings
    set locale_main = v_locale_main, updated_at = now()
    where user_id = p_user_id
      and locale_main is distinct from v_locale_main;
  end if;

  if v_timezone is not null and v_timezone <> '' then
    update public.user_settings
    set timezone = v_timezone, updated_at = now()
    where user_id = p_user_id
      and timezone is distinct from v_timezone;
  end if;

  if v_country_code is not null and v_country_code <> '' then
    update public.user_settings
    set country_code = v_country_code, updated_at = now()
    where user_id = p_user_id
      and country_code is distinct from v_country_code;

    update public.users
    set country_code = v_country_code
    where id = p_user_id
      and country_code is distinct from v_country_code;
  end if;

  if v_main_activity is not null and v_main_activity <> '' then
    update public.user_settings
    set main_activity = v_main_activity, updated_at = now()
    where user_id = p_user_id
      and main_activity is distinct from v_main_activity;

    v_act_conf_si := greatest(0, least(100, round(coalesce(v_act_conf, 0.8) * 100)::int))::smallint;

    insert into public.user_activities (
      user_id, main_activity, main_activity_confidence, main_activity_reason,
      last_observed_at, source, source_conversation_id, created_at, updated_at
    )
    values (
      p_user_id, v_main_activity, v_act_conf_si, left(coalesce(v_act_notes,''), 500),
      coalesce(v_act_updated_at, now()), 'user_facts', null, now(), now()
    )
    on conflict (user_id)
    do update set
      main_activity = excluded.main_activity,
      main_activity_confidence = excluded.main_activity_confidence,
      main_activity_reason = excluded.main_activity_reason,
      last_observed_at = excluded.last_observed_at,
      source = excluded.source,
      source_conversation_id = excluded.source_conversation_id,
      updated_at = now();
  end if;

end;
$function$
;

CREATE OR REPLACE FUNCTION public.fn_recompute_user_status(p_user_id uuid)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.fn_refresh_use_tu_form(p_user_id uuid)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.fn_refresh_user_agents_settings(p_user_id uuid)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.fn_revoke_personal_assistant_if_not_pro()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.fn_set_trial_started_at_from_billing_event()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.fn_sync_last_active_at_from_auth()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
    return new; -- pas de user public lié, on sort proprement
  end if;

  update public.user_settings us
  set last_active_at = new.last_sign_in_at,
      updated_at = now()
  where us.user_id = v_public_user_id;

  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.fn_trg_refresh_use_tu_form()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.fn_trg_refresh_user_agents_settings()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
begin
  perform public.fn_refresh_user_agents_settings(coalesce(new.user_id, old.user_id));
  return coalesce(new, old);
end;
$function$
;

CREATE OR REPLACE FUNCTION public.fn_users_set_signup_source_and_status()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'auth'
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.get_app_config(p_key text, p_default text DEFAULT NULL::text)
 RETURNS text
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  return coalesce(
    (select value from public.app_config where key = p_key limit 1),
    p_default
  );
end;
$function$
;

CREATE OR REPLACE FUNCTION public.get_free_quota_state(p_user_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_is_pro boolean;
  v_used int;
  v_limit int;
  v_remaining int;
  v_state text;
BEGIN
  IF p_user_id IS NULL THEN
    RETURN jsonb_build_object(
      'ok', false,
      'error', 'user_id_required'
    );
  END IF;

  -- vérité abonnement = users.is_pro (tu veux surtout pas toucher à ça)
  SELECT u.is_pro
    INTO v_is_pro
  FROM public.users u
  WHERE u.id = p_user_id;

  IF coalesce(v_is_pro, false) = true THEN
    RETURN jsonb_build_object(
      'ok', true,
      'user_id', p_user_id,
      'is_pro', true,
      'state', 'pro',
      'free_quota_used', NULL,
      'free_quota_limit', NULL,
      'free_quota_remaining', NULL
    );
  END IF;

  -- Ensure settings row (au cas où)
  INSERT INTO public.user_settings (user_id)
  VALUES (p_user_id)
  ON CONFLICT (user_id) DO NOTHING;

  SELECT
    coalesce(us.free_quota_used, 0),
    coalesce(us.free_quota_limit, 8)
  INTO v_used, v_limit
  FROM public.user_settings us
  WHERE us.user_id = p_user_id;

  v_remaining := greatest(v_limit - v_used, 0);

  -- State machine
  IF v_used >= v_limit THEN
    v_state := 'blocked';
  ELSIF v_used = (v_limit - 1) THEN
    v_state := 'warn_last_free';
  ELSE
    v_state := 'normal';
  END IF;

  RETURN jsonb_build_object(
    'ok', true,
    'user_id', p_user_id,
    'is_pro', false,
    'state', v_state,
    'free_quota_used', v_used,
    'free_quota_limit', v_limit,
    'free_quota_remaining', v_remaining
  );
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_user_smalltalk_stats(p_user_id uuid)
 RETURNS TABLE(total_user_msgs integer, smalltalk_turns integer, smalltalk_done boolean)
 LANGUAGE sql
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.handle_auth_user_created()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.mark_event_mentioned(event_id uuid)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
  UPDATE user_key_events
  SET 
    last_mentioned_at = NOW(),
    mention_count = mention_count + 1,
    updated_at = NOW()
  WHERE id = event_id;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.n8n_webhook_url(p_path text)
 RETURNS text
 LANGUAGE plpgsql
 STABLE
AS $function$
declare
  base_url text;
  clean_base text;
  clean_path text;
begin
  base_url := public.get_app_config('n8n_webhook_base_url', null);
  if base_url is null or length(trim(base_url)) = 0 then
    raise exception 'Missing app_config.n8n_webhook_base_url';
  end if;

  -- normalisation simple des slashes
  clean_base := regexp_replace(trim(base_url), '/+$', '');
  clean_path := regexp_replace(coalesce(trim(p_path), ''), '^/+', '');

  return clean_base || '/' || clean_path;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.next_allowed_push_time(p_now timestamp with time zone, p_tz text DEFAULT 'Europe/Paris'::text, p_quiet_start integer DEFAULT 22, p_quiet_end integer DEFAULT 6)
 RETURNS timestamp with time zone
 LANGUAGE plpgsql
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.pop_push_outbox(p_limit integer DEFAULT 25)
 RETURNS SETOF public.push_outbox
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.proactive_enqueue_inactivity_events(p_hours integer DEFAULT 48, p_limit integer DEFAULT 200)
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.proactive_mark_ready_due_messages(p_limit integer DEFAULT 50)
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.propagate_affiliate_code_to_users()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  IF NEW.auth_user_id IS NOT NULL AND NEW.code IS NOT NULL THEN
    UPDATE public.users
    SET affiliate_code = NEW.code
    WHERE auth_user_id = NEW.auth_user_id
      AND (affiliate_code IS NULL OR affiliate_code = '');
  END IF;

  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.propagate_use_tu_form_from_user_facts()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.refresh_user_settings_job_industry(p_user_id uuid)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
declare
  v_job_title   text;
  v_industry    text;
  v_work_status text;
  v_life_stage  text;

  v_main_activity text;
begin
  /*
    1) Facts propres
  */

  -- job_title (jsonb text ou string)
  select
    coalesce(
      uf.value->>'value',
      uf.value->>'text',
      trim(both '"' from uf.value::text)
    )
  into v_job_title
  from public.user_facts uf
  where uf.user_id = p_user_id
    and uf.fact_key = 'job_title'
    and uf.value_type = 'text'
    and uf.is_active = true
    and uf.value is not null
  order by uf.updated_at desc nulls last
  limit 1;

  -- industry
  select
    coalesce(
      uf.value->>'value',
      uf.value->>'text',
      trim(both '"' from uf.value::text)
    )
  into v_industry
  from public.user_facts uf
  where uf.user_id = p_user_id
    and uf.fact_key = 'industry'
    and uf.value_type = 'text'
    and uf.is_active = true
    and uf.value is not null
  order by uf.updated_at desc nulls last
  limit 1;

  /*
    2) Fallback job_title via work_status / life_stage (ton code existant)
  */
  if v_job_title is null or v_job_title = '' then
    select
      coalesce(
        uf.value->>'value',
        uf.value->>'text',
        trim(both '"' from uf.value::text)
      )
    into v_work_status
    from public.user_facts uf
    where uf.user_id = p_user_id
      and uf.fact_key = 'work_status'
      and uf.value_type = 'text'
      and uf.is_active = true
      and uf.value is not null
    order by uf.updated_at desc nulls last
    limit 1;

    if v_work_status is not null and v_work_status <> '' then
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

  if v_job_title is null or v_job_title = '' then
    select
      coalesce(
        uf.value->>'value',
        uf.value->>'text',
        trim(both '"' from uf.value::text)
      )
    into v_life_stage
    from public.user_facts uf
    where uf.user_id = p_user_id
      and uf.fact_key = 'life_stage'
      and uf.value_type = 'text'
      and uf.is_active = true
      and uf.value is not null
    order by uf.updated_at desc nulls last
    limit 1;

    if v_life_stage is not null and v_life_stage <> '' then
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
    3) ✅ main_activity = job_title (prioritaire), sinon industry
  */
  v_main_activity := nullif(trim(coalesce(v_job_title, '')), '');
  if v_main_activity is null then
    v_main_activity := nullif(trim(coalesce(v_industry, '')), '');
  end if;

  /*
    4) Update user_settings (si changement)
  */
  update public.user_settings us
  set
    job_title      = v_job_title,
    industry       = v_industry,
    main_activity  = v_main_activity,
    updated_at     = now()
  where us.user_id = p_user_id
    and (
      us.job_title     is distinct from v_job_title
      or us.industry   is distinct from v_industry
      or us.main_activity is distinct from v_main_activity
    );

end;
$function$
;

CREATE OR REPLACE FUNCTION public.regardless_split_part(p_text text, p_delim text, p_pos integer)
 RETURNS text
 LANGUAGE sql
 IMMUTABLE
AS $function$
  select (regexp_split_to_array(coalesce(p_text,''), '\s+'))[greatest(1, p_pos)];
$function$
;

CREATE OR REPLACE FUNCTION public.run_paywall_engagement()
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$declare
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
end;$function$
;

CREATE OR REPLACE FUNCTION public.run_paywall_time_expired(p_days integer DEFAULT 14)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.save_welcome_message(p_conversation_id uuid, p_content text, p_first_name text DEFAULT NULL::text)
 RETURNS TABLE(id uuid, sent_at timestamp with time zone)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.set_automation_templates_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  new.updated_at = now();
  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.set_plan_automation_pricing_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  new.updated_at = now();
  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.set_proactive_messages_queue_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  new.updated_at = now();
  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.set_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  new.updated_at = now();
  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.set_user_automations_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  new.updated_at = now();
  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.should_send_push(p_user_id uuid, p_kind text)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.sync_user_settings_last_message_at()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.tg_set_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  new.updated_at = now();
  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.track_doc_usage(doc_id uuid)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
  UPDATE lisa_service_docs
  SET 
    usage_count = usage_count + 1,
    last_used_at = NOW()
  WHERE id = doc_id;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.trg_billing_events_recompute_user_status()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  if new.user_id is not null and new.provider = 'revenuecat' then
    perform public.fn_recompute_user_status(new.user_id);
  end if;
  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.trg_conversation_message_enqueue_push()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.trg_increment_free_quota_used()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
  v_user_id uuid;
  v_is_pro boolean;
BEGIN
  -- 1) On ne compte QUE les messages user
  IF new.sender_type <> 'user' THEN
    RETURN new;
  END IF;

  -- 2) Résolution user_id
  v_user_id := new.user_id;

  IF v_user_id IS NULL THEN
    SELECT c.user_id
      INTO v_user_id
    FROM public.conversations c
    WHERE c.id = new.conversation_id;

    IF v_user_id IS NULL THEN
      RETURN new;
    END IF;
  END IF;

  -- 3) Vérifier statut Pro (vérité DB)
  SELECT u.is_pro
    INTO v_is_pro
  FROM public.users u
  WHERE u.id = v_user_id;

  IF coalesce(v_is_pro, false) = true THEN
    RETURN new;
  END IF;

  -- 4) Ensure user_settings existe
  INSERT INTO public.user_settings (user_id)
  VALUES (v_user_id)
  ON CONFLICT (user_id) DO NOTHING;

  -- 5) Incrément du quota avec plafond
  UPDATE public.user_settings us
  SET
    free_quota_used = LEAST(coalesce(us.free_quota_used, 0) + 1, coalesce(us.free_quota_limit, 8)),
    updated_at = now()
  WHERE us.user_id = v_user_id;

  RETURN new;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.trg_lisa_user_agents_onboarding_start()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  begin
    perform public.call_n8n_webhook(
      'onboarding-start',
      jsonb_build_object(
        'table', TG_TABLE_NAME,
        'op', TG_OP,
        'new', to_jsonb(NEW),
        'old', case when TG_OP = 'UPDATE' then to_jsonb(OLD) else null end
      ),
      5000
    );
  exception when others then
    -- NE BLOQUE JAMAIS
    raise notice 'onboarding_start trigger failed: %', sqlerrm;
  end;

  return NEW;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.trg_outbox_on_lisa_tech_issue()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.trg_outbox_on_task_created()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.trg_refresh_user_settings_job_industry()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
begin
  perform public.refresh_user_settings_job_industry(coalesce(new.user_id, old.user_id));
  return coalesce(new, old);
end;
$function$
;

CREATE OR REPLACE FUNCTION public.trg_user_facts_propagate_core()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
declare
  v_user_id uuid;
  v_key text;
begin
  v_user_id := coalesce(new.user_id, old.user_id);
  v_key := coalesce(new.fact_key, old.fact_key);

  if v_user_id is null then
    return coalesce(new, old);
  end if;

  if v_key in (
    -- names
    'core.preferred_name','core.full_name','first_name','full_name',
    -- location / locale / tz / country
    'context.primary_city','main_city','city_main',
    'locale_main','identity.locale_main',
    'timezone','context.timezone',
    'country_code','context.country_code',
    -- activity
    'main_activity','work.main_activity'
  ) then
    perform public.fn_propagate_core_user_facts(v_user_id);
  end if;

  return coalesce(new, old);
end;
$function$
;

CREATE OR REPLACE FUNCTION public.trg_users_recompute_status()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  perform public.fn_recompute_user_status(new.id);
  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.update_intro_smalltalk_state()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
declare
  v_user_id uuid;
  v_planned_turns int := 8; -- ajuste si besoin
begin
  -- 1) uniquement messages USER
  if new.sender_type <> 'user' then
    return new;
  end if;

  -- 2) resolve user_id
  v_user_id := new.user_id;
  if v_user_id is null then
    select c.user_id into v_user_id
    from public.conversations c
    where c.id = new.conversation_id;

    if v_user_id is null then
      return new;
    end if;
  end if;

  -- 3) ensure user_settings
  insert into public.user_settings (user_id)
  values (v_user_id)
  on conflict (user_id) do nothing;

  -- 4) update smalltalk state (ET RIEN D'AUTRE)
  update public.user_settings us
  set
    intro_smalltalk_turns = least(coalesce(us.intro_smalltalk_turns, 0) + 1, v_planned_turns),
    intro_smalltalk_done  = case
      when coalesce(us.intro_smalltalk_done, false) = true then true
      when (coalesce(us.intro_smalltalk_turns, 0) + 1) >= v_planned_turns then true
      else false
    end,
    updated_at = now()
  where us.user_id = v_user_id;

  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.update_lisa_service_docs_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_profiling_completion()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
  total_core_facts INT;
  user_core_facts_count INT;
  completion_pct NUMERIC;
  new_level TEXT;
BEGIN
  -- total core
  SELECT COUNT(*) INTO total_core_facts
  FROM public.fact_key_registry
  WHERE status = 'core';

  -- core facts user
  SELECT COUNT(DISTINCT fact_key) INTO user_core_facts_count
  FROM public.user_facts
  WHERE user_id = NEW.user_id
    AND fact_key IN (
      SELECT fact_key FROM public.fact_key_registry WHERE status = 'core'
    );

  -- ✅ SAFE: si 0 core facts, on met 0%
  IF COALESCE(total_core_facts, 0) = 0 THEN
    completion_pct := 0;
  ELSE
    completion_pct := (user_core_facts_count::NUMERIC / total_core_facts::NUMERIC) * 100;
  END IF;

  -- niveaux (j’ai gardé ton mapping tel quel, même si les labels sont chelous)
  IF completion_pct < 25 THEN
    new_level := 'max';
  ELSIF completion_pct < 50 THEN
    new_level := 'high';
  ELSIF completion_pct < 75 THEN
    new_level := 'medium';
  ELSE
    new_level := 'baseline';
  END IF;

  UPDATE public.user_settings
  SET
    profiling_facts_count = user_core_facts_count,
    profiling_facts_total = COALESCE(total_core_facts, 0),
    profiling_completion_pct = completion_pct,
    profiling_level = new_level,
    profiling_completed = (completion_pct >= 75),
    updated_at = now()
  WHERE user_id = NEW.user_id;

  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_timestamp()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  new.updated_at = now();
  return new;
end;
$function$
;

CREATE OR REPLACE FUNCTION public.update_user_key_events_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.upsert_push_device_safe(p_device_id text, p_expo_push_token text, p_platform text, p_is_app_active boolean, p_active_screen text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.user_is_on_chat(p_user_id uuid)
 RETURNS boolean
 LANGUAGE sql
 STABLE
AS $function$
  select exists (
    select 1
    from public.push_devices d
    where d.user_id = p_user_id
      and d.is_app_active = true
      and d.active_screen = 'chat'
      and d.last_seen_at > (now() - interval '2 minutes')
  );
$function$
;

grant delete on table "public"."affiliate_codes" to "anon";

grant insert on table "public"."affiliate_codes" to "anon";

grant references on table "public"."affiliate_codes" to "anon";

grant select on table "public"."affiliate_codes" to "anon";

grant trigger on table "public"."affiliate_codes" to "anon";

grant truncate on table "public"."affiliate_codes" to "anon";

grant update on table "public"."affiliate_codes" to "anon";

grant delete on table "public"."affiliate_codes" to "authenticated";

grant insert on table "public"."affiliate_codes" to "authenticated";

grant references on table "public"."affiliate_codes" to "authenticated";

grant select on table "public"."affiliate_codes" to "authenticated";

grant trigger on table "public"."affiliate_codes" to "authenticated";

grant truncate on table "public"."affiliate_codes" to "authenticated";

grant update on table "public"."affiliate_codes" to "authenticated";

grant delete on table "public"."affiliate_codes" to "service_role";

grant insert on table "public"."affiliate_codes" to "service_role";

grant references on table "public"."affiliate_codes" to "service_role";

grant select on table "public"."affiliate_codes" to "service_role";

grant trigger on table "public"."affiliate_codes" to "service_role";

grant truncate on table "public"."affiliate_codes" to "service_role";

grant update on table "public"."affiliate_codes" to "service_role";

grant delete on table "public"."affiliate_commissions" to "anon";

grant insert on table "public"."affiliate_commissions" to "anon";

grant references on table "public"."affiliate_commissions" to "anon";

grant select on table "public"."affiliate_commissions" to "anon";

grant trigger on table "public"."affiliate_commissions" to "anon";

grant truncate on table "public"."affiliate_commissions" to "anon";

grant update on table "public"."affiliate_commissions" to "anon";

grant delete on table "public"."affiliate_commissions" to "authenticated";

grant insert on table "public"."affiliate_commissions" to "authenticated";

grant references on table "public"."affiliate_commissions" to "authenticated";

grant select on table "public"."affiliate_commissions" to "authenticated";

grant trigger on table "public"."affiliate_commissions" to "authenticated";

grant truncate on table "public"."affiliate_commissions" to "authenticated";

grant update on table "public"."affiliate_commissions" to "authenticated";

grant delete on table "public"."affiliate_commissions" to "service_role";

grant insert on table "public"."affiliate_commissions" to "service_role";

grant references on table "public"."affiliate_commissions" to "service_role";

grant select on table "public"."affiliate_commissions" to "service_role";

grant trigger on table "public"."affiliate_commissions" to "service_role";

grant truncate on table "public"."affiliate_commissions" to "service_role";

grant update on table "public"."affiliate_commissions" to "service_role";

grant delete on table "public"."affiliates" to "anon";

grant insert on table "public"."affiliates" to "anon";

grant references on table "public"."affiliates" to "anon";

grant select on table "public"."affiliates" to "anon";

grant trigger on table "public"."affiliates" to "anon";

grant truncate on table "public"."affiliates" to "anon";

grant update on table "public"."affiliates" to "anon";

grant delete on table "public"."affiliates" to "authenticated";

grant insert on table "public"."affiliates" to "authenticated";

grant references on table "public"."affiliates" to "authenticated";

grant select on table "public"."affiliates" to "authenticated";

grant trigger on table "public"."affiliates" to "authenticated";

grant truncate on table "public"."affiliates" to "authenticated";

grant update on table "public"."affiliates" to "authenticated";

grant delete on table "public"."affiliates" to "service_role";

grant insert on table "public"."affiliates" to "service_role";

grant references on table "public"."affiliates" to "service_role";

grant select on table "public"."affiliates" to "service_role";

grant trigger on table "public"."affiliates" to "service_role";

grant truncate on table "public"."affiliates" to "service_role";

grant update on table "public"."affiliates" to "service_role";

grant delete on table "public"."app_config" to "anon";

grant insert on table "public"."app_config" to "anon";

grant references on table "public"."app_config" to "anon";

grant select on table "public"."app_config" to "anon";

grant trigger on table "public"."app_config" to "anon";

grant truncate on table "public"."app_config" to "anon";

grant update on table "public"."app_config" to "anon";

grant delete on table "public"."app_config" to "authenticated";

grant insert on table "public"."app_config" to "authenticated";

grant references on table "public"."app_config" to "authenticated";

grant select on table "public"."app_config" to "authenticated";

grant trigger on table "public"."app_config" to "authenticated";

grant truncate on table "public"."app_config" to "authenticated";

grant update on table "public"."app_config" to "authenticated";

grant delete on table "public"."app_config" to "service_role";

grant insert on table "public"."app_config" to "service_role";

grant references on table "public"."app_config" to "service_role";

grant select on table "public"."app_config" to "service_role";

grant trigger on table "public"."app_config" to "service_role";

grant truncate on table "public"."app_config" to "service_role";

grant update on table "public"."app_config" to "service_role";

grant delete on table "public"."automation_templates" to "anon";

grant insert on table "public"."automation_templates" to "anon";

grant references on table "public"."automation_templates" to "anon";

grant select on table "public"."automation_templates" to "anon";

grant trigger on table "public"."automation_templates" to "anon";

grant truncate on table "public"."automation_templates" to "anon";

grant update on table "public"."automation_templates" to "anon";

grant delete on table "public"."automation_templates" to "authenticated";

grant insert on table "public"."automation_templates" to "authenticated";

grant references on table "public"."automation_templates" to "authenticated";

grant select on table "public"."automation_templates" to "authenticated";

grant trigger on table "public"."automation_templates" to "authenticated";

grant truncate on table "public"."automation_templates" to "authenticated";

grant update on table "public"."automation_templates" to "authenticated";

grant delete on table "public"."automation_templates" to "service_role";

grant insert on table "public"."automation_templates" to "service_role";

grant references on table "public"."automation_templates" to "service_role";

grant select on table "public"."automation_templates" to "service_role";

grant trigger on table "public"."automation_templates" to "service_role";

grant truncate on table "public"."automation_templates" to "service_role";

grant update on table "public"."automation_templates" to "service_role";

grant delete on table "public"."billing_events" to "anon";

grant insert on table "public"."billing_events" to "anon";

grant references on table "public"."billing_events" to "anon";

grant select on table "public"."billing_events" to "anon";

grant trigger on table "public"."billing_events" to "anon";

grant truncate on table "public"."billing_events" to "anon";

grant update on table "public"."billing_events" to "anon";

grant delete on table "public"."billing_events" to "authenticated";

grant insert on table "public"."billing_events" to "authenticated";

grant references on table "public"."billing_events" to "authenticated";

grant select on table "public"."billing_events" to "authenticated";

grant trigger on table "public"."billing_events" to "authenticated";

grant truncate on table "public"."billing_events" to "authenticated";

grant update on table "public"."billing_events" to "authenticated";

grant delete on table "public"."billing_events" to "service_role";

grant insert on table "public"."billing_events" to "service_role";

grant references on table "public"."billing_events" to "service_role";

grant select on table "public"."billing_events" to "service_role";

grant trigger on table "public"."billing_events" to "service_role";

grant truncate on table "public"."billing_events" to "service_role";

grant update on table "public"."billing_events" to "service_role";

grant delete on table "public"."companies" to "anon";

grant insert on table "public"."companies" to "anon";

grant references on table "public"."companies" to "anon";

grant select on table "public"."companies" to "anon";

grant trigger on table "public"."companies" to "anon";

grant truncate on table "public"."companies" to "anon";

grant update on table "public"."companies" to "anon";

grant delete on table "public"."companies" to "authenticated";

grant insert on table "public"."companies" to "authenticated";

grant references on table "public"."companies" to "authenticated";

grant select on table "public"."companies" to "authenticated";

grant trigger on table "public"."companies" to "authenticated";

grant truncate on table "public"."companies" to "authenticated";

grant update on table "public"."companies" to "authenticated";

grant delete on table "public"."companies" to "service_role";

grant insert on table "public"."companies" to "service_role";

grant references on table "public"."companies" to "service_role";

grant select on table "public"."companies" to "service_role";

grant trigger on table "public"."companies" to "service_role";

grant truncate on table "public"."companies" to "service_role";

grant update on table "public"."companies" to "service_role";

grant delete on table "public"."conversation_messages" to "anon";

grant insert on table "public"."conversation_messages" to "anon";

grant references on table "public"."conversation_messages" to "anon";

grant select on table "public"."conversation_messages" to "anon";

grant trigger on table "public"."conversation_messages" to "anon";

grant truncate on table "public"."conversation_messages" to "anon";

grant update on table "public"."conversation_messages" to "anon";

grant delete on table "public"."conversation_messages" to "authenticated";

grant insert on table "public"."conversation_messages" to "authenticated";

grant references on table "public"."conversation_messages" to "authenticated";

grant select on table "public"."conversation_messages" to "authenticated";

grant trigger on table "public"."conversation_messages" to "authenticated";

grant truncate on table "public"."conversation_messages" to "authenticated";

grant update on table "public"."conversation_messages" to "authenticated";

grant delete on table "public"."conversation_messages" to "service_role";

grant insert on table "public"."conversation_messages" to "service_role";

grant references on table "public"."conversation_messages" to "service_role";

grant select on table "public"."conversation_messages" to "service_role";

grant trigger on table "public"."conversation_messages" to "service_role";

grant truncate on table "public"."conversation_messages" to "service_role";

grant update on table "public"."conversation_messages" to "service_role";

grant delete on table "public"."conversations" to "anon";

grant insert on table "public"."conversations" to "anon";

grant references on table "public"."conversations" to "anon";

grant select on table "public"."conversations" to "anon";

grant trigger on table "public"."conversations" to "anon";

grant truncate on table "public"."conversations" to "anon";

grant update on table "public"."conversations" to "anon";

grant delete on table "public"."conversations" to "authenticated";

grant insert on table "public"."conversations" to "authenticated";

grant references on table "public"."conversations" to "authenticated";

grant select on table "public"."conversations" to "authenticated";

grant trigger on table "public"."conversations" to "authenticated";

grant truncate on table "public"."conversations" to "authenticated";

grant update on table "public"."conversations" to "authenticated";

grant delete on table "public"."conversations" to "service_role";

grant insert on table "public"."conversations" to "service_role";

grant references on table "public"."conversations" to "service_role";

grant select on table "public"."conversations" to "service_role";

grant trigger on table "public"."conversations" to "service_role";

grant truncate on table "public"."conversations" to "service_role";

grant update on table "public"."conversations" to "service_role";

grant delete on table "public"."debug_auth_user_created_log" to "anon";

grant insert on table "public"."debug_auth_user_created_log" to "anon";

grant references on table "public"."debug_auth_user_created_log" to "anon";

grant select on table "public"."debug_auth_user_created_log" to "anon";

grant trigger on table "public"."debug_auth_user_created_log" to "anon";

grant truncate on table "public"."debug_auth_user_created_log" to "anon";

grant update on table "public"."debug_auth_user_created_log" to "anon";

grant delete on table "public"."debug_auth_user_created_log" to "authenticated";

grant insert on table "public"."debug_auth_user_created_log" to "authenticated";

grant references on table "public"."debug_auth_user_created_log" to "authenticated";

grant select on table "public"."debug_auth_user_created_log" to "authenticated";

grant trigger on table "public"."debug_auth_user_created_log" to "authenticated";

grant truncate on table "public"."debug_auth_user_created_log" to "authenticated";

grant update on table "public"."debug_auth_user_created_log" to "authenticated";

grant delete on table "public"."debug_auth_user_created_log" to "service_role";

grant insert on table "public"."debug_auth_user_created_log" to "service_role";

grant references on table "public"."debug_auth_user_created_log" to "service_role";

grant select on table "public"."debug_auth_user_created_log" to "service_role";

grant trigger on table "public"."debug_auth_user_created_log" to "service_role";

grant truncate on table "public"."debug_auth_user_created_log" to "service_role";

grant update on table "public"."debug_auth_user_created_log" to "service_role";

grant delete on table "public"."email_accounts" to "anon";

grant insert on table "public"."email_accounts" to "anon";

grant references on table "public"."email_accounts" to "anon";

grant select on table "public"."email_accounts" to "anon";

grant trigger on table "public"."email_accounts" to "anon";

grant truncate on table "public"."email_accounts" to "anon";

grant update on table "public"."email_accounts" to "anon";

grant delete on table "public"."email_accounts" to "authenticated";

grant insert on table "public"."email_accounts" to "authenticated";

grant references on table "public"."email_accounts" to "authenticated";

grant select on table "public"."email_accounts" to "authenticated";

grant trigger on table "public"."email_accounts" to "authenticated";

grant truncate on table "public"."email_accounts" to "authenticated";

grant update on table "public"."email_accounts" to "authenticated";

grant delete on table "public"."email_accounts" to "service_role";

grant insert on table "public"."email_accounts" to "service_role";

grant references on table "public"."email_accounts" to "service_role";

grant select on table "public"."email_accounts" to "service_role";

grant trigger on table "public"."email_accounts" to "service_role";

grant truncate on table "public"."email_accounts" to "service_role";

grant update on table "public"."email_accounts" to "service_role";

grant delete on table "public"."fact_key_registry" to "anon";

grant insert on table "public"."fact_key_registry" to "anon";

grant references on table "public"."fact_key_registry" to "anon";

grant select on table "public"."fact_key_registry" to "anon";

grant trigger on table "public"."fact_key_registry" to "anon";

grant truncate on table "public"."fact_key_registry" to "anon";

grant update on table "public"."fact_key_registry" to "anon";

grant delete on table "public"."fact_key_registry" to "authenticated";

grant insert on table "public"."fact_key_registry" to "authenticated";

grant references on table "public"."fact_key_registry" to "authenticated";

grant select on table "public"."fact_key_registry" to "authenticated";

grant trigger on table "public"."fact_key_registry" to "authenticated";

grant truncate on table "public"."fact_key_registry" to "authenticated";

grant update on table "public"."fact_key_registry" to "authenticated";

grant delete on table "public"."fact_key_registry" to "service_role";

grant insert on table "public"."fact_key_registry" to "service_role";

grant references on table "public"."fact_key_registry" to "service_role";

grant select on table "public"."fact_key_registry" to "service_role";

grant trigger on table "public"."fact_key_registry" to "service_role";

grant truncate on table "public"."fact_key_registry" to "service_role";

grant update on table "public"."fact_key_registry" to "service_role";

grant delete on table "public"."fact_profile_mappings" to "anon";

grant insert on table "public"."fact_profile_mappings" to "anon";

grant references on table "public"."fact_profile_mappings" to "anon";

grant select on table "public"."fact_profile_mappings" to "anon";

grant trigger on table "public"."fact_profile_mappings" to "anon";

grant truncate on table "public"."fact_profile_mappings" to "anon";

grant update on table "public"."fact_profile_mappings" to "anon";

grant delete on table "public"."fact_profile_mappings" to "authenticated";

grant insert on table "public"."fact_profile_mappings" to "authenticated";

grant references on table "public"."fact_profile_mappings" to "authenticated";

grant select on table "public"."fact_profile_mappings" to "authenticated";

grant trigger on table "public"."fact_profile_mappings" to "authenticated";

grant truncate on table "public"."fact_profile_mappings" to "authenticated";

grant update on table "public"."fact_profile_mappings" to "authenticated";

grant delete on table "public"."fact_profile_mappings" to "service_role";

grant insert on table "public"."fact_profile_mappings" to "service_role";

grant references on table "public"."fact_profile_mappings" to "service_role";

grant select on table "public"."fact_profile_mappings" to "service_role";

grant trigger on table "public"."fact_profile_mappings" to "service_role";

grant truncate on table "public"."fact_profile_mappings" to "service_role";

grant update on table "public"."fact_profile_mappings" to "service_role";

grant delete on table "public"."gmail_watch_subscriptions" to "anon";

grant insert on table "public"."gmail_watch_subscriptions" to "anon";

grant references on table "public"."gmail_watch_subscriptions" to "anon";

grant select on table "public"."gmail_watch_subscriptions" to "anon";

grant trigger on table "public"."gmail_watch_subscriptions" to "anon";

grant truncate on table "public"."gmail_watch_subscriptions" to "anon";

grant update on table "public"."gmail_watch_subscriptions" to "anon";

grant delete on table "public"."gmail_watch_subscriptions" to "authenticated";

grant insert on table "public"."gmail_watch_subscriptions" to "authenticated";

grant references on table "public"."gmail_watch_subscriptions" to "authenticated";

grant select on table "public"."gmail_watch_subscriptions" to "authenticated";

grant trigger on table "public"."gmail_watch_subscriptions" to "authenticated";

grant truncate on table "public"."gmail_watch_subscriptions" to "authenticated";

grant update on table "public"."gmail_watch_subscriptions" to "authenticated";

grant delete on table "public"."gmail_watch_subscriptions" to "service_role";

grant insert on table "public"."gmail_watch_subscriptions" to "service_role";

grant references on table "public"."gmail_watch_subscriptions" to "service_role";

grant select on table "public"."gmail_watch_subscriptions" to "service_role";

grant trigger on table "public"."gmail_watch_subscriptions" to "service_role";

grant truncate on table "public"."gmail_watch_subscriptions" to "service_role";

grant update on table "public"."gmail_watch_subscriptions" to "service_role";

grant delete on table "public"."heylisa_post_checkout_contexts" to "anon";

grant insert on table "public"."heylisa_post_checkout_contexts" to "anon";

grant references on table "public"."heylisa_post_checkout_contexts" to "anon";

grant select on table "public"."heylisa_post_checkout_contexts" to "anon";

grant trigger on table "public"."heylisa_post_checkout_contexts" to "anon";

grant truncate on table "public"."heylisa_post_checkout_contexts" to "anon";

grant update on table "public"."heylisa_post_checkout_contexts" to "anon";

grant delete on table "public"."heylisa_post_checkout_contexts" to "authenticated";

grant insert on table "public"."heylisa_post_checkout_contexts" to "authenticated";

grant references on table "public"."heylisa_post_checkout_contexts" to "authenticated";

grant select on table "public"."heylisa_post_checkout_contexts" to "authenticated";

grant trigger on table "public"."heylisa_post_checkout_contexts" to "authenticated";

grant truncate on table "public"."heylisa_post_checkout_contexts" to "authenticated";

grant update on table "public"."heylisa_post_checkout_contexts" to "authenticated";

grant delete on table "public"."heylisa_post_checkout_contexts" to "service_role";

grant insert on table "public"."heylisa_post_checkout_contexts" to "service_role";

grant references on table "public"."heylisa_post_checkout_contexts" to "service_role";

grant select on table "public"."heylisa_post_checkout_contexts" to "service_role";

grant trigger on table "public"."heylisa_post_checkout_contexts" to "service_role";

grant truncate on table "public"."heylisa_post_checkout_contexts" to "service_role";

grant update on table "public"."heylisa_post_checkout_contexts" to "service_role";

grant delete on table "public"."lisa_actions_catalog" to "anon";

grant insert on table "public"."lisa_actions_catalog" to "anon";

grant references on table "public"."lisa_actions_catalog" to "anon";

grant select on table "public"."lisa_actions_catalog" to "anon";

grant trigger on table "public"."lisa_actions_catalog" to "anon";

grant truncate on table "public"."lisa_actions_catalog" to "anon";

grant update on table "public"."lisa_actions_catalog" to "anon";

grant delete on table "public"."lisa_actions_catalog" to "authenticated";

grant insert on table "public"."lisa_actions_catalog" to "authenticated";

grant references on table "public"."lisa_actions_catalog" to "authenticated";

grant select on table "public"."lisa_actions_catalog" to "authenticated";

grant trigger on table "public"."lisa_actions_catalog" to "authenticated";

grant truncate on table "public"."lisa_actions_catalog" to "authenticated";

grant update on table "public"."lisa_actions_catalog" to "authenticated";

grant delete on table "public"."lisa_actions_catalog" to "service_role";

grant insert on table "public"."lisa_actions_catalog" to "service_role";

grant references on table "public"."lisa_actions_catalog" to "service_role";

grant select on table "public"."lisa_actions_catalog" to "service_role";

grant trigger on table "public"."lisa_actions_catalog" to "service_role";

grant truncate on table "public"."lisa_actions_catalog" to "service_role";

grant update on table "public"."lisa_actions_catalog" to "service_role";

grant delete on table "public"."lisa_agent_integrations" to "anon";

grant insert on table "public"."lisa_agent_integrations" to "anon";

grant references on table "public"."lisa_agent_integrations" to "anon";

grant select on table "public"."lisa_agent_integrations" to "anon";

grant trigger on table "public"."lisa_agent_integrations" to "anon";

grant truncate on table "public"."lisa_agent_integrations" to "anon";

grant update on table "public"."lisa_agent_integrations" to "anon";

grant delete on table "public"."lisa_agent_integrations" to "authenticated";

grant insert on table "public"."lisa_agent_integrations" to "authenticated";

grant references on table "public"."lisa_agent_integrations" to "authenticated";

grant select on table "public"."lisa_agent_integrations" to "authenticated";

grant trigger on table "public"."lisa_agent_integrations" to "authenticated";

grant truncate on table "public"."lisa_agent_integrations" to "authenticated";

grant update on table "public"."lisa_agent_integrations" to "authenticated";

grant delete on table "public"."lisa_agent_integrations" to "service_role";

grant insert on table "public"."lisa_agent_integrations" to "service_role";

grant references on table "public"."lisa_agent_integrations" to "service_role";

grant select on table "public"."lisa_agent_integrations" to "service_role";

grant trigger on table "public"."lisa_agent_integrations" to "service_role";

grant truncate on table "public"."lisa_agent_integrations" to "service_role";

grant update on table "public"."lisa_agent_integrations" to "service_role";

grant delete on table "public"."lisa_agents_catalog" to "anon";

grant insert on table "public"."lisa_agents_catalog" to "anon";

grant references on table "public"."lisa_agents_catalog" to "anon";

grant select on table "public"."lisa_agents_catalog" to "anon";

grant trigger on table "public"."lisa_agents_catalog" to "anon";

grant truncate on table "public"."lisa_agents_catalog" to "anon";

grant update on table "public"."lisa_agents_catalog" to "anon";

grant delete on table "public"."lisa_agents_catalog" to "authenticated";

grant insert on table "public"."lisa_agents_catalog" to "authenticated";

grant references on table "public"."lisa_agents_catalog" to "authenticated";

grant select on table "public"."lisa_agents_catalog" to "authenticated";

grant trigger on table "public"."lisa_agents_catalog" to "authenticated";

grant truncate on table "public"."lisa_agents_catalog" to "authenticated";

grant update on table "public"."lisa_agents_catalog" to "authenticated";

grant delete on table "public"."lisa_agents_catalog" to "service_role";

grant insert on table "public"."lisa_agents_catalog" to "service_role";

grant references on table "public"."lisa_agents_catalog" to "service_role";

grant select on table "public"."lisa_agents_catalog" to "service_role";

grant trigger on table "public"."lisa_agents_catalog" to "service_role";

grant truncate on table "public"."lisa_agents_catalog" to "service_role";

grant update on table "public"."lisa_agents_catalog" to "service_role";

grant delete on table "public"."lisa_brains" to "anon";

grant insert on table "public"."lisa_brains" to "anon";

grant references on table "public"."lisa_brains" to "anon";

grant select on table "public"."lisa_brains" to "anon";

grant trigger on table "public"."lisa_brains" to "anon";

grant truncate on table "public"."lisa_brains" to "anon";

grant update on table "public"."lisa_brains" to "anon";

grant delete on table "public"."lisa_brains" to "authenticated";

grant insert on table "public"."lisa_brains" to "authenticated";

grant references on table "public"."lisa_brains" to "authenticated";

grant select on table "public"."lisa_brains" to "authenticated";

grant trigger on table "public"."lisa_brains" to "authenticated";

grant truncate on table "public"."lisa_brains" to "authenticated";

grant update on table "public"."lisa_brains" to "authenticated";

grant delete on table "public"."lisa_brains" to "service_role";

grant insert on table "public"."lisa_brains" to "service_role";

grant references on table "public"."lisa_brains" to "service_role";

grant select on table "public"."lisa_brains" to "service_role";

grant trigger on table "public"."lisa_brains" to "service_role";

grant truncate on table "public"."lisa_brains" to "service_role";

grant update on table "public"."lisa_brains" to "service_role";

grant delete on table "public"."lisa_concierge_suggestions" to "anon";

grant insert on table "public"."lisa_concierge_suggestions" to "anon";

grant references on table "public"."lisa_concierge_suggestions" to "anon";

grant select on table "public"."lisa_concierge_suggestions" to "anon";

grant trigger on table "public"."lisa_concierge_suggestions" to "anon";

grant truncate on table "public"."lisa_concierge_suggestions" to "anon";

grant update on table "public"."lisa_concierge_suggestions" to "anon";

grant delete on table "public"."lisa_concierge_suggestions" to "authenticated";

grant insert on table "public"."lisa_concierge_suggestions" to "authenticated";

grant references on table "public"."lisa_concierge_suggestions" to "authenticated";

grant select on table "public"."lisa_concierge_suggestions" to "authenticated";

grant trigger on table "public"."lisa_concierge_suggestions" to "authenticated";

grant truncate on table "public"."lisa_concierge_suggestions" to "authenticated";

grant update on table "public"."lisa_concierge_suggestions" to "authenticated";

grant delete on table "public"."lisa_concierge_suggestions" to "service_role";

grant insert on table "public"."lisa_concierge_suggestions" to "service_role";

grant references on table "public"."lisa_concierge_suggestions" to "service_role";

grant select on table "public"."lisa_concierge_suggestions" to "service_role";

grant trigger on table "public"."lisa_concierge_suggestions" to "service_role";

grant truncate on table "public"."lisa_concierge_suggestions" to "service_role";

grant update on table "public"."lisa_concierge_suggestions" to "service_role";

grant delete on table "public"."lisa_dashboard_weekly_kpis" to "anon";

grant insert on table "public"."lisa_dashboard_weekly_kpis" to "anon";

grant references on table "public"."lisa_dashboard_weekly_kpis" to "anon";

grant select on table "public"."lisa_dashboard_weekly_kpis" to "anon";

grant trigger on table "public"."lisa_dashboard_weekly_kpis" to "anon";

grant truncate on table "public"."lisa_dashboard_weekly_kpis" to "anon";

grant update on table "public"."lisa_dashboard_weekly_kpis" to "anon";

grant delete on table "public"."lisa_dashboard_weekly_kpis" to "authenticated";

grant insert on table "public"."lisa_dashboard_weekly_kpis" to "authenticated";

grant references on table "public"."lisa_dashboard_weekly_kpis" to "authenticated";

grant select on table "public"."lisa_dashboard_weekly_kpis" to "authenticated";

grant trigger on table "public"."lisa_dashboard_weekly_kpis" to "authenticated";

grant truncate on table "public"."lisa_dashboard_weekly_kpis" to "authenticated";

grant update on table "public"."lisa_dashboard_weekly_kpis" to "authenticated";

grant delete on table "public"."lisa_dashboard_weekly_kpis" to "service_role";

grant insert on table "public"."lisa_dashboard_weekly_kpis" to "service_role";

grant references on table "public"."lisa_dashboard_weekly_kpis" to "service_role";

grant select on table "public"."lisa_dashboard_weekly_kpis" to "service_role";

grant trigger on table "public"."lisa_dashboard_weekly_kpis" to "service_role";

grant truncate on table "public"."lisa_dashboard_weekly_kpis" to "service_role";

grant update on table "public"."lisa_dashboard_weekly_kpis" to "service_role";

grant delete on table "public"."lisa_integrations_catalog" to "anon";

grant insert on table "public"."lisa_integrations_catalog" to "anon";

grant references on table "public"."lisa_integrations_catalog" to "anon";

grant select on table "public"."lisa_integrations_catalog" to "anon";

grant trigger on table "public"."lisa_integrations_catalog" to "anon";

grant truncate on table "public"."lisa_integrations_catalog" to "anon";

grant update on table "public"."lisa_integrations_catalog" to "anon";

grant delete on table "public"."lisa_integrations_catalog" to "authenticated";

grant insert on table "public"."lisa_integrations_catalog" to "authenticated";

grant references on table "public"."lisa_integrations_catalog" to "authenticated";

grant select on table "public"."lisa_integrations_catalog" to "authenticated";

grant trigger on table "public"."lisa_integrations_catalog" to "authenticated";

grant truncate on table "public"."lisa_integrations_catalog" to "authenticated";

grant update on table "public"."lisa_integrations_catalog" to "authenticated";

grant delete on table "public"."lisa_integrations_catalog" to "service_role";

grant insert on table "public"."lisa_integrations_catalog" to "service_role";

grant references on table "public"."lisa_integrations_catalog" to "service_role";

grant select on table "public"."lisa_integrations_catalog" to "service_role";

grant trigger on table "public"."lisa_integrations_catalog" to "service_role";

grant truncate on table "public"."lisa_integrations_catalog" to "service_role";

grant update on table "public"."lisa_integrations_catalog" to "service_role";

grant delete on table "public"."lisa_priority_emails" to "anon";

grant insert on table "public"."lisa_priority_emails" to "anon";

grant references on table "public"."lisa_priority_emails" to "anon";

grant select on table "public"."lisa_priority_emails" to "anon";

grant trigger on table "public"."lisa_priority_emails" to "anon";

grant truncate on table "public"."lisa_priority_emails" to "anon";

grant update on table "public"."lisa_priority_emails" to "anon";

grant delete on table "public"."lisa_priority_emails" to "authenticated";

grant insert on table "public"."lisa_priority_emails" to "authenticated";

grant references on table "public"."lisa_priority_emails" to "authenticated";

grant select on table "public"."lisa_priority_emails" to "authenticated";

grant trigger on table "public"."lisa_priority_emails" to "authenticated";

grant truncate on table "public"."lisa_priority_emails" to "authenticated";

grant update on table "public"."lisa_priority_emails" to "authenticated";

grant delete on table "public"."lisa_priority_emails" to "service_role";

grant insert on table "public"."lisa_priority_emails" to "service_role";

grant references on table "public"."lisa_priority_emails" to "service_role";

grant select on table "public"."lisa_priority_emails" to "service_role";

grant trigger on table "public"."lisa_priority_emails" to "service_role";

grant truncate on table "public"."lisa_priority_emails" to "service_role";

grant update on table "public"."lisa_priority_emails" to "service_role";

grant delete on table "public"."lisa_service_docs" to "anon";

grant insert on table "public"."lisa_service_docs" to "anon";

grant references on table "public"."lisa_service_docs" to "anon";

grant select on table "public"."lisa_service_docs" to "anon";

grant trigger on table "public"."lisa_service_docs" to "anon";

grant truncate on table "public"."lisa_service_docs" to "anon";

grant update on table "public"."lisa_service_docs" to "anon";

grant delete on table "public"."lisa_service_docs" to "authenticated";

grant insert on table "public"."lisa_service_docs" to "authenticated";

grant references on table "public"."lisa_service_docs" to "authenticated";

grant select on table "public"."lisa_service_docs" to "authenticated";

grant trigger on table "public"."lisa_service_docs" to "authenticated";

grant truncate on table "public"."lisa_service_docs" to "authenticated";

grant update on table "public"."lisa_service_docs" to "authenticated";

grant delete on table "public"."lisa_service_docs" to "service_role";

grant insert on table "public"."lisa_service_docs" to "service_role";

grant references on table "public"."lisa_service_docs" to "service_role";

grant select on table "public"."lisa_service_docs" to "service_role";

grant trigger on table "public"."lisa_service_docs" to "service_role";

grant truncate on table "public"."lisa_service_docs" to "service_role";

grant update on table "public"."lisa_service_docs" to "service_role";

grant delete on table "public"."lisa_tasks" to "anon";

grant insert on table "public"."lisa_tasks" to "anon";

grant references on table "public"."lisa_tasks" to "anon";

grant select on table "public"."lisa_tasks" to "anon";

grant trigger on table "public"."lisa_tasks" to "anon";

grant truncate on table "public"."lisa_tasks" to "anon";

grant update on table "public"."lisa_tasks" to "anon";

grant delete on table "public"."lisa_tasks" to "authenticated";

grant insert on table "public"."lisa_tasks" to "authenticated";

grant references on table "public"."lisa_tasks" to "authenticated";

grant select on table "public"."lisa_tasks" to "authenticated";

grant trigger on table "public"."lisa_tasks" to "authenticated";

grant truncate on table "public"."lisa_tasks" to "authenticated";

grant update on table "public"."lisa_tasks" to "authenticated";

grant delete on table "public"."lisa_tasks" to "service_role";

grant insert on table "public"."lisa_tasks" to "service_role";

grant references on table "public"."lisa_tasks" to "service_role";

grant select on table "public"."lisa_tasks" to "service_role";

grant trigger on table "public"."lisa_tasks" to "service_role";

grant truncate on table "public"."lisa_tasks" to "service_role";

grant update on table "public"."lisa_tasks" to "service_role";

grant delete on table "public"."lisa_user_agent_settings_gmail" to "anon";

grant insert on table "public"."lisa_user_agent_settings_gmail" to "anon";

grant references on table "public"."lisa_user_agent_settings_gmail" to "anon";

grant select on table "public"."lisa_user_agent_settings_gmail" to "anon";

grant trigger on table "public"."lisa_user_agent_settings_gmail" to "anon";

grant truncate on table "public"."lisa_user_agent_settings_gmail" to "anon";

grant update on table "public"."lisa_user_agent_settings_gmail" to "anon";

grant delete on table "public"."lisa_user_agent_settings_gmail" to "authenticated";

grant insert on table "public"."lisa_user_agent_settings_gmail" to "authenticated";

grant references on table "public"."lisa_user_agent_settings_gmail" to "authenticated";

grant select on table "public"."lisa_user_agent_settings_gmail" to "authenticated";

grant trigger on table "public"."lisa_user_agent_settings_gmail" to "authenticated";

grant truncate on table "public"."lisa_user_agent_settings_gmail" to "authenticated";

grant update on table "public"."lisa_user_agent_settings_gmail" to "authenticated";

grant delete on table "public"."lisa_user_agent_settings_gmail" to "service_role";

grant insert on table "public"."lisa_user_agent_settings_gmail" to "service_role";

grant references on table "public"."lisa_user_agent_settings_gmail" to "service_role";

grant select on table "public"."lisa_user_agent_settings_gmail" to "service_role";

grant trigger on table "public"."lisa_user_agent_settings_gmail" to "service_role";

grant truncate on table "public"."lisa_user_agent_settings_gmail" to "service_role";

grant update on table "public"."lisa_user_agent_settings_gmail" to "service_role";

grant delete on table "public"."lisa_user_agents" to "anon";

grant insert on table "public"."lisa_user_agents" to "anon";

grant references on table "public"."lisa_user_agents" to "anon";

grant select on table "public"."lisa_user_agents" to "anon";

grant trigger on table "public"."lisa_user_agents" to "anon";

grant truncate on table "public"."lisa_user_agents" to "anon";

grant update on table "public"."lisa_user_agents" to "anon";

grant delete on table "public"."lisa_user_agents" to "authenticated";

grant insert on table "public"."lisa_user_agents" to "authenticated";

grant references on table "public"."lisa_user_agents" to "authenticated";

grant select on table "public"."lisa_user_agents" to "authenticated";

grant trigger on table "public"."lisa_user_agents" to "authenticated";

grant truncate on table "public"."lisa_user_agents" to "authenticated";

grant update on table "public"."lisa_user_agents" to "authenticated";

grant delete on table "public"."lisa_user_agents" to "service_role";

grant insert on table "public"."lisa_user_agents" to "service_role";

grant references on table "public"."lisa_user_agents" to "service_role";

grant select on table "public"."lisa_user_agents" to "service_role";

grant trigger on table "public"."lisa_user_agents" to "service_role";

grant truncate on table "public"."lisa_user_agents" to "service_role";

grant update on table "public"."lisa_user_agents" to "service_role";

grant delete on table "public"."lisa_user_integrations" to "anon";

grant insert on table "public"."lisa_user_integrations" to "anon";

grant references on table "public"."lisa_user_integrations" to "anon";

grant select on table "public"."lisa_user_integrations" to "anon";

grant trigger on table "public"."lisa_user_integrations" to "anon";

grant truncate on table "public"."lisa_user_integrations" to "anon";

grant update on table "public"."lisa_user_integrations" to "anon";

grant delete on table "public"."lisa_user_integrations" to "authenticated";

grant insert on table "public"."lisa_user_integrations" to "authenticated";

grant references on table "public"."lisa_user_integrations" to "authenticated";

grant select on table "public"."lisa_user_integrations" to "authenticated";

grant trigger on table "public"."lisa_user_integrations" to "authenticated";

grant truncate on table "public"."lisa_user_integrations" to "authenticated";

grant update on table "public"."lisa_user_integrations" to "authenticated";

grant delete on table "public"."lisa_user_integrations" to "service_role";

grant insert on table "public"."lisa_user_integrations" to "service_role";

grant references on table "public"."lisa_user_integrations" to "service_role";

grant select on table "public"."lisa_user_integrations" to "service_role";

grant trigger on table "public"."lisa_user_integrations" to "service_role";

grant truncate on table "public"."lisa_user_integrations" to "service_role";

grant update on table "public"."lisa_user_integrations" to "service_role";

grant delete on table "public"."lisa_user_monthly_memory" to "anon";

grant insert on table "public"."lisa_user_monthly_memory" to "anon";

grant references on table "public"."lisa_user_monthly_memory" to "anon";

grant select on table "public"."lisa_user_monthly_memory" to "anon";

grant trigger on table "public"."lisa_user_monthly_memory" to "anon";

grant truncate on table "public"."lisa_user_monthly_memory" to "anon";

grant update on table "public"."lisa_user_monthly_memory" to "anon";

grant delete on table "public"."lisa_user_monthly_memory" to "authenticated";

grant insert on table "public"."lisa_user_monthly_memory" to "authenticated";

grant references on table "public"."lisa_user_monthly_memory" to "authenticated";

grant select on table "public"."lisa_user_monthly_memory" to "authenticated";

grant trigger on table "public"."lisa_user_monthly_memory" to "authenticated";

grant truncate on table "public"."lisa_user_monthly_memory" to "authenticated";

grant update on table "public"."lisa_user_monthly_memory" to "authenticated";

grant delete on table "public"."lisa_user_monthly_memory" to "service_role";

grant insert on table "public"."lisa_user_monthly_memory" to "service_role";

grant references on table "public"."lisa_user_monthly_memory" to "service_role";

grant select on table "public"."lisa_user_monthly_memory" to "service_role";

grant trigger on table "public"."lisa_user_monthly_memory" to "service_role";

grant truncate on table "public"."lisa_user_monthly_memory" to "service_role";

grant update on table "public"."lisa_user_monthly_memory" to "service_role";

grant delete on table "public"."proactive_events_outbox" to "anon";

grant insert on table "public"."proactive_events_outbox" to "anon";

grant references on table "public"."proactive_events_outbox" to "anon";

grant select on table "public"."proactive_events_outbox" to "anon";

grant trigger on table "public"."proactive_events_outbox" to "anon";

grant truncate on table "public"."proactive_events_outbox" to "anon";

grant update on table "public"."proactive_events_outbox" to "anon";

grant delete on table "public"."proactive_events_outbox" to "authenticated";

grant insert on table "public"."proactive_events_outbox" to "authenticated";

grant references on table "public"."proactive_events_outbox" to "authenticated";

grant select on table "public"."proactive_events_outbox" to "authenticated";

grant trigger on table "public"."proactive_events_outbox" to "authenticated";

grant truncate on table "public"."proactive_events_outbox" to "authenticated";

grant update on table "public"."proactive_events_outbox" to "authenticated";

grant delete on table "public"."proactive_events_outbox" to "service_role";

grant insert on table "public"."proactive_events_outbox" to "service_role";

grant references on table "public"."proactive_events_outbox" to "service_role";

grant select on table "public"."proactive_events_outbox" to "service_role";

grant trigger on table "public"."proactive_events_outbox" to "service_role";

grant truncate on table "public"."proactive_events_outbox" to "service_role";

grant update on table "public"."proactive_events_outbox" to "service_role";

grant delete on table "public"."proactive_messages_queue" to "anon";

grant insert on table "public"."proactive_messages_queue" to "anon";

grant references on table "public"."proactive_messages_queue" to "anon";

grant select on table "public"."proactive_messages_queue" to "anon";

grant trigger on table "public"."proactive_messages_queue" to "anon";

grant truncate on table "public"."proactive_messages_queue" to "anon";

grant update on table "public"."proactive_messages_queue" to "anon";

grant delete on table "public"."proactive_messages_queue" to "authenticated";

grant insert on table "public"."proactive_messages_queue" to "authenticated";

grant references on table "public"."proactive_messages_queue" to "authenticated";

grant select on table "public"."proactive_messages_queue" to "authenticated";

grant trigger on table "public"."proactive_messages_queue" to "authenticated";

grant truncate on table "public"."proactive_messages_queue" to "authenticated";

grant update on table "public"."proactive_messages_queue" to "authenticated";

grant delete on table "public"."proactive_messages_queue" to "service_role";

grant insert on table "public"."proactive_messages_queue" to "service_role";

grant references on table "public"."proactive_messages_queue" to "service_role";

grant select on table "public"."proactive_messages_queue" to "service_role";

grant trigger on table "public"."proactive_messages_queue" to "service_role";

grant truncate on table "public"."proactive_messages_queue" to "service_role";

grant update on table "public"."proactive_messages_queue" to "service_role";

grant delete on table "public"."project_events" to "anon";

grant insert on table "public"."project_events" to "anon";

grant references on table "public"."project_events" to "anon";

grant select on table "public"."project_events" to "anon";

grant trigger on table "public"."project_events" to "anon";

grant truncate on table "public"."project_events" to "anon";

grant update on table "public"."project_events" to "anon";

grant delete on table "public"."project_events" to "authenticated";

grant insert on table "public"."project_events" to "authenticated";

grant references on table "public"."project_events" to "authenticated";

grant select on table "public"."project_events" to "authenticated";

grant trigger on table "public"."project_events" to "authenticated";

grant truncate on table "public"."project_events" to "authenticated";

grant update on table "public"."project_events" to "authenticated";

grant delete on table "public"."project_events" to "service_role";

grant insert on table "public"."project_events" to "service_role";

grant references on table "public"."project_events" to "service_role";

grant select on table "public"."project_events" to "service_role";

grant trigger on table "public"."project_events" to "service_role";

grant truncate on table "public"."project_events" to "service_role";

grant update on table "public"."project_events" to "service_role";

grant delete on table "public"."projects" to "anon";

grant insert on table "public"."projects" to "anon";

grant references on table "public"."projects" to "anon";

grant select on table "public"."projects" to "anon";

grant trigger on table "public"."projects" to "anon";

grant truncate on table "public"."projects" to "anon";

grant update on table "public"."projects" to "anon";

grant delete on table "public"."projects" to "authenticated";

grant insert on table "public"."projects" to "authenticated";

grant references on table "public"."projects" to "authenticated";

grant select on table "public"."projects" to "authenticated";

grant trigger on table "public"."projects" to "authenticated";

grant truncate on table "public"."projects" to "authenticated";

grant update on table "public"."projects" to "authenticated";

grant delete on table "public"."projects" to "service_role";

grant insert on table "public"."projects" to "service_role";

grant references on table "public"."projects" to "service_role";

grant select on table "public"."projects" to "service_role";

grant trigger on table "public"."projects" to "service_role";

grant truncate on table "public"."projects" to "service_role";

grant update on table "public"."projects" to "service_role";

grant delete on table "public"."push_devices" to "anon";

grant insert on table "public"."push_devices" to "anon";

grant references on table "public"."push_devices" to "anon";

grant select on table "public"."push_devices" to "anon";

grant trigger on table "public"."push_devices" to "anon";

grant truncate on table "public"."push_devices" to "anon";

grant update on table "public"."push_devices" to "anon";

grant delete on table "public"."push_devices" to "authenticated";

grant insert on table "public"."push_devices" to "authenticated";

grant references on table "public"."push_devices" to "authenticated";

grant select on table "public"."push_devices" to "authenticated";

grant trigger on table "public"."push_devices" to "authenticated";

grant truncate on table "public"."push_devices" to "authenticated";

grant update on table "public"."push_devices" to "authenticated";

grant delete on table "public"."push_devices" to "service_role";

grant insert on table "public"."push_devices" to "service_role";

grant references on table "public"."push_devices" to "service_role";

grant select on table "public"."push_devices" to "service_role";

grant trigger on table "public"."push_devices" to "service_role";

grant truncate on table "public"."push_devices" to "service_role";

grant update on table "public"."push_devices" to "service_role";

grant delete on table "public"."push_outbox" to "anon";

grant insert on table "public"."push_outbox" to "anon";

grant references on table "public"."push_outbox" to "anon";

grant select on table "public"."push_outbox" to "anon";

grant trigger on table "public"."push_outbox" to "anon";

grant truncate on table "public"."push_outbox" to "anon";

grant update on table "public"."push_outbox" to "anon";

grant delete on table "public"."push_outbox" to "authenticated";

grant insert on table "public"."push_outbox" to "authenticated";

grant references on table "public"."push_outbox" to "authenticated";

grant select on table "public"."push_outbox" to "authenticated";

grant trigger on table "public"."push_outbox" to "authenticated";

grant truncate on table "public"."push_outbox" to "authenticated";

grant update on table "public"."push_outbox" to "authenticated";

grant delete on table "public"."push_outbox" to "service_role";

grant insert on table "public"."push_outbox" to "service_role";

grant references on table "public"."push_outbox" to "service_role";

grant select on table "public"."push_outbox" to "service_role";

grant trigger on table "public"."push_outbox" to "service_role";

grant truncate on table "public"."push_outbox" to "service_role";

grant update on table "public"."push_outbox" to "service_role";

grant delete on table "public"."referrals" to "anon";

grant insert on table "public"."referrals" to "anon";

grant references on table "public"."referrals" to "anon";

grant select on table "public"."referrals" to "anon";

grant trigger on table "public"."referrals" to "anon";

grant truncate on table "public"."referrals" to "anon";

grant update on table "public"."referrals" to "anon";

grant delete on table "public"."referrals" to "authenticated";

grant insert on table "public"."referrals" to "authenticated";

grant references on table "public"."referrals" to "authenticated";

grant select on table "public"."referrals" to "authenticated";

grant trigger on table "public"."referrals" to "authenticated";

grant truncate on table "public"."referrals" to "authenticated";

grant update on table "public"."referrals" to "authenticated";

grant delete on table "public"."referrals" to "service_role";

grant insert on table "public"."referrals" to "service_role";

grant references on table "public"."referrals" to "service_role";

grant select on table "public"."referrals" to "service_role";

grant trigger on table "public"."referrals" to "service_role";

grant truncate on table "public"."referrals" to "service_role";

grant update on table "public"."referrals" to "service_role";

grant delete on table "public"."user_activities" to "anon";

grant insert on table "public"."user_activities" to "anon";

grant references on table "public"."user_activities" to "anon";

grant select on table "public"."user_activities" to "anon";

grant trigger on table "public"."user_activities" to "anon";

grant truncate on table "public"."user_activities" to "anon";

grant update on table "public"."user_activities" to "anon";

grant delete on table "public"."user_activities" to "authenticated";

grant insert on table "public"."user_activities" to "authenticated";

grant references on table "public"."user_activities" to "authenticated";

grant select on table "public"."user_activities" to "authenticated";

grant trigger on table "public"."user_activities" to "authenticated";

grant truncate on table "public"."user_activities" to "authenticated";

grant update on table "public"."user_activities" to "authenticated";

grant delete on table "public"."user_activities" to "service_role";

grant insert on table "public"."user_activities" to "service_role";

grant references on table "public"."user_activities" to "service_role";

grant select on table "public"."user_activities" to "service_role";

grant trigger on table "public"."user_activities" to "service_role";

grant truncate on table "public"."user_activities" to "service_role";

grant update on table "public"."user_activities" to "service_role";

grant delete on table "public"."user_automations" to "anon";

grant insert on table "public"."user_automations" to "anon";

grant references on table "public"."user_automations" to "anon";

grant select on table "public"."user_automations" to "anon";

grant trigger on table "public"."user_automations" to "anon";

grant truncate on table "public"."user_automations" to "anon";

grant update on table "public"."user_automations" to "anon";

grant delete on table "public"."user_automations" to "authenticated";

grant insert on table "public"."user_automations" to "authenticated";

grant references on table "public"."user_automations" to "authenticated";

grant select on table "public"."user_automations" to "authenticated";

grant trigger on table "public"."user_automations" to "authenticated";

grant truncate on table "public"."user_automations" to "authenticated";

grant update on table "public"."user_automations" to "authenticated";

grant delete on table "public"."user_automations" to "service_role";

grant insert on table "public"."user_automations" to "service_role";

grant references on table "public"."user_automations" to "service_role";

grant select on table "public"."user_automations" to "service_role";

grant trigger on table "public"."user_automations" to "service_role";

grant truncate on table "public"."user_automations" to "service_role";

grant update on table "public"."user_automations" to "service_role";

grant delete on table "public"."user_companies" to "anon";

grant insert on table "public"."user_companies" to "anon";

grant references on table "public"."user_companies" to "anon";

grant select on table "public"."user_companies" to "anon";

grant trigger on table "public"."user_companies" to "anon";

grant truncate on table "public"."user_companies" to "anon";

grant update on table "public"."user_companies" to "anon";

grant delete on table "public"."user_companies" to "authenticated";

grant insert on table "public"."user_companies" to "authenticated";

grant references on table "public"."user_companies" to "authenticated";

grant select on table "public"."user_companies" to "authenticated";

grant trigger on table "public"."user_companies" to "authenticated";

grant truncate on table "public"."user_companies" to "authenticated";

grant update on table "public"."user_companies" to "authenticated";

grant delete on table "public"."user_companies" to "service_role";

grant insert on table "public"."user_companies" to "service_role";

grant references on table "public"."user_companies" to "service_role";

grant select on table "public"."user_companies" to "service_role";

grant trigger on table "public"."user_companies" to "service_role";

grant truncate on table "public"."user_companies" to "service_role";

grant update on table "public"."user_companies" to "service_role";

grant delete on table "public"."user_daily_life_signals" to "anon";

grant insert on table "public"."user_daily_life_signals" to "anon";

grant references on table "public"."user_daily_life_signals" to "anon";

grant select on table "public"."user_daily_life_signals" to "anon";

grant trigger on table "public"."user_daily_life_signals" to "anon";

grant truncate on table "public"."user_daily_life_signals" to "anon";

grant update on table "public"."user_daily_life_signals" to "anon";

grant delete on table "public"."user_daily_life_signals" to "authenticated";

grant insert on table "public"."user_daily_life_signals" to "authenticated";

grant references on table "public"."user_daily_life_signals" to "authenticated";

grant select on table "public"."user_daily_life_signals" to "authenticated";

grant trigger on table "public"."user_daily_life_signals" to "authenticated";

grant truncate on table "public"."user_daily_life_signals" to "authenticated";

grant update on table "public"."user_daily_life_signals" to "authenticated";

grant delete on table "public"."user_daily_life_signals" to "service_role";

grant insert on table "public"."user_daily_life_signals" to "service_role";

grant references on table "public"."user_daily_life_signals" to "service_role";

grant select on table "public"."user_daily_life_signals" to "service_role";

grant trigger on table "public"."user_daily_life_signals" to "service_role";

grant truncate on table "public"."user_daily_life_signals" to "service_role";

grant update on table "public"."user_daily_life_signals" to "service_role";

grant delete on table "public"."user_facts" to "anon";

grant insert on table "public"."user_facts" to "anon";

grant references on table "public"."user_facts" to "anon";

grant select on table "public"."user_facts" to "anon";

grant trigger on table "public"."user_facts" to "anon";

grant truncate on table "public"."user_facts" to "anon";

grant update on table "public"."user_facts" to "anon";

grant delete on table "public"."user_facts" to "authenticated";

grant insert on table "public"."user_facts" to "authenticated";

grant references on table "public"."user_facts" to "authenticated";

grant select on table "public"."user_facts" to "authenticated";

grant trigger on table "public"."user_facts" to "authenticated";

grant truncate on table "public"."user_facts" to "authenticated";

grant update on table "public"."user_facts" to "authenticated";

grant delete on table "public"."user_facts" to "service_role";

grant insert on table "public"."user_facts" to "service_role";

grant references on table "public"."user_facts" to "service_role";

grant select on table "public"."user_facts" to "service_role";

grant trigger on table "public"."user_facts" to "service_role";

grant truncate on table "public"."user_facts" to "service_role";

grant update on table "public"."user_facts" to "service_role";

grant delete on table "public"."user_financial_profile" to "anon";

grant insert on table "public"."user_financial_profile" to "anon";

grant references on table "public"."user_financial_profile" to "anon";

grant select on table "public"."user_financial_profile" to "anon";

grant trigger on table "public"."user_financial_profile" to "anon";

grant truncate on table "public"."user_financial_profile" to "anon";

grant update on table "public"."user_financial_profile" to "anon";

grant delete on table "public"."user_financial_profile" to "authenticated";

grant insert on table "public"."user_financial_profile" to "authenticated";

grant references on table "public"."user_financial_profile" to "authenticated";

grant select on table "public"."user_financial_profile" to "authenticated";

grant trigger on table "public"."user_financial_profile" to "authenticated";

grant truncate on table "public"."user_financial_profile" to "authenticated";

grant update on table "public"."user_financial_profile" to "authenticated";

grant delete on table "public"."user_financial_profile" to "service_role";

grant insert on table "public"."user_financial_profile" to "service_role";

grant references on table "public"."user_financial_profile" to "service_role";

grant select on table "public"."user_financial_profile" to "service_role";

grant trigger on table "public"."user_financial_profile" to "service_role";

grant truncate on table "public"."user_financial_profile" to "service_role";

grant update on table "public"."user_financial_profile" to "service_role";

grant delete on table "public"."user_key_events" to "anon";

grant insert on table "public"."user_key_events" to "anon";

grant references on table "public"."user_key_events" to "anon";

grant select on table "public"."user_key_events" to "anon";

grant trigger on table "public"."user_key_events" to "anon";

grant truncate on table "public"."user_key_events" to "anon";

grant update on table "public"."user_key_events" to "anon";

grant delete on table "public"."user_key_events" to "authenticated";

grant insert on table "public"."user_key_events" to "authenticated";

grant references on table "public"."user_key_events" to "authenticated";

grant select on table "public"."user_key_events" to "authenticated";

grant trigger on table "public"."user_key_events" to "authenticated";

grant truncate on table "public"."user_key_events" to "authenticated";

grant update on table "public"."user_key_events" to "authenticated";

grant delete on table "public"."user_key_events" to "service_role";

grant insert on table "public"."user_key_events" to "service_role";

grant references on table "public"."user_key_events" to "service_role";

grant select on table "public"."user_key_events" to "service_role";

grant trigger on table "public"."user_key_events" to "service_role";

grant truncate on table "public"."user_key_events" to "service_role";

grant update on table "public"."user_key_events" to "service_role";

grant delete on table "public"."user_settings" to "anon";

grant insert on table "public"."user_settings" to "anon";

grant references on table "public"."user_settings" to "anon";

grant select on table "public"."user_settings" to "anon";

grant trigger on table "public"."user_settings" to "anon";

grant truncate on table "public"."user_settings" to "anon";

grant update on table "public"."user_settings" to "anon";

grant delete on table "public"."user_settings" to "authenticated";

grant insert on table "public"."user_settings" to "authenticated";

grant references on table "public"."user_settings" to "authenticated";

grant select on table "public"."user_settings" to "authenticated";

grant trigger on table "public"."user_settings" to "authenticated";

grant truncate on table "public"."user_settings" to "authenticated";

grant update on table "public"."user_settings" to "authenticated";

grant delete on table "public"."user_settings" to "service_role";

grant insert on table "public"."user_settings" to "service_role";

grant references on table "public"."user_settings" to "service_role";

grant select on table "public"."user_settings" to "service_role";

grant trigger on table "public"."user_settings" to "service_role";

grant truncate on table "public"."user_settings" to "service_role";

grant update on table "public"."user_settings" to "service_role";

grant delete on table "public"."userfacts_daily_queue" to "anon";

grant insert on table "public"."userfacts_daily_queue" to "anon";

grant references on table "public"."userfacts_daily_queue" to "anon";

grant select on table "public"."userfacts_daily_queue" to "anon";

grant trigger on table "public"."userfacts_daily_queue" to "anon";

grant truncate on table "public"."userfacts_daily_queue" to "anon";

grant update on table "public"."userfacts_daily_queue" to "anon";

grant delete on table "public"."userfacts_daily_queue" to "authenticated";

grant insert on table "public"."userfacts_daily_queue" to "authenticated";

grant references on table "public"."userfacts_daily_queue" to "authenticated";

grant select on table "public"."userfacts_daily_queue" to "authenticated";

grant trigger on table "public"."userfacts_daily_queue" to "authenticated";

grant truncate on table "public"."userfacts_daily_queue" to "authenticated";

grant update on table "public"."userfacts_daily_queue" to "authenticated";

grant delete on table "public"."userfacts_daily_queue" to "service_role";

grant insert on table "public"."userfacts_daily_queue" to "service_role";

grant references on table "public"."userfacts_daily_queue" to "service_role";

grant select on table "public"."userfacts_daily_queue" to "service_role";

grant trigger on table "public"."userfacts_daily_queue" to "service_role";

grant truncate on table "public"."userfacts_daily_queue" to "service_role";

grant update on table "public"."userfacts_daily_queue" to "service_role";

grant delete on table "public"."users" to "anon";

grant insert on table "public"."users" to "anon";

grant references on table "public"."users" to "anon";

grant select on table "public"."users" to "anon";

grant trigger on table "public"."users" to "anon";

grant truncate on table "public"."users" to "anon";

grant update on table "public"."users" to "anon";

grant delete on table "public"."users" to "authenticated";

grant insert on table "public"."users" to "authenticated";

grant references on table "public"."users" to "authenticated";

grant select on table "public"."users" to "authenticated";

grant trigger on table "public"."users" to "authenticated";

grant truncate on table "public"."users" to "authenticated";

grant update on table "public"."users" to "authenticated";

grant delete on table "public"."users" to "service_role";

grant insert on table "public"."users" to "service_role";

grant references on table "public"."users" to "service_role";

grant select on table "public"."users" to "service_role";

grant trigger on table "public"."users" to "service_role";

grant truncate on table "public"."users" to "service_role";

grant update on table "public"."users" to "service_role";


  create policy "affiliate_codes_select_own"
  on "public"."affiliate_codes"
  as permissive
  for select
  to authenticated
using ((user_id = auth.uid()));



  create policy "affiliate_commissions_service_full"
  on "public"."affiliate_commissions"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "affiliates_service_full"
  on "public"."affiliates"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "affiliates_user_can_select_own"
  on "public"."affiliates"
  as permissive
  for select
  to authenticated
using ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = affiliates.user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "automation_templates_service_full"
  on "public"."automation_templates"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "companies_service_full"
  on "public"."companies"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "cm_delete_none"
  on "public"."conversation_messages"
  as permissive
  for delete
  to authenticated
using (false);



  create policy "cm_insert_user_only"
  on "public"."conversation_messages"
  as permissive
  for insert
  to authenticated
with check (((sender_type = 'user'::public.conversation_sender_enum) AND (EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = conversation_messages.user_id) AND (u.auth_user_id = auth.uid()) AND (u.deleted_at IS NULL)))) AND (EXISTS ( SELECT 1
   FROM public.conversations c
  WHERE ((c.id = conversation_messages.conversation_id) AND (c.user_id = conversation_messages.user_id))))));



  create policy "cm_select_own"
  on "public"."conversation_messages"
  as permissive
  for select
  to authenticated
using ((EXISTS ( SELECT 1
   FROM (public.conversations c
     JOIN public.users u ON ((u.id = c.user_id)))
  WHERE ((c.id = conversation_messages.conversation_id) AND (u.auth_user_id = auth.uid()) AND (u.deleted_at IS NULL)))));



  create policy "cm_update_none"
  on "public"."conversation_messages"
  as permissive
  for update
  to authenticated
using (false);



  create policy "conversation_messages_service_role_full"
  on "public"."conversation_messages"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "conversations_delete_own"
  on "public"."conversations"
  as permissive
  for delete
  to public
using ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = conversations.user_id) AND (u.auth_user_id = auth.uid()) AND (u.deleted_at IS NULL)))));



  create policy "conversations_front_read_only"
  on "public"."conversations"
  as permissive
  for select
  to public
using ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));



  create policy "conversations_insert_own"
  on "public"."conversations"
  as permissive
  for insert
  to public
with check ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = conversations.user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "conversations_select_own"
  on "public"."conversations"
  as permissive
  for select
  to public
using ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = conversations.user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "conversations_service_full_access"
  on "public"."conversations"
  as permissive
  for all
  to public
using ((auth.role() = 'service_role'::text))
with check ((auth.role() = 'service_role'::text));



  create policy "conversations_update_own"
  on "public"."conversations"
  as permissive
  for update
  to public
using ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = conversations.user_id) AND (u.auth_user_id = auth.uid())))))
with check ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = conversations.user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "email_accounts_front_read"
  on "public"."email_accounts"
  as permissive
  for select
  to authenticated, anon
using ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));



  create policy "email_accounts_service_full"
  on "public"."email_accounts"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "fact_key_registry_service_full"
  on "public"."fact_key_registry"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "fact_profile_mappings_service_full"
  on "public"."fact_profile_mappings"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "gmail_watch_subscriptions_service_full"
  on "public"."gmail_watch_subscriptions"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "heylisa_post_checkout_contexts_service_full"
  on "public"."heylisa_post_checkout_contexts"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "lisa_brains_service_full"
  on "public"."lisa_brains"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "lisa_concierge_suggestions_service_full"
  on "public"."lisa_concierge_suggestions"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "Users can read their own lisa dashboard kpis"
  on "public"."lisa_dashboard_weekly_kpis"
  as permissive
  for select
  to authenticated
using ((user_id = ( SELECT u.id
   FROM public.users u
  WHERE (u.auth_user_id = auth.uid())
 LIMIT 1)));



  create policy "lisa_integrations_catalog_service_full"
  on "public"."lisa_integrations_catalog"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "lisa_priority_emails_service_full"
  on "public"."lisa_priority_emails"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "lisa_service_docs_service_full"
  on "public"."lisa_service_docs"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "lisa_tasks_service_full"
  on "public"."lisa_tasks"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "gmail_settings_insert_own"
  on "public"."lisa_user_agent_settings_gmail"
  as permissive
  for insert
  to public
with check ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agent_settings_gmail.user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "gmail_settings_select_own"
  on "public"."lisa_user_agent_settings_gmail"
  as permissive
  for select
  to public
using ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agent_settings_gmail.user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "gmail_settings_update_own"
  on "public"."lisa_user_agent_settings_gmail"
  as permissive
  for update
  to public
using ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agent_settings_gmail.user_id) AND (u.auth_user_id = auth.uid())))))
with check ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agent_settings_gmail.user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "Agents: read own rows"
  on "public"."lisa_user_agents"
  as permissive
  for select
  to authenticated
using ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agents.user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "lisa_user_agents_insert_own"
  on "public"."lisa_user_agents"
  as permissive
  for insert
  to public
with check ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agents.user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "lisa_user_agents_select_own"
  on "public"."lisa_user_agents"
  as permissive
  for select
  to public
using ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agents.user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "lisa_user_agents_update_own"
  on "public"."lisa_user_agents"
  as permissive
  for update
  to public
using ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agents.user_id) AND (u.auth_user_id = auth.uid())))))
with check ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_agents.user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "realtime_select_own_agents"
  on "public"."lisa_user_agents"
  as permissive
  for select
  to public
using ((user_id IN ( SELECT users.id
   FROM public.users
  WHERE (users.auth_user_id = auth.uid()))));



  create policy "select own integrations"
  on "public"."lisa_user_integrations"
  as permissive
  for select
  to authenticated
using ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_integrations.user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "update own integrations"
  on "public"."lisa_user_integrations"
  as permissive
  for update
  to authenticated
using ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_integrations.user_id) AND (u.auth_user_id = auth.uid())))))
with check ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = lisa_user_integrations.user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "lisa_user_monthly_memory_front_read"
  on "public"."lisa_user_monthly_memory"
  as permissive
  for select
  to authenticated, anon
using ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));



  create policy "lisa_user_monthly_memory_service_full"
  on "public"."lisa_user_monthly_memory"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "project_events_service_full"
  on "public"."project_events"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "projects_service_full"
  on "public"."projects"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "push_devices_insert_own"
  on "public"."push_devices"
  as permissive
  for insert
  to authenticated
with check ((user_id = public.current_user_id()));



  create policy "push_devices_select_own"
  on "public"."push_devices"
  as permissive
  for select
  to public
using ((user_id IN ( SELECT users.id
   FROM public.users
  WHERE (users.auth_user_id = auth.uid()))));



  create policy "push_devices_update_own"
  on "public"."push_devices"
  as permissive
  for update
  to public
using ((user_id IN ( SELECT users.id
   FROM public.users
  WHERE (users.auth_user_id = auth.uid()))))
with check ((user_id IN ( SELECT users.id
   FROM public.users
  WHERE (users.auth_user_id = auth.uid()))));



  create policy "push_devices_upsert_own"
  on "public"."push_devices"
  as permissive
  for insert
  to public
with check ((user_id IN ( SELECT users.id
   FROM public.users
  WHERE (users.auth_user_id = auth.uid()))));



  create policy "referrals_insert_own"
  on "public"."referrals"
  as permissive
  for insert
  to public
with check ((referred_user_id = auth.uid()));



  create policy "referrals_select_involved"
  on "public"."referrals"
  as permissive
  for select
  to authenticated
using (((referrer_user_id = auth.uid()) OR (referred_user_id = auth.uid())));



  create policy "referrals_select_own"
  on "public"."referrals"
  as permissive
  for select
  to authenticated
using ((EXISTS ( SELECT 1
   FROM public.users u
  WHERE ((u.id = referrals.referred_user_id) AND (u.auth_user_id = auth.uid())))));



  create policy "User can insert own activity"
  on "public"."user_activities"
  as permissive
  for insert
  to public
with check ((auth.uid() = user_id));



  create policy "User can read own activity"
  on "public"."user_activities"
  as permissive
  for select
  to public
using ((auth.uid() = user_id));



  create policy "User can update own activity"
  on "public"."user_activities"
  as permissive
  for update
  to public
using ((auth.uid() = user_id))
with check ((auth.uid() = user_id));



  create policy "user_automations_front_read"
  on "public"."user_automations"
  as permissive
  for select
  to authenticated, anon
using ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));



  create policy "user_automations_service_full"
  on "public"."user_automations"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "user_companies_front_read"
  on "public"."user_companies"
  as permissive
  for select
  to authenticated, anon
using ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));



  create policy "user_companies_service_full"
  on "public"."user_companies"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "user_daily_life_signals_front_read"
  on "public"."user_daily_life_signals"
  as permissive
  for select
  to authenticated, anon
using ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));



  create policy "user_daily_life_signals_service_full"
  on "public"."user_daily_life_signals"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "user_facts_front_read"
  on "public"."user_facts"
  as permissive
  for select
  to authenticated, anon
using ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));



  create policy "user_facts_service_full"
  on "public"."user_facts"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "user_financial_profile_front_read"
  on "public"."user_financial_profile"
  as permissive
  for select
  to authenticated, anon
using ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));



  create policy "user_financial_profile_service_full"
  on "public"."user_financial_profile"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "user_key_events_front_read"
  on "public"."user_key_events"
  as permissive
  for select
  to authenticated, anon
using ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));



  create policy "user_key_events_service_full"
  on "public"."user_key_events"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "user_settings_front_read"
  on "public"."user_settings"
  as permissive
  for select
  to authenticated, anon
using ((auth.role() = ANY (ARRAY['anon'::text, 'authenticated'::text])));



  create policy "user_settings_insert_own"
  on "public"."user_settings"
  as permissive
  for insert
  to authenticated
with check ((user_id = ( SELECT u.id
   FROM public.users u
  WHERE (u.auth_user_id = auth.uid())
 LIMIT 1)));



  create policy "user_settings_select_own"
  on "public"."user_settings"
  as permissive
  for select
  to authenticated
using ((user_id = ( SELECT u.id
   FROM public.users u
  WHERE (u.auth_user_id = auth.uid())
 LIMIT 1)));



  create policy "user_settings_service_full"
  on "public"."user_settings"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "user_settings_update_own"
  on "public"."user_settings"
  as permissive
  for update
  to authenticated
using ((user_id = ( SELECT u.id
   FROM public.users u
  WHERE (u.auth_user_id = auth.uid())
 LIMIT 1)))
with check ((user_id = ( SELECT u.id
   FROM public.users u
  WHERE (u.auth_user_id = auth.uid())
 LIMIT 1)));



  create policy "public_can_select_users_for_now"
  on "public"."users"
  as permissive
  for select
  to public
using (true);



  create policy "service_can_manage_users"
  on "public"."users"
  as permissive
  for all
  to service_role
using (true)
with check (true);



  create policy "users_can_update_self"
  on "public"."users"
  as permissive
  for update
  to authenticated
using ((auth_user_id = auth.uid()))
with check ((auth_user_id = auth.uid()));


CREATE TRIGGER set_updated_at_affiliate_codes BEFORE UPDATE ON public.affiliate_codes FOR EACH ROW EXECUTE FUNCTION public.tg_set_updated_at();

CREATE TRIGGER trg_automation_templates_updated_at BEFORE UPDATE ON public.automation_templates FOR EACH ROW EXECUTE FUNCTION public.set_automation_templates_updated_at();

CREATE TRIGGER trg_billing_events_normalize_timestamps BEFORE INSERT OR UPDATE OF payload ON public.billing_events FOR EACH ROW EXECUTE FUNCTION public.fn_billing_events_normalize_timestamps();

CREATE TRIGGER trg_billing_events_recompute_user_status AFTER INSERT OR UPDATE OF expiration_at, event_type, payload, user_id ON public.billing_events FOR EACH ROW EXECUTE FUNCTION public.trg_billing_events_recompute_user_status();

CREATE TRIGGER trg_billing_events_recompute_user_status_ins AFTER INSERT ON public.billing_events FOR EACH ROW EXECUTE FUNCTION public.trg_billing_events_recompute_user_status();

CREATE TRIGGER trg_billing_events_resolve_user_id BEFORE INSERT ON public.billing_events FOR EACH ROW EXECUTE FUNCTION public.fn_billing_events_resolve_user_id();

CREATE TRIGGER trg_set_trial_started_at_from_billing_event AFTER INSERT ON public.billing_events FOR EACH ROW EXECUTE FUNCTION public.fn_set_trial_started_at_from_billing_event();

CREATE TRIGGER conversation_messages_enqueue_push AFTER INSERT ON public.conversation_messages FOR EACH ROW EXECUTE FUNCTION public.trg_conversation_message_enqueue_push();

CREATE TRIGGER conversation_messages_increment_free_quota AFTER INSERT ON public.conversation_messages FOR EACH ROW EXECUTE FUNCTION public.trg_increment_free_quota_used();

CREATE TRIGGER outbox_on_lisa_tech_issue AFTER INSERT ON public.conversation_messages FOR EACH ROW EXECUTE FUNCTION public.trg_outbox_on_lisa_tech_issue();

CREATE TRIGGER trg_update_intro_smalltalk AFTER INSERT ON public.conversation_messages FOR EACH ROW EXECUTE FUNCTION public.update_intro_smalltalk_state();

CREATE TRIGGER trg_sync_user_settings_last_message_at AFTER UPDATE OF last_message_at ON public.conversations FOR EACH ROW WHEN ((new.last_message_at IS DISTINCT FROM old.last_message_at)) EXECUTE FUNCTION public.sync_user_settings_last_message_at();

CREATE TRIGGER trg_lisa_actions_catalog_updated_at BEFORE UPDATE ON public.lisa_actions_catalog FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_service_docs_updated_at BEFORE UPDATE ON public.lisa_service_docs FOR EACH ROW EXECUTE FUNCTION public.update_lisa_service_docs_updated_at();

CREATE TRIGGER outbox_on_task_created AFTER INSERT ON public.lisa_tasks FOR EACH ROW EXECUTE FUNCTION public.trg_outbox_on_task_created();

CREATE TRIGGER trg_gmail_settings_updated_at BEFORE UPDATE ON public.lisa_user_agent_settings_gmail FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER "addon_onboarding-start" AFTER INSERT OR UPDATE ON public.lisa_user_agents FOR EACH ROW EXECUTE FUNCTION public.trg_lisa_user_agents_onboarding_start();

CREATE TRIGGER trg_lisa_user_agents_updated_at BEFORE UPDATE ON public.lisa_user_agents FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_refresh_user_agents_settings AFTER INSERT OR DELETE OR UPDATE ON public.lisa_user_agents FOR EACH ROW EXECUTE FUNCTION public.fn_trg_refresh_user_agents_settings();

CREATE TRIGGER trg_set_proactive_messages_queue_updated_at BEFORE UPDATE ON public.proactive_messages_queue FOR EACH ROW EXECUTE FUNCTION public.set_proactive_messages_queue_updated_at();

CREATE TRIGGER trg_push_devices_updated_at BEFORE UPDATE ON public.push_devices FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_user_activities_set_updated_at BEFORE UPDATE ON public.user_activities FOR EACH ROW EXECUTE FUNCTION public.tg_set_updated_at();

CREATE TRIGGER trg_user_automations_updated_at BEFORE UPDATE ON public.user_automations FOR EACH ROW EXECUTE FUNCTION public.set_user_automations_updated_at();

CREATE TRIGGER trg_propagate_use_tu_form_from_user_facts AFTER INSERT OR UPDATE OF value, is_active, fact_key ON public.user_facts FOR EACH ROW EXECUTE FUNCTION public.propagate_use_tu_form_from_user_facts();

CREATE TRIGGER trg_refresh_use_tu_form AFTER INSERT OR DELETE OR UPDATE ON public.user_facts FOR EACH ROW EXECUTE FUNCTION public.fn_trg_refresh_use_tu_form();

CREATE TRIGGER trg_update_profiling_on_fact_change AFTER INSERT OR DELETE OR UPDATE ON public.user_facts FOR EACH ROW EXECUTE FUNCTION public.update_profiling_completion();

CREATE TRIGGER trg_user_facts_propagate_core AFTER INSERT OR DELETE OR UPDATE OF value, is_active, fact_key ON public.user_facts FOR EACH ROW EXECUTE FUNCTION public.trg_user_facts_propagate_core();

CREATE TRIGGER trg_user_facts_refresh_user_settings_job_industry AFTER INSERT OR DELETE OR UPDATE ON public.user_facts FOR EACH ROW EXECUTE FUNCTION public.trg_refresh_user_settings_job_industry();

CREATE TRIGGER trg_user_key_events_updated_at BEFORE UPDATE ON public.user_key_events FOR EACH ROW EXECUTE FUNCTION public.update_user_key_events_updated_at();

CREATE TRIGGER trg_activate_personal_assistant_if_pro AFTER UPDATE OF is_pro ON public.users FOR EACH ROW WHEN (((new.is_pro = true) AND (old.is_pro IS DISTINCT FROM new.is_pro))) EXECUTE FUNCTION public.fn_activate_personal_assistant_if_pro();

CREATE TRIGGER trg_ensure_user_settings_row AFTER INSERT ON public.users FOR EACH ROW EXECUTE FUNCTION public.ensure_user_settings_row();

CREATE TRIGGER trg_revoke_personal_assistant_if_not_pro AFTER UPDATE OF is_pro ON public.users FOR EACH ROW WHEN (((new.is_pro = false) AND (old.is_pro IS DISTINCT FROM new.is_pro))) EXECUTE FUNCTION public.fn_revoke_personal_assistant_if_not_pro();

CREATE TRIGGER trg_users_enqueue_stripe_customer_ins AFTER INSERT ON public.users FOR EACH ROW EXECUTE FUNCTION public.enqueue_stripe_customer_creation();
ALTER TABLE "public"."users" DISABLE TRIGGER "trg_users_enqueue_stripe_customer_ins";

CREATE TRIGGER trg_users_enqueue_stripe_customer_upd AFTER UPDATE OF auth_user_id ON public.users FOR EACH ROW EXECUTE FUNCTION public.enqueue_stripe_customer_creation();
ALTER TABLE "public"."users" DISABLE TRIGGER "trg_users_enqueue_stripe_customer_upd";

CREATE TRIGGER trg_users_recompute_status AFTER INSERT OR UPDATE OF signup_source ON public.users FOR EACH ROW EXECUTE FUNCTION public.trg_users_recompute_status();

CREATE TRIGGER trg_users_recompute_status_ins AFTER INSERT ON public.users FOR EACH ROW EXECUTE FUNCTION public.trg_users_recompute_status();

CREATE TRIGGER trg_users_set_signup_source_ins BEFORE INSERT ON public.users FOR EACH ROW EXECUTE FUNCTION public.fn_users_set_signup_source_and_status();

CREATE TRIGGER trg_users_set_signup_source_upd_auth BEFORE UPDATE OF auth_user_id ON public.users FOR EACH ROW WHEN (((new.auth_user_id IS NOT NULL) AND (new.auth_user_id IS DISTINCT FROM old.auth_user_id))) EXECUTE FUNCTION public.fn_users_set_signup_source_and_status();

CREATE TRIGGER update_users_timestamp BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();

CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_auth_user_created();

CREATE TRIGGER trg_sync_last_active_at AFTER UPDATE OF last_sign_in_at ON auth.users FOR EACH ROW WHEN ((new.last_sign_in_at IS DISTINCT FROM old.last_sign_in_at)) EXECUTE FUNCTION public.fn_sync_last_active_at_from_auth();


