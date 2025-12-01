from django.contrib import admin
from .models import (
    Team,
    TeamMembership,
    DistributionList,
    DistributionListEntry,
    Incident,
    IncidentMessage,
    MessageAttachment,
)


class DistributionListEntryInline(admin.TabularInline):
    model = DistributionListEntry
    extra = 0


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_by", "created_at")
    search_fields = ("name", "slug")


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "role", "created_at")
    list_filter = ("role", "team")
    search_fields = ("user__username", "user__email", "team__name")


@admin.register(DistributionList)
class DistributionListAdmin(admin.ModelAdmin):
    list_display = ("name", "team", "description", "created_by", "created_at")
    list_filter = ("team",)
    search_fields = ("name", "description")
    inlines = [DistributionListEntryInline]


class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0


class IncidentMessageInline(admin.TabularInline):
    model = IncidentMessage
    extra = 0


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("reference_id", "title", "team", "status", "severity", "created_at")
    list_filter = ("team", "status", "severity", "template_type")
    search_fields = ("reference_id", "title")
    inlines = [IncidentMessageInline]


@admin.register(IncidentMessage)
class IncidentMessageAdmin(admin.ModelAdmin):
    list_display = ("incident", "subject", "template_type", "created_at")
    list_filter = ("template_type",)
    search_fields = ("subject", "incident__reference_id")
    inlines = [MessageAttachmentInline]
