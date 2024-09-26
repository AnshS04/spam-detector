import re
import datetime
import jwt
import os

from .models import User
from .models import Contact

from django.http import JsonResponse

def validate_phone_number(phone_number):
    if not re.match(r'^\d{10}$', phone_number):
        return JsonResponse({'error': 'Phone number must be 10 digits long and contain only numbers'}, status=400)
    return None

def generate_jwt(phone_number):
    payload = {
        'phone_number': phone_number,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7), 
        'iat': datetime.datetime.utcnow(), 
    }
    return jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm='HS256')


def decode_jwt(auth_header):
    try:
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=['HS256'])
        user_phone_number = payload['phone_number']
        user = User.objects.get(phone_number=user_phone_number)
        return user, None
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None, JsonResponse({'error': 'Invalid token'}, status=401)
    except User.DoesNotExist:
        return None, JsonResponse({'error': 'Token does not exist'}, status=404)

    

def calculateSpamLikelihood(contact_number):
    
    total_count = Contact.objects.filter(phone_number=contact_number).count()
    
    if total_count == 0:
        return 0.0
    
    spam_count = Contact.objects.filter(phone_number=contact_number, is_spam=True).count()
    
    
    spam_likelihood = spam_count / total_count
    
    return spam_likelihood


def find_unique(results):
    seen_phone_numbers = set()
    unique_results = []

    for obj in results:
        phone_number = obj.phone_number
        if phone_number not in seen_phone_numbers:
            seen_phone_numbers.add(phone_number)
            unique_results.append(obj)

    return unique_results
    
