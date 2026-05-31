from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainpage', '0008_post_image_post_video_alter_post_title_passwordreset'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventRSVP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response', models.CharField(choices=[('yes', 'Yes'), ('no', 'No')], max_length=3)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rsvps', to='mainpage.event')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_rsvps', to='mainpage.student')),
            ],
            options={
                'ordering': ['-updated_at'],
                'unique_together': {('event', 'student')},
            },
        ),
    ]
