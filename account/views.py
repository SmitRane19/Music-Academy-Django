from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponseServerError, HttpResponseForbidden,HttpResponseRedirect,HttpResponse
from .forms import StudentCreationForm, TeacherCreationForm, UserProfileForm, CustomUser
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
# from .forms import OfflineContentFileAdminForm
from account.models import Student, Teacher, CustomUser
from product.models import Category, CartOfflineCourse,CartOnlineCourse, Order, OrderItem, Batch, Enrollment, OnlineCourse, OfflineCourse, Wishlist, Session, Announcement,Attendance,Message,OfflineCourseContent,OfflineContentFile,OnlineContentFile,OnlineCourseContent,Notes,FAQ,UploadOfflineCourseContent
from django.http import JsonResponse
from django.contrib.auth.forms import SetPasswordForm
from django.db.models import Q
import random
import razorpay
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json
from fuzzywuzzy import process
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from .forms import PasswordResetEmailForm 
from django.core.mail import send_mail
from django.conf import settings
from datetime import date, datetime,timedelta

def student_signup(request):
    if request.method == 'POST':
        form = StudentCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('signin')
        else:
            error = "Something went wrong. Please check the form fields."
            return render(request, "student_signup.html", {"error": error, "form": form})
    else:
        form = StudentCreationForm()
    return render(request, "student_signup.html", {"form": form})

def teacher_signup(request):
    if request.method == 'POST':
        form = TeacherCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('signin')
        else:
            error = "Something went wrong. Please check the form fields."
            return render(request, "teacher_signup.html", {"error": error, "form": form})
    else:
        form = TeacherCreationForm()
    return render(request, "teacher_signup.html", {"form": form})

