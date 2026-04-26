from django.contrib import admin
from django.db import models
from ckeditor.widgets import CKEditorWidget
from django import forms
from .models import Category, Batch, Enrollment, Order, OrderItem, OfflineCourse, OnlineCourse,CartOnlineCourse,CartOfflineCourse, Session,Announcement,Attendance,OnlineContentFile,OnlineCourseContent,OfflineContentFile,OfflineCourseContent,Notes,FAQ,UploadOfflineCourseContent

# Register Category model
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

admin.site.register(Category, CategoryAdmin)

class OnlineCourseAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget},  # Apply CKEditor to all TextFields
    }
    list_display = ['id','title', 'category', 'fees', 'duration', 'created_at', 'updated_at']
    list_filter = ['category']
    search_fields = ['title', 'description']


admin.site.register(OnlineCourse, OnlineCourseAdmin)


class OfflineCourseAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget},  # Apply CKEditor to all TextFields
    }
    list_display = ['title', 'category', 'fees', 'course_code', 'created_at', 'updated_at']
    search_fields = ['title', 'course_code']


admin.site.register(OfflineCourse, OfflineCourseAdmin)

# Register Batch model
class BatchAdmin(admin.ModelAdmin):
    list_display = ['batch_code', 'course', 'teacher', 'start_date', 'end_date']
    list_filter = ['course', 'teacher']
    search_fields = ['batch_code', 'course__title']

admin.site.register(Batch, BatchAdmin)

# Register Enrollment model
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'batch', 'enrollment_date', 'status']
    list_filter = ['status', 'batch']
    search_fields = ['student__username', 'batch__batch_code']

admin.site.register(Enrollment, EnrollmentAdmin)

# Register Order model
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'student', 'order_date', 'payment_status', 'order_status', 'order_amount']
    list_filter = ['payment_status', 'order_status']
    search_fields = ['order_id', 'student__username']

admin.site.register(Order, OrderAdmin)

# Register OrderItem model
# Register CartOnlineCourse model
class CartOnlineCourseAdmin(admin.ModelAdmin):
    list_display = ['student', 'course']
    search_fields = ['student__username', 'course__title']
    
admin.site.register(CartOnlineCourse, CartOnlineCourseAdmin)

# Register CartOfflineCourse model
class CartOfflineCourseAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'batch']  # Add batch to the list_display
    search_fields = ['student__username', 'course__title', 'batch__batch_code']

admin.site.register(CartOfflineCourse, CartOfflineCourseAdmin)


# Register OrderItem model
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'get_course', 'unit_price']
    search_fields = ['order__order_id', 'online_course__title', 'offline_course__title']

    # Custom method to display course info in the admin list view
    def get_course(self, obj):
        if obj.online_course:
            return obj.online_course.title
        if obj.offline_course:
            return obj.offline_course.title
        return '-'
    get_course.short_description = 'Course'

admin.site.register(OrderItem, OrderItemAdmin)

from .models import Wishlist

# Register Wishlist model
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['student', 'get_online_course', 'get_offline_course']
    search_fields = ['student__username']
    
    # Custom methods to display course info in the admin list view
    def get_online_course(self, obj):
        return obj.online_course.title if obj.online_course else '-'
    get_online_course.short_description = 'Online Course'
    
    def get_offline_course(self, obj):
        return obj.offline_course.title if obj.offline_course else '-'
    get_offline_course.short_description = 'Offline Course'

admin.site.register(Wishlist, WishlistAdmin)

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('batch', 'date', 'start_time', 'end_time', 'topic')
    list_filter = ('batch', 'date')
    search_fields = ('topic', 'batch__batch_code')
    ordering = ('-date', 'start_time')
    autocomplete_fields = ('batch',)  # Enables quick lookup for related Batch

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('session', 'student', 'status', 'remarks')
    list_filter = ('status', 'session__batch', 'session__date')
    search_fields = ('student__username', 'session__topic', 'session__batch__batch_code')
    autocomplete_fields = ('session', 'student')  # Enables quick lookup for related Session and Student

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('batch', 'title', 'created_at', 'updated_at', 'recipient_selection')
    list_filter = ('batch', 'created_at')
    search_fields = ('title', 'message', 'batch__batch_code')
    ordering = ('-created_at',)
    autocomplete_fields = ('batch', 'recipients')  # Enable autocomplete for students (recipients)
    
    # Display method to show the selected recipients (students)
    def recipient_selection(self, obj):
        if obj.recipients.all():
            return ", ".join([student.name for student in obj.recipients.all()])
        else:
            return "All Students"
    recipient_selection.short_description = 'Recipients'

class OfflineContentFileInline(admin.TabularInline):
    model = OfflineContentFile
    extra = 1
    fields = ("title", "file_type", "file")
    verbose_name = "Content File"
    verbose_name_plural = "Content Files"

@admin.register(OfflineCourseContent)
class OfflineCourseContentAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "created_at")
    search_fields = ("title", "course__title")
    list_filter = ("course",)
    inlines = [OfflineContentFileInline]

@admin.register(UploadOfflineCourseContent)
class UploadOfflineCourseContentAdmin(admin.ModelAdmin):
    list_display = ("title", "batch", "teacher", "uploaded_at")
    search_fields = ("title", "batch__batch_code", "batch__course__title", "teacher__name")
    list_filter = ("batch", "teacher", "uploaded_at")
    date_hierarchy = "uploaded_at"
    ordering = ("-uploaded_at",)

class OnlineContentFileInline(admin.TabularInline):
    model = OnlineContentFile
    extra = 1
    fields = ("title", "file_type", "file")
    verbose_name = "Content File"
    verbose_name_plural = "Content Files"


@admin.register(OnlineCourseContent)
class OnlineCourseContentAdmin(admin.ModelAdmin):
    list_display = ('id',"title", "course", "created_at")
    search_fields = ("title", "course__title")
    list_filter = ("course",)
    inlines = [OnlineContentFileInline]

class NotesAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget(config_name='default'))  # Make sure to use the CKEditor widget

    class Meta:
        model = Notes
        fields = '__all__'

class NotesAdmin(admin.ModelAdmin):
    form = NotesAdminForm
    list_display = ('student', 'course', 'batch', 'created_at')
    search_fields = ('student__name', 'course__title', 'batch__batch_code')
    list_filter = ('course', 'batch')

admin.site.register(Notes, NotesAdmin)

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer')  # Columns to display in the admin list view
    search_fields = ('question',)         # Add a search box for questions
    list_per_page = 20                    # Pagination for long lists