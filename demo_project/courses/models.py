from django.db import models
from django.contrib.auth.models import User

class CourseRequest(models.Model):
    COURSE_TYPES = [
        ('qualification', 'Повышение квалификации'),
        ('retraining', 'Переподготовка'),
        ('safety', 'Охрана труда'),
    ]
    PAYMENT_METHODS = [
        ('card', 'Банковская карта'),
        ('online', 'Онлайн-оплата'),
        ('receipt', 'Квитанция'),
    ]
    STATUSES = [
        ('new', 'Новая'),
        ('in_progress', 'Идёт обучение'),
        ('completed', 'Обучение завершено'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    course_type = models.CharField(max_length=20, choices=COURSE_TYPES)
    start_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUSES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_course_type_display()}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    request = models.OneToOneField(CourseRequest, on_delete=models.CASCADE, related_name='review')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Отзыв от {self.user.username} на заявку #{self.request.id}"