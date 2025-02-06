from django.db import models
from django.contrib.auth.models import User

class ProductReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Associate review with a user
    product_name = models.CharField(max_length=255)
    review_text = models.TextField()
    rating = models.FloatField()
    location = models.CharField(max_length=255, default="Unknown")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.product_name}"
