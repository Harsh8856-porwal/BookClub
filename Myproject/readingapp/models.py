
from django.db import models
from django.contrib.auth.models import User

class Book(models.Model):

    CATEGORY_CHOICES = [
        ('Classic','Classic'),
        ('Mystery','Mystery'),
        ('Romantic','Romantic'),
        ('Spiritual','Spiritual'),
        ('Fiction','Fiction'),
        ('Adventure','Adventure'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    username = models.CharField(max_length=30)
    email = models.EmailField()

    book_name = models.CharField(max_length=200)
    author_name = models.CharField(max_length=200)

    book_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    book_chapter = models.IntegerField()
    book_pages = models.IntegerField()

    book_img = models.ImageField(upload_to='uploadedFiles', null=True, blank=True)
    book_file = models.FileField(upload_to='documents', null=True, blank=True)
    book_agegroup= models.CharField(max_length=15,null=True)

    def __str__(self):
        return self.book_name

