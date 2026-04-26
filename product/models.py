from django.db import models
from account.models import *
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.timezone import now
from ckeditor.fields import RichTextField
from django.db.models import F



class Category(models.Model):
    name = models.CharField(
        max_length=100,
        choices=[
            ('guitar', 'Guitar'),
            ('piano', 'Piano'),
            ('vocals', 'Vocals'),
        ],
    )

    def __str__(self):
        return self.name


class OnlineCourse(models.Model):
    title = models.CharField(max_length=255)
    description = RichTextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    fees = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duration in hours")
    created_at = models.DateTimeField(default=timezone.now)  # Timestamp for creation
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)

    def __str__(self):
        return self.title


class OfflineCourse(models.Model):
    title = models.CharField(max_length=255)
    course_code = models.CharField(max_length=50, unique=True)
    description = RichTextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    fees = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)  # Timestamp for creation
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)

    def __str__(self):
        return self.title



class Batch(models.Model):
    course = models.ForeignKey(OfflineCourse, on_delete=models.CASCADE)
    batch_code = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(default="09:00:00")  # New field for start time
    end_time = models.TimeField(default="17:00:00")    # New field for end time
    teacher = models.ForeignKey('account.Teacher', on_delete=models.SET_NULL, null=True)
    max_students = models.PositiveIntegerField(default=30)  # Maximum number of students
    current_students = models.PositiveIntegerField(default=0)  # Number of students enrolled

    def clean(self):
        """Validation for start_date, end_date, start_time, end_time, and student count."""
        # Ensure the start date is not in the past
        if self.start_date < timezone.now().date():
            raise ValidationError("The start date cannot be earlier than today.")
        
        # Ensure the end date is not earlier than the start date
        if self.end_date < self.start_date:
            raise ValidationError("The end date cannot be earlier than the start date.")
        
        # Ensure start time is before end time
        if self.start_time >= self.end_time:
            raise ValidationError("The start time must be earlier than the end time.")
        
        # Ensure the current_students count does not exceed max_students
        if self.current_students > self.max_students:
            raise ValidationError("The number of students exceeds the maximum allowed for this batch.")

    def save(self, *args, **kwargs):
        """Override save to ensure clean method is called."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.batch_code} - {self.course.title} "
            f"({self.current_students}/{self.max_students} students, {self.start_date} {self.start_time} - {self.end_date} {self.end_time})"
        )




class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ]
    student = models.ForeignKey('account.Student', on_delete=models.RESTRICT)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    enrollment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')

    def save(self, *args, **kwargs):
        # Increment the current_students count for the related batch if the status is 'active'
        if self.status == 'active' and self.pk is None:  # Ensure it's a new enrollment
            batch = self.batch
            if batch.current_students < batch.max_students:  # Ensure space is available
                # Use the F expression to atomically increment current_students in the database
                Batch.objects.filter(id=batch.id).update(current_students=F('current_students') + 1)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.batch}"


class Order(models.Model):
    order_id = models.CharField(max_length=50, primary_key=True)
    student = models.ForeignKey('account.Student', on_delete=models.CASCADE)
    order_date = models.DateField(auto_now_add=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('paid', 'Paid'),
            ('unpaid', 'Unpaid'),
        ],
        default='unpaid',
    )
    order_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
        ],
        default='pending',
    )
    order_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.order_id


class CartOnlineCourse(models.Model):
    student = models.ForeignKey('account.Student', on_delete=models.CASCADE)
    course = models.ForeignKey(OnlineCourse, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student.username} - {self.course.title}"

class CartOfflineCourse(models.Model):
    student = models.ForeignKey('account.Student', on_delete=models.CASCADE)
    course = models.ForeignKey(OfflineCourse, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True)  # Allowing None/empty for batch

    def __str__(self):
        return f"{self.student} - {self.course} - {self.batch}"



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    online_course = models.ForeignKey(OnlineCourse, on_delete=models.CASCADE, null=True, blank=True)
    offline_course = models.ForeignKey(OfflineCourse, on_delete=models.CASCADE, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.online_course and self.offline_course:
            raise ValueError("An OrderItem cannot have both an online and offline course.")
        if not self.online_course and not self.offline_course:
            raise ValueError("An OrderItem must have either an online or offline course.")
        
        # Set the price based on the course type
        if self.online_course:
            self.unit_price = self.online_course.fees
        elif self.offline_course:
            self.unit_price = self.offline_course.fees

        super().save(*args, **kwargs)

    def __str__(self):
        if self.online_course:
            return f"Online Course: {self.online_course.title} - Price: ₹{self.unit_price}"
        elif self.offline_course:
            return f"Offline Course: {self.offline_course.title} - Price: ₹{self.unit_price}"
        
class Wishlist(models.Model):
    student = models.ForeignKey('account.Student', on_delete=models.CASCADE)
    online_course = models.ForeignKey(OnlineCourse, on_delete=models.CASCADE, null=True, blank=True)
    offline_course = models.ForeignKey(OfflineCourse, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = (('student', 'online_course'), ('student', 'offline_course'))

    def __str__(self):
        return f"Wishlist of {self.student.username}"
    

class Session(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='sessions')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    topic = models.CharField(max_length=255, help_text="Topic covered in this session")

    def __str__(self):
        return f"Session on {self.date} ({self.topic}) for {self.batch.batch_code}"

    class Meta:
        unique_together = (('batch', 'date', 'start_time'),)
        ordering = ['-date', 'start_time']

class Attendance(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey('account.Student', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=[
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('late', 'Late'),
        ],
        default='absent',
    )
    remarks = models.TextField(blank=True, null=True, help_text="Optional remarks for the student's attendance")

    def __str__(self):
        return f"{self.student} - {self.session} ({self.status})"

    class Meta:
        unique_together = (('session', 'student'),)

class Announcement(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=255, help_text="Short title for the announcement")
    message = models.TextField(help_text="Detailed announcement message")
    recipients = models.ManyToManyField('account.Student', blank=True, related_name='announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Announcement: {self.title} ({self.batch.batch_code})"

    class Meta:
        ordering = ['-created_at']


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        limit_choices_to={'is_teacher': True},  # Ensure sender is a teacher
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        limit_choices_to={'is_teacher': True},  # Ensure receiver is a teacher
    )
    subject = models.CharField(max_length=100)
    content = models.TextField()
    timestamp = models.DateTimeField(default=now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'Message from {self.sender} to {self.receiver}: {self.subject[:20]}'

    class Meta:
        ordering = ['-timestamp']

class OnlineCourseContent(models.Model):
    course = models.ForeignKey(OnlineCourse, on_delete=models.CASCADE, related_name="contents")
    title = models.CharField(max_length=255, help_text="Title for the content (e.g., Module 1)")
    description = RichTextField(blank=True, null=True, help_text="Optional description for this content")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.course.title}"


class OnlineContentFile(models.Model):
    content = models.ForeignKey(
        OnlineCourseContent, on_delete=models.CASCADE, related_name="files"
    )
    file_type_choices = [
        ("pdf", "PDF"),
        ("video", "Video"),
    ]
    file_type = models.CharField(max_length=10, choices=file_type_choices)
    file = models.FileField(upload_to="online_course_files/")
    title = models.CharField(max_length=255, help_text="Title for the file")

    def __str__(self):
        return f"{self.title} ({self.get_file_type_display()})"

class OfflineCourseContent(models.Model):
    course = models.ForeignKey(OfflineCourse, on_delete=models.CASCADE, related_name="contents")
    title = models.CharField(max_length=255, help_text="Title for the content (e.g., Module 1)")
    description = RichTextField(blank=True, null=True, help_text="Optional description for this content")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.course.title}"
    
class OfflineContentFile(models.Model):
    content = models.ForeignKey(
        OfflineCourseContent, on_delete=models.CASCADE, related_name="files"
    )
    file_type_choices = [
        ("pdf", "PDF"),
        ("video", "Video"),
    ]
    file_type = models.CharField(max_length=10, choices=file_type_choices)
    file = models.FileField(upload_to="offline_course_files/")
    title = models.CharField(max_length=255, help_text="Title for the file")

    def __str__(self):
        return f"{self.title} ({self.get_file_type_display()})"

class UploadOfflineCourseContent(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="uploaded_contents")
    title = models.CharField(max_length=255, help_text="Title of the content (e.g., Week 1 Material)")
    description = RichTextField(blank=True, null=True, help_text="Optional description for this content")
    file = models.FileField(upload_to="offline_course_content_files/", help_text="Upload content file")
    file_type_choices = [
        ("pdf", "PDF"),
        ("video", "Video"),
        # Add more types if needed
    ]
    file_type = models.CharField(max_length=10, choices=file_type_choices, default="pdf",help_text="Type of the content file")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    teacher = models.ForeignKey(
        'account.Teacher', on_delete=models.CASCADE, related_name="uploaded_contents"
    )

    def clean(self):
        """Ensure the teacher matches the teacher assigned to the batch."""
        if self.teacher != self.batch.teacher:
            raise ValidationError("The teacher uploading the content must be assigned to the batch.")

    def save(self, *args, **kwargs):
        """Override save to ensure clean method is called."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.batch.batch_code}"




class Notes(models.Model):
    student = models.ForeignKey('account.Student', on_delete=models.CASCADE, related_name="notes")
    content = RichTextField(help_text="Personal notes for the course")
    course = models.ForeignKey(OnlineCourse, on_delete=models.CASCADE, blank=True, null=True, related_name="online_notes")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, blank=True, null=True, related_name="offline_notes")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notes by {self.student} for {self.course or self.batch}"
    
class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return self.question