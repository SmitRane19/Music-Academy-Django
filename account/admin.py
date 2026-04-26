from django.contrib import admin
from .models import CustomUser, Student, Teacher
from product.models import Batch

# Base Admin for CustomUser
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'contact', 'is_staff', 'is_active')
    ordering = ('username',)
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active')

# Admin for Student
class StudentAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'contact', 'dob', 'gender', 'profile_picture', 'get_batches')
    ordering = ('username',)
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('gender', 'batches')

    def get_batches(self, obj):
        """Displays the batches the student is enrolled in."""
        return ", ".join([batch.batch_code for batch in obj.batches.all()])

    get_batches.short_description = 'Batches'  # Rename the column in the admin panel


# Admin for Teacher
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'contact', 'dob', 'gender', 'category', 'profile_picture')
    ordering = ('username',)
    search_fields = ('username', 'email', 'first_name', 'last_name', 'category')
    list_filter = ('gender', 'category')

# Registering models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Teacher, TeacherAdmin)
