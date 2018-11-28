from sklearn.externals import joblib
from sklearn.preprocessing import LabelBinarizer
import numpy as np
import pyodbc
import math
from datetime import datetime, timedelta

class NeuralNetEssentials:
    # def __init__(self):
    #     pass

    def sigmoid(self, x):
        return 1 / (1 + math.exp(-x))

    def everyFiveMinutes(self, prediction_length): # Count the number of five minutes period in prediction length
        return int(prediction_length * 24 * 60 / 5)

    def convertWeekdayToSQLFormat(self, date):
        if date.isoweekday() < 7:
            return date.isoweekday() + 1
        else:
            return 1

    def convertFeaturesApplication(self, combination=[i for i in range(0, 12)], date="", procedure_name="", provider_name="", patient_id="", duration=0, prediction_length=0, allow_duplicate=False):
        DBconnection = pyodbc.connect(driver='{SQL Server}',
                                      server='localhost',
                                      database='cap_project',
                                      uid='sa',
                                      pwd='wenda')
        cursor = DBconnection.cursor()
        date_object = datetime.strptime(date, '%Y-%m-%d')
        self.years = []
        self.months = []
        self.days = []
        self.hours = []
        self.minutes = []
        weekdays = []
        completes = []
        cancels = []
        noshows = []
        procedure_names = []
        provider_names = []
        durations = []
        prediction_lengths = []

        # Get completed appointments count for the patient
        if 9 in combination:
            complete_count_query = """
            SELECT COUNT(*) FROM [cap_project].[dbo].[event] b 
            WHERE b.Patient_ID = '%s' AND b.[CheckIn_Time] is not null AND b.[CheckIn_Time] < '%s' AND (b.[NoShow_Flag] is NULL AND b.[Canceled_Flag] is NULL)
            GROUP BY b.[Patient_ID]
            """ % (patient_id, date)
            cursor.execute(complete_count_query)
            complete_count = np.array(cursor.fetchall())
            if not complete_count:  # If complete count is null, which is 0
                complete_count = np.array([0]).reshape(1, 1)
        else:
            complete_count = np.array([0]).reshape(1, 1)
        print("Complete Count: %s" % complete_count)

        # Get cancelled appointments count for the patient
        if 10 in combination:
            cancel_count_query = """
            SELECT TOP 1 COUNT(*) FROM [cap_project].[dbo].[event] c 
            WHERE c.[Appointment_Date] < '%s' AND (c.[Canceled_Flag] is NOT NULL)  AND c.[Patient_ID] = '%s'
            GROUP BY c.[Patient_ID]
            """ % (date, patient_id)
            cursor.execute(cancel_count_query)
            cancel_count = np.array(cursor.fetchall())
            if not cancel_count:
                cancel_count = np.array([0]).reshape(1, 1)
        else:
            cancel_count = np.array([0]).reshape(1, 1)

        # Get no show appointments count for the patient
        if 11 in combination:
            noshow_count_query = """
                    SELECT TOP 1 COUNT(*) FROM [cap_project].[dbo].[event]
                    WHERE [Appointment_Date] < '%s' AND ([NoShow_Flag] is NOT NULL)  AND [Patient_ID] = '%s'
                    GROUP BY [Patient_ID]
                    """ % (date, patient_id)
            cursor.execute(noshow_count_query)
            noshow_count = np.array(cursor.fetchall())
            if not noshow_count:
                noshow_count = np.array([0]).reshape(1, 1)
        else:
            noshow_count = np.array([0]).reshape(1, 1)

        # A query for polling future appointment data, will be used for time slot duplication checking
        if not allow_duplicate:
            reserved_appts_query = """SELECT TOP (1000) 
                [Appt_Durantion]
                ,[Appointment_Date]
                ,[Provider_Name]
                FROM [cap_project].[dbo].[event]
                WHERE [CheckIn_Time] = 'NULL' AND [NoShow_Flag] IS NULL AND [Canceled_Flag] IS NULL AND [Provider_Name] = '%s' AND [Appointment_Date] >= '%s' AND [Appointment_Date] < DATEADD(DAY, %s ,'%s')
                """ % (provider_name, date, prediction_length, date)
            cursor.execute(reserved_appts_query)
            reserved_appts_arrary = np.array(cursor.fetchall())
            # Loop through every time schedule in that duration
            for fiveMinutesCount in range(self.everyFiveMinutes(prediction_length)):
                start_appt_time = date_object + timedelta(seconds=fiveMinutesCount * 60 * 5)
                end_appt_time = start_appt_time + timedelta(seconds=duration * 60)
                collision = False
                for index in range(reserved_appts_arrary.shape[0]):
                    appt_duration = reserved_appts_arrary[index, 0]
                    start_reserved_time = reserved_appts_arrary[index, 1]
                    end_reserved_time = start_reserved_time + timedelta(seconds=appt_duration * 60)
                    if not (start_appt_time > end_reserved_time or end_appt_time < start_reserved_time):
                        collision = True
                if collision == False and (7 < start_appt_time.hour < 17 and end_appt_time.hour < 17):
                    temp_date_object = date_object + timedelta(seconds=fiveMinutesCount * 5 * 60)
                    self.years.append(temp_date_object.year)
                    self.months.append(temp_date_object.month)
                    self.days.append(temp_date_object.day)
                    self.hours.append(temp_date_object.hour)
                    self.minutes.append(temp_date_object.minute)
                    # convert datetime weekday format to SQL format
                    weekdays.append(self.convertWeekdayToSQLFormat(temp_date_object))
                    completes.append(complete_count[0])
                    cancels.append(cancel_count[0])
                    noshows.append(noshow_count[0])
                    procedure_names.append(procedure_name)
                    provider_names.append(provider_name)
                    durations.append(duration)
                    prediction_lengths.append(prediction_length)

        # Setup LabelBinarizer for provider
        if 1 in combination:
            provider_name_query = """
                    SELECT [Provider_Name]
                    FROM [cap_project].[dbo].[event]
                    GROUP BY [Provider_Name]
                    ORDER BY [Provider_Name]
                    """
            cursor.execute(provider_name_query)
            lb_provider_name = LabelBinarizer().fit(np.array(cursor.fetchall()))
            provider_name_vec = lb_provider_name.transform(provider_names)

        # Setup LabelBinarizer for procedure
        if 0 in combination:
            procedure_name_query = """
                    SELECT [Procedure_Name]
                    FROM [cap_project].[dbo].[event]
                    GROUP BY [Procedure_Name]
                    ORDER BY [Procedure_Name]
                    """
            cursor.execute(procedure_name_query)
            lb_procedure_name = LabelBinarizer().fit(np.array(cursor.fetchall()))
            procedure_name_vec = lb_procedure_name.transform(procedure_names)

        # Setup Procedure Duration
        procedure_duration_vec = np.array(durations).reshape(len(self.years), 1)

        complete_count = np.array(completes)
        cancel_count = np.array(cancels)
        noshow_count = np.array(noshows)

        # Get weekday value, aka, day of the week number
        weekday_query = """
        SELECT DATEPART(WEEKDAY, '%s') WEEKDAY
        """ % (date)
        cursor.execute(weekday_query)
        weekdaylist = np.array(cursor.fetchall())

        # Define the time list for victorization
        yearlist = np.array(range(1970, 2050))
        monthlist = np.array(range(1, 13))
        daylist = np.array(range(1, 32))
        hourlist = np.array(range(8, 17))
        # Minute with step size of 5, like 15, 20, 30, 45, etc...
        minutelist = np.array(range(0, 61, 5))
        weeklist = np.array(range(1, 8))

        # Convert the time list to LabelBinarizer Object for vectorizing input (features)
        lb_year = LabelBinarizer().fit(yearlist)
        lb_month = LabelBinarizer().fit(monthlist)
        lb_day = LabelBinarizer().fit(daylist)
        lb_hour = LabelBinarizer().fit(hourlist)
        lb_minute = LabelBinarizer().fit(minutelist)
        lb_weekday = LabelBinarizer().fit(weeklist)

        year = lb_year.transform(list(self.years))
        month = lb_month.transform(list(self.months))
        day = lb_day.transform(list(self.days))
        hour = lb_hour.transform(list(self.hours))
        minute = lb_minute.transform(list(self.minutes))
        weekday = lb_weekday.transform(list(weekdays))
        print(year[0])
        print(self.years[0])
        print(month[0])
        print(self.months[0])
        print(day[0])
        print(self.days[0])
        print(hour[0])
        print(self.hours[0])
        print(minute[0])
        print(self.minutes[0])
        print(weekday[0])
        print(weekdays[0])
        # Assemble features into one dictionary
        dict_features = {0: procedure_name_vec,
                         1: provider_name_vec,
                         2: procedure_duration_vec,
                         3: year,
                         4: month,
                         5: day,
                         6: hour,
                         7: minute,
                         8: weekday,
                         9: complete_count,
                         10: cancel_count,
                         11: noshow_count}
        dict_features_names = {0: "Procedure Name",
                               1: "Provider Name",
                               2: "Appointment Duration",
                               3: "year",
                               4: "Month",
                               5: "Day",
                               6: "Hour",
                               7: "Minute",
                               8: "Weekday",
                               9: "Completed Counts",
                               10: "Canceled Counts",
                               11: "No show Counts"}
        temp_tuple_features = ()
        for id in combination:
            print(dict_features_names[id])
            print("id: %s, shape: %s" % (str(id), dict_features[id].shape))
            temp_tuple_features += (dict_features[id],)
        self.feature_data = np.concatenate(temp_tuple_features, axis=1).astype(np.float)

        return self.feature_data

    def predictResults(self, modelPath):
        print(self.feature_data[0])
        result = []
        model = joblib.load(modelPath)
        for i in range(self.feature_data.shape[0]):
            tempdatetime = datetime(year=self.years[i],
                                    month=self.months[i],
                                    day=self.days[i],
                                    hour=self.hours[i],
                                    minute=self.minutes[i]
                                    )
            predict = model.predict(self.feature_data[i].reshape(1, -1))
            result += [[
                tempdatetime.strftime("%Y-%m-%d"),
                predict.tolist()[0],
                        tempdatetime,
                       tempdatetime + timedelta(seconds=300)]]
        return result
        # model = joblib.load(modelPath)
        # predict_result = model.predict(self.feature_data)
        # for item in self.feature_data:
        #
        # return
