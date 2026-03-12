# This app handles authentication views
# User model is defined in the users app


from django.db import models

class Tenant(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name