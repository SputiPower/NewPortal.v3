from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0010_alter_category_color'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='posts/gallery/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['png'])])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media_files', to='portal.post')),
            ],
            options={
                'verbose_name': 'Файл поста',
                'verbose_name_plural': 'Файлы поста',
                'ordering': ['created_at'],
            },
        ),
    ]
