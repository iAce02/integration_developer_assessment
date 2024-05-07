from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from hotel import pms_systems


@csrf_exempt
@require_POST
def webhook(request, pms_name):
    """
    Assume a webhook call from the PMS with a status update for a reservation.
    The webhook call is a POST request to the url: /webhook/<pms_name>/
    The body of the request should always be a valid JSON string and contain the needed information to perform an update.
    """

    pms = pms_systems.get_pms(pms_name)
    payload_cleaned = pms.clean_webhook_payload(request.body)
    success = pms.handle_webhook(payload_cleaned)
    if not success:
        return success
    else:
        return HttpResponse("Thanks for the update.")