def signin(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Redirect based on user role
            if hasattr(user, 'teacher'):  
                return redirect('teacher_index')  
            elif hasattr(user, 'student'): 
                return redirect('index') 
            
            # Default fallback if no role is matched
            return redirect('index')
        else:
            error = "Invalid username or password. Please try again."
            return render(request, "signin.html", {"form": form, "error": error})
    else:
        form = AuthenticationForm()
    return render(request, "signin.html", {'form': form})

def signout(request):
    logout(request)
    return redirect("index")

def index(request):
    online_courses = OnlineCourse.objects.all()
    offline_courses = OfflineCourse.objects.all()

    # Assume the following categories for each carousel item
    guitar_course = offline_courses.filter(title__icontains='Guitar').first()
    piano_course = offline_courses.filter(title__icontains='Piano').first()
    vocals_course = offline_courses.filter(title__icontains='Vocal').first()

    # Fetch all teachers for display
    teachers = Teacher.objects.all()

    context = {
        'online_courses': online_courses,
        'offline_courses': offline_courses,
        'guitar_course': guitar_course,
        'piano_course': piano_course,
        'vocals_course': vocals_course,
        'teachers': teachers,  
    }
    return render(request, "index.html", context)

def about_us(request):
    # Fetch all teachers from the database
    teachers = Teacher.objects.all()
    
    # Render the template with the list of teachers
    return render(request, 'about_us.html', {'teachers': teachers})

def sorting(online_courses, sort_by):
    """Sort the online courses based on the selected fees criteria."""
    if sort_by == 'fees_asc':
        return online_courses.order_by('fees')
    elif sort_by == 'fees_desc':
        return online_courses.order_by('-fees')
    return online_courses  

def category(request):
    category_name = request.GET.get('category')  #
    sort_by = request.GET.get('sort_by')  

    if not category_name:
        return redirect('index')  

    # Retrieve the category object based on the name
    category_object = get_object_or_404(Category, name__iexact=category_name)

    # Filter online and offline courses belonging to the selected category
    online_courses = OnlineCourse.objects.filter(category=category_object)
    offline_courses = OfflineCourse.objects.filter(category=category_object)

    # Apply sorting to online courses based on fees
    online_courses = sorting(online_courses, sort_by)

    context = {
        'category_name': category_name.capitalize(),
        'online_courses': online_courses,
        'offline_courses': offline_courses,
        'sort_by': sort_by,  
    }
    return render(request, "category.html", context)

def search_bar(request):
    # Get the search term
    search_term = request.GET.get('search_bar', '')

    # Initialize both online and offline courses
    online_courses = OnlineCourse.objects.all()
    offline_courses = OfflineCourse.objects.all()

    # Only filter if there is a search term
    if search_term:
        online_courses = online_courses.filter(
            Q(category__name__icontains=search_term) | 
            Q(title__icontains=search_term) |
            Q(description__icontains=search_term)
        )
        offline_courses = offline_courses.filter(
            Q(category__name__icontains=search_term) | 
            Q(title__icontains=search_term) |
            Q(description__icontains=search_term)
        )

    # Context for passing courses and the search term to the template
    context = {
        'online_courses': online_courses,
        'offline_courses': offline_courses,
        'search_term': search_term,
    }

    return render(request, 'search_results.html', context)

def profile(request):
    if not request.user.is_authenticated:
        return redirect('signin')

    user = request.user

    # Initialize variables
    courses_count = 0
    batches_count = 0
    dob = None
    gender = None
    is_student = False
    is_teacher = False
    base_template = 'base.html'
    online_courses = None
    offline_courses = None
    attendance_summary = {}

    if isinstance(user, CustomUser):
        try:
            # Student-specific data
            student = Student.objects.get(customuser_ptr=user)
            is_student = True
            base_template = 'base.html'

            # Fetch attendance records and summarize them
            attendance_counts = Attendance.objects.filter(student=student).values('status').annotate(count=Count('status'))
            attendance_summary = {entry['status']: entry['count'] for entry in attendance_counts}
            # Modify attendance summary to include session details
            attendance_records = Attendance.objects.filter(student=student).select_related('session__batch')

            # Prepare attendance data for display
            attendance_data = []
            for record in attendance_records:
                attendance_data.append({
                    'batch': record.session.batch.batch_code,
                    'session_date': record.session.date,
                    'session_topic': record.session.topic,
                    'status': record.get_status_display(),
                    'remarks': record.remarks or 'N/A',
                })

            # Fetch enrolled courses
            orders = Order.objects.filter(student=user, payment_status='paid')
            courses_count = OrderItem.objects.filter(order__in=orders).filter(
                Q(online_course__isnull=False) | Q(offline_course__isnull=False)
            ).count()
            online_courses = OrderItem.objects.filter(order__in=orders, online_course__isnull=False)
            offline_courses = OrderItem.objects.filter(order__in=orders, offline_course__isnull=False)

            dob = student.dob
            gender = student.get_gender_display()

        except Student.DoesNotExist:
            try:
                # Teacher-specific data
                teacher = Teacher.objects.get(customuser_ptr=user)
                is_teacher = True
                base_template = 'teacher_base.html'
                batches_count = teacher.batch_set.count()
                dob = teacher.dob
                gender = teacher.get_gender_display()
            except Teacher.DoesNotExist:
                raise Http404("User type is not valid.")

    return render(request, 'profile.html', {
        'user': user,
        'courses_count': courses_count,
        'batches_count': batches_count,
        'dob': dob,
        'gender': gender,
        'is_student': is_student,
        'is_teacher': is_teacher,
        'base_template': base_template,
        'online_courses': online_courses,
        'offline_courses': offline_courses,
        'attendance_summary': attendance_summary,
        'attendance_data': attendance_data
    })

def student_profile(request, student_id):
    
    #View to display a specific student's profile.
    student = get_object_or_404(Student, id=student_id)

    # Count the courses the student is enrolled in
    courses_count = OrderItem.objects.filter(
        order__student=student,
        online_course__isnull=False
    ).count() + OrderItem.objects.filter(
        order__student=student,
        offline_course__isnull=False
    ).count()

    # Prepare the data for rendering
    profile_data = {
        'user': student,
        'dob': student.dob,
        'gender': student.get_gender_display(),
        'courses_count': courses_count,
    }

    return render(request, 'student_profile.html', profile_data)

def edit_profile(request):
    if not request.user.is_authenticated:
        return redirect('login') 

    user = request.user
    base_template = 'base.html'  

    # Determine the user's type and set the base template accordingly
    try:
        if hasattr(user, 'student'):  
            base_template = 'base.html'
        elif hasattr(user, 'teacher'):  
            base_template = 'teacher_base.html'
        else:
            return HttpResponseForbidden("User type not recognized.")  
    except Exception as e:
        return HttpResponseServerError(f"Error determining user type: {str(e)}")

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            # Update basic user fields
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.contact = form.cleaned_data['contact']
            if 'profile_picture' in request.FILES:
                user.profile_picture = form.cleaned_data['profile_picture']

            # Save additional fields based on user type
            if hasattr(user, 'student'):  
                user.student.dob = form.cleaned_data['dob']
                user.student.gender = form.cleaned_data['gender']
                user.student.save()
            elif hasattr(user, 'teacher'):  
                user.teacher.dob = form.cleaned_data['dob']
                user.teacher.gender = form.cleaned_data['gender']
                user.teacher.save()

            user.save()
            return redirect('profile') 
    else:
        # Pre-fill form data based on user type
        initial_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'contact': user.contact,
            'profile_picture': user.profile_picture,
        }

        if hasattr(user, 'student'):
            initial_data.update({
                'dob': user.student.dob,
                'gender': user.student.gender,
            })
        elif hasattr(user, 'teacher'):
            initial_data.update({
                'dob': user.teacher.dob,
                'gender': user.teacher.gender,
            })

        form = UserProfileForm(initial=initial_data)

    return render(request, 'edit_profile.html', {
        'form': form,
        'base_template': base_template,  
    })

