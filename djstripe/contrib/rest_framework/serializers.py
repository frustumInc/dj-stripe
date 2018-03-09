# -*- coding: utf-8 -*-
"""
.. module:: dj-stripe.contrib.rest_framework.serializers
    :synopsis: dj-stripe Serializer for Subscription.

.. moduleauthor:: Philippe Luickx (@philippeluickx)

"""

from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer
from djstripe.models import CurrentSubscription, Invoice, InvoiceItem, Charge
from rest_framework import serializers
import stripe


class SubscriptionSerializer(ModelSerializer):

    class Meta:
        model = CurrentSubscription


class CreateSubscriptionSerializer(serializers.Serializer):

    stripe_token = serializers.CharField(max_length=200, required=False)
    plan = serializers.CharField(max_length=200)


class InvoiceSerializer(serializers.ModelSerializer):

    """
        High-level metadata
    """
    card_info = serializers.SerializerMethodField()
    plan = serializers.SerializerMethodField()

    class Meta:
        model = Invoice

    def get_card_info(self, instance):
        charge = Charge.objects.get(stripe_id=instance.charge)
        card_info = {
          "kind": charge.card_kind,
          "last4": charge.card_last_4
        }
        return card_info

    def get_plan(self, instance):
        inv_item_plan = instance.items.get(plan__isnull=False)
        return inv_item_plan.plan


class InvoiceItemSerializer(serializers.ModelSerializer):

    """
        Line-item details for an invoice
    """
    class Meta:
        model = InvoiceItem


class InvoiceDetailSerializer(serializers.Serializer):
    """
        Invoice details required for client-side invoice doc data
    """

    stripe_id = serializers.CharField(max_length=200, required=False)
    total = serializers.SerializerMethodField()
    line_items = serializers.SerializerMethodField()
    billing_info = serializers.SerializerMethodField()

    def get_total(self, instance):
        return instance.total

    def get_line_items(self, instance):
        invoices = InvoiceItem.objects.filter(invoice_id=instance.id).order_by('created')
        return [InvoiceItemSerializer(invoice).data for invoice in invoices]

    def get_billing_info(self, instance):
        charge = Charge.objects.get(stripe_id=instance.charge) # abbreviated django model
        charge_details = stripe.Charge.retrieve(charge.stripe_id) # need address details from Stripe API
        return {
            "period_start": instance.period_start,
            "period_end": instance.period_end,
            "card": {"kind": charge_details.card.brand, "last4": charge_details.card.last4},
            "address": {address: value for (address, value) in charge_details.card.items() if "address" in address}
        }


class ChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Charge
