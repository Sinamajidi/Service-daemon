CREATE TABLE IF NOT EXISTS task_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  category text NOT NULL,
  description text NOT NULL,
  classification jsonb NOT NULL,
  scheduling_options jsonb NOT NULL,
  allowed_frequencies jsonb NOT NULL,
  parameters jsonb NOT NULL,
  preconditions jsonb NOT NULL,
  postconditions jsonb NOT NULL,
  resources_required jsonb NOT NULL,
  time_estimate jsonb NOT NULL,
  cost_model jsonb NOT NULL,
  safety_level text NOT NULL,
  output_schema jsonb NOT NULL,
  quality_checks jsonb NOT NULL,
  retry_policy jsonb NOT NULL,
  concurrency_limits jsonb NOT NULL,
  visibility jsonb NOT NULL,
  virtual_effects jsonb NOT NULL,
  audit_fields_required jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS task_instances (
  instance_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id uuid NOT NULL REFERENCES task_templates(id) ON DELETE CASCADE,
  target_entity_id uuid NOT NULL,
  creator_id uuid NOT NULL,
  assignee_ids jsonb NOT NULL,
  scheduled_time timestamptz NOT NULL,
  parameters jsonb NOT NULL,
  status text NOT NULL,
  attempts integer NOT NULL DEFAULT 0,
  result jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  logs jsonb NOT NULL,
  attached_files jsonb NOT NULL,
  idempotency_key text NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS operation_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_instance_id uuid NOT NULL REFERENCES task_instances(instance_id) ON DELETE CASCADE,
  event_payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
