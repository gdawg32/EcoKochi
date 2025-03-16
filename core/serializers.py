from rest_framework import serializers
from .models import WasteCollector, WasteSchedule, ResidentApplication, WasteCollectionActivity, Resident, Complaint, Payment, Notification, Feedback, SystemStatus
from django.utils import timezone


class GarbageCollectorSerializer(serializers.ModelSerializer):
    ward_name = serializers.CharField(source='ward.name', read_only=True)

    class Meta:
        model = WasteCollector
        fields = [
            'id',
            'user',
            'name',
            'ward',
            'ward_name',
            'phone_number',
            'assigned_at',
            'active'
        ]
        read_only_fields = ['id', 'assigned_at']

class WasteCollectionActivitySerializer(serializers.ModelSerializer):
    resident_name = serializers.CharField(source='resident.name', read_only=True)
    resident_house_number = serializers.CharField(source='resident.house_number', read_only=True)
    collector_username = serializers.CharField(source='collector.user.username', read_only=True)  # Optional

    class Meta:
        model = WasteCollectionActivity
        fields = [
            'id', 'resident', 'resident_name', 'resident_house_number',
            'collector_username',
            'date_time', 'biodegradable_waste', 'recyclable_waste',
            'non_recyclable_waste', 'hazardous_waste', 'notes'
        ]
        read_only_fields = ['date_time']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation


class WasteScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteSchedule
        fields = ['id', 'collection_day', 'start_time', 'end_time', 'active']

class ResidentApplicationSerializer(serializers.ModelSerializer):
    ward_name = serializers.ReadOnlyField(source="ward.name")  # Include ward name in the response

    class Meta:
        model = ResidentApplication
        fields = [
            "id",
            "name",
            "ward",
            "ward_name",
            "house_number",
            "phone_number",
            "qr_code_string",
            "status",
            "submitted_at",
        ]

class ResidentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resident
        fields = ['name', 'house_number', 'phone_number', 'ward']
        read_only_fields = ['ward']

class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['id', 'title', 'description', 'status', 'created_at', 'updated_at']
        read_only_fields = ['status', 'created_at', 'updated_at']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'payment_date', 'status', 'transaction_id', 'payment_method']
        read_only_fields = ['payment_date', 'status']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'created_at']
        read_only_fields = ['created_at']

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'waste_collection', 'rating', 'comment', 'created_at']
        read_only_fields = ['created_at']

class WasteCollectorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteCollector
        fields = ['name', 'phone_number', 'ward', 'active']
        read_only_fields = ['ward']

class DailyCollectionMetricsSerializer(serializers.Serializer):
    total_houses = serializers.IntegerField()
    total_waste_collected = serializers.FloatField()
    biodegradable_total = serializers.FloatField()
    recyclable_total = serializers.FloatField()
    non_recyclable_total = serializers.FloatField()
    hazardous_total = serializers.FloatField()
    collection_date = serializers.DateField()

class QRValidationSerializer(serializers.Serializer):
    qr_code = serializers.CharField(required=True)
    collector_id = serializers.IntegerField(required=True)
    timestamp = serializers.DateTimeField(required=False, default=timezone.now)

class QRValidationResponseSerializer(serializers.Serializer):
    is_valid = serializers.BooleanField()
    resident_details = ResidentProfileSerializer(required=False)
    message = serializers.CharField()
    timestamp = serializers.DateTimeField()


class ResidentCollectionHistorySerializer(serializers.ModelSerializer):
    resident_name = serializers.CharField(source='resident.name', read_only=True)
    resident_house_number = serializers.CharField(source='resident.house_number', read_only=True)

    class Meta:
        model = WasteCollectionActivity
        fields = [
            'id', 'resident_name', 'resident_house_number',
            'date_time', 'biodegradable_waste', 'recyclable_waste',
            'non_recyclable_waste', 'hazardous_waste', 'notes'
        ]
