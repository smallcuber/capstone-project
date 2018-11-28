from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views import generic
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from .models import Event
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Value, Count, Q
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.core.files.storage import FileSystemStorage
from .nn_prediction import NeuralNetEssentials
from datetime import datetime
import os
import configparser


# User = get_user_model()
login_redirect_link = '/userlogin/'

def providers_list(max_results=0, name_starts_with=''):
    name_list = []
    if name_starts_with:
        name_list_query = Event.objects.values('provider_scheduled', 'provider_name').filter(
            provider_name__contains=name_starts_with).annotate(provider_count=Count("provider_name"))[:max_results]
        name_list = [name for name in name_list_query]
    return name_list


@login_required(login_url=login_redirect_link)
@csrf_exempt
def providers(request):
    template = 'data/providers.html'
    name_list = []
    if request.is_ajax() and request.method == 'POST':
        print(request.POST['empfname'])
        starts_with = request.POST['empfname']
        name_list = providers_list(10, starts_with)
        print(name_list)
        return JsonResponse(name_list, safe=False)
    return render(request, template, {'name_list': name_list})


def scheduleview_list(max_results=0):
    schedule_list_query = Event.objects.order_by('appointment_date'). \
                              values_list('provider_name', 'patient_id', 'appointment_date', 'appt_durantion')[
                          :max_results]
    schedule_list = [[str(field) for field in schedule] for schedule in schedule_list_query]
    return schedule_list


@login_required(login_url=login_redirect_link)
@csrf_exempt
def scheduleview(request):  #
    template = 'data/schedule.html'

    array = []
    # array = [['Magnolia Room', 'Beginning JavaScript', '2017-12-05 13:22:14.000', '12/5/2017 13:57'],['Magnolia Room', 'Beginning JavaScript', '2017-12-05 15:22:14.000', '12/5/2017 15:57']]
    if request.is_ajax() and request.method == 'POST':
        if request.POST.get('type') == 'providerName':
            array = scheduleview_list(30)
            return JsonResponse(array, safe=False)
        elif request.POST.get("type") == 'labels':
            # Query get list of provider names
            providers_list_query = Event.objects.values('provider_name'). \
                annotate(provider_count=Count("provider_name"))
            providers_list = [provider['provider_name'] for provider in providers_list_query]
            # Query get list of procedure names
            procedureName_list_query = Event.objects.values('procedure_name'). \
                annotate(procedure_count=Count('procedure_name'))
            procedureName_list = [procedureNames['procedure_name'] for procedureNames in procedureName_list_query]
            # Query get list of patient ids
            patient_id_list_query = Event.objects.values('patient_id'). \
                annotate(patient_id_count=Count('patient_id'))
            patient_id_list = [patient_id['patient_id'] for patient_id in patient_id_list_query]
            labels = [providers_list, procedureName_list, patient_id_list]
            return JsonResponse(labels, safe=False)
        elif request.POST.get("type") == 'prediction':
            provider_name = request.POST.get("providerName")
            print(provider_name)
            procedure_name = request.POST.get("procedureName")
            print(procedure_name)
            procedure_duration = request.POST.get("procedureDuration")
            print(procedure_duration)
            app_date = request.POST.get("appDate")
            print(app_date)
            app_time = request.POST.get("appTime")
            print(app_time)
            patient_id = request.POST.get("patientID")
            print(patient_id)
            prediction_length = request.POST.get("predictionLength")
            print(prediction_length)

            config = configparser.ConfigParser()
            config.read('model.ini')
            selected_model_path = config['Path']['ModelPath'] #TODO: read config file and load it to model path

            featureData = NeuralNetEssentials()
            featureData.convertFeaturesApplication(
                combination=[0, 1, 2, 3, 4, 5, 6, 8, 9, 10],
                date=app_date,
                patient_id=patient_id,
                procedure_name=procedure_name,
                provider_name=provider_name,
                duration=int(procedure_duration),
                prediction_length=int(prediction_length)
            )
            result = featureData.predictResults(
                # "data/nn_model/model-2018-11-16 07810894340351556 and 10.sav"
                modelPath= "data/nn_model/model-2018-11-16 07810894340351556 and 10.sav" # selected_model_path
            )
            return JsonResponse(result, safe=False)

    return render(request, template)


