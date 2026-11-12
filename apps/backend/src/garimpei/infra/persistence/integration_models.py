from django.db import models


class IntegrationSettings(models.Model):
    id = models.CharField(primary_key=True, max_length=16, default="local")
    facebook_revision = models.PositiveBigIntegerField(default=0)
    facebook_file = models.CharField(max_length=100, blank=True)
    facebook_baseline_cycle = models.UUIDField(null=True)
    facebook_saved_at = models.DateTimeField(null=True)
    facebook_expires_at = models.DateTimeField(null=True)
    facebook_mode = models.CharField(max_length=16, default="cookies")
    facebook_login_state = models.CharField(max_length=20, blank=True)
    facebook_login_request = models.UUIDField(null=True)
    facebook_login_requested_at = models.DateTimeField(null=True)
    whatsapp_configured = models.BooleanField(default=False)
    whatsapp_session = models.CharField(max_length=200, blank=True)
    whatsapp_account = models.CharField(max_length=200, blank=True)
    whatsapp_group = models.CharField(max_length=200, blank=True)
    whatsapp_group_name = models.CharField(max_length=300, blank=True)
    alerts_enabled = models.BooleanField(default=False)
