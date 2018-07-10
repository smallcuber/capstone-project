from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views import generic, View
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from .models import Event
from django.contrib.auth import get_user_model
from django.db.models import Value, Count, Q
from django.views.decorators.csrf import csrf_exempt
import json

User = get_user_model()


def providers_list(max_results=0, name_starts_with=''):
    name_list = []
    if name_starts_with:
        name_list_query = Event.objects.values('provider_scheduled', 'provider_name').filter(
            provider_name__contains=name_starts_with).annotate(provider_count=Count("provider_name"))[:max_results]
        name_list = [name for name in name_list_query]
    return name_list


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
    schedule_list_query = Event.objects.order_by('appointment_date').\
                              values_list('provider_name', 'patient_id','appointment_date', 'appt_durantion')[
                          :max_results]
    schedule_list = [[str(field) for field in schedule] for schedule in schedule_list_query]
    return schedule_list


@csrf_exempt
def scheduleview(request):  #
    template = 'data/schedule.html'
    array = []
    # array = [['Magnolia Room', 'Beginning JavaScript', '2017-12-05 13:22:14.000', '12/5/2017 13:57'],['Magnolia Room', 'Beginning JavaScript', '2017-12-05 15:22:14.000', '12/5/2017 15:57']]
    if request.is_ajax() and request.method == 'POST':
        array = scheduleview_list(30)
        return JsonResponse(array, safe=False)
    return render(request, template, {'array': json.dumps(array)})


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


def patientovview_cr_list(start_date, end_date):
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


@csrf_exempt
def patientovview(request):
    template = 'data/patientov.html'
    if request.is_ajax() and request.method == 'POST':
        if request.POST.get('type') == 'overview':
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            array = patientovview_list(start_date, end_date)
            print(array)
            return JsonResponse(array, safe=False)
        elif request.POST.get('type') == 'canceled_reason':
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            array = patientovview_cr_list(start_date, end_date)
            print(array)
            return JsonResponse(array, safe=False)
    print("a\n\n")
    return render(request, template)


class PatientInfo(generic.ListView):  # Individual patient view
    model = Event
    template_name = 'data/patient_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['appt_counts'] = {}
        try:  # Individual canceled appointments count
            canceled_query = self.model.objects. \
                values_list('canceled_flag'). \
                filter(patient_id=self.kwargs['patient_id'],
                       canceled_flag__isnull=False)
            context['appt_counts'].update({'canceled': canceled_query.count()})
        except ObjectDoesNotExist:
            context['appt_counts'].update({'canceled': 0})

        try:  # Individual no show appointments count
            canceled_query = self.model.objects. \
                values_list('noshow_flag'). \
                filter(patient_id=self.kwargs['patient_id'],
                       noshow_flag__isnull=False)
            context['appt_counts'].update({'noshow': canceled_query.count()})
        except ObjectDoesNotExist:
            context['appt_counts'].update({'noshow': 0})

        try:  # Individual completed appointments count
            canceled_query = self.model.objects. \
                values_list('checkout_time'). \
                filter(patient_id=self.kwargs['patient_id'],
                       noshow_flag__isnull=True,
                       canceled_flag__isnull=True)
            context['appt_counts'].update({'completed': canceled_query.count()})
        except ObjectDoesNotExist:
            context['appt_counts'].update({'completed': 0})

        return context


class ProviderInfo(generic.ListView):  # Individual provider view
    model = Event
    template_name = 'data/provider_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['providerInfo'] = {}
        try:  # Individual canceled appointments count
            completed_query = self.model.objects. \
                values_list('provider_scheduled'). \
                filter(provider_scheduled=self.kwargs['provider_scheduled'],
                       noshow_flag__isnull=True,
                       canceled_flag__isnull=True)
            context['providerInfo'].update({'Completed': completed_query.count()})
        except ObjectDoesNotExist:
            context['providerInfo'].update({'Completed': 0})

        try:  # Individual canceled appointments count
            completed_query = self.model.objects. \
                values_list('provider_scheduled'). \
                filter(provider_scheduled=self.kwargs['provider_scheduled'],
                       noshow_flag__isnull=True,
                       canceled_flag__isnull=True)
            context['providerInfo'].update({'Completed': completed_query.count()})
        except ObjectDoesNotExist:
            context['providerInfo'].update({'Completed': 0})

        return context

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