# View to add a course to the wishlist
def add_to_wishlist(request, course_id, course_type):
    if not request.user.is_authenticated:
        return redirect('signin')  
    
    # Ensure that request.user is treated as a Student
    try:
        student = request.user.student  
    except Student.DoesNotExist:
        return redirect('index')  

    if course_type == 'online':
        course = get_object_or_404(OnlineCourse, id=course_id)
    elif course_type == 'offline':
        course = get_object_or_404(OfflineCourse, id=course_id)
    else:
        return redirect('index')

    # Check if the course is already in the wishlist
    wishlist_item = Wishlist.objects.filter(student=student, 
                                            online_course=course if course_type == 'online' else None, 
                                            offline_course=course if course_type == 'offline' else None).first()
    
    if not wishlist_item:
        Wishlist.objects.create(student=student,  # Now it's guaranteed to be a Student instance
                                online_course=course if course_type == 'online' else None, 
                                offline_course=course if course_type == 'offline' else None)

    return redirect('wishlist')

def wishlist(request):
    if not request.user.is_authenticated:
        return redirect('signin')  
    
    
    wishlist_items = Wishlist.objects.filter(student=request.user)

    # Separate online and offline courses
    online_courses = [item.online_course for item in wishlist_items if item.online_course]
    offline_courses = [item.offline_course for item in wishlist_items if item.offline_course]

    # Fetch batches for each offline course
    for course in offline_courses:
        course.batches = Batch.objects.filter(course=course)

    context = {
        'online_courses': online_courses,
        'offline_courses': offline_courses,
    }
    return render(request, 'wishlist.html', context)

def remove_from_wishlist(request, course_id, course_type):
    if not request.user.is_authenticated:
        return redirect('signin')  
    
    # Determine course type and get the course
    if course_type == 'online':
        course = get_object_or_404(OnlineCourse, id=course_id)
    elif course_type == 'offline':
        course = get_object_or_404(OfflineCourse, id=course_id)
    else:
        return redirect('wishlist')  
    
    # Remove course from wishlist
    wishlist_item = Wishlist.objects.filter(student=request.user, 
                                            online_course=course if course_type == 'online' else None, 
                                            offline_course=course if course_type == 'offline' else None).first()
    
    if wishlist_item:
        wishlist_item.delete() 
    
    return redirect('wishlist') 

# def sorting(request):
#     sort_by = request.GET.get('sort')
#     if sort_by == 'lth':
#         online_courses = OnlineCourse.objects.order_by('fees')
#         offline_courses = OfflineCourse.objects.order_by('fees')
#     else:
#         online_courses = OnlineCourse.objects.order_by('-fees')
#         offline_courses = OfflineCourse.objects.order_by('-fees')

#     context = {
#         'online_courses': online_courses,
#         'offline_courses': offline_courses
#     }
#     return render(request, "index.html", context)

def online_course_details(request, id):
    course = get_object_or_404(OnlineCourse, id=id)
    context = {
        'course': course,
        'course_type': 'online',
    }
    return render(request, 'course_details.html', context)

# View for offline course details
def offline_course_details(request, id):
    course = get_object_or_404(OfflineCourse, id=id)
    today = datetime.now().date()

    # Show batches that:
    # 1. Have not started yet (start_date >= today)
    # 2. Started within the last 7 days (start_date + 7 >= today)
    batches = Batch.objects.filter(
        course=course
    ).filter(start_date__gte=today - timedelta(days=7))  # Show batches until 7 days after start_date

    context = {
        'course': course,
        'course_type': 'offline',
        'batches': batches,
    }
    return render(request, 'course_details.html', context)

