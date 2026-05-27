create table if not exists events (
  id               bigserial primary key,
  occurred_at      timestamptz not null,
  kind             text not null
                   check (kind in ('pr_merged', 'build_completed', 'deploy',
                                   'incident_opened', 'incident_closed')),
  actor            text not null,
  repo             text,
  status           text,
  duration_seconds int,
  payload          jsonb not null default '{}'::jsonb
);

create index if not exists events_kind_occurred_idx
  on events (kind, occurred_at desc);
create index if not exists events_occurred_idx
  on events (occurred_at desc);
create index if not exists events_actor_idx
  on events (actor);
