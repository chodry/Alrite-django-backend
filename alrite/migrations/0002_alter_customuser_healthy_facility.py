# Generated by Django 4.0.5 on 2022-07-02 11:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('alrite', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='healthy_facility',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='alrite.health_facility'),
        ),
    ]