def add_cart(request, id, course_type):
    if not request.user.is_authenticated:
        # Redirect to the sign-in page if the user is not authenticated
        return redirect('signin')

    if course_type == 'online':
        course = OnlineCourse.objects.get(id=id)
        # Check if the course is already purchased
        already_purchased = OrderItem.objects.filter(
            order__student=request.user.student,
            order__payment_status='paid',
            online_course=course
        ).exists()

        if already_purchased:
            messages.info(request, f'You have already purchased the course: {course.title}.')
            return redirect('purchased_courses')

        # Add the course to the cart
        CartOnlineCourse.objects.create(student=request.user.student, course=course)
        messages.success(request, f'{course.title} added to your cart.')

    elif course_type == 'offline':
        course = OfflineCourse.objects.get(id=id)
        batch_id = request.POST.get('selected_batch')
        batch = Batch.objects.get(id=batch_id)

        # Check if the course and batch are already purchased
        already_purchased = OrderItem.objects.filter(
            order__student=request.user.student,
            order__payment_status='paid',
            offline_course=course,
            offline_course__batch=batch 
        ).exists()

        if already_purchased:
            messages.info(request, f'You have already purchased the course: {course.title} for this batch.')
            return redirect('purchased_courses')

        # Add the course to the cart
        CartOfflineCourse.objects.create(student=request.user.student, course=course, batch=batch)
        messages.success(request, f'{course.title} added to your cart.')

    return redirect('cart')

def cart(request):
    if request.user.is_authenticated:
        student = request.user.student

        online_courses = CartOnlineCourse.objects.filter(student=student)
        offline_courses = CartOfflineCourse.objects.filter(student=student)

        # Calculate the total amount
        total_amount = sum([item.course.fees for item in online_courses]) + sum([item.course.fees for item in offline_courses])

        context = {
            'online_courses': online_courses,
            'offline_courses': offline_courses,
            'total_amount': total_amount,
        }

        return render(request, 'cart.html', context)
    else:
        return redirect('signin')

def cart_count(request):
    if request.user.is_authenticated:
        student = request.user.student

        online_courses = CartOnlineCourse.objects.filter(student=student)
        offline_courses = CartOfflineCourse.objects.filter(student=student)

        # Calculate the total number of items in the cart
        total_items = online_courses.count() + offline_courses.count()

        return JsonResponse({'cart_count': total_items})
    else:
        return JsonResponse({'cart_count': 0})

def remove_item(request, id, course_type):
    cart_online_course = None  
    cart_offline_course = None 

    # Try to remove the specific online course for the logged-in student
    if course_type == 'online':
        cart_online_course = CartOnlineCourse.objects.filter(course__id=id, student=request.user.student).first()
        if cart_online_course:
            cart_online_course.delete()
            messages.success(request, "Online course removed from the cart.")
        else:
            messages.error(request, "Online course not found in your cart.")
    
    # Try to remove the specific offline course for the logged-in student
    elif course_type == 'offline':
        cart_offline_course = CartOfflineCourse.objects.filter(course__id=id, student=request.user.student).first()
        if cart_offline_course:
            cart_offline_course.delete()
            messages.success(request, "Offline course removed from the cart.")
        else:
            messages.error(request, "Offline course not found in your cart.")
    
    # If neither online nor offline course was found, display an error
    if not cart_online_course and not cart_offline_course:
        messages.error(request, "Course not found in your cart.")
    
    return redirect('cart')

def generate_unique_order_id():
    while True:
        order_id = random.randint(1000, 9999)
        if not Order.objects.filter(order_id=order_id).exists():
            return order_id

def confirm_order(request):
    if request.user.is_authenticated:
        student = request.user.student

        # Fetch cart items for both online and offline courses
        online_cart_items = CartOnlineCourse.objects.filter(student=student)
        offline_cart_items = CartOfflineCourse.objects.filter(student=student)

        # Calculate the total amount
        total_amount = sum([item.course.fees for item in online_cart_items]) + sum([item.course.fees for item in offline_cart_items])

        if request.method == "POST":
            # Generate a unique order ID
            order_id = generate_unique_order_id()

            # Create a new order
            order = Order.objects.create(
                order_id=order_id,
                student=student,
                order_amount=total_amount,
                payment_status='unpaid',
                order_status='pending'
            )

            # Create OrderItem entries for all cart items
            for item in online_cart_items:
                OrderItem.objects.create(
                    order=order,
                    online_course=item.course,
                    unit_price=item.course.fees
                )

            for item in offline_cart_items:
                OrderItem.objects.create(
                    order=order,
                    offline_course=item.course,
                    unit_price=item.course.fees
                )

            # Clear the cart
            online_cart_items.delete()
            offline_cart_items.delete()

            messages.success(request, "Order confirmed successfully!")
            return redirect('payment', order_id=order.order_id)  

        context = {
            'online_courses': online_cart_items,
            'offline_courses': offline_cart_items,
            'total_amount': total_amount,
        }

        return render(request, 'confirm_order.html', context)
    else:
        return redirect('signin')


