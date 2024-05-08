from abc import ABC, abstractmethod
import inspect
import sys
from .external_api import get_reservations_for_given_checkin_date, get_guest_details, get_reservation_details, APIError
from .models import Stay, Guest, Hotel
import json
import datetime
import phonenumbers
import pycountry

from typing import Optional


class PMS(ABC):
    """
    Abstract class for Property Management Systems.
    """

    def __init__(self):
        pass

    @property
    def name(self):
        longname = self.__class__.__name__
        return longname[4:]

    @abstractmethod
    def clean_webhook_payload(self, payload: str) -> dict:
        """
        Clean the json payload and return a usable object.
        Make sure the payload contains all the needed information to handle it properly
        """

        raise NotImplementedError

    @abstractmethod
    def handle_webhook(self, webhook_data: dict) -> bool:
        """
        This method is called when we receive a webhook from the PMS.
        Handle webhook handles the events and updates relevant models in the database.
        Requirements:
            - Now that the PMS has notified you about an update of a reservation, you need to
                get more details of this reservation. For this, you can use the mock API
                call get_reservation_details(reservation_id).
            - Handle the payload for the correct hotel.
            - Update or create a Stay.
            - Update or create Guest details.
        """
        raise NotImplementedError

    @abstractmethod
    def update_tomorrows_stays(self) -> bool:
        """
        This method is called every day at 00:00 to update the stays with a checkin date tomorrow.
        Requirements:
            - Get all stays checking in tomorrow by calling the mock API endpoint get_reservations_for_given_checkin_date.
            - Update or create the Stays.
            - Update or create Guest details. Deal with missing and incomplete data yourself
                as you see fit. Deal with the Language yourself. country != language.
        """
        raise NotImplementedError

    @abstractmethod
    def stay_has_breakfast(self, stay: Stay) -> Optional[bool]:
        """
        This method is called when we want to know if the stay includes breakfast.
        Notice that the breakfast data is not stored in any of the models, we always want real time data.
        - Return True if the stay includes breakfast, otherwise False. Return None if you don't know.
        """
        raise NotImplementedError


