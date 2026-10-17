from django.db import models
from accounts.models import User
from students.models import StudentProfile


class Evaluation(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='evaluations')
    supervisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_evaluations')
    # Criteria (0-100 each)
    punctuality = models.IntegerField(default=0)
    attendance = models.IntegerField(default=0)
    work_quality = models.IntegerField(default=0)
    professionalism = models.IntegerField(default=0)
    communication = models.IntegerField(default=0)
    teamwork = models.IntegerField(default=0)
    initiative = models.IntegerField(default=0)
    remarks = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)
    final_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'supervisor')

    def __str__(self):
        return f"Evaluation: {self.student} by {self.supervisor.get_full_name()}"

    def compute_final_score(self):
        scores = [
            self.punctuality, self.attendance, self.work_quality,
            self.professionalism, self.communication, self.teamwork, self.initiative
        ]
        self.final_score = round(sum(scores) / len(scores), 2)
        return self.final_score

    def get_grade_letter(self):
        s = float(self.final_score)
        if s >= 90: return 'A'
        elif s >= 85: return 'B+'
        elif s >= 80: return 'B'
        elif s >= 75: return 'C+'
        elif s >= 70: return 'C'
        else: return 'F'
