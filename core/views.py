from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import *
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.core.exceptions import ObjectDoesNotExist
import uuid
from django.utils.timezone import now
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from .forms import WasteScheduleForm
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from django.conf import settings

def is_superuser(user):
    return user.is_superuser
def index(request):
    return render(request, 'core/index.html')

def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            return render(request, 'core/admin_login.html', {
                'error': "Invalid credentials or insufficient permissions."
            })

    return render(request, 'core/admin_login.html')

@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    return render(request, 'core/admin_dashboard.html', {
        'title': 'Admin Dashboard',
        'admin_name': request.user.username,  # Pass admin name for personalization
    })
@user_passes_test(is_superuser, login_url='/admin-login/', redirect_field_name=None)
def ward_management(request):
    # Fetch all wards
    wards = Ward.objects.all()

    # Ensure the wardmanager group exists with required permissions
    ward_manager_group, created = Group.objects.get_or_create(name='wardmanager')
    if created:
        # Assign permissions to the group if needed
        try:
            permission = Permission.objects.get(codename='manage_wardmanager')
            ward_manager_group.permissions.add(permission)
        except Permission.DoesNotExist:
            messages.error(request, "Required permission 'manage_wardmanager' not found.")

    if request.method == "POST":
        # Handle creation of a new WardManager
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        ward_id = request.POST.get('ward')

        # Validate inputs
        if not username or not email or not password or not ward_id:
            messages.error(request, "All fields are required.")
            return render(request, 'core/ward_management.html', {'wards': wards})

        try:
            # Ensure the ward exists
            ward = Ward.objects.get(id=ward_id)

            # Check if the username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists. Please choose another.")
                return render(request, 'core/ward_management.html', {'wards': wards})

            # Create the user and associate with the group
            user = User.objects.create_user(username=username, email=email, password=password)
            user.groups.add(ward_manager_group)

            # Create a WardManager instance
            WardManager.objects.create(user=user, ward=ward)

            messages.success(request, f"Ward Manager '{username}' successfully created.")
            return redirect('ward_management')

        except ObjectDoesNotExist:
            messages.error(request, "Selected ward does not exist.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")

    return render(request, 'core/ward_management.html', {'wards': wards})

