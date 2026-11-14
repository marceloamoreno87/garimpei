"""Keep the persistent authorization fence exact for the active evidence policy."""

from django.db import migrations

FORWARD_SQL = """
CREATE OR REPLACE FUNCTION garimpei_gold_authorization_guard() RETURNS trigger AS $$
DECLARE adopted text; permitted boolean; expected_policy text;
BEGIN
  IF current_setting('garimpei.integrity_restore', true) = 'on'
    AND EXISTS(SELECT 1 FROM runtime_recoverybarrier WHERE state='blocked') THEN
    RETURN NEW;
  END IF;
  SELECT state INTO adopted FROM runtime_goldpolicyadoption WHERE installation='local';
  SELECT CASE WHEN EXISTS(SELECT 1 FROM runtime_assistancepolicy WHERE id=1 AND active)
    THEN 'assisted-evidence-v1' ELSE 'gold-alert-v1' END INTO expected_policy;
  IF expected_policy = 'assisted-evidence-v1' AND adopted IS DISTINCT FROM 'active' THEN
    RAISE EXCEPTION 'assisted policy requires active gold policy';
  END IF;
  IF adopted IS NULL THEN
    RAISE EXCEPTION 'gold policy unavailable';
  END IF;
  IF adopted = 'active' THEN
    IF NEW.gold_policy_verified IS DISTINCT FROM expected_policy THEN
      RAISE EXCEPTION 'gold consumer incompatible';
    END IF;
    SELECT q.state='qualified' AND q.policy=expected_policy
      AND q.observation_id=l.latest_id
      AND (q.valid_until IS NULL OR q.valid_until>=NEW.authorized_at)
      INTO permitted
      FROM runtime_alertintent i
      JOIN runtime_goldqualification q ON q.id=i.gold_qualification_id
      JOIN runtime_listing l ON l.id=q.listing_id
      WHERE i.id=NEW.intent_id;
    IF permitted IS DISTINCT FROM true THEN
      RAISE EXCEPTION 'gold qualification required';
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

# Original 0027 body, with CREATE OR REPLACE to preserve the attached trigger.
REVERSE_SQL = """
CREATE OR REPLACE FUNCTION garimpei_gold_authorization_guard() RETURNS trigger AS $$
DECLARE adopted text; permitted boolean;
BEGIN
  IF current_setting('garimpei.integrity_restore', true) = 'on'
    AND EXISTS(SELECT 1 FROM runtime_recoverybarrier WHERE state='blocked') THEN
    RETURN NEW;
  END IF;
  SELECT state INTO adopted FROM runtime_goldpolicyadoption WHERE installation='local';
  IF adopted IS NULL THEN
    RAISE EXCEPTION 'gold policy unavailable';
  END IF;
  IF adopted = 'active' THEN
    IF NEW.gold_policy_verified IS DISTINCT FROM 'gold-alert-v1' THEN
      RAISE EXCEPTION 'gold consumer incompatible';
    END IF;
    SELECT q.state='qualified' AND q.policy='gold-alert-v1'
      AND q.observation_id=l.latest_id
      AND (q.valid_until IS NULL OR q.valid_until>=NEW.authorized_at)
      INTO permitted
      FROM runtime_alertintent i
      JOIN runtime_goldqualification q ON q.id=i.gold_qualification_id
      JOIN runtime_listing l ON l.id=q.listing_id
      WHERE i.id=NEW.intent_id;
    IF permitted IS DISTINCT FROM true THEN
      RAISE EXCEPTION 'gold qualification required';
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


class Migration(migrations.Migration):
    dependencies = [("runtime", "0030_inference_legacy_targets")]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