def patientovview_list(start_date, ende_date):  # Three types of event: Completed, No Show, Canceled
    result = [['Event', 'Counts']]
    try:
        patientov_list_query_success = Event.objects. \
            values_list('checkout_time'). \
            filter(checkout_time__isnull=False,
                   appointment_date__gte=start_date,
                   appointment_date__lte=ende_date)
        result.append(['Completed', patientov_list_query_success.count()])
    except ObjectDoesNotExist:
        result.append(['Completed', 0])
    try:
        patientov_list_query_noshow = Event.objects. \
            values_list('noshow_flag'). \
            filter(noshow_flag__isnull=False,
                   appointment_date__gte=start_date,
                   appointment_date__lte=ende_date)
        result.append(['No Show', patientov_list_query_noshow.count()])
    except ObjectDoesNotExist:
        result.append(['No Show', 0])
    try:
        patientov_list_query_canceled = Event.objects. \
            values_list('canceled_flag'). \
            filter(canceled_flag__isnull=False,
                   appointment_date__gte=start_date,
                   appointment_date__lte=ende_date)
        result.append(['Canceled', patientov_list_query_canceled.count()])
    except ObjectDoesNotExist:
        result.append(['Canceled', 0])
    return result


def patientovview_cr_list(start_date, end_date):  # Canceled Appointment Reasons graph
    result = [['Reason', 'Counts']]
    try:
        cancel_reason_list_query = Event.objects. \
            values('cancelation_reason').all(). \
            filter(appointment_date__gte=start_date,
                   appointment_date__lte=end_date). \
            exclude(cancelation_reason='NULL'). \
            annotate(total=Count('cancelation_reason')). \
            order_by('-total')
        print(cancel_reason_list_query)
    except ObjectDoesNotExist:
        return result
    for cancel_reason_list in cancel_reason_list_query:
        result.append([cancel_reason_list['cancelation_reason'], cancel_reason_list['total']])
    print(result)
    return result


def patient_list(max_results=0, id_starts_with=''):  # Patient name list
    name_list = []
    if id_starts_with:
        name_list_query = Event.objects.values('patient_id').filter(
            patient_id__contains=id_starts_with).annotate(count=Count("patient_id"))[:max_results]
        name_list = [name for name in name_list_query]
    return name_list


@login_required(login_url=login_redirect_link)
@csrf_exempt
def patientovview(request):
    template = 'data/patientov.html'
    if request.is_ajax() and request.method == 'POST':  # For Historical Appointment Summary graph
        if request.POST.get('type') == 'overview':
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            array = patientovview_list(start_date, end_date)
            print(array)
            return JsonResponse(array, safe=False)
        elif request.POST.get('type') == 'canceled_reason':  # For Canceled Appointment Reasons graph
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            array = patientovview_cr_list(start_date, end_date)
            print(array)
            return JsonResponse(array, safe=False)
        elif request.POST.get('type') == 'patient_list':  # For Patient name list
            array = patient_list(10, request.POST['pid'])
            print(array)
            return JsonResponse(array, safe=False)
    return render(request, template)


