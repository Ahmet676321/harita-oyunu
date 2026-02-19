from django.db import models


class Score(models.Model):
    name = models.CharField(max_length=32)
    score = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score", "-created_at"]

    def __str__(self) -> str:
        return f"{self.name} - {self.score}"
