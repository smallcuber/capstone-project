# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Event(models.Model):
    unique_id = models.FloatField(db_column='Unique_ID', blank=True, null=True)  # Field name made lowercase.
    patient_id = models.CharField(db_column='Patient_ID', max_length=255, blank=True, null=True)  # Field name made lowercase.
    procedure_name = models.CharField(db_column='Procedure_Name', max_length=255, blank=True, null=True)  # Field name made lowercase.
    appt_durantion = models.FloatField(db_column='Appt_Durantion', blank=True, null=True)  # Field name made lowercase.
    appointment_date = models.DateTimeField(db_column='Appointment_Date', blank=True, null=True)  # Field name made lowercase.
    provider_scheduled = models.FloatField(db_column='Provider_Scheduled', blank=True, null=True)  # Field name made lowercase.
    provider_name = models.CharField(db_column='Provider_Name', max_length=255, blank=True, null=True)  # Field name made lowercase.
    cpso = models.CharField(db_column='CPSO', max_length=255, blank=True, null=True)  # Field name made lowercase.
    checkin_time = models.DateTimeField(db_column='CheckIn_Time', blank=True, null=True)  # Field name made lowercase.
    checkout_time = models.CharField(db_column='CheckOut_Time', max_length=255, blank=True, null=True)  # Field name made lowercase.
    roomed_time = models.CharField(db_column='Roomed_Time', max_length=255, blank=True, null=True)  # Field name made lowercase.
    noshow_flag = models.CharField(db_column='NoShow_Flag', max_length=255, blank=True, null=True)  # Field name made lowercase.
    canceled_flag = models.CharField(db_column='Canceled_Flag', max_length=255, blank=True, null=True)  # Field name made lowercase.
    cancelation_date = models.CharField(db_column='Cancelation_Date', max_length=255, blank=True, null=True)  # Field name made lowercase.
    cancelation_reason = models.CharField(db_column='Cancelation_Reason', max_length=255, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'event'

# TODO: Add Database for new data