# Generated by Django 2.0.4 on 2019-08-26 02:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_id', models.FloatField(blank=True, db_column='Unique_ID', null=True)),
                ('patient_id', models.CharField(blank=True, db_column='Patient_ID', max_length=255, null=True)),
                ('procedure_name', models.CharField(blank=True, db_column='Procedure_Name', max_length=255, null=True)),
                ('appt_durantion', models.FloatField(blank=True, db_column='Appt_Durantion', null=True)),
                ('appointment_date', models.DateTimeField(blank=True, db_column='Appointment_Date', null=True)),
                ('provider_scheduled', models.FloatField(blank=True, db_column='Provider_Scheduled', null=True)),
                ('provider_name', models.CharField(blank=True, db_column='Provider_Name', max_length=255, null=True)),
                ('cpso', models.CharField(blank=True, db_column='CPSO', max_length=255, null=True)),
                ('checkin_time', models.DateTimeField(blank=True, db_column='CheckIn_Time', null=True)),
                ('checkout_time', models.CharField(blank=True, db_column='CheckOut_Time', max_length=255, null=True)),
                ('roomed_time', models.CharField(blank=True, db_column='Roomed_Time', max_length=255, null=True)),
                ('noshow_flag', models.CharField(blank=True, db_column='NoShow_Flag', max_length=255, null=True)),
                ('canceled_flag', models.CharField(blank=True, db_column='Canceled_Flag', max_length=255, null=True)),
                ('cancelation_date', models.CharField(blank=True, db_column='Cancelation_Date', max_length=255, null=True)),
                ('cancelation_reason', models.CharField(blank=True, db_column='Cancelation_Reason', max_length=255, null=True)),
            ],
            options={
                'db_table': 'event',
                'managed': False,
            },
        ),
    ]
