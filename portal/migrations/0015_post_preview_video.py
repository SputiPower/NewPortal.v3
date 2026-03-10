from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0014_boardad_emailverificationcode_adresponse'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='preview_video',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='posts/videos/',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['mp4'])],
            ),
        ),
    ]
