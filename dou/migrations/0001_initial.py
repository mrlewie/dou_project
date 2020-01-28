# Generated by Django 2.2.2 on 2019-06-24 10:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('web_id', models.CharField(blank=True, max_length=25, null=True)),
                ('version', models.CharField(blank=True, max_length=5, null=True)),
                ('name_en', models.CharField(blank=True, max_length=150, null=True)),
                ('name_jp', models.CharField(blank=True, max_length=150, null=True)),
                ('name_rj', models.CharField(blank=True, max_length=150, null=True)),
                ('released', models.CharField(blank=True, max_length=15, null=True)),
                ('num_pages', models.CharField(blank=True, max_length=5, null=True)),
                ('is_adult', models.CharField(blank=True, max_length=5, null=True)),
                ('is_anthology', models.CharField(blank=True, max_length=5, null=True)),
                ('language', models.CharField(blank=True, max_length=50, null=True)),
                ('url', models.URLField(blank=True, max_length=255, null=True)),
                ('filename', models.TextField(unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Circle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('web_id', models.CharField(blank=True, max_length=100, null=True)),
                ('version', models.CharField(blank=True, max_length=5, null=True)),
                ('name_en', models.CharField(blank=True, max_length=100, null=True)),
                ('name_jp', models.CharField(blank=True, max_length=100, null=True)),
                ('name_rj', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Content',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('web_id', models.CharField(blank=True, max_length=100, null=True)),
                ('version', models.CharField(blank=True, max_length=5, null=True)),
                ('name_en', models.CharField(blank=True, max_length=100, null=True)),
                ('name_jp', models.CharField(blank=True, max_length=100, null=True)),
                ('name_rj', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Convention',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('web_id', models.CharField(blank=True, max_length=100, null=True)),
                ('version', models.CharField(blank=True, max_length=5, null=True)),
                ('name_en', models.CharField(blank=True, max_length=100, null=True)),
                ('name_jp', models.CharField(blank=True, max_length=100, null=True)),
                ('name_rj', models.CharField(blank=True, max_length=100, null=True)),
                ('start_date', models.CharField(blank=True, max_length=15, null=True)),
                ('finish_date', models.CharField(blank=True, max_length=15, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Parody',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('web_id', models.CharField(blank=True, max_length=100, null=True)),
                ('version', models.CharField(blank=True, max_length=5, null=True)),
                ('name_en', models.CharField(blank=True, max_length=100, null=True)),
                ('name_jp', models.CharField(blank=True, max_length=100, null=True)),
                ('name_rj', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('web_id', models.CharField(blank=True, max_length=100, null=True)),
                ('version', models.CharField(blank=True, max_length=5, null=True)),
                ('name_en', models.CharField(blank=True, max_length=100, null=True)),
                ('name_jp', models.CharField(blank=True, max_length=100, null=True)),
                ('name_rj', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('web_id', models.CharField(blank=True, max_length=100, null=True)),
                ('version', models.CharField(blank=True, max_length=5, null=True)),
                ('name_en', models.CharField(blank=True, max_length=100, null=True)),
                ('name_jp', models.CharField(blank=True, max_length=100, null=True)),
                ('name_rj', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name='type',
            constraint=models.UniqueConstraint(fields=('web_id',), name='type_unq'),
        ),
        migrations.AddConstraint(
            model_name='publisher',
            constraint=models.UniqueConstraint(fields=('web_id',), name='publisher_unq'),
        ),
        migrations.AddConstraint(
            model_name='parody',
            constraint=models.UniqueConstraint(fields=('web_id',), name='parody_unq'),
        ),
        migrations.AddConstraint(
            model_name='convention',
            constraint=models.UniqueConstraint(fields=('web_id',), name='convention_unq'),
        ),
        migrations.AddConstraint(
            model_name='content',
            constraint=models.UniqueConstraint(fields=('web_id',), name='content_unq'),
        ),
        migrations.AddConstraint(
            model_name='circle',
            constraint=models.UniqueConstraint(fields=('web_id',), name='circle_unq'),
        ),
        migrations.AddField(
            model_name='book',
            name='circles',
            field=models.ManyToManyField(blank=True, to='dou.Circle'),
        ),
        migrations.AddField(
            model_name='book',
            name='contents',
            field=models.ManyToManyField(blank=True, to='dou.Content'),
        ),
        migrations.AddField(
            model_name='book',
            name='convention',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dou.Convention'),
        ),
        migrations.AddField(
            model_name='book',
            name='parodies',
            field=models.ManyToManyField(blank=True, to='dou.Parody'),
        ),
        migrations.AddField(
            model_name='book',
            name='publishers',
            field=models.ManyToManyField(blank=True, to='dou.Publisher'),
        ),
        migrations.AddField(
            model_name='book',
            name='type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dou.Type'),
        ),
    ]
