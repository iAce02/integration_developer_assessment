# Runnr.ai integration developer assessment
This repository contains working Django code. Run your code locally, you don't need any external services.
The repo also contains a sqlite database, it contains a single `Hotel` record that you can use for testing. The `pms_hotel_id` corresponds with the example payloads.

## Prerequisites:
- use Python version 3.11
- install dependencies by running: `pip install -r requirements.txt`

## Run server
`python manage.py runserver 0.0.0.0:8000`

## TODO
- Fork the repo into your own Github account. Make the fork public.
- Implement the 4 PMS methods `clean_webhook_payload`, `handle_webhook`, `update_tomorrows_stays`, `stay_has_breakfast` for Mews PMS class.
- Test the webhook call by making a (Postman) POST request to the url: `http://localhost:8000/webhook/mews/` with the payload:
```
{
    "HotelId": "851df8c8-90f2-4c4a-8e01-a4fc46b25178",
    "IntegrationId": "c8bee838-7fb1-4f4e-8fac-ac87008b2f90",
    "Events": [
        {
            "Name": "ReservationUpdated",
            "Value": {
                "ReservationId": "5a9469b7-f13f-4a8d-b092-afe400fd7721"
            }
        },
        {
            "Name": "SomeRandomEvent",
            "Value": {
                "ReservationId": "7c22cb23-c517-48f9-a5d4-da811043bd67"
            }
        }
    ]
}
```
- Test the `update_tomorrows_stays` method by running a Django shell and calling the method manually.
- Make sure all methods create or update the necessary database models
