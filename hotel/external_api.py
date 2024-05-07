import datetime
import json
import random
import uuid

"""
This document simulates the external API that our system uses to communicate with the
booking systems from hotels (Property Management Systems). Use the below functions to
simulate the communication with the external API.
"""


class APIError(Exception):
    # in this case the status codes and response from external_api are None,
    # but it is a good message if later that is handled differently
    def __init__(self, message, status_code=None, response=None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(message)

    def __str__(self):
        return f"{self.message} - Status Code: {self.status_code} - Response: {self.response}"


reservation_statuses = [
    "in_house",
    "checked_out",
    "cancelled",
    "no_show",
    "not_confirmed",
    "booked",
]


def get_reservations_for_given_checkin_date(checkin_date: str) -> str:
    """
    Returns reservations for a given checkin date.
    The reservations are returned as a JSON string.
    Note, the checkin date is a string in the format YYYY-MM-DD.
    This is just to simulate the external API.
    """

    assert isinstance(checkin_date, str), "checkin_date should be a string."
    assert datetime.datetime.strptime(checkin_date, "%Y-%m-%d"), "checkin_date should have the format: YYYY-MM-DD."

    # This API call can fail randomly, just to simulate a real API.
    if random.randint(0, 10) == 0:
        raise APIError("The API is not available.")

    return json.dumps(
        [
            {
                "HotelId": "851df8c8-90f2-4c4a-8e01-a4fc46b25178",
                "ReservationId": str(uuid.uuid4()),
                "GuestId": str(uuid.uuid4()),
                "Status": reservation_statuses[random.randint(0, len(reservation_statuses) - 1)],
                "CheckInDate": checkin_date,
                "CheckOutDate": (
                    datetime.datetime.strptime(checkin_date, "%Y-%m-%d")
                    + datetime.timedelta(days=random.randint(1, 10))
                ).strftime("%Y-%m-%d"),
                "BreakfastIncluded": random.choice([True, False]),
                "RoomNumber": random.randint(1, 100),
            }
            for _ in range(random.randint(1, 10))
        ]
    )


def get_reservation_details(reservation_id: str) -> str:
    """
    Returns the reservation details for any given reservation ID.
    The reservation details are returned as a JSON string.
    """

    # This API call can fail randomly, just to simulate a real API.
    if random.randint(0, 10) == 0:
        raise APIError("The API is not available.")

    return json.dumps(
        {
            "HotelId": "851df8c8-90f2-4c4a-8e01-a4fc46b25178",
            "ReservationId": reservation_id,
            "GuestId": str(uuid.uuid4()),
            "Status": reservation_statuses[random.randint(0, len(reservation_statuses) - 1)],
            "CheckInDate": (datetime.date.today() - datetime.timedelta(days=random.randint(0, 10))).strftime(
                "%Y-%m-%d"
            ),
            "CheckOutDate": (datetime.date.today() + datetime.timedelta(days=random.randint(1, 10))).strftime(
                "%Y-%m-%d"
            ),
            "BreakfastIncluded": random.choice([True, False]),
            "RoomNumber": random.randint(1, 100),
        }
    )


def get_guest_details(guest_id: str) -> str:
    """
    Returns the guest details for any given guest ID.
    The guest details are returned as a JSON string.
    """

    # This API call can fail randomly, just to simulate a real API.
    if random.randint(0, 10) == 0:
        raise APIError("The API is not available.")

    countries = ["NL", "DE", "GG", "GB", "", "CA", "BR", "CN", None, "AU"]
    names = [
        "John Doe",
        "Jane Doe",
        "John Smith",
        "Jane Smith",
        "",
        "Izzy",
        "Sara",
        "Bob",
        "Alice",
        None,
    ]
    phones = [
        "+491234567890",
        "123",
        "0123456789",
        "+442071234567",
        "Not available",
        "+16041234567",
        "",
        "+8612345678901",
        None,
        "+61491570156",
    ]

    return json.dumps(
        {
            "GuestId": guest_id,
            "Name": names[random.randint(0, len(names) - 1)],
            "Phone": phones[random.randint(0, len(phones) - 1)],
            "Country": countries[random.randint(0, len(countries) - 1)],
        }
    )
