from django.db import models

class ProductReview(models.Model):
    product_name = models.CharField(max_length=255)
    review_text = models.TextField()
    rating = models.DecimalField(max_digits=3, decimal_places=1)  # You can adjust the precision
    location = models.CharField(max_length=255)
    review_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.product_name} - Rating: {self.rating}"

