from django.urls import path
from . import views

urlpatterns = [
    # Homepage and Authentication
    path('', views.index, name='index'),
    path('admin_login/', views.admin_login, name='admin_login'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),

    # Ward Manager Routes
    path('ward-management/', views.ward_management, name='ward_management'),
    path('ward-manager-login/', views.ward_manager_login, name='ward_manager_login'),
    path('ward-manager-dashboard/', views.ward_manager_dashboard, name='ward_manager_dashboard'),
    path('ward-manager-logout/', views.ward_manager_logout, name='ward_manager_logout'),

    # Resident Approval (Now Managed by Ward Managers)
    path('ward-manager-dashboard/residents/', views.list_resident_applications, name='list_resident_applications'),
    path('ward-manager-dashboard/residents/approve/<int:application_id>/', views.approve_resident_application, name='approve_resident'),
    path('ward-manager-dashboard/residents/reject/<int:application_id>/', views.reject_resident_application, name='reject_resident'),
    path('ward-manager-dashboard/assign-residents/', views.assign_residents_view, name='assign-residents'),
    path('ward-manager-dashboard/auto-assign/', views.auto_assign_residents_view, name='auto-assign-residents'),
    path('ward-manager-dashboard/view-assignments/', views.view_assignments, name='view-assignments'),

    # Resident Management
    path('register-resident/', views.register_resident, name='register_resident'),

    # Waste Collection Activity
    path('api/waste-collection/add/', views.WasteCollectionActivityView.as_view(), name="add-waste-collection"),
    path('api/waste-collection/update/<int:pk>/', views.UpdateWasteCollectionActivityView.as_view(), name="update-waste-collection"),
    path('api/waste-collection/delete/<int:pk>/', views.DeleteWasteCollectionActivityView.as_view(), name="delete-waste-collection"),
    path('api/waste-collection/resident/<str:username>/', views.ResidentWasteCollectionActivityView.as_view(), name="resident-waste-collection"),

    # QR Code Validation
    path('api/garbage-collector/waste-collections/verify_qr/', views.WasteCollectionActivityViewSet.as_view({'post': 'verify_qr'}), name='verify-qr'),

    # Collector APIs
    path('api/collector/profile/', views.WasteCollectorProfileView.as_view(), name='collector-profile'),
    path('api/collector/route/', views.WasteCollectorRouteView.as_view(), name='collector-route'),
    path('api/collector/daily-status/', views.WasteCollectorDailyStatusView.as_view(), name='collector-daily-status'),
    path('api/collector/emergency-report/', views.WasteCollectorEmergencyReportView.as_view(), name='collector-emergency'),
    path('api/collector/assignments/', views.CollectorAssignmentListView.as_view(), name='collector-assignment-api'),

    # Collector Authentication
    path('api/garbage-collector/login/', views.GarbageCollectorLoginView.as_view(), name='garbage_collector_login'),
    path('api/garbage-collector/logout/', views.GarbageCollectorLogoutView.as_view(), name='garbage_collector_logout'),

    # Resident Authentication & Features
    path('api/resident/login/', views.ResidentLoginView.as_view(), name='resident-login'),
    path('api/resident/logout/', views.ResidentLogoutView.as_view(), name='resident-logout'),
    path('api/resident/apply/', views.ResidentSignupView.as_view(), name='resident-application'),
    path('api/resident/profile/', views.ResidentProfileView.as_view(), name='resident-profile'),
    path('api/resident/schedules/', views.ResidentScheduleView.as_view(), name='resident-schedules'),
    path('api/resident/complaints/', views.ResidentComplaintView.as_view(), name='resident-complaints'),
    path('api/resident/payments/', views.ResidentPaymentView.as_view(), name='resident-payments'),
    path('api/resident/notifications/', views.ResidentNotificationView.as_view(), name='resident-notifications'),
    path('api/resident/notifications/<int:notification_id>/', views.ResidentNotificationView.as_view(), name='resident-notification-update'),
    path('api/resident/history/', views.ResidentHistoryView.as_view(), name='resident-history'),
    path('api/resident/feedback/', views.ResidentFeedbackView.as_view(), name='resident-feedback'),
    path("api/resident/qr-code/", views.ResidentQRCodeView.as_view(), name="resident-qr-code"),
    path('api/resident/assignments/', views.ResidentAssignmentListView.as_view(), name='resident-assignment-api'),

    # System & Wards
    path('api/wards/', views.WardListView.as_view(), name='ward-list'),

    # Get all collections (optionally filter by ?date=YYYY-MM-DD)
    path('api/collector/collections/', views.SimpleCollectorCollectionsView.as_view(), name='simple-collector-collections'),


    # Waste Schedule Management (for Ward Manager)
    path('ward-manager-dashboard/schedules/', views.manage_schedules, name='manage_schedules'),
    path('ward-manager-dashboard/schedules/delete/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
    path('api/schedules/', views.WasteScheduleListView.as_view(), name='schedule-list'),
]
