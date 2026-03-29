from rest_framework import serializers
from App.models import Pocket, Transaction, PatternRule


class PocketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pocket
        fields = [
            'id', 'name', 'pocket_type', 'balance',
            'budget_limit', 'is_archived', 'created_at',
        ]
        read_only_fields = ['id', 'balance', 'created_at']


class TransactionSerializer(serializers.ModelSerializer):
    pocket_name = serializers.CharField(source='pocket.name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'pocket', 'pocket_name', 'amount', 'direction',
            'source_bank', 'raw_sms', 'assigned_by',
            'confidence_score', 'note', 'transacted_at', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'pocket_name']


class SuggestRequestSerializer(serializers.Serializer):
    """
    What the app sends when it wants a pocket suggestion.
    """
    amount      = serializers.IntegerField(min_value=1)
    direction   = serializers.ChoiceField(choices=['credit', 'debit'])
    source_bank = serializers.CharField(max_length=32, allow_blank=True, default='')


class SuggestResponseSerializer(serializers.Serializer):
    """
    What Django sends back — the suggested pocket and confidence.
    """
    suggested_pocket_id   = serializers.UUIDField(allow_null=True)
    suggested_pocket_name = serializers.CharField(allow_null=True)
    confidence            = serializers.FloatField()
    # 'auto'       → confidence >= 0.85, app should assign silently
    # 'suggestion' → confidence >= 0.5,  app should pre-select
    # 'none'       → not enough data,    app shows all pockets
    action = serializers.ChoiceField(choices=['auto', 'suggestion', 'none'])


class ConfirmSerializer(serializers.Serializer):
    """
    Sent after user confirms or corrects a suggestion.
    transaction_id: the transaction that was just logged
    confirmed:      True if user kept the suggestion, False if they changed it
    """
    transaction_id = serializers.UUIDField()
    confirmed      = serializers.BooleanField()
