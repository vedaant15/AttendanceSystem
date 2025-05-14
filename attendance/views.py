from django.shortcuts import render, HttpResponse, redirect
from attendance.models import Signup,Attendance
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.contrib.auth.forms import AuthenticationForm
import qrcode
from django.contrib.auth.decorators import login_required
from io import BytesIO
import base64
import pytz
from django.utils import timezone
from geopy.distance import geodesic
from zoneinfo import ZoneInfo   


def index(request):
    signup_user = None
    if request.user.is_authenticated:
        try:
            signup_user = Signup.objects.get(email=request.user.email)
        except Signup.DoesNotExist:
            signup_user = None
    return render(request, 'index.html', {'signup_user': signup_user})


@login_required
def generate_qr(request):
    user = request.user
    try:
        signup_user = Signup.objects.get(email=user.email)
    except Signup.DoesNotExist:
        return HttpResponse("User not found.", status=404)

    qr_data = f"Name: {signup_user.name}, Enrollment Number: {signup_user.enrollment_number}"
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Save image to memory and encode as base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    image_data_url = f"data:image/png;base64,{img_base64}"
    return render(request, "show_qr.html", {
    "qr_code": img_base64,
    "qr_image": image_data_url
})

def qrcodescanner(request):
    return render(request, 'qrcodescanner.html')

# def attendance_record(request):
#     return render(request, '.html')

def loginSignup(request):
    return render(request, 'loginSignup.html')

def signup(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not name or not email or not password:
            messages.error(request, "All fields are required.")
            return render(request, "loginSignup.html")

        if Signup.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "loginSignup.html")

        try:
            from django.contrib.auth.hashers import make_password
            Signup.objects.create(
                name=name,
                email=email,
                password=make_password(password)
            )
            messages.success(request, 'Signup successful! Please log in.')
            return redirect('loginSignup')  # Make sure your template shows messages

        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")

    return render(request, "loginSignup.html")

        
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            signup_user = Signup.objects.get(email=email)
            if check_password(password, signup_user.password):
                # Create or get a linked Django User
                user, created = User.objects.get_or_create(username=email, defaults={
                    'email': email,
                    'first_name': signup_user.name,
                })
                # Set a random password if it's a new user, so it can't be logged in externally
                if created:
                    user.set_unusable_password()
                    user.save()
                
                # Log in Django's session system
                login(request, user)
                request.session['enrollment_number'] = signup_user.enrollment_number
                messages.success(request, f"Welcome back, {signup_user.name}! Enrollment No: {signup_user.enrollment_number}")
                return redirect('index')
            else:
                messages.error(request, "Invalid password.")
        except Signup.DoesNotExist:
            messages.error(request, "No account found with this email.")

    return render(request, "loginSignup.html")



def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login_view')







ALLOWED_LOCATION = (28.5821195, 77.3266991)
ALLOWED_RADIUS_METERS = 1000
@login_required
def mark_attendance(request, enrollment_number):
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect('index')

    # 👇 Check session enrollment number matches scanned one
    session_enrollment = request.session.get('enrollment_number')
    print("Session enrollment:", session_enrollment)
    print("Scanned enrollment:", enrollment_number)
    if str(session_enrollment) != str(enrollment_number):
        messages.error(request, "You are not authorized to mark attendance for this student.")
        return redirect('index')

    # ✅ Student is authorized
    try:
        student = Signup.objects.get(enrollment_number=enrollment_number)
    except Signup.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('index')

    # 🔍 Location validation
    try:
        lat = float(request.POST.get('latitude'))
        lon = float(request.POST.get('longitude'))
        user_location = (lat, lon)
    except (TypeError, ValueError):
        messages.error(request, "Invalid or missing location data.")
        return redirect('index')

    distance = geodesic(ALLOWED_LOCATION, user_location).meters
    print("Allowed location:", ALLOWED_LOCATION)
    print("User location:", user_location)
    print("Distance (meters):", distance)
    if distance > ALLOWED_RADIUS_METERS:
        messages.error(request, "You are not within the allowed area to mark attendance.")
        return redirect('index')

    # 🕒 Timezone and attendance marking
    try:
        tz = ZoneInfo(student.timezone or "UTC")
    except Exception:
        tz = ZoneInfo("UTC")

    local_now = timezone.now().astimezone(tz).date()

    if Attendance.objects.filter(student=student, date=local_now).exists():
        messages.warning(request, "Attendance already marked for today.")
    else:
        Attendance.objects.create(student=student, date=local_now, is_present=True)
        messages.success(request, "Attendance marked successfully.")

    return redirect('view_attendance')


@login_required
def attendance_list(request):
    attendances = Attendance.objects.all()

    # Convert the date to the student's timezone before displaying
    for attendance in attendances:
        student_timezone = pytz.timezone(attendance.student.timezone)
        attendance.date = attendance.date.astimezone(student_timezone)

    return render(request, 'attendance_list.html', {'attendances': attendances})


@login_required
def view_attendance(request):
    try:
        signup_user = Signup.objects.get(email=request.user.email)
        attendance_records = Attendance.objects.filter(
            student=signup_user,
            date__month=timezone.now().month
        ).order_by('-date')

        return render(request, 'attendance.html', {
            'signup_user': signup_user,
            'attendance_records': attendance_records
        })
    except Signup.DoesNotExist:
        return render(request, 'attendance.html', {
            'error': "User not found."
        })
    
    from django.contrib.auth.views import LoginView

