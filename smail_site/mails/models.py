from __future__ import unicode_literals

from django.db import models

# Create your models here.


class GoogleUser(models.Model):
    email = models.EmailField()
    google_id = models.CharField(max_length=100)

    def __str__(self):
        return "email: %s, google_id: %s" % (self.email, self.google_id)
