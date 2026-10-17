from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0003_attendancerecord_approval_status_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExcuseRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField()),
                ('date', models.DateField()),
                ('supporting_document', models.FileField(blank=True, null=True, upload_to='excuses/%Y/%m/')),
                ('notes', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('supervisor_comment', models.TextField(blank=True)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_excuse_requests', to='accounts.user')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='excuse_requests', to='students.studentprofile')),
                ('supervisor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='excuse_requests', to='accounts.user')),
            ],
            options={
                'ordering': ['-submitted_at'],
                'unique_together': {('student', 'date')},
            },
        ),
    ]
