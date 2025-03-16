import uuid
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Ward(models.Model):
    ward_no = models.PositiveIntegerField(unique=True, help_text="Ward number")
    name = models.CharField(max_length=100, help_text="Name of the ward")
    location = models.TextField(blank=True, help_text="Optional geographical location or description of the ward")

    def __str__(self):
        return f"{self.ward_no} - {self.name}"


class WardManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ward_manager', help_text="User associated with the ward manager")
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='managers', help_text="Ward assigned to the manager")
    phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="Phone number of the ward manager")
    assigned_at = models.DateTimeField(auto_now_add=True, help_text="Time when the manager was assigned")

    def __str__(self):
        return f"Manager of {self.ward.name} ({self.user.username})"
    
class WasteCollector(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='waste_collector', help_text="User associated with the waste collector")
    name = models.CharField(max_length=100, help_text="Full name of the waste collector")  # Added name field
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='collectors', help_text="Ward assigned to the waste collector")
    phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="Phone number of the waste collector")
    assigned_at = models.DateTimeField(auto_now_add=True, help_text="Time when the collector was assigned")
    active = models.BooleanField(default=True, help_text="Whether the collector is active")

    def __str__(self):
        return f"Waste Collector for {self.ward.name} ({self.name})"

class Resident(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resident', help_text="User associated with the resident")  # If you want to link the resident to a user
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='residents', help_text="Ward to which the resident belongs")
    name = models.CharField(max_length=200, help_text="Full name of the resident")
    house_number = models.CharField(max_length=50, help_text="House number of the resident")
    phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="Phone number of the resident")
    qr_code_string = models.UUIDField(default=uuid.uuid4, unique=True, help_text="Unique long string for QR code verification")
    assigned_at = models.DateTimeField(auto_now_add=True, help_text="Time when the resident was registered")

    def __str__(self):
        return f"Resident {self.name} in {self.ward.name} (House No: {self.house_number})"

    def get_qr_code(self):
        return str(self.qr_code_string)

# 1. WasteType
class WasteType(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="Name of the waste type (e.g., Organic, Plastic).")
    description = models.TextField(help_text="Description of the waste type (e.g., compostable materials).")
    recycling_guidelines = models.TextField(blank=True, null=True, help_text="Guidelines for recycling this waste type.")
    active = models.BooleanField(default=True, help_text="Is this waste type active for use?")

    def __str__(self):
        return self.name


# 2. WasteSchedule
class WasteSchedule(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    ward = models.ForeignKey(
        Ward, on_delete=models.CASCADE, 
        related_name="waste_schedules", 
        help_text="Ward associated with the schedule."
    )
    collection_day = models.CharField(
        max_length=10, 
        choices=DAYS_OF_WEEK, 
        help_text="Day of the week for collection."
    )
    start_time = models.TimeField(help_text="Start time for waste collection.")
    end_time = models.TimeField(help_text="End time for waste collection.")
    active = models.BooleanField(default=True, help_text="Is this schedule active?")

    def __str__(self):
        return f"{self.ward.name} - {self.collection_day} ({self.start_time} to {self.end_time})"



# 3. WasteReport
class WasteReport(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]

    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name="waste_reports", help_text="Resident reporting the issue.")
    waste_type = models.ForeignKey(WasteType, on_delete=models.CASCADE, related_name="reports", help_text="Type of waste involved.")
    description = models.TextField(help_text="Details about the waste issue.")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Pending', help_text="Status of the waste report.")
    reported_at = models.DateTimeField(auto_now_add=True, help_text="Time when the issue was reported.")
    resolved_at = models.DateTimeField(blank=True, null=True, help_text="Time when the issue was resolved.")

    def __str__(self):
        return f"Report by {self.resident} - {self.status}"


class WasteCollectionActivity(models.Model):
    waste_collector = models.ForeignKey(
        'WasteCollector',
        on_delete=models.CASCADE,
        related_name="activities",
        help_text="Waste collector who performed the collection."
    )
    resident = models.ForeignKey(
        'Resident',
        on_delete=models.CASCADE,
        related_name="waste_collections",
        help_text="Resident whose waste was collected."
    )
    date_time = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the collection activity took place."
    )
    biodegradable_waste = models.FloatField(
        default=0.0,
        help_text="Amount of biodegradable waste collected (in kg)."
    )
    recyclable_waste = models.FloatField(
        default=0.0,
        help_text="Amount of recyclable waste collected (in kg)."
    )
    non_recyclable_waste = models.FloatField(
        default=0.0,
        help_text="Amount of non-recyclable waste collected (in kg)."
    )
    hazardous_waste = models.FloatField(
        default=0.0,
        help_text="Amount of hazardous waste collected (in kg)."
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional details about the collection activity."
    )

    def __str__(self):
        return f"Collection by {self.waste_collector} at {self.resident} on {self.date_time}"

    def total_waste_collected(self):
        """Returns the total waste collected during this activity."""
        return (
            self.biodegradable_waste +
            self.recyclable_waste +
            self.non_recyclable_waste +
            self.hazardous_waste
        )
    
class ResidentApplication(models.Model):
    PENDING = 'Pending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    name = models.CharField(max_length=200, help_text="Full name of the resident")
    ward = models.ForeignKey(
        'Ward',
        on_delete=models.CASCADE,
        related_name='resident_applications',
        help_text="Ward to which the resident belongs",
    )
    house_number = models.CharField(max_length=50, help_text="House number of the resident")
    phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="Phone number of the resident")
    qr_code_string = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, help_text="Unique long string for QR code verification")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, help_text="Approval status")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="Time when the application was submitted")
    reviewed_at = models.DateTimeField(null=True, blank=True, help_text="Time when the application was reviewed")
    admin_comments = models.TextField(blank=True, null=True, help_text="Comments from the admin")

    def __str__(self):
        return f"{self.name} ({self.ward.name}) - {self.get_status_display()}"

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed')
    ]
    
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_comments = models.TextField(blank=True, null=True)

class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ]
    
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=50)

class Notification(models.Model):
    TYPE_CHOICES = [
        ('SCHEDULE', 'Schedule Update'),
        ('PAYMENT', 'Payment Reminder'),
        ('GENERAL', 'General Notice'),
        ('COLLECTION', 'Collection Update')
    ]
    
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Feedback(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars')
    ]
    
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    waste_collection = models.ForeignKey(WasteCollectionActivity, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SystemStatus(models.Model):
    STATUS_CHOICES = [
        ('OPERATIONAL', 'System Fully Operational'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('DEGRADED', 'Partially Operational'),
        ('DOWN', 'System Down')
    ]

    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPERATIONAL')
    message = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    scheduled_maintenance = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "System Status"
    
    def __str__(self):
        return f"System Status: {self.current_status} (Updated: {self.last_updated})"

class CollectorAssignment(models.Model):
    waste_collector = models.ForeignKey(WasteCollector, on_delete=models.CASCADE)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        unique_together = ('waste_collector', 'resident', 'date')

    def __str__(self):
        return f"{self.resident.name} → {self.waste_collector.user.username} on {self.date}"
