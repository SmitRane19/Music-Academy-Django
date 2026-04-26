"""
URL configuration for Goonj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from account import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('teacher_index/', views.teacher_index, name='teacher_index'),
    path('student_signup/', views.student_signup, name='student_signup'),
    path('teacher_signup/',views.teacher_signup,name='teacher_signup'),
    path('signin/',views.signin,name='signin'),
    path('signout/',views.signout,name='signout'),
    path('category/', views.category, name='category'),
    # path('search_bar/', views.search_bar, name='search_bar'),
    path('sorting/', views.sorting, name='sorting'),
    # path('course_details/<int:id>/', views.course_details, name='course_details'),
    path('add_cart/<int:id>/<str:course_type>/', views.add_cart, name='add_cart'),
    
    path('cart/', views.cart, name='cart'),
    path('cart/count/', views.cart_count, name='cart_count'),
    path('remove_item/<int:id>/<str:course_type>/', views.remove_item, name='remove_item'),
    path('confirm_order/', views.confirm_order, name='confirm_order'),
    path('payment/<int:order_id>/', views.payment, name='payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('my_orders/', views.my_orders, name='my_orders'),
    path('course/online/<int:id>/', views.online_course_details, name='online_course_details'),
    path('course/offline/<int:id>/', views.offline_course_details, name='offline_course_details'),
    path('purchased_courses/', views.purchased_courses, name='purchased_courses'),
    path('search/', views.search_bar, name='search_bar'),
    path('about-us/', views.about_us, name='about_us'),
    path('profile/', views.profile, name='profile'),
     path('student/<int:student_id>/', views.student_profile, name='student_profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('add_to_wishlist/<int:course_id>/<str:course_type>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('remove_from_wishlist/<int:course_id>/<str:course_type>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('forgot_password',views.forgot_password,name='forgot_password'),
    path('verify_otp',views.verify_otp,name='verify_otp'),
    path('reset_password/<int:user_id>/', views.reset_password, name='reset_password'),
    path('teacher_batches/', views.teacher_batches, name='teacher_batches'),
    path('view_enrolled_students/',views.view_enrolled_students,name='view_enrolled_students'),
    path('batch/<int:batch_id>/', views.batch_details, name='batch_details'),
    path('batch/<int:batch_id>/mark_attendance/<int:session_id>/', views.mark_attendance, name='mark_attendance'),
    path('batch/<int:batch_id>/create_announcement/', views.create_announcement, name='create_announcement'),
    path('batch/<int:batch_id>/schedule_session/', views.schedule_session, name='schedule_session'),
    path('messages/', views.messages_page, name='messages'),
    path('schedule/',views.schedule_view,name='schedule'),
    path('online_course_content/<int:course_id>/<int:content_id>/', views.online_course_content, name='online_course_content'),
    path('offline_course_content/<int:course_id>/<int:content_id>/', views.offline_course_content, name='offline_course_content'),
    path('delete_notes/<int:note_id>/', views.delete_notes, name='delete_notes'),
    path('upload-course-content/<int:batch_id>/', views.upload_course_content, name='upload_course_content'),
    path('chatbot-api/', views.chatbot_response, name='chatbot_response'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)