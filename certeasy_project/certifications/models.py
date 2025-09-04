from django.db import models

class Certification(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=255)
    progress = models.PositiveIntegerField(default=0)  # % progress (0-100)
    students = models.PositiveIntegerField(default=0)  # number of enrolled users
    image = models.ImageField(upload_to='media/certifications/', null=True, blank=True)
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2, default=39.00)
    yearly_price = models.DecimalField(max_digits=8, decimal_places=2, default=399.00)

    def __str__(self):
        return self.title

    def image_url(self):
        if self.image:
            return self.image.url
        return '/static/placeholders/default-cert.png'  # fallback image
