# -*- coding: utf-8 -*-
"""
.. module:: dj-stripe.contrib.rest_framework.views
    :synopsis: dj-stripe REST views for Subscription.

.. moduleauthor:: Philippe Luickx (@philippeluickx)

"""

from __future__ import unicode_literals

import logging
import stripe
from decimal import Decimal

import django.dispatch
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from djstripe.models import Invoice
from djstripe.contrib.rest_framework.serializers import InvoiceSerializer

from ...settings import subscriber_request_callback, CANCELLATION_AT_PERIOD_END
from ...models import Customer, Plan
from .serializers import SubscriptionSerializer, CreateSubscriptionSerializer
from .permissions import DJStripeSubscriptionPermission

logger = logging.getLogger(__name__)


class SubscriptionRestView(APIView):
    """
    A REST API for Stripes implementation in the backend
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        """
        Return the users current subscription.
        Returns with status code 200.
        """

        try:
            customer, created = Customer.get_or_create(
                subscriber=subscriber_request_callback(self.request)
            )
            subscription = customer.current_subscription

            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data)

        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, format=None):
        """
        Create a new current subscription for the user.
        Returns with status code 201.
        """

        serializer = CreateSubscriptionSerializer(data=request.data)

        if serializer.is_valid():
            try:
                customer, created = Customer.get_or_create(
                    subscriber=subscriber_request_callback(self.request)
                )
                stripe_token = serializer.data.get("stripe_token", None)
                if stripe_token:
                    customer.update_card(stripe_token)
                customer.subscribe(serializer.data["plan"])
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

            except:
                # TODO
                # Better error messages
                return Response(
                    "Something went wrong processing the payment.",
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, format=None):
        """
        Marks the users current subscription as cancelled.
        Returns with status code 204.
        """

        try:
            customer, created = Customer.get_or_create(
                subscriber=subscriber_request_callback(self.request)
            )
            customer.cancel_subscription(
                at_period_end=CANCELLATION_AT_PERIOD_END
            )

            return Response(status=status.HTTP_204_NO_CONTENT)

        except:
            return Response(
                "Something went wrong cancelling the subscription.",
                status=status.HTTP_400_BAD_REQUEST
            )


class PlanRestView(APIView):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        plans = [settings.DJSTRIPE_PLANS[plan] for plan in settings.DJSTRIPE_PLANS.keys()]
        return Response(plans)


class InvoiceRestView(generics.ListAPIView):

    permission_classes = (IsAuthenticated,)
    serializer_class = InvoiceSerializer

    def get_queryset(self, *args, **kwargs):
        customer, created = Customer.get_or_create(
            subscriber=subscriber_request_callback(self.request)
        )
        return Invoice.objects.filter(customer=customer).order_by('created')


class ChangeCreditCardRestView(APIView):
    permission_classes = (IsAuthenticated, DJStripeSubscriptionPermission)

    def post(self, request):
        customer, created = Customer.get_or_create(
            subscriber=subscriber_request_callback(self.request)
        )
        try:
            send_invoice = customer.card_fingerprint == ""
            customer.update_card(
                request.data.get("stripe_token")
            )
            if send_invoice:
                customer.send_invoice()
            customer.retry_unpaid_invoices()
        except stripe.StripeError as exc:
            return Response({'stripe_error': str(exc)})
        return Response({'info': 'your card has been updated'})


credit_card_charged = django.dispatch.Signal(
        providing_args=['customer', 'amount'])

credit_card_charge_failed = django.dispatch.Signal(
        providing_args=['customer', 'amount', 'exception'])


class ChargeCreditCardRestView(APIView):
    """Individual Charge Users Card"""

    permission_classes = (IsAuthenticated, DJStripeSubscriptionPermission)

    def post(self, request):
        customer, created = Customer.get_or_create(
            subscriber=request.user
        )
        amount = Decimal(request.data.get('amount'))
        description = request.data.get('description', None)

        try:
            charged = customer.charge(
                amount,
                description=description,
                send_receipt=True,
                receipt_email=customer.subscriber.email
            )
            credit_card_charged.send(
                    sender=self.__class__, customer=customer, amount=amount)
            logger.info("Charged %s from customer %s" % (amount, customer.id))
            return Response({'info': "your card has been charged"})
        except Exception, e:
            logger.error(e)
            credit_card_charge_failed.send(
                    sender=self.__class__,
                    customer=customer,
                    amount=amount,
                    exception=e)

            return Response(
                    {'info': e.message}, status=status.HTTP_400_BAD_REQUEST)