def payment(request, order_id):
    if request.user.is_authenticated:
        order = get_object_or_404(Order, order_id=order_id)
        total_amount = order.order_amount

        # Convert total_amount to an integer or float
        total_amount_in_paise = int(total_amount * 100) 

        # Initialize Razorpay client
        client = razorpay.Client(auth=("rzp_test_n0lhpmrEfeIhGJ", "UOrbXQGnsEc2dhB1IFg0zNWZ"))

        # Create a Razorpay order
        data = {
            "amount": total_amount_in_paise, 
            "currency": "INR",
            "receipt": str(order.order_id),
            "payment_capture": 1,  
        }
        payment = client.order.create(data=data)

        # Pass payment details to the template
        context = {
            "payment": payment,  
            "data": {
                "amount": total_amount,
                "receipt": order.order_id
            },
        }
        return render(request, 'pay.html', context)

    else:
        return redirect('signin')
def payment_success(request):
    payment_id = request.GET.get('payment_id', 'N/A')
    order_id = request.GET.get('order_id', 'N/A')
    order = get_object_or_404(Order, order_id=order_id)

    # Update payment status
    order.payment_status = 'paid'
    order.save()

    # Prepare email details
    online_courses = []
    offline_courses = []

    for order_item in order.orderitem_set.all():
        if order_item.online_course:  
            course = order_item.online_course
            online_courses.append(course.title)
        elif order_item.offline_course:  
            course = order_item.offline_course
            batch = Batch.objects.filter(course=course).first()
            if batch:
                # Enroll the student in the batch and trigger save (which will increment current_students)
                Enrollment.objects.create(student=request.user.student, batch=batch)

                offline_courses.append({
                    'name': course.title,
                    'batch_code': batch.batch_code,
                    'teacher': f"{batch.teacher.first_name} {batch.teacher.last_name}",
                    'start_date': batch.start_date.strftime('%d-%m-%Y'),
                    'end_date': batch.end_date.strftime('%d-%m-%Y'),
                    'start_time': batch.start_time.strftime('%I:%M %p'),
                    'end_time': batch.end_time.strftime('%I:%M %p'),
                })

    # Render email template
    email_subject = "Enrollment Confirmation - Goonj Music Academy"
    email_body = render_to_string('emails/enrollment_confirmation.html', {
        'user': request.user,
        'online_courses': online_courses,
        'offline_courses': offline_courses,
    })

    # Send email
    email = EmailMessage(
        subject=email_subject,
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[request.user.email],
    )
    email.content_subtype = 'html'  
    email.send()

    # Return success page
    return render(request, 'payment_success.html', {
        'payment_id': payment_id,
        'order_id': order_id,
        'success_message': 'Payment was successful. You are now enrolled in the selected courses!'
    })


def my_orders(request):
    if request.user.is_authenticated:
        # Fetch all orders for the logged-in student where the payment is successful
        orders = Order.objects.filter(student=request.user.student, payment_status='paid')

        # Fetch the courses related to the orders (OrderItems)
        order_items = OrderItem.objects.filter(order__in=orders)

        # Pass orders and order items to the context
        context = {
            'orders': orders,
            'order_items': order_items
        }

        return render(request, 'my_orders.html', context)
    else:
        return redirect('signin')


def purchased_courses(request):
    if request.user.is_authenticated:
        # Check if the logged-in user is a student
        if hasattr(request.user, 'student'):
            # Fetch all order items related to the logged-in student where the payment is successful
            order_items = OrderItem.objects.filter(order__student=request.user.student, order__payment_status='paid')

            # Pass order_items to the context
            context = {
                'order_items': order_items
            }

            return render(request, 'purchased_courses.html', context)
        else:
            # If the user is not a student, show an error or redirect
            return render(request, '403.html') 
    else:
        # If the user is not authenticated, redirect to the signin page
        return redirect('signin')


def generate_otp(request):
    otp = random.randint(100000, 999999)
    return otp


def forgot_password(request):
    if request.method == 'POST':
        form = PasswordResetEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                otp = generate_otp(request)
                request.session['otp'] = otp
                request.session['request_user_id'] = user.id
                
                send_mail(
                    'Password Reset OTP',  
                    f'Your OTP for password reset is: {otp}', 
                    settings.EMAIL_HOST_USER, 
                    [user.email], 
                    fail_silently=False,
                )
                return redirect('verify_otp')
                
            except CustomUser.DoesNotExist:
                messages.error(request, 'No User was found with this email address')
                return render(request, 'password_reset_request.html', {'form': form})
    else:
        form = PasswordResetEmailForm()
    
    return render(request, 'password_reset_request.html', {'form': form})


