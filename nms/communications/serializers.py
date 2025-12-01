from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    Team,
    TeamMembership,
    DistributionList,
    DistributionListEntry,
    Incident,
    IncidentMessage,
    MessageAttachment,
)
from .constants import ANNOUNCEMENT_TEMPLATES

User = get_user_model()


class TeamMembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = TeamMembership
        fields = ["id", "team", "user", "user_email", "user_name", "role", "created_at"]
        read_only_fields = ["id", "created_at"]


class TeamSerializer(serializers.ModelSerializer):
    membership_role = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "created_at",
            "updated_at",
            "membership_role",
        ]
        read_only_fields = ["slug", "created_at", "updated_at", "membership_role"]

    def get_membership_role(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        if user.is_staff or user.is_superuser:
            return TeamMembership.Role.TEAM_ADMIN
        membership = obj.memberships.filter(user=user).first()
        return membership.role if membership else None


class DistributionListEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DistributionListEntry
        fields = ["id", "email", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class DistributionListSerializer(serializers.ModelSerializer):
    entries = DistributionListEntrySerializer(many=True, required=False)
    scope = serializers.CharField(read_only=True)

    class Meta:
        model = DistributionList
        fields = [
            "id",
            "team",
            "name",
            "description",
            "scope",
            "entries",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "scope"]

    def create(self, validated_data):
        entries = validated_data.pop("entries", [])
        request = self.context.get("request")
        validated_data["created_by"] = request.user if request else None
        distribution_list = DistributionList.objects.create(**validated_data)
        for entry_data in entries:
            DistributionListEntry.objects.create(
                distribution_list=distribution_list,
                added_by=request.user if request else None,
                **entry_data,
            )
        return distribution_list

    def update(self, instance, validated_data):
        entries = validated_data.pop("entries", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if entries is not None:
            instance.entries.all().delete()
            request = self.context.get("request")
            for entry_data in entries:
                DistributionListEntry.objects.create(
                    distribution_list=instance,
                    added_by=request.user if request else None,
                    **entry_data,
                )
        return instance


class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ["id", "original_name", "file", "uploaded_at"]
        read_only_fields = ["id", "original_name", "uploaded_at"]


class IncidentSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.name", read_only=True)
    primary_distribution_list_name = serializers.CharField(
        source="primary_distribution_list.name", read_only=True
    )
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    created_by_email = serializers.CharField(source="created_by.email", read_only=True)
    is_closed = serializers.BooleanField(source="is_closed", read_only=True)
    messages_count = serializers.SerializerMethodField()

    def get_messages_count(self, obj):
        annotated = getattr(obj, "message_total", None)
        if annotated is not None:
            return annotated
        return obj.messages.count()

    def create(self, validated_data):
        request = self.context.get("request")
        if request:
            validated_data["created_by"] = request.user
        return super().create(validated_data)

    class Meta:
        model = Incident
        fields = [
            "id",
            "reference_id",
            "team",
            "team_name",
            "title",
            "summary",
            "impact",
            "severity",
            "status",
            "template_type",
            "primary_distribution_list",
            "primary_distribution_list_name",
            "created_by",
            "created_by_name",
            "created_by_email",
            "created_at",
            "updated_at",
            "closed_at",
            "closed_by",
            "is_closed",
            "messages_count",
        ]
        read_only_fields = [
            "id",
            "reference_id",
            "team_name",
            "primary_distribution_list_name",
            "created_by",
            "created_by_name",
            "created_by_email",
            "created_at",
            "updated_at",
            "closed_at",
            "closed_by",
            "is_closed",
            "messages_count",
        ]
        extra_kwargs = {
            "primary_distribution_list": {"allow_null": True, "required": False},
        }


class IncidentMessageSerializer(serializers.ModelSerializer):
    incident_reference = serializers.CharField(source="incident.reference_id", read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)

    class Meta:
        model = IncidentMessage
        fields = [
            "id",
            "incident",
            "incident_reference",
            "author",
            "author_name",
            "distribution_list",
            "subject",
            "body",
            "template_type",
            "extra_recipients",
            "sent_to",
            "delivery_status",
            "created_at",
            "attachments",
        ]
        read_only_fields = [
            "id",
            "incident_reference",
            "author",
            "author_name",
            "sent_to",
            "delivery_status",
            "created_at",
            "attachments",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        files = request.FILES.getlist("attachments") if request else []
        validated_data["author"] = request.user if request else None
        message = IncidentMessage.objects.create(**validated_data)
        for file in files:
            MessageAttachment.objects.create(
                message=message,
                file=file,
                original_name=getattr(file, "name", ""),
            )
        return message

    def validate_extra_recipients(self, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value or []


class IncidentCloseSerializer(serializers.Serializer):
    final_subject = serializers.CharField()
    final_body = serializers.CharField()
    distribution_list = serializers.PrimaryKeyRelatedField(
        queryset=DistributionList.objects.all(), allow_null=True, required=False
    )
    template_type = serializers.ChoiceField(
        choices=Incident.TemplateType.choices, default=Incident.TemplateType.INCIDENT
    )
    extra_recipients = serializers.ListField(
        child=serializers.EmailField(), required=False, allow_empty=True
    )

    def validate_extra_recipients(self, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value or []


class AnnouncementTemplateSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    subject = serializers.CharField()
    body = serializers.CharField()


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        request = self.context.get("request")
        teams = Team.objects.filter(memberships__user=user).distinct()
        data["teams"] = TeamSerializer(teams, many=True, context={"request": request}).data
        return data