class PMS_Mews(PMS):
    # I believe integration ID is not needed
    def clean_webhook_payload(self, payload: str) -> dict:
        response = json.loads(payload)
        hotel_id = response.get('HotelId')
        events = response.get('Events', [])
        reservations_ids = []
        if events is not None and events != []:
            for event in events:
                res_id = event.get('Value').get('ReservationId')
                reservations_ids.append(res_id)
        cleaned_list = list(set(reservations_ids))
        result = {'hotel_id': hotel_id, 'reservation_ids': cleaned_list}
        return result

    def handle_webhook(self, webhook_data: dict) -> bool:
        hotel_id = webhook_data.get('hotel_id')
        reservation_ids = webhook_data.get('reservation_ids', [])
        hotel = Hotel.objects.filter(pms_hotel_id=hotel_id).first()

        if not hotel:
            print(f"Hotel with PMS Hotel ID {hotel_id} not found.")
            return False

        for reservation_id in reservation_ids:
            try:
                reservation_details_json = get_reservation_details(reservation_id)
                reservation_details = json.loads(reservation_details_json)

                guest_details_json = get_guest_details(reservation_details['GuestId'])
                guest_details = json.loads(guest_details_json)

                guest_phone = guest_details.get('Phone')
                guest_name = guest_details.get('Name')
                guest_language = guest_details.get('Country')

                # Validate and clean phone number
                try:
                    guest_phone_parsed = phonenumbers.parse(guest_phone, None)
                    if not phonenumbers.is_valid_number(guest_phone_parsed):
                        print(f"Invalid phone number '{guest_phone}'. Skipping.")
                        continue
                    guest_phone_formatted = phonenumbers.format_number(guest_phone_parsed,
                                                                       phonenumbers.PhoneNumberFormat.E164)
                    guest_phone = guest_phone_formatted.lstrip('+')
                except phonenumbers.phonenumberutil.NumberParseException as e:
                    print(f"Error parsing phone number '{guest_phone}': {e}")
                    continue

                if guest_name is None or guest_name == '':
                    print("Guest not available (no name specified). Skipping.")
                    continue

                # Validate country code and pass language based on country
                if guest_language:
                    try:
                        country = pycountry.countries.get(alpha_2=guest_language)
                        guest_language = country.alpha_2 if country else 'en'
                    except Exception as e:
                        print(f"Error validating country code: {e}")
                        guest_language = 'en'
                else:
                    guest_language = 'en'

                existing_guest = Guest.objects.filter(phone=guest_phone).first()
                if existing_guest:
                    existing_guest.name = guest_name
                    existing_guest.language = guest_language
                    existing_guest.save()
                    guest = existing_guest
                else:
                    guest = Guest.objects.create(
                        phone=guest_phone,
                        name=guest_name,
                        language=guest_language
                    )

                existing_stay = Stay.objects.filter(hotel=hotel, pms_reservation_id=reservation_id).first()
                if existing_stay:
                    print(
                        f"Stay with hotel_id={hotel.id} and pms_reservation_id={reservation_id} already exists. Skipping.")
                    continue

                stay_instance, stay_created = Stay.objects.Stay.objects.get_or_create(
                    hotel_id=hotel,
                    pms_reservation_id=reservation_id,
                    checkin=reservation_details['CheckInDate'],
                    checkout=reservation_details['CheckOutDate'],
                    pms_guest_id=reservation_details['GuestId'],
                    status=Stay.Status.BEFORE,
                    guest=guest
                )

            except APIError as e:
                print(f"API Error: {e}")
                return False

        return True

    def update_tomorrows_stays(self) -> bool:
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%Y-%m-%d")

        try:
            reservations_json = get_reservations_for_given_checkin_date(tomorrow_str)
            reservations = json.loads(reservations_json)

            for reservation in reservations:
                guest_details_json = get_guest_details(reservation['GuestId'])
                guest_details = json.loads(guest_details_json)

                guest_phone = guest_details.get('Phone')
                guest_name = guest_details.get('Name')
                guest_language = guest_details.get('Country')

                # validate and clean phone number
                # skip if no phone number is present
                # validate and clean phone number
                try:
                    guest_phone_parsed = phonenumbers.parse(guest_phone, None)
                    if not phonenumbers.is_valid_number(guest_phone_parsed):
                        print("Invalid phone number. Skipping.")
                        continue
                    guest_phone_formatted = phonenumbers.format_number(guest_phone_parsed,
                                                                       phonenumbers.PhoneNumberFormat.E164)
                    guest_phone = guest_phone_formatted.lstrip('+')
                except phonenumbers.phonenumberutil.NumberParseException as e:
                    print(f"Error parsing phone number: {e}")
                    print(f"Phone number causing the error: {guest_phone}")
                    continue

                # If no guest name is specified, skip, again not sure we want to skip
                if guest_name is None or guest_name == '':
                    print("Guest not available (no name specified). Skipping.")
                    continue

                # validate country code and pass language based on country
                # If no country is specified set the default language english
                if guest_language:
                    try:
                        country = pycountry.countries.get(alpha_2=guest_language)
                        if country:
                            primary_language = pycountry.languages.get(alpha_2=country.alpha_2)
                            if primary_language:
                                guest_language = primary_language.alpha_2
                            else:
                                guest_language = 'en'
                        else:
                            guest_language = 'en'
                    except Exception as e:
                        print(f"Error validating country code: {e}")
                        guest_language = 'en'
                else:
                    guest_language = 'en'

                existing_guest = Guest.objects.filter(phone=guest_phone).first()

                if existing_guest:
                    existing_guest.name = guest_name
                    existing_guest.language = guest_language
                    existing_guest.save()
                    guest = existing_guest
                else:
                    guest = Guest.objects.create(
                        phone=guest_phone,
                        name=guest_name,
                        language=guest_language
                    )

                existing_stay = Stay.objects.filter(
                    hotel__pms_hotel_id=reservation['HotelId'],  # Assuming pms_hotel_id is the identifier for hotels
                    pms_reservation_id=reservation['ReservationId']
                ).first()

                # If a stay already exists, skip
                if existing_stay:
                    print(f"Stay with hotel_id={reservation['HotelId']} and pms_reservation_id="
                          f"{reservation['ReservationId']} already exists. Skipping.")
                    continue

                hotel = Hotel.objects.filter(pms_hotel_id=reservation['HotelId']).first()

                Stay.objects.create(
                    hotel=hotel,
                    pms_reservation_id=reservation['ReservationId'],
                    checkin=tomorrow,
                    checkout=reservation['CheckOutDate'],
                    pms_guest_id=reservation['GuestId'],
                    status=Stay.Status.BEFORE,
                    guest=guest
                )

        except APIError as e:
            print(f"API Error: {e}")
            return False

        return True

    def stay_has_breakfast(self, stay: Stay) -> Optional[bool]:
        reservation_id = stay.pms_reservation_id
        reservation_details_json = get_reservation_details(reservation_id)
        reservation_details = json.loads(reservation_details_json)
        return reservation_details.get('BreakfastIncluded')


def get_pms(name):
    fullname = "PMS_" + name.capitalize()
    # find all class names in this module
    # from https://stackoverflow.com/questions/1796180/
    current_module = sys.modules[__name__]
    clsnames = [x[0] for x in inspect.getmembers(current_module, inspect.isclass)]

    # if we have a PMS class for the given name, return an instance of it
    return getattr(current_module, fullname)() if fullname in clsnames else False
