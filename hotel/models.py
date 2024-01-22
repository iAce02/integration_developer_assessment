from django.db import models


class Language(models.TextChoices):
    GERMAN = "de", "German"
    BRITISH_ENGLISH = "en-GB", "British English"
    SPANISH_SPAIN = "es-ES", "Spanish (Spain)"
    FRENCH = "fr", "French"
    ITALIAN = "it", "Italian"
    DUTCH = "nl", "Dutch"
    PORTUGUESE_PORTUGAL = "pt-PT", "Portuguese (Portugal)"
    SWEDISH = "sv", "Swedish"
    DANISH = "da", "Danish"


class Hotel(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=200, blank=False, null=False)
    pms_hotel_id = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.city} - {self.name}"


class Guest(models.Model):
    """
    Guests are identified by their phone number.
    """

    name = models.CharField(max_length=200)
    phone = models.CharField(
        max_length=200,
        unique=True,
    )
    language = models.CharField(
        max_length=5, choices=Language.choices, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Stay(models.Model):
    """
    One guest can stay in multiple hotels.
    One hotel can have multiple guests and multiple stays.
    Stays are unique by hotel and pms_reservation_id.
    """

    class Status(models.TextChoices):
        CANCEL = "cancel", "The guest has cancelled the reservation"
        BEFORE = "before", "The guest has not checked in yet"
        INSTAY = "instay", "The guest is currently in the hotel"
        AFTER = "after", "The guest has checked out"
        UNKNOWN = "unknown", "The status is unknown"

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="stays")
    guest = models.ForeignKey(
        Guest, on_delete=models.CASCADE, related_name="stays", blank=True, null=True
    )
    pms_reservation_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="The reservation ID from the Property Management System",
    )
    pms_guest_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="""The guest ID from the Property Management System.
        This is intended to be on Stay level, as the same person (phone) can stay in
        multiple hotels with different guest IDs.""",
    )
    status = models.CharField(
        choices=Status.choices, default=Status.UNKNOWN, max_length=50
    )
    checkin = models.DateField(blank=True, null=True)
    checkout = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("hotel", "pms_reservation_id")
