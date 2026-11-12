# Exact Django-owned hooks/metadata: see quality/entrypoints.json for consumers.
_.urlpatterns
_.application
_.PersistenceConfig
_.help
_.add_arguments
_.handle
_.process_exception
_.default_auto_field
_.label
_.Meta
_.constraints
_.indexes
_.SECRET_KEY
_.DEBUG
_.ALLOWED_HOSTS
_.INSTALLED_APPS
_.MIDDLEWARE
_.ROOT_URLCONF
_.WSGI_APPLICATION
_.DATABASES
_.TEMPLATES
_.STATIC_URL
_.STATICFILES_DIRS
_.STATIC_ROOT
_.USE_TZ
_.TIME_ZONE
_.LANGUAGE_CODE
_.DEFAULT_AUTO_FIELD
_.PROCRASTINATE_AUTODISCOVER_MODULE_NAME
_.PROCRASTINATE_IMPORT_PATHS
_.LOGGING

# Django dynamic middleware/commands/formatter and model/migration metadata.
ErrorMiddleware
Command
JsonFormatter
_.format
_.initial
_.dependencies
_.operations
_.started_at
_.last_probe_at
_.created_at
# TypedDict keys consumed through mappings, not Python attributes.
_.wait
_.concurrency
_.pgid
_.checkout
_.processes
_.containers
_.session_kind

# F03 exact framework/template and immutable public DTO fields; see entrypoints.json.
_.CSRF_FAILURE_VIEW
csrf_failure
_.updated_at
_.db_table
_.configured
_.configuration_id
_.pickup_city
_.pickup_state
_.pickup_radius_km
_.shipping_scope
_.source_url
_.verified_at
_.evidence_url

# F04 immutable projections, template fields and public factories exercised via Django shell.
build_read_listing
build_read_listing_changes
_.distance_km
_.pickup_reason
_.scope_current
_.current_coverage
_.applicable_freight
_.last_valid_observation
_.currency
_.observation_id
_.previous_price
_.previous_observation_id
_.previous_observed_at
_.last_attempt_at

# Django ORM fields read through query keyword arguments and auditable migration metadata.
_.initial_scope
_.query_key

# F04 public coverage/window projections for downstream consumers, verified in contract tests.
_.pickup_label
_.shipping_label
_.window_proofs

# F05 Django template properties and condition gate consumed by F09's public port.
# Exact consumers and verification are recorded in entrypoints.json.
_.conflict
_.tab_label
_.satisfies_alert_condition

# F06 exact public shell boundary and ORM audit fields; entrypoints.json records consumers.
build_read_valuation
_.origin_diagnostic
_.requested_at
_.attempts

# F07 published projection fields/factory; exact shell consumers in entrypoints.json.
build_read_profit
_.configuration_revision
_.evaluation_id
_.evaluation_revision
_.calculated_at
_.fee_percent
_.principal
_.resale_scope
_.excluded_costs
_.retryable

# F08 fields read through Django templates/ORM; exact consumers in entrypoints.json.
_.last_valid_at
_.superseded_at
_.automatic_tab
# F05 programmatic compatibility factory remains supported alongside the F08 HTTP composition.
build_condition_handler

# F09 audit columns read through ORM filters, SQL diagnostics and contract shell tests.
_.confirmed_at
_.confirmed_message
_.confirmed_ack
_.installation
_.condition_revision

# F10 Playwright JSON schema and Django template/context registry; exact consumers in entrypoints.json.
_.httpOnly
_.secure
_.sameSite
_.groups_unavailable
integration_context

# F19: verified template/stdlib/argparse consumers in entrypoints.json.
_.last_result_at
_.makefile
_.download

# F19 optional manifest capability recorded by lifecycle and consumed by Docker transport.
_.inference_container

# F13: contracted research API; exact consumer in entrypoints.json.
RequestResearchUseCase

# F13 persistent receipt audit queried through ORM; exact consumer in entrypoints.json.
_.turn_order
_.consumed_pages
_.consumed_details
_.observation_ids

# F13 progress template fields; exact consumer in entrypoints.json.
_.buffered
_.page_limit
_.term_limit

# F13 contracted historical research query; exact shell consumer in entrypoints.json.
ReadResearchUseCase
_.shared_pages

# F13 suggestions budget template/public projection; exact consumers in entrypoints.json.
_.limit_reason
_.detail_limit
_.seconds_limit
_.interval_seconds
_.capacity_reason
_.budget

# F16 diagnostic template/public query fields; exact consumers in entrypoints.json.
_.current_reason
_.current_label
_.matches_displayed_observation
_.first_alert_deadline
_.first_alert_state
_.next_action_at
_.valuation_revision
_.intent_reference
