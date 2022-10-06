import csv
import datetime

from django.shortcuts import render
from .serializers import *
from .models import *
from .forms import *
from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, FormView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.hashers import make_password
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, ListAPIView
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, ListAPIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import authentication, permissions, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
import json
from bs4 import BeautifulSoup as bs
from django.db.models import F
from django.db.models import Sum


# Create your views here.
class RegisterView(LoginRequiredMixin, CreateView):
    template_name = 'registration/register.html'
    form_class = CreateUser
    success_url = reverse_lazy('clinicians')

    def form_valid(self, form):
        # user = form.save(commit=False)
        first = form.cleaned_data['first_name']
        last = form.cleaned_data['last_name']
        healthy = form.cleaned_data['healthy_facility']
        password = form.cleaned_data['password']
        username = first + "_" + last

        clinician_code = CustomUser.objects.filter(healthy_facility=healthy)

        if clinician_code.exists():
            clinician_code = clinician_code.latest('date_joined').code
            new_code = int(clinician_code)
            new_code = new_code + 1
            code = "0" + str(new_code)
        else:
            code = "01"

        user = form.save(commit=False)
        user.username = username
        user.password = make_password(password)
        user.is_nurse = True
        user.code = code

        user.save()

        return super(RegisterView, self).form_valid(form)


@api_view(['POST'])
def login_api(request):
    serializer = AuthTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    token = Token.objects.get(user=user).key

    return Response({
        'user_info': {
            'code': user.code,
            'healthy_facility': user.healthy_facility.code
        },
        'token': token
    })


# def checking():
#     code = "AL0101AL0101AL0101AL010123"
#     if "_" in code:
#         print('fbubvf')
#     else:
#         first = code[0:5]
#         last = code[-2:]
#         sty = first + last
#         print(sty)


class HomePageView(LoginRequiredMixin, TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):


        checking()

        patient = Patient.objects.all()

        clinicians = CustomUser.objects.filter(is_nurse=True).count()
        forms = patient.count()
        complete = Patient.objects.filter(incomplete="complete").count()
        incomplete = Patient.objects.filter(incomplete="incomplete").count()
        severe = Patient.objects.filter(diagnosis_1__isnull=False).count()
        brochodilator = Patient.objects.filter(bronchodilator="Bronchodialtor Given")
        eligible = brochodilator.count()
        reassessed = brochodilator.filter(after_bronchodilator__isnull=False).count()

        # counter details
        app_opening = (Counter.objects.aggregate(Sum('app_opening_count')))['app_opening_count__sum']
        rr_counter = (Counter.objects.aggregate(Sum('rr_counter_count')))['rr_counter_count__sum']
        learn = (Counter.objects.aggregate(Sum('learn_opening_count')))['learn_opening_count__sum']
        active_users = Patient.objects.values('clinician').distinct().count()

        context = super(HomePageView, self).get_context_data(**kwargs)

        context.update({
            "patients": patient,
            "clinicians": clinicians,
            "forms": forms,
            "complete": complete,
            "incomplete": incomplete,
            "severe": severe,
            "eligible": eligible,
            "reassessed": reassessed,
            "app_opening": app_opening,
            "rr_counter": rr_counter,
            "learn": learn,
            "active_users": active_users,
        })

        return context


class CliniciansPageView(LoginRequiredMixin, TemplateView):
    template_name = 'clinicians.html'

    def get_context_data(self, **kwargs):

        clinicians = CustomUser.objects.filter(is_nurse=True)

        context = super(CliniciansPageView, self).get_context_data(**kwargs)

        context.update({
            "clinicians": clinicians,
        })

        return context


class AppUsageView(LoginRequiredMixin, TemplateView):
    template_name = "app_usage.html"


