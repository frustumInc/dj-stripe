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


class SubscriptionSerializer(ModelSerializer):

    class Meta:
        model = CurrentSubscription


class CreateSubscriptionSerializer(serializers.Serializer):

    stripe_token = serializers.CharField(max_length=200, required=False)
    plan = serializers.CharField(max_length=200)


class InvoiceSerializer(serializers.ModelSerializer):

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
    class Meta:
        model = InvoiceItem


class ChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Charge