def ward_manager_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            # Check if the user belongs to the 'ward_manager_group'
            if user.groups.filter(name='wardmanager').exists():
                login(request, user)
                return redirect('ward_manager_dashboard')
            else:
                messages.error(request, "You are not authorized as a Ward Manager.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'core/ward_manager_login.html')

@login_required
def ward_manager_dashboard(request):
    # Ensure the logged-in user belongs to the 'ward_manager_group'
    if not request.user.groups.filter(name='wardmanager').exists():
        raise PermissionDenied("You are not authorized to access this page.")

    username = request.user.username if request.user else None
    ward = request.user.ward_manager.ward if request.user and hasattr(request.user, 'ward_manager') else None

    if request.method == 'POST':
        # Handle creation of a new Waste Collector
        name = request.POST.get('name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        phone_number = request.POST.get('phone_number')

        # Validate inputs
        if not name or not username or not password:
            messages.error(request, "All fields except phone number are required.")
            return render(request, 'core/ward_manager_dashboard.html', {
                'username': username,
                'ward': ward
            })

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another.")
            return render(request, 'core/ward_manager_dashboard.html', {
                'username': username,
                'ward': ward
            })

        # Create the Waste Collector
        try:
            user = User.objects.create_user(username=username, password=password)
            WasteCollector.objects.create(user=user, name=name, ward=ward, phone_number=phone_number)
            messages.success(request, f"Waste Collector '{name}' successfully created.")
            return redirect('ward_manager_dashboard')
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")


    return render(request, 'core/ward_manager_dashboard.html', {
        'ward_manager': username,
        'ward': ward
    })

def admin_logout(request):
    logout(request)
    return redirect('admin_login')


def register_resident(request):
    # Ensure the logged-in user is a Ward Manager

    # Get the ward associated with the Ward Manager
    ward_manager = request.user.ward_manager
    ward = ward_manager.ward

    if request.method == "POST":
        # Get form data
        name = request.POST.get('name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        house_number = request.POST.get('house_number')
        phone_number = request.POST.get('phone_number')

        # Generate unique ID for the resident
        unique_id = str(uuid.uuid4())

        # Create the resident's user account and associate with the ward
        user = User.objects.create_user(username=username, password=password)
        resident = Resident.objects.create(
            user=user,
            ward=ward,
            house_number=house_number,
            phone_number=phone_number,
            qr_code_string=unique_id
        )
        resident.save()

        return redirect('ward_manager_dashboard')  # Redirect to the Ward Manager Dashboard or a success page

    return render(request, 'core/register_resident.html', {'ward': ward})

def ward_manager_logout(request):
    logout(request)
    return redirect('ward_manager_login')

class GarbageCollectorLoginView(APIView):
    permission_classes = [AllowAny]  # Anyone can access this view

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user:
            # Check if the user exists in the WasteCollector model
            if WasteCollector.objects.filter(user=user).exists():
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    "message": "Login successful",
                    "token": token.key
                }, status=200)
            else:
                return Response({
                    "message": "You are not authorized as a Garbage Collector."
                }, status=403)

        return Response({
            "message": "Invalid username or password."
        }, status=401)

class GarbageCollectorLogoutView(APIView):
    def post(self, request):
        try:
            # Delete the token to log the user out
            request.user.auth_token.delete()
            return Response({
                "message": "Logout successful"
            }, status=200)
        except (AttributeError, Exception):
            return Response({
                "message": "You are not logged in."
            }, status=400)

class ResidentLogoutView(APIView):
    def post(self, request):
        try:
            # Delete the token to log the user out
            request.user.auth_token.delete()
            return Response({
                "message": "Logout successful"
            }, status=200)
        except (AttributeError, Exception):
            return Response({
                "message": "You are not logged in."
            }, status=400)


def manage_schedules(request):
    ward_manager = request.user.ward_manager
    ward = ward_manager.ward
    schedules = WasteSchedule.objects.filter(ward=ward)

    if request.method == "POST":
        form = WasteScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.ward = ward
            schedule.save()
            return redirect('manage_schedules')
    else:
        form = WasteScheduleForm()

    return render(request, 'core/manage_schedules.html', {
        'ward': ward,
        'schedules': schedules,
        'form': form,
    })


def delete_schedule(request, schedule_id):
    schedule = get_object_or_404(WasteSchedule, id=schedule_id)

    if schedule.ward != request.user.ward_manager.ward:
        raise PermissionDenied("You are not allowed to delete this schedule.")

    schedule.delete()
    return redirect('manage_schedules')

class WasteScheduleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Ensure the user is a Waste Collector
        try:
            waste_collector = request.user.waste_collector
        except AttributeError:
            return Response({"message": "You are not authorized to view this data."}, status=403)

        # Get the schedules for the ward managed by the logged-in Waste Collector
        ward = waste_collector.ward
        schedules = WasteSchedule.objects.filter(ward=ward)
        serializer = WasteScheduleSerializer(schedules, many=True)

        return Response(serializer.data, status=200)

class ResidentLoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        # Authenticate the user
        user = authenticate(username=username, password=password)

        if user is not None:
            try:
                # Check if the authenticated user is a resident
                resident = Resident.objects.get(user=user)
            except Resident.DoesNotExist:
                return Response(
                    {"error": "User is not associated with any resident."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Get or create an authentication token for the resident
            token, created = Token.objects.get_or_create(user=user)

            # Return the token and resident details
            return Response(
                {
                    "token": token.key,
                    "resident": {
                        "name": resident.name,
                        "house_number": resident.house_number,
                        "ward": resident.ward.name,
                        "phone_number": resident.phone_number,
                        "qr_code_string": resident.qr_code_string,
                    },
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Invalid credentials. Please try again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

class ResidentSignupView(APIView):
    def post(self, request):
        name = request.data.get("name")
        ward_id = request.data.get("ward_no")  
        house_number = request.data.get("house_number")
        phone_number = request.data.get("phone_number")

        print("Ward",ward_id, name, house_number, phone_number)
        # Check if the ward exists
        try:
            ward = Ward.objects.get(id=ward_id)
        except Ward.DoesNotExist:
            return Response(
                {"error": "Invalid ward ID provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a ResidentApplication
        try:
            resident_application = ResidentApplication.objects.create(
                name=name,
                ward=ward,
                house_number=house_number,
                phone_number=phone_number,
            )
            serializer = ResidentApplicationSerializer(resident_application)
            return Response(
                {"message": "Application submitted successfully. Await admin approval.", "application": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred while submitting the application: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WardListView(APIView):
    def get(self, request):
        wards = Ward.objects.all().values("ward_no", "name")
        return Response(wards, status=status.HTTP_200_OK)
    
def list_resident_applications(request):
    applications = ResidentApplication.objects.filter(status=ResidentApplication.PENDING)
    return render(request, 'core/approve_residents.html', {'applications': applications})


@login_required
@csrf_exempt
def approve_resident_application(request, application_id):
    if request.method == "POST":
        application = get_object_or_404(ResidentApplication, id=application_id)

        # Create a User with phone_number as username and assign a random password
        user = User.objects.create_user(
            username=application.phone_number,
            password=application.phone_number,  # Use phone number as the password
        )

        # Create a Resident object
        Resident.objects.create(
            user=user,
            ward=application.ward,
            name=application.name,
            house_number=application.house_number,
            phone_number=application.phone_number,
            qr_code_string=application.qr_code_string,
        )

        # Update application status
        application.status = ResidentApplication.APPROVED
        application.reviewed_at = now()
        application.admin_comments = "Application approved."
        application.save()

        return redirect('list_resident_applications')

@login_required
@csrf_exempt
def reject_resident_application(request, application_id):
    if request.method == "POST":
        application = get_object_or_404(ResidentApplication, id=application_id)
        application.status = ResidentApplication.REJECTED
        application.reviewed_at = now()
        application.admin_comments = "Application rejected."
        application.save()

        return redirect('list_resident_applications')
    

class WasteCollectionActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        waste_collector = request.user.waste_collector  # Assuming a one-to-one relation between User and WasteCollector
        serializer = WasteCollectionActivitySerializer(data=request.data)

        if serializer.is_valid():
            try:
                activity = serializer.save(waste_collector=waste_collector)
                return Response(
                    {"message": "Waste collection activity added successfully.", "data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            except serializers.ValidationError as e:
                return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateWasteCollectionActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        """
        Update an existing WasteCollectionActivity record.
        """
        try:
            # Fetch the waste collection activity by primary key
            activity = WasteCollectionActivity.objects.get(pk=pk)

            # Ensure the waste collector updating the record is the one who created it
            if activity.waste_collector != request.user.waste_collector:
                return Response(
                    {"error": "You do not have permission to update this record."},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = WasteCollectionActivitySerializer(activity, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "Waste collection activity updated successfully.", "data": serializer.data},
                    status=status.HTTP_200_OK
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except WasteCollectionActivity.DoesNotExist:
            return Response(
                {"error": "Waste collection activity not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class DeleteWasteCollectionActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        """
        Delete a WasteCollectionActivity record by its primary key.
        """
        try:
            # Fetch the waste collection activity by primary key
            activity = WasteCollectionActivity.objects.get(pk=pk)

            # Ensure the waste collector deleting the record is the one who created it
            if activity.waste_collector != request.user.waste_collector:
                return Response(
                    {"error": "You do not have permission to delete this record."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Delete the record
            activity.delete()
            return Response(
                {"message": "Waste collection activity deleted successfully."},
                status=status.HTTP_200_OK
            )

        except WasteCollectionActivity.DoesNotExist:
            return Response(
                {"error": "Waste collection activity not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class ResidentWasteCollectionActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        """
        Retrieve all waste collection activities for a specific resident.
        """
        try:
            # Find the resident by their username (phone number)
            resident = Resident.objects.get(user__username=username)

            # Get all waste collection activities for the resident
            activities = WasteCollectionActivity.objects.filter(resident=resident)

            # Serialize the data
            serializer = WasteCollectionActivitySerializer(activities, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Resident.DoesNotExist:
            return Response(
                {"error": "Resident not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ResidentQRCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve the QR code string for the authenticated resident.
        """
        try:
            # Get the resident associated with the authenticated user
            resident = Resident.objects.get(user=request.user)
            
            return Response({
                "qr_code_string": resident.qr_code_string
            }, status=status.HTTP_200_OK)

        except Resident.DoesNotExist:
            return Response({
                "error": "No resident profile found for this user."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResidentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            resident = request.user.resident
            serializer = ResidentProfileSerializer(resident)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Resident.DoesNotExist:
            return Response(
                {"error": "Resident profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request):
        try:
            resident = request.user.resident
            serializer = ResidentProfileSerializer(resident, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Resident.DoesNotExist:
            return Response(
                {"error": "Resident profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class ResidentScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            resident = request.user.resident
            schedules = WasteSchedule.objects.filter(ward=resident.ward)
            serializer = WasteScheduleSerializer(schedules, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Resident.DoesNotExist:
            return Response(
                {"error": "Resident profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class ResidentComplaintView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        complaints = Complaint.objects.filter(resident=request.user.resident)
        serializer = ComplaintSerializer(complaints, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ComplaintSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(resident=request.user.resident)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResidentPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(resident=request.user.resident)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(resident=request.user.resident)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResidentNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(resident=request.user.resident)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id, 
                resident=request.user.resident
            )
            notification.is_read = True
            notification.save()
            return Response({"message": "Notification marked as read"}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)

class ResidentHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        activities = WasteCollectionActivity.objects.filter(resident=request.user.resident)
        serializer = ResidentCollectionHistorySerializer(activities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ResidentFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        feedback = Feedback.objects.filter(resident=request.user.resident)
        serializer = FeedbackSerializer(feedback, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(resident=request.user.resident)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WasteCollectorProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            collector = request.user.waste_collector
            serializer = WasteCollectorProfileSerializer(collector)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except WasteCollector.DoesNotExist:
            return Response(
                {"error": "Waste collector profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request):
        try:
            collector = request.user.waste_collector
            serializer = WasteCollectorProfileSerializer(
                collector, 
                data=request.data, 
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except WasteCollector.DoesNotExist:
            return Response(
                {"error": "Waste collector profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class WasteCollectorRouteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            collector = request.user.waste_collector
            today = timezone.now().strftime('%A')
            
            # Get today's schedule
            schedule = WasteSchedule.objects.filter(
                ward=collector.ward,
                collection_day=today,
                active=True
            ).first()
            
            # Get all residents in the ward
            residents = Resident.objects.filter(ward=collector.ward)
            
            # Get already collected waste for today
            collected_residents = WasteCollectionActivity.objects.filter(
                waste_collector=collector,
                date_time__date=timezone.now().date()
            ).values_list('resident_id', flat=True)
            
            # Separate collected and pending residents
            pending_residents = residents.exclude(id__in=collected_residents)
            
            return Response({
                'schedule': WasteScheduleSerializer(schedule).data if schedule else None,
                'pending_collections': ResidentProfileSerializer(pending_residents, many=True).data,
                'total_pending': pending_residents.count(),
                'total_collected': len(collected_residents)
            })
        except WasteCollector.DoesNotExist:
            return Response(
                {"error": "Waste collector profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class WasteCollectorDailyStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            collector = request.user.waste_collector
            today = timezone.now().date()
            
            # Get today's collections
            collections = WasteCollectionActivity.objects.filter(
                waste_collector=collector,
                date_time__date=today
            )
            
            metrics = {
                'total_houses': collections.count(),
                'total_waste_collected': collections.aggregate(
                    total=Sum('biodegradable_waste') + 
                          Sum('recyclable_waste') + 
                          Sum('non_recyclable_waste') + 
                          Sum('hazardous_waste')
                )['total'] or 0,
                'biodegradable_total': collections.aggregate(
                    total=Sum('biodegradable_waste')
                )['total'] or 0,
                'recyclable_total': collections.aggregate(
                    total=Sum('recyclable_waste')
                )['total'] or 0,
                'non_recyclable_total': collections.aggregate(
                    total=Sum('non_recyclable_waste')
                )['total'] or 0,
                'hazardous_total': collections.aggregate(
                    total=Sum('hazardous_waste')
                )['total'] or 0,
                'collection_date': today
            }
            
            serializer = DailyCollectionMetricsSerializer(metrics)
            return Response(serializer.data)
        except WasteCollector.DoesNotExist:
            return Response(
                {"error": "Waste collector profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class WasteCollectionActivityViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WasteCollectionActivitySerializer

    def get_queryset(self):
        return WasteCollectionActivity.objects.filter(
            waste_collector=self.request.user.waste_collector
        )

    def perform_create(self, serializer):
        serializer.save(waste_collector=self.request.user.waste_collector)

    @action(detail=False, methods=['post'])
    def verify_qr(self, request):
        qr_code = request.data.get('qr_code')
        try:
            resident = Resident.objects.get(qr_code_string=qr_code)
            # Check if waste was already collected today
            already_collected = WasteCollectionActivity.objects.filter(
                waste_collector=request.user.waste_collector,
                resident=resident,
                date_time__date=timezone.now().date()
            ).exists()
            
            if already_collected:
                return Response(
                    {"error": "Waste already collected from this resident today"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            return Response({
                "resident_id": resident.id,
                "name": resident.name,
                "house_number": resident.house_number
            })
        except Resident.DoesNotExist:
            return Response(
                {"error": "Invalid QR code"},
                status=status.HTTP_404_NOT_FOUND
            )

class WasteCollectorEmergencyReportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            collector = request.user.waste_collector
            # Create notification for ward manager
            Notification.objects.create(
                title="Emergency Report from Waste Collector",
                message=request.data.get('message', ''),
                notification_type='EMERGENCY',
                ward=collector.ward
            )
            return Response(
                {"message": "Emergency report submitted successfully"},
                status=status.HTTP_201_CREATED
            )
        except WasteCollector.DoesNotExist:
            return Response(
                {"error": "Waste collector profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class QRCodeValidationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = QRValidationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        qr_code = serializer.validated_data['qr_code']
        collector_id = serializer.validated_data['collector_id']
        timestamp = serializer.validated_data['timestamp']
        
        # Rate limiting check
        cache_key = f"qr_validation_{collector_id}_{timezone.now().strftime('%Y%m%d%H%M')}"
        request_count = cache.get(cache_key, 0)
        
        if request_count >= getattr(settings, 'QR_VALIDATION_RATE_LIMIT', 60):  # 60 requests per minute
            return Response(
                {"error": "Rate limit exceeded. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Increment rate limit counter
        cache.set(cache_key, request_count + 1, 60)  # Expires in 60 seconds
        
        try:
            # Verify the collector
            collector = WasteCollector.objects.get(id=collector_id)
            
            # Check if collector is active
            if not collector.active:
                return Response({
                    "is_valid": False,
                    "message": "Collector account is inactive",
                    "timestamp": timezone.now()
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Verify the QR code
            resident = Resident.objects.get(qr_code_string=qr_code)
            
            # Check if waste was already collected today
            already_collected = WasteCollectionActivity.objects.filter(
                resident=resident,
                date_time__date=timezone.now().date()
            ).exists()
            
            if already_collected:
                return Response({
                    "is_valid": False,
                    "message": "Waste has already been collected from this resident today",
                    "timestamp": timezone.now()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if resident belongs to collector's ward
            if resident.ward != collector.ward:
                return Response({
                    "is_valid": False,
                    "message": "Resident does not belong to collector's assigned ward",
                    "timestamp": timezone.now()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            response_data = {
                "is_valid": True,
                "resident_details": ResidentProfileSerializer(resident).data,
                "message": "QR code validated successfully",
                "timestamp": timezone.now()
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except WasteCollector.DoesNotExist:
            return Response({
                "is_valid": False,
                "message": "Invalid collector ID",
                "timestamp": timezone.now()
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Resident.DoesNotExist:
            return Response({
                "is_valid": False,
                "message": "Invalid QR code",
                "timestamp": timezone.now()
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                "is_valid": False,
                "message": "An error occurred during validation",
                "timestamp": timezone.now()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SystemStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get or create system status
            status_obj, created = SystemStatus.objects.get_or_create(
                id=1,  # We'll always use ID 1 as we only need one status record
                defaults={
                    'current_status': 'OPERATIONAL',
                    'message': 'System is running normally'
                }
            )
            
            # Get various system health metrics
            metrics = {
                'database_connection': self._check_database(),
                'cache_connection': self._check_cache(),
                'storage_space': self._check_storage(),
                'recent_errors': self._check_recent_errors(),
            }
            
            # Add system uptime and other metrics
            response_data = {
                'status': SystemStatusSerializer(status_obj).data,
                'metrics': metrics,
                'api_version': getattr(settings, 'API_VERSION', '1.0'),
                'timestamp': timezone.now()
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Error fetching system status',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _check_database(self):
        try:
            # Simple database check
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {'status': 'operational', 'latency': '0ms'}
        except:
            return {'status': 'error', 'message': 'Database connection failed'}
    
    def _check_cache(self):
        try:
            # Check if cache is working
            test_key = 'system_status_test'
            cache.set(test_key, 'test', 10)
            cache.get(test_key)
            return {'status': 'operational'}
        except:
            return {'status': 'error', 'message': 'Cache connection failed'}
    
    def _check_storage(self):
        import shutil
        total, used, free = shutil.disk_usage("/")
        return {
            'total': total // (2**30),  # GB
            'used': used // (2**30),    # GB
            'free': free // (2**30),    # GB
            'status': 'warning' if free // (2**30) < 10 else 'operational'  # Warning if less than 10GB free
        }



