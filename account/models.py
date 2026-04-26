from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from product.models import Batch,OnlineCourse

class CustomUser(AbstractUser):
    contact = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\d{10}$', 'Enter a valid 10-digit contact number')],
    )
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return self.username

class Student(CustomUser):  # Inherits from CustomUser
    dob = models.DateField()
    gender = models.CharField(
        max_length=10,
        choices=(('male', 'Male'), ('female', 'Female'), ('others', 'Others')),
    )
    primary_batch = models.ForeignKey(
        Batch, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='primary_students',
        help_text="The main batch for this student"
    )  # Each student has one primary batch
    batches = models.ManyToManyField(
        Batch, 
        related_name='students',
        blank=True,
        help_text="Other batches the student is part of"
    )  # Many-to-Many relationship with Batch
    courses = models.ManyToManyField(OnlineCourse, related_name='students', blank=True)

    def __str__(self):
        return f'Student: {self.first_name} {self.last_name}'
    
    class Meta:
        db_table = 'Student'
        db_table = 'Student'

class Teacher(CustomUser):
    CATEGORY_CHOICES = [
        ('guitar', 'Guitar'),
        ('piano', 'Piano'),
        ('vocals', 'Vocals'),
    ]
    dob = models.DateField()
    gender = models.CharField(
        max_length=10,
        choices=(('male', 'Male'), ('female', 'Female'), ('others', 'Others')),
    )
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)

    def __str__(self):
        return f'Teacher: {self.first_name} {self.last_name} - {self.category}'
    
    class Meta:
        db_table = 'Teacher'
