# -*- coding: utf-8 -*-
from rest_framework.permissions import BasePermission

from djstripe.models import Customer

from ...utils import subscriber_has_active_subscription
from ...settings import subscriber_request_callback


class DJStripeSubscriptionPermission(BasePermission):

    def has_permission(self, request, view):
        """
        Check if the subscriber has an active subscription.

        Returns false if:
            * a subscriber isn't passed through the request

        See ``utils.subscriber_has_active_subscription`` for more rules.

        """

        try:
            customer, created = Customer.get_or_create(
                subscriber=subscriber_request_callback(request)
            )
            return customer.has_active_subscription()
        except AttributeError:
            return False