class PatientInfo(generic.ListView):  # Individual patient view
    model = Event
    template_name = 'data/patient_detail.html'

    def get_context_data(self, **kwargs):
        # Initialize variables to prevent glitch values
        context = super().get_context_data(**kwargs)
        context['patientInfo'] = {'sum': 0}
        canceled_count = 0
        completed_count = 0
        noshow_count = 0

        # This query could be improved by having a separate table consists doctor's info
        # To get provider's name
        name_query = self.model.objects. \
            values('patient_id'). \
            filter(patient_id=self.kwargs['patient_id']). \
            annotate(pcount=Count('unique_id'))
        context['patientInfo'].update({'patient_id': name_query[0]['patient_id']})

        try:  # Individual appointments sum
            canceled_query = self.model.objects. \
                values_list('canceled_flag'). \
                filter(patient_id=self.kwargs['patient_id'],
                       canceled_flag__isnull=False)
            canceled_count = canceled_query.count()
            context['patientInfo'].update({'canceled': canceled_count})
        except ObjectDoesNotExist:
            context['patientInfo'].update({'canceled': 0})

        try:  # Individual no show appointments count
            noshow_query = self.model.objects. \
                values_list('noshow_flag'). \
                filter(patient_id=self.kwargs['patient_id'],
                       noshow_flag__isnull=False)
            noshow_count = noshow_query.count()
            context['patientInfo'].update({'noshow': noshow_count})
        except ObjectDoesNotExist:
            context['patientInfo'].update({'noshow': 0})

        try:  # Individual completed appointments count
            completed_query = self.model.objects. \
                values_list('checkout_time'). \
                filter(patient_id=self.kwargs['patient_id'],
                       checkin_time__isnull=False)
            completed_count = completed_query.count()
            context['patientInfo'].update({'completed': completed_count})
        except ObjectDoesNotExist:
            context['patientInfo'].update({'completed': 0})

        total_count = canceled_count + noshow_count + completed_count
        context['patientInfo'].update({'sum': total_count})
        try:  # Individual complete rate count
            context['patientInfo'].update({'complete_rate': round(completed_count * 100 / total_count, 2)})
        except ZeroDivisionError:
            context['patientInfo'].update({'complete_rate': 'No Record'})

        try:  # Individual no show rate count
            context['patientInfo'].update({'no_show_rate': round(noshow_count * 100 / total_count, 2)})
        except ZeroDivisionError:
            context['patientInfo'].update({'no_show_rate': 'No Record'})

        try:  # Individual canceled rate count
            context['patientInfo'].update({'canceled_rate': round(canceled_count * 100 / total_count, 2)})
        except ZeroDivisionError:
            context['patientInfo'].update({'canceled_rate': 'No Record'})

        return context


class ProviderInfo(generic.ListView):  # Individual provider view
    model = Event
    template_name = 'data/provider_detail.html'

    def get_context_data(self, **kwargs):
        individual_sum_error = False
        individual_success_error = False

        context = super().get_context_data(**kwargs)
        context['providerInfo'] = {}

        # This query could be improved by having a separate table consists doctor's info
        # To get provider's name
        name_query = self.model.objects. \
            values('provider_name'). \
            filter(provider_scheduled=self.kwargs['provider_scheduled']). \
            annotate(pcount=Count('provider_name'))
        context['providerInfo'].update({'provider_name': name_query[0]['provider_name']})

        try:  # Individual appointments sum
            total_query = self.model.objects. \
                values_list('provider_scheduled'). \
                filter(Q(checkin_time__isnull=False) | Q(canceled_flag__isnull=False) | Q(noshow_flag__isnull=False),
                       provider_scheduled=self.kwargs['provider_scheduled'])
            context['providerInfo'].update({'total_count': total_query.count()})
        except ObjectDoesNotExist:
            individual_sum_error = True
            context['providerInfo'].update({'total_count': 0})

        try:  # Individual successful appointments count
            completed_query = self.model.objects. \
                values_list('provider_scheduled'). \
                filter(provider_scheduled=self.kwargs['provider_scheduled'],
                       noshow_flag__isnull=True,
                       canceled_flag__isnull=True,
                       checkin_time__isnull=False)
            context['providerInfo'].update({'completed_count': completed_query.count()})
        except ObjectDoesNotExist:
            individual_success_error = True
            context['providerInfo'].update({'completed_count': 0})

        try:  # Calculate the successful appointment rate and return it
            if individual_sum_error is False and individual_success_error is False:
                # return as percentage
                complete_rate = round((completed_query.count() * 100 / total_query.count()), 2)
            else:
                complete_rate = 0
            context['providerInfo'].update({'completed_rate': complete_rate})
            context['providerInfo'].update({'data_error': False})
        except ZeroDivisionError:
            context['providerInfo'].update({'completed_rate': 0})
            context['providerInfo'].update({'data_error': True})

        return context

@login_required(login_url=login_redirect_link)
@csrf_exempt
def performanceview(request):
    template = 'data/performance.html'
    if request.is_ajax() and request.method == 'POST':  # For Historical Appointment Summary graph
        if request.POST.get('type') == 'overview':
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            array = patientovview_list(start_date, end_date)
            print(array)
            return JsonResponse(array, safe=False)
        elif request.POST.get('type') == 'canceled_reason':  # For Canceled Appointment Reasons graph
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            array = patientovview_cr_list(start_date, end_date)
            print(array)
            return JsonResponse(array, safe=False)
    return render(request, template)