# def convertFeaturesTraining(combination=[i for i in range(0, 12)], rows=np.array([])):



# fe_data = convertFeatures(combination=[0, 1, 2, 3, 4, 5, 7, 8, 9],
#                           date="2018-10-10",
#                           time="12:15",
#                           procedure_name="MCKC MODALITY BRANTFORD",
#                           provider_name="DUNPHY, SAUNDRA",
#                           procedure_duration="30",
#                           patient_id="Z1234567")
# print(fe_data)
#
# DBconnection = pyodbc.connect(driver='{SQL Server}',
#                             server='localhost',
#                             database='cap_project',
#                             uid='sa',
#                             pwd='wenda')
#
# cursor = DBconnection.cursor()
# print(cursor)
#
# # This query fetch for Inputs
# cursor.execute("""
# SELECT a.[Procedure_Name], a.[Appt_Durantion], a.[Provider_Name], YEAR(a.[Appointment_Date]) _YEAR , MONTH(a.[Appointment_Date]) _MONTH, DAY(a.[Appointment_Date]) _DAY, DATEPART(HOUR, a.[Appointment_Date]) _HOUR, DATEPART(MINUTE, a.[Appointment_Date]) _MINUTE, DATEPART(WEEKDAY, a.[Appointment_Date]) _WEEKDAY,
# 	CASE
# 		WHEN
# 	(SELECT TOP 1 COUNT(*) FROM [cap_project].[dbo].[event] b
# 	WHERE b.[CheckIn_Time] is not null AND b.[CheckIn_Time] < a.[CheckIn_Time] AND (b.[NoShow_Flag] is NULL AND b.[Canceled_Flag] is NULL)
# 	GROUP BY b.[Patient_ID]
# 	HAVING b.[Patient_ID] = a.[Patient_ID]) IS NULL THEN 0
# 	ELSE (SELECT TOP 1 COUNT(*) FROM [cap_project].[dbo].[event] b
# 	WHERE b.[CheckIn_Time] is not null AND b.[CheckIn_Time] < a.[CheckIn_Time] AND (b.[NoShow_Flag] is NULL AND b.[Canceled_Flag] is NULL)
# 	GROUP BY b.[Patient_ID]
# 	HAVING b.[Patient_ID] = a.[Patient_ID])
# 	END as complete,
# 	CASE
# 		WHEN (SELECT TOP 1 COUNT(*) FROM [cap_project].[dbo].[event] c
# 	WHERE c.[Appointment_Date] < a.[Appointment_Date] AND (c.[Canceled_Flag] is NOT NULL)
# 	GROUP BY c.[Patient_ID]
# 	HAVING c.[Patient_ID] = a.[Patient_ID]) IS NULL
# 		THEN 0
# 		ELSE (SELECT TOP 1 COUNT(*) FROM [cap_project].[dbo].[event] c
# 	WHERE c.[Appointment_Date] < a.[Appointment_Date] AND (c.[Canceled_Flag] is NOT NULL)
# 	GROUP BY c.[Patient_ID]
# 	HAVING c.[Patient_ID] = a.[Patient_ID])
# 	END as cancel,
# 	CASE
# 		WHEN (SELECT TOP 1 COUNT(*) FROM [cap_project].[dbo].[event] d
# 	WHERE d.[Appointment_Date] < a.[Appointment_Date] AND (d.[NoShow_Flag] is NOT NULL)
# 	GROUP BY d.[Patient_ID]
# 	HAVING d.[Patient_ID] = a.[Patient_ID]) IS NULL THEN 0
# 		ELSE (SELECT TOP 1 COUNT(*) FROM [cap_project].[dbo].[event] d
# 	WHERE d.[Appointment_Date] < a.[Appointment_Date] AND (d.[NoShow_Flag] is NOT NULL)
# 	GROUP BY d.[Patient_ID]
# 	HAVING d.[Patient_ID] = a.[Patient_ID])
# 	END AS noshow,
# 	CASE
# 		WHEN a.[NoShow_Flag] = 'Y' THEN 'BAD'
# 		WHEN a.[Canceled_Flag] = 'Y' THEN 'BAD'
# 		WHEN a.[CheckIn_Time] IS NOT NULL THEN 'COMP'
# 	END as ans
#   FROM [cap_project].[dbo].[event] a
#   WHERE a.[NoShow_Flag] = 'Y' OR a.[Canceled_Flag] = 'Y' OR a.[CheckIn_Time] IS NOT NULL
# """)
#
# # This query fetch for outputs
#
# rows = cursor.fetchall()  # The SQL query result
# ROWS = np.array(rows)  # transform query to np array
# print("Rows shape %s: " % (str(ROWS.shape)))
# print(ROWS[0])
#
# # ------------------------Prepare Data-----------------------------
# procedure_name = ROWS[:, 0]  # vectorize
# appt_duration = ROWS[:, 1]  # discrete
# provider_name = ROWS[:, 2]  # vectorize
#
# # vectorize by year, month, day, self.hours, and minute
# appointment_year = ROWS[:, 3].astype(np.string_)
# appointment_month = ROWS[:, 4].astype(np.string_)
# appointment_day = ROWS[:, 5].astype(np.string_)
# appointment_hour = ROWS[:, 6].astype(np.string_)
# appointment_minute = ROWS[:, 7].astype(np.string_)
# appointment_weekday = ROWS[:, 8].astype(np.string_)
#
# complete = ROWS[:, 9]  # discrete
# cancel = ROWS[:, 10]  # discrete
# noshow = ROWS[:, 11]  # discrete
#
# answer = ROWS[:, 12]  # The answer
# # Provide list of datetime categories
# yearlist = np.array(range(1970, 2050)).astype(np.string_)
# monthlist = np.array(range(1, 13)).astype(np.string_)
# daylist = np.array(range(1, 32)).astype(np.string_)
# hourlist = np.array(range(8, 17)).astype(np.string_)
# # Minute with step size of 5, like 15, 20, 30, 45, etc...
# minutelist = np.array(range(1, 61, 5)).astype(np.string_)
# weeklist = np.array(range(1, 8)).astype(np.string_)
# # ------------------------End Prepare Data-----------------------------
#
# # ------------------------Vectorize-------------------------------
# vectorizer = LabelBinarizer()  # Vectorize by going through the SQL result
#
# procedure_name_vec = vectorizer.fit_transform(procedure_name)
# print("Procedure Name")
# print(procedure_name_vec[0])
# provider_name_vec = vectorizer.fit_transform(provider_name)
# print("Provider Name")
# print(provider_name_vec[0])
# answer_vec = vectorizer.fit_transform(answer)  # This is the output
# print("Answer shape")
# print(answer_vec.shape)
#
# appt_duration_vec = appt_duration[:, None]
# complete_vec = complete[:, None]
# cancel_vec = cancel[:, None]
# noshow_vec = noshow[:, None]
#
# lb_year = LabelBinarizer().fit(yearlist)
# lb_month = LabelBinarizer().fit(monthlist)
# lb_day = LabelBinarizer().fit(daylist)
# lb_hour = LabelBinarizer().fit(hourlist)
# lb_minute = LabelBinarizer().fit(minutelist)
# lb_week = LabelBinarizer().fit(weeklist)
# # In format of [0, 0, 0, 1, 0...]
# vect_year = lb_year.transform(list(appointment_year))
# vect_month = lb_month.transform(list(appointment_month))
# vect_day = lb_day.transform(list(appointment_day))
# vect_hour = lb_hour.transform(list(appointment_hour))
# vect_minute = lb_minute.transform(list(appointment_minute))
# vect_weekday = lb_week.transform(list(appointment_weekday))
# # --------------------------End Vectorize--------------------------------
#
# # -----------------------Feature (as Input)-------------------
# dict_features = {0: procedure_name_vec,
#                  1: provider_name_vec,
#                  2: appt_duration_vec,
#                  3: vect_year,
#                  4: vect_month,
#                  5: vect_day,
#                  6: vect_hour,
#                  7: vect_minute,
#                  8: vect_weekday,
#                  9: complete_vec,
#                  10: cancel_vec,
#                  11: noshow_vec
#                  }
# # -----------------------End Feature (as Input)-------------------
#
# dict_features_names = {0: "Procedure Name",
#                  1: "Provider Name",
#                  2: "Appointment Duration",
#                  3: "year",
#                  4: "Month",
#                  5: "Day",
#                  6: "Hour",
#                  7: "Minute",
#                  8: "Weekday",
#                  9: "Completed Counts",
#                  10: "Canceled Counts",
#                  11: "No show Counts"}
#
# single_year = lb_year.transform([2018])
# print("single_year: %s " % (str(single_year)))
# single_month = lb_month.transform([11])
# single_day = lb_day.transform([10])
# single_weekday = lb_week.transform([2])
# single_hour = lb_hour.transform([10])
# single_minute = lb_minute.transform([15])
# single_duration = appt_duration_vec[10]
# s_complete_vec = np.array([complete_vec[10]])
# s_cancel_vec = np.array([cancel_vec[10]])
# s_noshow_vec = np.array([noshow_vec[10]])
#
# provider_name_vect = LabelBinarizer().fit(provider_name)
# procedure_name_vect = LabelBinarizer().fit(procedure_name)
#
# single_provider_name = provider_name_vect.transform(['MARGETTS, PETER JOSEPH'])
# single_procedure_name = procedure_name_vect.transform(['NPH BRANTFORD F/UP 15 MIN'])
# print("single_name: %s " % (str(provider_name)))
#
# new_dict_features = {
#     0: single_procedure_name,
#     1: single_provider_name,
#     2: single_duration,
#     3: single_year,
#     4: single_month,
#     5: single_day,
#     6: single_hour,
#     7: single_minute,
#     8: single_weekday,
#     9: s_complete_vec,
#     10: s_cancel_vec,
#     11: s_noshow_vec
# }
#
# result = [0, 1, 3, 4, 5, 7, 8, 9]
# print("running with %i of combinations" % (1))
# temp_tuple_features = ()
# print("result names: ", end="")
# for id in result:
#     print("%s, %s" % (dict_features_names[id], new_dict_features[id].shape))
#     temp_tuple_features += (new_dict_features[id], )
#
# # temp_tuple_features = map(tuple_features.__getitem__, result)
#
# feature_data = NeuralNetEssentials().convertFeaturesApplication(
#     combination=[0, 1, 3, 4, 5, 8, 9, 10, 11],
#                           date="2017-10-20",
#                           procedure_name="MCKC MODALITY BRANTFORD",
#                           provider_name="DUNPHY, SAUNDRA",
#                           patient_id="Z1234567",
#                           duration=5,
#                           allow_duplicate=False)
#
# filename = 'data/nn_model/model-2018-10-29 0, 1, 3, 4, 5, 8, 9, 10, 11.sav'
#
# loaded_model = joblib.load(filename)

# dict_features_names = {0: "Procedure Name",
#                  1: "Provider Name",
#                  2: "Appointment Duration",
#                  3: "year",
#                  4: "Month",
#                  5: "Day",
#                  6: "Hour",
#                  7: "Minute",
#                  8: "Weekday",
#                  9: "Completed Counts",
#                  10: "Canceled Counts",
#                  11: "No show Counts"}
#
# input = np.array(["MCKC CLINIC VISIT 15 MIN",
#                                "MARGETTS, PETER JOSEPH",
#                                "2018",
#                                "4",
#                                "5",
#                                "0",
#                                "5",
#                                "4"]).reshape(1, -1)
#
#
# input = input.astype(np.string_)
#
#
# no = 0
# yes = 0
# for one in loaded_model.predict(feature_data):
#     # print("One: %s" % str(one))
#     if one == 1:
#         yes += 1
#     elif one == 0:
#         no += 1
# print("Total success %s" % str(yes))
# print("Total fail %s" % str(no))

# print("Prediction %s" % (loaded_model.predict(feature_data)))