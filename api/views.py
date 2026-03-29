from django.shortcuts import render

# Create your views here.

from django.db import models


from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

from App.models import Pocket, Transaction, PatternRule, Direction, AssignedBy
from .serializers import (
    PocketSerializer,
    TransactionSerializer,
    SuggestRequestSerializer,
    SuggestResponseSerializer,
    ConfirmSerializer,
)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    Returns: { "token": "...", "user_id": ..., "username": "..." }
    """
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()

    if not username or not password:
        return Response(
            {'error': 'Username and password are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(username=username, password=password)
    if not user:
        return Response(
            {'error': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token':    token.key,
        'user_id':  user.id,
        'username': user.username,
    })


# ---------------------------------------------------------------------------
# Pockets
# ---------------------------------------------------------------------------

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def pockets(request):
    """
    GET  /api/pockets/  — list all active (non-archived) pockets
    POST /api/pockets/  — create a new pocket
    """
    if request.method == 'GET':
        qs = Pocket.objects.filter(user=request.user, is_archived=False)
        return Response(PocketSerializer(qs, many=True).data)

    serializer = PocketSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def pocket_detail(request, pk):
    """
    GET    /api/pockets/<id>/  — single pocket detail
    PATCH  /api/pockets/<id>/  — rename or archive
    DELETE /api/pockets/<id>/  — hard delete (use archive instead in production)
    """
    pocket = get_object_or_404(Pocket, pk=pk, user=request.user)

    if request.method == 'GET':
        return Response(PocketSerializer(pocket).data)

    if request.method == 'PATCH':
        serializer = PocketSerializer(pocket, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        pocket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def transactions(request):
    """
    GET  /api/transactions/?pocket=<id>  — history (filter by pocket optional)
    POST /api/transactions/              — log a new transaction
    """
    if request.method == 'GET':
        qs = Transaction.objects.filter(pocket__user=request.user)
        pocket_id = request.query_params.get('pocket')
        if pocket_id:
            qs = qs.filter(pocket__id=pocket_id)
        return Response(TransactionSerializer(qs, many=True).data)

    # POST — validate that the pocket belongs to this user
    serializer = TransactionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    pocket = get_object_or_404(Pocket, pk=serializer.validated_data['pocket'].id, user=request.user)
    transaction = serializer.save(pocket=pocket)
    return Response(TransactionSerializer(transaction).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def reassign_transaction(request, pk):
    """
    PATCH /api/transactions/<id>/reassign/
    Body: { "pocket": "<new_pocket_id>" }

    Undo / correct a wrong pocket assignment.
    Moves the transaction to a different pocket and updates both balances.
    Also marks the original pattern rule as unconfirmed (lowers confidence).
    """
    transaction = get_object_or_404(Transaction, pk=pk, pocket__user=request.user)
    new_pocket_id = request.data.get('pocket')

    if not new_pocket_id:
        return Response({'error': 'pocket is required.'}, status=status.HTTP_400_BAD_REQUEST)

    new_pocket = get_object_or_404(Pocket, pk=new_pocket_id, user=request.user)

    if transaction.pocket == new_pocket:
        return Response({'error': 'Transaction is already in that pocket.'}, status=status.HTTP_400_BAD_REQUEST)

    # Reverse the balance on the old pocket
    transaction._update_pocket_balance(-1)

    # Move to new pocket and apply balance there
    transaction.pocket = new_pocket
    transaction.assigned_by = AssignedBy.USER   # human corrected it
    transaction.save(update_fields=['pocket', 'assigned_by'])

    # Re-apply balance on new pocket (save() skips this since it's not new)
    transaction._update_pocket_balance(+1)

    # Penalise any pattern rule that auto-assigned this wrongly
    _penalise_pattern(request.user, transaction)

    return Response(TransactionSerializer(transaction).data)


# ---------------------------------------------------------------------------
# Pattern suggestion
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def suggest(request):
    """
    POST /api/suggest/
    Body: { "amount": 4500, "direction": "credit", "source_bank": "HBL" }

    Returns the best matching pocket and a confidence score.
    The app uses the 'action' field to decide what to do:
      'auto'       → assign silently, fire notification
      'suggestion' → pre-select in UI, ask user to confirm
      'none'       → show all pockets, let user pick
    """
    serializer = SuggestRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    amount      = serializer.validated_data['amount']
    direction   = serializer.validated_data['direction']
    source_bank = serializer.validated_data['source_bank']

    rule = _find_best_rule(request.user, amount, direction, source_bank)

    if rule is None or rule.confidence < 0.5:
        response_data = {
            'suggested_pocket_id':   None,
            'suggested_pocket_name': None,
            'confidence':            0.0,
            'action':                'none',
        }
    else:
        action = 'auto' if rule.confidence >= 0.85 else 'suggestion'
        response_data = {
            'suggested_pocket_id':   rule.suggested_pocket.id,
            'suggested_pocket_name': rule.suggested_pocket.name,
            'confidence':            round(rule.confidence, 4),
            'action':                action,
        }

    return Response(SuggestResponseSerializer(response_data).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_suggestion(request):
    """
    POST /api/suggest/confirm/
    Body: { "transaction_id": "<uuid>", "confirmed": true }

    Called after a transaction is logged to update the pattern score.
    - confirmed=true  → user kept the suggestion → match_count++ confirm_count++
    - confirmed=false → user changed it         → match_count++ only
    """
    serializer = ConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    transaction = get_object_or_404(
        Transaction, pk=serializer.validated_data['transaction_id'],
        pocket__user=request.user,
    )
    confirmed = serializer.validated_data['confirmed']

    _update_pattern(request.user, transaction, confirmed)

    return Response({'status': 'ok'})


# ---------------------------------------------------------------------------
# Pattern engine helpers (private)
# ---------------------------------------------------------------------------

def _find_best_rule(user, amount, direction, source_bank):
    """
    Find the highest-confidence PatternRule that matches this transaction.
    Matching criteria (in order of specificity):
      1. bank + direction + amount in range  (most specific)
      2. direction + amount in range         (no bank filter)
    Returns the best rule, or None if nothing matches.
    """
    rules = PatternRule.objects.filter(
        user=user,
        direction=direction,
        amount_min__lte=amount,
        amount_max__gte=amount,
    )

    # Prefer a rule that also matches the bank
    if source_bank:
        bank_match = rules.filter(source_bank=source_bank).first()
        if bank_match:
            return bank_match

    # Fall back to a bank-agnostic rule
    return rules.filter(source_bank='').first()


def _update_pattern(user, transaction, confirmed):
    """
    After a transaction is logged, find or create a PatternRule for it
    and update the match/confirm counts.
    """
    # Round amount to a broad range so small variations still match
    amount = transaction.amount
    bucket_min, bucket_max = _amount_bucket(amount)

    rule, created = PatternRule.objects.get_or_create(
        user=user,
        suggested_pocket=transaction.pocket,
        direction=transaction.direction,
        source_bank=transaction.source_bank,
        amount_min=bucket_min,
        amount_max=bucket_max,
        defaults={'match_count': 0, 'confirm_count': 0, 'confidence': 0.0},
    )

    rule.match_count += 1
    if confirmed:
        rule.confirm_count += 1
    rule.last_seen = timezone.now()
    rule.save(update_fields=['match_count', 'confirm_count', 'last_seen'])
    rule.recalculate_confidence()


def _penalise_pattern(user, transaction):
    """
    When a user reassigns a transaction, find the rule that caused
    the wrong auto-assignment and reduce its confidence by not
    incrementing confirm_count (match already counted, so ratio drops).
    We do this by bumping match_count only.
    """
    amount = transaction.amount
    bucket_min, bucket_max = _amount_bucket(amount)

    PatternRule.objects.filter(
        user=user,
        direction=transaction.direction,
        amount_min=bucket_min,
        amount_max=bucket_max,
    ).update(match_count=models.F('match_count') + 1)

    # Recalculate confidence for affected rules
    for rule in PatternRule.objects.filter(
        user=user,
        direction=transaction.direction,
        amount_min=bucket_min,
        amount_max=bucket_max,
    ):
        rule.recalculate_confidence()


def _amount_bucket(amount):
    """
    Group amounts into broad ranges so the pattern engine
    doesn't create a separate rule for every unique amount.

    Buckets:
      1       – 1,000
      1,001   – 5,000
      5,001   – 15,000
      15,001  – 50,000
      50,001  – 150,000
      150,001 – ∞
    """
    buckets = [
        (1,       1_000),
        (1_001,   5_000),
        (5_001,   15_000),
        (15_001,  50_000),
        (50_001,  150_000),
        (150_001, 999_999_999),
    ]
    for low, high in buckets:
        if low <= amount <= high:
            return low, high
    return 1, 999_999_999
