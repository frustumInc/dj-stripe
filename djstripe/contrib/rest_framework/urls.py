# -*- coding: utf-8 -*-
"""
.. module:: dj-stripe.contrib.rest_framework.urls
    :synopsis: dj-stripe url REST routing for Subscription.

.. moduleauthor:: Philippe Luickx (@philippeluickx)

Wire this into the root URLConf this way::

    url(
        r'^api/v1/stripe/',
        include('djstripe.contrib.rest_framework.urls', namespace="rest_djstripe")
    ),
    # url can be changed
    # Call to 'djstripe.contrib.rest_framework.urls' and 'namespace' must stay as is

"""

from __future__ import unicode_literals
from django.conf.urls import url

from . import views


urlpatterns = [

    # REST api
    url(
        r"^subscription/$",
        views.SubscriptionRestView.as_view(),
        name="subscription"
    ),
    url(
        r"^plans/$",
        views.PlanRestView.as_view(),
        name="plan"
    ),
    url(
        r"^invoices/$",
        views.InvoiceRestView.as_view(),
        name="invoice"
    ),
    url(
        r"^invoices/(?P<invoice_id>\w+)/$",
        views.InvoiceItemsRestView.as_view(),
        name="invoice-item"
    ),
    url(
        r"^billing-info/$",
        views.BillingInfoRestView.as_view(),
        name="billing-info"
    ),
    url(
        r"^charges/$",
        views.ChargeRestView.as_view(),
        name="charge"
    ),
    url(
        r"^change-card/$",
        views.ChangeCreditCardRestView.as_view(),
        name="change-card"
    ),
    url(
        r"^charge/$",
        views.ChargeCreditCardRestView.as_view(),
        name="charge-card"
    ),
]
