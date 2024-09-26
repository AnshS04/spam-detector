from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, phone_number, name, email=None, password=None):
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        user = self.model(phone_number=phone_number, name=name, email=email)
        user.set_password(password) 
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, name, email=None, password=None):
        user = self.create_user(phone_number, name, email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    phone_number = models.CharField(max_length=15, primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True, unique=True) 
    password = models.CharField(max_length=128) 
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.name

    @property
    def id(self):
        return self.phone_number


class Contact(models.Model):
    phone_number = models.CharField(max_length=15)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)
    is_spam = models.BooleanField(default=False)

    def __str__(self):
        return {
            'added_by': self.added_by.phone_number,
            'phone_number': self.phone_number,
            'name': self.name,
            'is_spam': self.is_spam
        } 