# this function is for user login page
def userLogin(request):
    context = {}
    template = 'data/login.html'
    if request.method == "POST" and request.is_ajax():
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        print('message')
        print(username)
        print(password)
        if user:
            login(request, user)
            context['Message'] = "You have successfully logged in."
            context['verified'] = True
            context['username'] = username
            return JsonResponse(context)
        else:
            context['Message'] = "Wrong user name or password, please try again."
            context['verified'] = False
            return JsonResponse(context)
    else:
        return render(request, template)


@login_required(login_url=login_redirect_link)
@csrf_exempt
def userLogout(request):
    template = 'data/logout.html'
    if request.method == "POST":
        logout(request)
        return redirect('login')
    else:
        return render(request, template)


# This function is for upload model page
@permission_required('contenttypes.content_type.can_delete_content_type',
                     login_url=login_redirect_link)
@login_required(login_url=login_redirect_link)
@csrf_exempt
def uploadModel(request):
    template = 'data/upload_model.html'
    context = {}

    def getModelList(context):
        loc = FileSystemStorage().location
        file_names = [name for name in os.listdir(loc) if name.endswith('.sav')]

        config = configparser.ConfigParser()
        config.read('model.ini')
        selected_model_path = config['Path']['ModelPath']

        table_data = []
        for fname in file_names:
            temp_path_file = os.path.join(loc, fname)
            temp_row = [None,
                        fname,
                        datetime.fromtimestamp(os.path.getctime(temp_path_file)).strftime('%Y-%m-%d %H:%M:%S')]
            if temp_path_file == selected_model_path:
                temp_row[0] = 1
            table_data.append(temp_row)
        context['table_data'] = table_data
        return context

    context = getModelList(context)
    if request.method == "POST" and request.FILES:
        if request.FILES['inputFileName']:
            model = request.FILES['inputFileName']
            fs = FileSystemStorage()
            file_name = fs.save(model.name, model)
            if file_name.endswith('.sav'):
                print("Model name %s" % (model.name))
                print("Model size: %s" % (model.size))
                uploaded_file_url = fs.url(file_name)
                print("Uploaded file url: %s" % (uploaded_file_url))
                context['uploaded_file_url'] = uploaded_file_url
                return render(request, template, context)
            else:
                print("Wrong file extension.")
                context['wrong_file_extension'] = True
                return render(request, template, context)
    elif request.method == "POST" and request.POST:
        if request.POST['selectFileName']:
            success = writeModelPath(request.POST['selectFileName'])
            if success is True:
                context['changed_file_name'] = request.POST['selectFileName']
            context = getModelList(context)
            return render(request, template, context)
    return render(request, template, context)


# This function is just for writing the changed model name to a config file
def writeModelPath(name):
    try:
        path = os.path.join(FileSystemStorage().location, name)
        config = configparser.ConfigParser()
        config['Path'] = {'ModelPath': path}
        with open('model.ini', 'w') as configfile:
            config.write(configfile)
        print("write_success")
        return True
    except:
        return False





        # template_name = 'display/this.html'
        #
        # def get(self, request):ve
        #     try:a
        #         this_query = Categories.objects.values("categoryname", "description").order_by('categoryid')
        #     except Categories.DoesNotExist:
        #         raise Http404('The object does not exist.')
        #     return render(request, self.template_name, {'this_query': this_query})

# def get_data(request):
#     try:
#         categories = Event.objects.values("categoryname", "description").order_by('categoryid')
#     except Event.DoesNotExist:
#         raise Http404('The object does not exist.')
#     html = "<h1>Return Message</h1>"
#     response_data = {}
#     response_data['data'] = html
#     response_data['message'] = list(categories)
#
#     return JsonResponse(response_data)
#
#
# def dataEmp(request):
#     try:
#         querySet = Event.objects.order_by('employeeid')
#         this_query = serializers.serialize('json', list(querySet), fields=('employeeid', 'firstname', 'lastname'))
#     except Event.DoesNotExist:
#         raise Http404('The object does not exist.')
#     return JsonResponse(this_query, safe=False)


# def dataCat(request):
#     try:
#         categories = Event.objects.values("categoryname", "description").order_by('categoryid')
#     except Event.DoesNotExist:
#         raise Http404('The object does not exist.')
#     return JsonResponse(categories)
#
#
# class chart_data(APIView):
#     authentication_classes = []
#     permission_classes = []
#
#     def get(self, request, format=None):
#         data = {
#             "sales": 101230,
#             "customers": 110,
#             "users": User.objects.all().count(),
#         }
#         return Response(data)