def verify_otp(request):
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        otp_stored = request.session.get('otp')

        if otp_entered and otp_stored and otp_entered == str(otp_stored): 
            user_id = request.session.get('request_user_id')
            if user_id:
                # Clear session data to avoid repeated OTP usage
                del request.session['otp']
                del request.session['request_user_id']
                
                return redirect('reset_password', user_id=user_id)
            else:
                messages.error(request, "Session Expired. Please Request OTP again.")
                return redirect('forgot_password')
        else:
            messages.error(request, "Invalid or expired OTP.")
            return render(request, 'verify_otp.html')

    return render(request, 'verify_otp.html')



def reset_password(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    if request.method == "POST":
        form = SetPasswordForm(user=user,data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password Reset Successful")
            return redirect('signin')
    else:
        form = SetPasswordForm(user=user)
    return render(request, 'reset_password.html', {'form':form})


def teacher_batches(request):
    
    if not request.user.is_authenticated:
        return redirect('signin')  

    # Check if the user is a teacher
    if not hasattr(request.user, 'teacher'):
        return render(request, '403.html') 

    # Fetch batches assigned to the teacher
    teacher = request.user.teacher
    batches = Batch.objects.filter(teacher=teacher)  

    
    batch_student_mapping = {}
    for batch in batches:
        
        enrolled_students = Enrollment.objects.filter(batch=batch).values_list('student', flat=True)
        students = Student.objects.filter(id__in=enrolled_students)  
        batch_student_mapping[batch] = students

    context = {
        'batch_student_mapping': batch_student_mapping,
    }
    return render(request, 'batches.html', context)

def view_enrolled_students(request):
    
    if not request.user.is_authenticated:
        return redirect('signin')  

    # Check if the user is a teacher
    if not hasattr(request.user, 'teacher'):
        return render(request, '403.html') 

    # Fetch the teacher
    teacher = request.user.teacher

    
    batches = Batch.objects.filter(teacher=teacher)

    
    batch_student_mapping = {}
    for batch in batches:
        
        enrolled_students = Enrollment.objects.filter(batch=batch).values_list('student', flat=True)
        students = Student.objects.filter(id__in=enrolled_students)  
        batch_student_mapping[batch] = students

    context = {
        'batch_student_mapping': batch_student_mapping,
    }
    return render(request, 'view_enrolled_students.html', context)



def teacher_index(request):
    
    if not request.user.is_authenticated:
        raise Http404("You must be logged in to access this page.") 
    
    
    try:
        teacher = request.user.teacher  
    except AttributeError:
        raise Http404("You do not have access to this page.") 
    
    
    batches = (
        Batch.objects.filter(teacher=teacher)
        .annotate(active_students=Count('enrollment__id', filter=Q(enrollment__status='active')))
    )

    
    return render(request, 'teacher_index.html', {'batches': batches})

def batch_details(request, batch_id):
    
    if not request.user.is_authenticated:
        raise Http404("You must be logged in to access this page.")

    # Ensure the authenticated user is a teacher
    try:
        teacher = request.user.teacher
    except AttributeError:
        raise Http404("You do not have access to this page.")

    # Fetch the batch handled by the teacher
    batch = get_object_or_404(Batch, id=batch_id, teacher=teacher)

    # Get current time
    current_time = timezone.now()

    # Check if the user has a related student profile
    try:
        student = request.user.student
    except AttributeError:
        student = None  

    if student:
        
        announcements = Announcement.objects.filter(batch=batch, created_at__gte=current_time, recipients__in=[student]).order_by('-created_at')
    else:
        announcements = Announcement.objects.filter(batch=batch, created_at__gte=current_time).order_by('-created_at')

    
    sessions = Session.objects.filter(batch=batch, date__gte=current_time).order_by('-date')
    upcoming_sessions = sessions 
    attendance = Attendance.objects.filter(session__in=upcoming_sessions)

    return render(request, 'batch_details.html', {
        'batch': batch,
        'sessions': sessions,
        'announcements': announcements,
        'attendance': attendance  
    })


def mark_attendance(request, batch_id, session_id):
    
    if not request.user.is_authenticated:
        raise Http404("You must be logged in to access this page.")

    # Ensure the authenticated user is a teacher
    try:
        teacher = request.user.teacher
    except AttributeError:
        raise Http404("You do not have access to this page.")

    # Fetch the batch handled by the teacher
    batch = get_object_or_404(Batch, id=batch_id, teacher=teacher)

    # Fetch the session to mark attendance for
    session = get_object_or_404(Session, id=session_id, batch=batch)

    # Get the students enrolled in this batch
    students = batch.enrollment_set.all()  

    if request.method == "POST":
        # Process attendance form submission
        for enrollment in students:
            status = request.POST.get(f'status_{enrollment.student.id}')
            notes = request.POST.get(f'notes_{enrollment.student.id}')
            if status:
                # Create or update the attendance record
                attendance, created = Attendance.objects.get_or_create(session=session, student=enrollment.student)
                attendance.status = status
                attendance.notes = notes
                attendance.save()
        return redirect('batch_details', batch_id=batch.id)

    return render(request, 'mark_attendance.html', {
        'batch': batch,
        'session': session,
        'sessions': batch.sessions.all(),
        'students': students
    })



def create_announcement(request, batch_id):
    
    if not request.user.is_authenticated:
        raise Http404("You must be logged in to access this page.")

    # Ensure the authenticated user is a teacher
    try:
        teacher = request.user.teacher
    except AttributeError:
        raise Http404("You do not have access to this page.")

    # Fetch the batch handled by the teacher
    batch = get_object_or_404(Batch, id=batch_id, teacher=teacher)

    if request.method == "POST":
        # Process announcement manually without form
        announcement_title = request.POST.get('title')
        announcement_message = request.POST.get('message')
        recipient_ids = request.POST.getlist('recipients')  

        if announcement_title and announcement_message:
            announcement = Announcement(batch=batch, title=announcement_title, message=announcement_message)
            announcement.save()

            if recipient_ids:
                
                students = Student.objects.filter(id__in=recipient_ids)
                announcement.recipients.set(students)

            messages.success(request, "Announcement created successfully.")
            return redirect('batch_details', batch_id=batch.id)
        else:
            messages.error(request, "Title and message are required.")

    
    students_in_batch = Student.objects.filter(batches=batch)

    return render(request, 'create_announcement.html', {'batch': batch, 'students_in_batch': students_in_batch})


def schedule_session(request, batch_id):
    if not request.user.is_authenticated:
        raise Http404("You must be logged in to access this page.")

    # Ensure the authenticated user is a teacher
    try:
        teacher = request.user.teacher
    except AttributeError:
        raise Http404("You do not have access to this page.")

    # Fetch the batch handled by the teacher
    batch = get_object_or_404(Batch, id=batch_id, teacher=teacher)

    if request.method == "POST":
        session_date = request.POST.get('date')
        session_topic = request.POST.get('topic')
        session_start_time = request.POST.get('start_time')  
        session_end_time = request.POST.get('end_time')  

        # Validate the session date
        if session_date:
            session_date_obj = date.fromisoformat(session_date)  # Convert string to date object
            if session_date_obj < date.today():
                return render(
                    request, 
                    'schedule_session.html', 
                    {'batch': batch, 'error': "You cannot schedule a session for a past date."}
                )

        if session_date and session_topic and session_start_time and session_end_time:
            session = Session(
                batch=batch,
                date=session_date,
                topic=session_topic,
                start_time=session_start_time,
                end_time=session_end_time
            )
            session.save()
            return redirect('batch_details', batch_id=batch.id)

    return render(request, 'schedule_session.html', {'batch': batch})

def messages_page(request):
    
    if not request.user.is_authenticated:
        return redirect('login') 

    # Ensure the user is a teacher
    if not hasattr(request.user, 'teacher'):
        return redirect('403')  

    # Fetch received and sent messages
    received_messages = Message.objects.filter(receiver=request.user)
    sent_messages = Message.objects.filter(sender=request.user)

    if request.method == 'POST':
        # Handle message sending
        receiver_id = request.POST.get('receiver')
        subject = request.POST.get('subject')
        content = request.POST.get('content')

        try:
            receiver = Teacher.objects.get(id=receiver_id)
            Message.objects.create(
                sender=request.user,
                receiver=receiver,
                subject=subject,
                content=content
            )
            
            # Success message
            messages.success(request, f'Message sent to {receiver.first_name} {receiver.last_name}!')
        except Teacher.DoesNotExist:
            # Error message
            messages.error(request, "Selected teacher does not exist.")
        
        return redirect('messages')

    teachers = Teacher.objects.exclude(id=request.user.id) 

    context = {
        'received_messages': received_messages,
        'sent_messages': sent_messages,
        'teachers': teachers,
    }
    
    return render(request, 'messages.html', context)

def schedule_view(request):
    if not request.user.is_authenticated:
        raise Http404("You must be logged in to access this page.")

    # Ensure the authenticated user is a teacher
    try:
        teacher = request.user.teacher
    except AttributeError:
        raise Http404("You do not have access to this page.")

    
    batches = Batch.objects.filter(teacher=teacher)

   
    now = timezone.now()
    sessions = Session.objects.filter(batch__in=batches, date__gte=now).order_by('date', 'start_time')

    return render(request, 'schedule.html', {'sessions': sessions})

def online_course_content(request, course_id, content_id):
    # Get the specific content object using both course_id and content_id
    course_content = get_object_or_404(OnlineCourseContent, id=content_id, course_id=course_id)

    # Get the associated course from the content object
    course = course_content.course

    # Get the student's notes for this course (if any)
    student_notes = Notes.objects.filter(student=request.user.student, course=course).first()

    # Get all course content for the specific course (filter by the course)
    all_course_contents = OnlineCourseContent.objects.filter(course=course).order_by('title')

    if request.method == 'POST':
        content = request.POST.get('content')

        # If student already has notes, update them, otherwise create new notes
        if student_notes:
            student_notes.content = content
            student_notes.save()
        else:
            Notes.objects.create(student=request.user.student, course=course, content=content)

        # Redirect to the same page after submitting
        return redirect(reverse('online_course_content', args=[course.id, content_id]))

    # Render the content to the template
    return render(request, 'online_course_content.html', {
        'course_content': course_content,
        'student_notes': student_notes,
        'all_course_contents': all_course_contents,
    })


def offline_course_content(request, content_id, course_id):
    # Fetch the specific course by its course_id
    course = get_object_or_404(OfflineCourse, id=course_id)
    
    # Fetch the specific course content by its content_id
    course_content = get_object_or_404(OfflineCourseContent, id=content_id, course=course)

    # Now filter content based on the same course that course_content belongs to
    related_course_contents = OfflineCourseContent.objects.filter(course=course)

    # Initialize variables for attendance, announcements, and teacher-uploaded files
    announcements = []
    teacher_uploaded_files = []


    if course:
        related_batches = course.batch_set.all()

        # Fetch announcements for the batches related to the course and specific student
        announcements = Announcement.objects.filter(
            Q(batch__in=related_batches),
            Q(recipients=request.user.student) | Q(recipients__isnull=True)
        ).distinct()

        # Filter the teacher-uploaded files by the course, not by batch
        teacher_uploaded_files = UploadOfflineCourseContent.objects.filter(
            batch__course=course  # Ensure the uploaded files belong to the same course
        )
    else:
        announcements = Announcement.objects.filter(recipients__isnull=True)

    return render(request, 'offline_course_content.html', {
        'course_content': course_content,
        'related_course_contents': related_course_contents,
        'announcements': announcements,
        'teacher_uploaded_files': teacher_uploaded_files,
    })

def delete_notes(request, note_id):
    note = get_object_or_404(Notes, id=note_id)
    
    if note.student == request.user.student:
        note.delete()
    return redirect('online_course_content', content_id=note.course.id)


def upload_course_content(request, batch_id):
    # Get the batch object
    batch = get_object_or_404(Batch, id=batch_id)

    
    if not hasattr(request.user, 'teacher') or batch.teacher != request.user.teacher:
        messages.error(request, "You are not authorized to upload content for this batch.")
        return redirect('some_error_page')  

    if request.method == 'POST':
        # Retrieve form data
        content_title = request.POST.get('title')
        description = request.POST.get('description')  
        uploaded_file = request.FILES.get('file')

        # Validate inputs
        if not content_title or not uploaded_file:
            messages.error(request, "Title and file are required.")
            return redirect('upload_course_content', batch_id=batch_id)

        # Create the course content
        try:
            UploadOfflineCourseContent.objects.create(
                batch=batch,
                title=content_title,
                description=description,
                file=uploaded_file,
                teacher=request.user.teacher
            )
            messages.success(request, "Course content uploaded successfully.")
        except ValidationError as e:
            messages.error(request, f"Error: {e.message}")
        except Exception as e:
            messages.error(request, "An unexpected error occurred while uploading content.")
        
        return redirect('upload_course_content', batch_id=batch_id) 

    return render(request, 'upload_course_content.html', {
        'batch': batch
    })


@csrf_exempt
def chatbot_response(request):
    if request.method == 'POST':
       
        try:
            data = json.loads(request.body)
            query = data.get('query', '').lower() 
        except json.JSONDecodeError:
            return JsonResponse({'response': 'Error: Invalid input.'})

       
        query = query.strip().lower()

      
        questions = FAQ.objects.values_list('question', flat=True)

       
        best_match = process.extractOne(query, questions)

       
        print(f"User Query: {query}")
        print(f"Best Match: {best_match}")

        if best_match and best_match[1] > 80:  
           
            response = FAQ.objects.get(question=best_match[0])
            return JsonResponse({'response': response.answer})
        else:
          
            suggestions = process.extract(query, questions, limit=5)  
            suggestion_list = [suggestion[0] for suggestion in suggestions]

            return JsonResponse({
                'response': "Sorry, I couldn't find an answer to your question.",
                'suggestions': suggestion_list 
            })

    return JsonResponse({'response': "Invalid request method."}, status=400)
