create schema if not exists robo_global_core;

revoke all on schema robo_global_core from public, anon, authenticated;
grant usage on schema robo_global_core to service_role;

create table if not exists robo_global_core.demands (
  id uuid primary key default gen_random_uuid(),
  market text not null,
  language text not null,
  category text,
  problem text not null,
  desire text,
  source text not null,
  signal_strength numeric not null default 0 check (signal_strength between 0 and 1),
  economic_intent_score numeric not null default 0 check (economic_intent_score between 0 and 1),
  evidence jsonb not null default '{}'::jsonb,
  status text not null default 'observed' check (status in ('observed','qualified','rejected','archived')),
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists robo_global_core.intent_signals (
  id uuid primary key default gen_random_uuid(),
  demand_id uuid references robo_global_core.demands(id) on delete cascade,
  source_channel text not null,
  signal_type text not null,
  raw_signal text,
  intent_stage text not null check (intent_stage in ('awareness','research','comparison','decision','purchase')),
  confidence numeric not null default 0 check (confidence between 0 and 1),
  metadata jsonb not null default '{}'::jsonb,
  observed_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create table if not exists robo_global_core.offers (
  id uuid primary key default gen_random_uuid(),
  platform text not null,
  external_product_id text,
  name text not null,
  affiliate_url text not null,
  market text,
  language text,
  currency text not null default 'BRL',
  price numeric,
  commission_type text check (commission_type in ('fixed','percent','unknown')),
  commission_value numeric,
  commission_rate numeric check (commission_rate is null or commission_rate between 0 and 1),
  refund_rate numeric check (refund_rate is null or refund_rate between 0 and 1),
  evidence jsonb not null default '{}'::jsonb,
  status text not null default 'candidate' check (status in ('candidate','validated','active','paused','rejected','expired')),
  tracking_strategy text not null default 'none' check (tracking_strategy in ('none','query_param','url_template','platform_adapter')),
  tracking_template text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index if not exists ux_rgcore_offers_platform_external_product on robo_global_core.offers(platform, external_product_id) where external_product_id is not null;
create unique index if not exists ux_rgcore_offers_affiliate_url on robo_global_core.offers(affiliate_url);

create table if not exists robo_global_core.opportunities (
  id uuid primary key default gen_random_uuid(),
  demand_id uuid not null references robo_global_core.demands(id) on delete restrict,
  offer_id uuid not null references robo_global_core.offers(id) on delete restrict,
  market text not null,
  language text not null,
  audience text,
  angle text not null,
  economic_potential numeric not null default 0 check (economic_potential between 0 and 1),
  signal_quality numeric not null default 0 check (signal_quality between 0 and 1),
  offer_fit numeric not null default 0 check (offer_fit between 0 and 1),
  data_confidence numeric not null default 0 check (data_confidence between 0 and 1),
  score numeric not null default 0,
  score_version integer not null default 1,
  status text not null default 'candidate' check (status in ('candidate','testing','winner','loser','paused','archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(demand_id, offer_id, market, language, angle)
);

create table if not exists robo_global_core.assets (
  id uuid primary key default gen_random_uuid(),
  opportunity_id uuid not null references robo_global_core.opportunities(id) on delete cascade,
  channel text not null,
  asset_type text not null,
  language text not null,
  content_ref text,
  published_url text,
  metadata jsonb not null default '{}'::jsonb,
  status text not null default 'draft' check (status in ('draft','ready','published','paused','retired')),
  created_at timestamptz not null default now(),
  published_at timestamptz,
  updated_at timestamptz not null default now()
);

create table if not exists robo_global_core.interactions (
  id uuid primary key default gen_random_uuid(),
  opportunity_id uuid references robo_global_core.opportunities(id) on delete set null,
  asset_id uuid references robo_global_core.assets(id) on delete set null,
  offer_id uuid references robo_global_core.offers(id) on delete set null,
  event_type text not null check (event_type in ('impression','engagement','click','redirect')),
  attribution_key text,
  session_id text,
  source text,
  referrer text,
  user_agent_hash text,
  ip_hash text,
  metadata jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);
create unique index if not exists ux_rgcore_interactions_attribution_key on robo_global_core.interactions(attribution_key) where attribution_key is not null;
create index if not exists ix_rgcore_interactions_opportunity_time on robo_global_core.interactions(opportunity_id, occurred_at desc);
create index if not exists ix_rgcore_interactions_offer_time on robo_global_core.interactions(offer_id, occurred_at desc);

create table if not exists robo_global_core.affiliate_events_raw (
  id uuid primary key default gen_random_uuid(),
  platform text not null,
  external_event_id text,
  event_type text,
  payload jsonb not null,
  payload_hash text not null unique,
  received_at timestamptz not null default now(),
  processed_at timestamptz,
  processing_status text not null default 'pending' check (processing_status in ('pending','processed','ignored','failed')),
  processing_error text
);
create unique index if not exists ux_rgcore_affiliate_events_external on robo_global_core.affiliate_events_raw(platform, external_event_id) where external_event_id is not null;

create table if not exists robo_global_core.conversions (
  id uuid primary key default gen_random_uuid(),
  platform text not null,
  external_sale_id text not null,
  offer_id uuid references robo_global_core.offers(id) on delete set null,
  opportunity_id uuid references robo_global_core.opportunities(id) on delete set null,
  interaction_id uuid references robo_global_core.interactions(id) on delete set null,
  attribution_key text,
  gross_value numeric not null default 0,
  commission_value numeric not null default 0,
  currency text not null default 'BRL',
  status text not null check (status in ('pending','approved','refunded','chargeback','cancelled')),
  occurred_at timestamptz not null,
  approved_at timestamptz,
  raw_event_id uuid references robo_global_core.affiliate_events_raw(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(platform, external_sale_id)
);
create index if not exists ix_rgcore_conversions_opportunity_time on robo_global_core.conversions(opportunity_id, occurred_at desc);
create index if not exists ix_rgcore_conversions_offer_time on robo_global_core.conversions(offer_id, occurred_at desc);

create table if not exists robo_global_core.economic_outcomes (
  id uuid primary key default gen_random_uuid(),
  conversion_id uuid references robo_global_core.conversions(id) on delete set null,
  opportunity_id uuid references robo_global_core.opportunities(id) on delete set null,
  raw_event_id uuid references robo_global_core.affiliate_events_raw(id) on delete set null,
  event_type text not null check (event_type in ('commission_accrued','commission_reversed','refund','chargeback','fee','adjustment')),
  amount numeric not null,
  currency text not null default 'BRL',
  occurred_at timestamptz not null,
  created_at timestamptz not null default now()
);
create unique index if not exists ux_rgcore_economic_outcomes_raw_event on robo_global_core.economic_outcomes(raw_event_id) where raw_event_id is not null;
create index if not exists ix_rgcore_economic_outcomes_opportunity_time on robo_global_core.economic_outcomes(opportunity_id, occurred_at desc);

create table if not exists robo_global_core.decisions (
  id uuid primary key default gen_random_uuid(),
  entity_type text not null check (entity_type in ('demand','offer','opportunity','asset','channel','market')),
  entity_id uuid,
  decision_type text not null check (decision_type in ('qualify','reject','test','scale','pause','resume','retire')),
  reason text not null,
  evidence jsonb not null default '{}'::jsonb,
  score numeric,
  model_version text,
  decision_version integer not null default 1,
  status text not null default 'active' check (status in ('active','superseded','reverted')),
  decided_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);
create index if not exists ix_rgcore_decisions_entity on robo_global_core.decisions(entity_type, entity_id, decided_at desc);

alter table robo_global_core.demands enable row level security;
alter table robo_global_core.intent_signals enable row level security;
alter table robo_global_core.offers enable row level security;
alter table robo_global_core.opportunities enable row level security;
alter table robo_global_core.assets enable row level security;
alter table robo_global_core.interactions enable row level security;
alter table robo_global_core.affiliate_events_raw enable row level security;
alter table robo_global_core.conversions enable row level security;
alter table robo_global_core.economic_outcomes enable row level security;
alter table robo_global_core.decisions enable row level security;

revoke all on all tables in schema robo_global_core from public, anon, authenticated;
grant select, insert, update, delete on all tables in schema robo_global_core to service_role;

alter default privileges in schema robo_global_core revoke all on tables from public, anon, authenticated;
alter default privileges in schema robo_global_core grant select, insert, update, delete on tables to service_role;
