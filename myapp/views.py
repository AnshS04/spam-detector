from .models import User
from .models import Contact

import re
import json
import jwt
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from dotenv import load_dotenv
from . import helpers

load_dotenv()

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            phone_number = data.get('phone_number')
            email = data.get('email')
            password = data.get('password')
            
            if not name or not phone_number or not password:
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            error_response = helpers.validate_phone_number(phone_number)
            if error_response:
                return error_response
            
            if User.objects.filter(phone_number=phone_number).exists():
                return JsonResponse({'error': 'Phone number already exists'}, status=400)
            
            if email:
                if User.objects.filter(email=email).exists():
                    return JsonResponse({'error': 'Email already exists'}, status=400)


            hashed_password = make_password(password)
            
            
            user = User(phone_number=phone_number, name=name, email=email, password=hashed_password)
            user.save()

            
            return JsonResponse({'message': 'User registered successfully'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            password = data.get('password')

            
            if not phone_number or not password:
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            error_response = helpers.validate_phone_number(phone_number)
            if error_response:
                return error_response

        
            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                return JsonResponse({'error': 'Invalid phone number or password'}, status=400)

            
            if not check_password(password, user.password):
                return JsonResponse({'error': 'Invalid phone number or password'}, status=400)

            
            access_token  = helpers.generate_jwt(user.phone_number)
            return JsonResponse({'message': 'Login successful', 'access': access_token}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def report_spam(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')

            
            auth_header = request.META.get('HTTP_AUTHORIZATION', None)
            if auth_header is None:
                return JsonResponse({'error': 'Authorization header is missing'}, status=401)

            
            user, error_response = helpers.decode_jwt(auth_header)

            if error_response:
                return error_response

            if not phone_number:
                return JsonResponse({'error': 'Phone number is required'}, status=400)

            error_response = helpers.validate_phone_number(phone_number)
            if error_response:
                return error_response

            
            contact = Contact.objects.filter(phone_number=phone_number, added_by=user).first()
            userExist = User.objects.filter(phone_number=phone_number).first()

            if contact:
                
                if contact.is_spam:
                    return JsonResponse({'message': 'Already marked spam'}, status=201)
                
                contact.is_spam = True
                contact.save()
                return JsonResponse({'message': 'Spam reported successfully'}, status=201)
            elif userExist: 
                spamUser = Contact.objects.create(
                    phone_number=userExist.phone_number,
                    name=userExist.name,
                    added_by=user,
                    is_spam=True
                )
                return JsonResponse({'message': 'Spam reported successfully'}, status=201)
            else:
                
                spam_report = Contact.objects.create(
                    phone_number=phone_number,
                    name="Spam",
                    added_by=user,
                    is_spam=True
                )
                return JsonResponse({'message': 'Spam reported successfully'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def add_contact(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            phone_number = data.get('phone_number')
            auth_header = request.META.get('HTTP_AUTHORIZATION', None)

            
            if auth_header is None:
                return JsonResponse({'error': 'Authorization header is missing'}, status=401)

            
            user, error_response = helpers.decode_jwt(auth_header)

            if error_response:
                return error_response
            
            if not name or not phone_number:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            error_response = helpers.validate_phone_number(phone_number)
            if error_response:
                return error_response

            if Contact.objects.filter(phone_number=phone_number, added_by=user).exists():
                return JsonResponse({'error': 'Contact already exists'}, status=400)

            
            contact = Contact(phone_number=phone_number, name=name, added_by=user)
            contact.save()

            
            return JsonResponse({'message': 'Contact added successfully'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)



def search_contacts(request):
    if request.method == 'GET':
        auth_header = request.META.get('HTTP_AUTHORIZATION', None)

        
        if auth_header is None:
            return JsonResponse({'error': 'Authorization header is missing'}, status=401)

        
        user, error_response = helpers.decode_jwt(auth_header)

        if error_response:
            return error_response

        query = request.GET.get('name', '') 

        if not query:
            return JsonResponse({'error': 'No search query provided'}, status=400)

        
        results_start_contacts = Contact.objects.filter(name__istartswith=query).exclude(name="Spam")

        results_contains_contacts = Contact.objects.filter(name__icontains=query).exclude(name__istartswith=query).exclude(name="Spam")

        results_start_users = User.objects.filter(name__istartswith=query)

        results_contains_users = User.objects.filter(name__icontains=query).exclude(name__istartswith=query)

        results = (
            list(results_start_contacts) + 
            list(results_contains_contacts) + 
            list(results_start_users) + 
            list(results_contains_users)
        )

        results.sort(key=lambda x: (not x.name.startswith(query), x.name.lower()))

        unique_results = helpers.find_unique(results)

        formatted_results = [{
            'name': contact.name,
            'phone_number': contact.phone_number,
            'spam_likelihood': helpers.calculateSpamLikelihood(contact.phone_number),
            'open_contact': f'http://localhost:8000/api/getDetails?registered={"no" if hasattr(contact, "added_by") else "yes"}&id={contact.id if hasattr(contact, "added_by") else contact.phone_number}'
        } for contact in unique_results]


        return JsonResponse(formatted_results, safe=False, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def search_by_phone_number(request):
    if request.method == 'GET':
        auth_header = request.META.get('HTTP_AUTHORIZATION', None)


        if auth_header is None:
            return JsonResponse({'error': 'Authorization header is missing'}, status=401)

        
        user, error_response = helpers.decode_jwt(auth_header)

        if error_response:
            return error_response
        
        phone_number = request.GET.get('phone_number', '')

        if not phone_number:
            return JsonResponse({'error': 'No search query provided'}, status=400)
        
        error_response = helpers.validate_phone_number(phone_number)
        if error_response:
            return error_response
        
        user = User.objects.filter(phone_number=phone_number).first()
        
        if user:
            return JsonResponse({
                'Phone': user.phone_number,
                'Name': user.name,
                'open_contact': f'http://localhost:8000/api/getDetails?registered=yes&id={user.phone_number}',
            }, status=200)
        else:
            contacts = Contact.objects.filter(phone_number=phone_number)
            
            if contacts.exists():
                contact_list = [
                    {
                        'phone': contact.phone_number,
                        'name': contact.name,
                        'open_contact': f'http://localhost:8000/api/getDetails?registered=no&id={contact.id}',
                    }
                    for contact in contacts
                ]

                return JsonResponse({
                    'contacts': contact_list
                }, status=200)
            else:
                return JsonResponse({
                    'message': 'No results found for this phone number.'
                }, status=405
                )
    return JsonResponse({'error': 'Invalid request method'}, status=405)



def get_details(request):
    if request.method == 'GET':
        auth_header = request.META.get('HTTP_AUTHORIZATION', None)

            
        if auth_header is None:
            return JsonResponse({'error': 'Authorization header is missing'}, status=401)

        
        user, error_response = helpers.decode_jwt(auth_header)

        if error_response:
            return error_response
        
        registered = request.GET.get('registered', '')
        identifier = request.GET.get('id', '')

        if not registered or not identifier:
            return JsonResponse({'error': 'Provide all search queries'}, status=400)
        

        if registered == "no":
            contact = Contact.objects.filter(id=identifier).first()
            if contact:
                return JsonResponse({
                    'Name': contact.name,
                    'Phone': contact.phone_number,
                    'Spam Likelihood': helpers.calculateSpamLikelihood(contact.phone_number)
                }, status=200)
            else:
                return JsonResponse({
                    "message": "cannot find user"
                }, status=400)
                
        else:
            userFound = User.objects.filter(phone_number=identifier).first()
            inContacts = Contact.objects.filter(
                phone_number=user.phone_number,
                added_by=userFound
            ).exclude(name="Spam")

            if userFound:
                if inContacts:
                    return JsonResponse({
                        'Name': userFound.name,
                        'Phone': userFound.phone_number,
                        'Email': userFound.email,
                        'Spam Likelihood': helpers.calculateSpamLikelihood(identifier)
                    }, status=200)
                else:
                    return JsonResponse({
                        'Name': userFound.name,
                        'Phone': userFound.phone_number,
                        'Spam Likelihood': helpers.calculateSpamLikelihood(identifier)
                    }, status=200)
            else:
                return JsonResponse({
                    "message": "cannot find user"
                })
    return JsonResponse({'error': 'Invalid request method'}, status=405)