class SavePatientDataView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @csrf_exempt
    def post(self, request):

        file = request.FILES.get('patient')
        print(file)

        user = self.request.user

        bs_content = bs(file, 'lxml')
        list_ = list(bs_content.find('map').children)
        list_ = list(filter(lambda a: a != '\n', list_))

        myDict = {}
        for c in list_:
            myDict[c.get('name')] = c.text

        if "clinician" in myDict:
            username = myDict["clinician"]
            username = CustomUser.objects.get(username=username)
            if "incomplete" in myDict:
                incomplete = myDict['incomplete']
                if incomplete == "incomplete":
                    CustomUser.objects.filter(username=username)\
                        .update(forms=F("forms") + 1, incomplete_forms=F("incomplete_forms") + 1)
                    incomplete = "incomplete"
                else:
                    CustomUser.objects.filter(username=username) \
                        .update(forms=F("forms") + 1, completed_forms=F("completed_forms") + 1)
                    incomplete = "complete"
            else:
                incomplete = ""

        else:
            username = CustomUser.objects.get(username="chodrine")
            incomplete = ""

        study_id = myDict['study_id']
        if "_" in study_id:
            study = study_id
        else:
            first = study_id[0:5]
            last = study_id[-2:]
            study = first + last

        popKey("diagnosis", myDict)
        popKey("oxDiagnosis", myDict)
        popKey("stDiagnosis", myDict)
        popKey("gnDiagnosis", myDict)
        popKey("gnDiagnosis", myDict)
        popKey("clinician", myDict)
        popKey("second", myDict)
        popKey("filename", myDict)
        popKey("final", myDict)
        popKey("study_id_2", myDict)
        popKey("reassess", myDict)
        popKey("pending", myDict)
        popKey("incomplete", myDict)
        popKey("study_id", myDict)

        Patient.objects.create(**myDict, clinician_2=user, clinician=username, incomplete=incomplete, study_id=study)

        return Response("Data saved successfully")


def popKey(key, dict):
    if key in dict:
        dict.pop(key)


class SaveCountDataView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @csrf_exempt
    def post(self, request):

        file = request.FILES.get('counter')
        # new changes

        user = self.request.user

        bs_content = bs(file, 'lxml')
        list_ = list(bs_content.find('map').children)
        list_ = list(filter(lambda a: a != '\n', list_))

        myDict = {}
        for c in list_:
            myDict[c.get('name')] = c.text

        Counter.objects.create(**myDict, clinician=user)

        return Response("Data saved successfully")


def export_csv(request):

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=Alrite_Dataset_' + str(datetime.datetime.now()) + '.csv'

    writer = csv.writer(response)
    writer.writerow(['date', 'patient_study_id', 'age(months)', 'gender', 'weight', 'muac', 'symptoms',
                     'difficulty_breathing', 'days_with_breathing_difficulties', 'hiv_status', 'child_in_hiv_care',
                     'temperature', 'febrile_to_touch', 'blood_oxygen_saturation', 'respiratory_rate', 'breathing_rate',
                     'respiratory_rate_score', 'stridor', 'nasal_flaring', 'wheezing', 'stethoscope_used',
                     'chest_indrawing', 'bronchodilator', 'bronchodilator_not_given_reason', 'duration', 'diagnosis_1',
                     'diagnosis_2', 'diagnosis_3', 'diagnosis_4', 'diagnosis_5', 'diagnosis_6', 'diagnosis_7',
                     'diagnosis_8', 'diagnosis_9', 'diagnosis_10',
                     'diagnosis_11', 'respiratory_rate_2', 'breathing_rate_2', 'respiratory_rate_score_2',
                     'wheezing_2', 'chest_indrawing_2', 'wheezing_before_this_illness', 'child_breathless',
                     'breathing_difficulties_last_year', 'child_ever_had_eczema', 'child_parents_with_allergies',
                     'smoke_tobacco', 'use_kerosene', 'clinician_diagnosis', 'clinician_treatment' 'incomplete'])

    patients = Patient.objects.all()

    for patient in patients:
        writer.writerow([patient.end_date, patient.study_id, patient.age, patient.gender,
                         patient.weight, patient.muac, patient.symptoms, patient.difficulty_breathing, patient.days_with_breathing_difficulties,
                         patient.hiv_status, patient.child_in_hiv_care, patient.temperature, patient.febrile_to_touch,
                         patient.blood_oxygen_saturation, patient.respiratory_rate, patient.breathing_rate, patient.respiratory_rate_score,
                         patient.stridor, patient.nasal_flaring, patient.wheezing, patient.stethoscope_used, patient.chest_indrawing,
                         patient.bronchodilator, patient.bronchodilator_not_given_reason, patient.duration, patient.diagnosis_1,
                         patient.diagnosis_2, patient.diagnosis_3, patient.diagnosis_4, patient.diagnosis_5, patient.diagnosis_6,
                         patient.diagnosis_7, patient.diagnosis_8, patient.diagnosis_9, patient.diagnosis_10, patient.diagnosis_11,
                         patient.respiratory_rate_2, patient.breathing_rate_2, patient.respiratory_rate_score_2,
                         patient.wheezing_2, patient.chest_indrawing_2, patient.wheezing_before_this_illness,
                         patient.child_breathless, patient.breathing_difficulties_last_year, patient.child_ever_had_eczema,
                         patient.child_parents_with_allergies, patient.smoke_tobacco, patient.use_kerosene, patient.clinician_diagnosis,
                         patient.clinician_treatment, patient.incomplete])

    return response






