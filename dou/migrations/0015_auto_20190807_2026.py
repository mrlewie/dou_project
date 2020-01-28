# Generated by Django 2.2.2 on 2019-08-07 12:26

from django.db import migrations, models
import imagekit.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dou', '0014_page'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='page_id',
        ),
        migrations.AddField(
            model_name='page',
            name='extension',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='filename',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='page_thumb_lg',
            field=imagekit.models.fields.ProcessedImageField(blank=True, default='placeholders/book_default_thumb.jpg', null=True, upload_to='pages/'),
        ),
    ]
