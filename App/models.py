import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models import Sum


# ---------------------------------------------------------------------------
# Pocket
# ---------------------------------------------------------------------------

class PocketType(models.TextChoices):
    SALARY  = 'salary',  'Salary'
    SAVING  = 'saving',  'Saving'
    CUSTOM  = 'custom',  'Custom'


class Pocket(models.Model):
    """
    A named money container belonging to one user.
    Replaces the old Total / Salary / Saving / Others split.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pockets')
    name         = models.CharField(max_length=64)                  # e.g. "Salary", "Travel fund"
    pocket_type  = models.CharField(max_length=16, choices=PocketType.choices, default=PocketType.CUSTOM)
    balance      = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    budget_limit = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    is_archived  = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} ({self.user.username}) — Rs {self.balance:,}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('Bank:Pocket', args=[str(self.id)])

    # ------------------------------------------------------------------
    # Convenience: recalculate balance from transaction log at any time.
    # Useful if you ever suspect the balance field drifted.
    # ------------------------------------------------------------------
    def recalculate_balance(self):
        credits = self.transactions.filter(direction=Direction.CREDIT).aggregate(
            total=Sum('amount'))['total'] or 0
        debits  = self.transactions.filter(direction=Direction.DEBIT).aggregate(
            total=Sum('amount'))['total'] or 0
        self.balance = credits - debits
        self.save(update_fields=['balance'])
        return self.balance


# ---------------------------------------------------------------------------
# Transaction
# ---------------------------------------------------------------------------

class Direction(models.TextChoices):
    CREDIT = 'credit', 'Credit'
    DEBIT  = 'debit',  'Debit'


class AssignedBy(models.TextChoices):
    USER       = 'user',       'User'        # human picked the pocket
    SUGGESTION = 'suggestion', 'Suggestion'  # system suggested, user confirmed
    AUTO       = 'auto',       'Auto'        # system assigned silently


class Transaction(models.Model):
    """
    Every money movement — whether auto-detected from SMS or manually entered.
    This is the single source of truth for all financial history.
    """
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pocket           = models.ForeignKey(Pocket, on_delete=models.CASCADE, related_name='transactions')
    amount           = models.PositiveIntegerField()                 # always positive; direction tells the sign
    direction        = models.CharField(max_length=6,  choices=Direction.choices)
    source_bank      = models.CharField(max_length=32, blank=True)  # "HBL", "MCB", "UBL", etc.
    raw_sms          = models.TextField(blank=True)                  # original SMS body for re-parsing later
    assigned_by      = models.CharField(max_length=16, choices=AssignedBy.choices, default=AssignedBy.USER)
    confidence_score = models.FloatField(null=True, blank=True)      # score at time of auto/suggestion
    note             = models.CharField(max_length=128, blank=True)  # optional user note
    transacted_at    = models.DateTimeField()                        # when the bank says it happened
    created_at       = models.DateTimeField(auto_now_add=True)       # when we logged it

    class Meta:
        ordering = ['-transacted_at']

    def __str__(self):
        return f"{self.direction} Rs {self.amount:,} → {self.pocket.name} ({self.assigned_by})"

    # ------------------------------------------------------------------
    # Saving a transaction also updates the pocket balance atomically.
    # ------------------------------------------------------------------
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self._update_pocket_balance(+1)

    def delete(self, *args, **kwargs):
        self._update_pocket_balance(-1)
        super().delete(*args, **kwargs)

    def _update_pocket_balance(self, multiplier):
        """
        multiplier=+1  when adding a transaction
        multiplier=-1  when deleting / undoing one
        """
        delta = self.amount * multiplier
        if self.direction == Direction.CREDIT:
            self.pocket.balance = models.F('balance') + delta
        else:
            self.pocket.balance = models.F('balance') - delta
        self.pocket.save(update_fields=['balance'])


# ---------------------------------------------------------------------------
# PatternRule
# ---------------------------------------------------------------------------

class PatternRule(models.Model):
    """
    One learned pattern for a user.
    The engine creates rows here and updates match_count + confidence
    every time a transaction confirms the pattern.

    Example row:
        source_bank="HBL", direction="credit",
        amount_min=1, amount_max=5000,
        suggested_pocket=<Salary pocket>,
        match_count=12, confidence=0.91
    """
    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user               = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pattern_rules')
    suggested_pocket   = models.ForeignKey(Pocket, on_delete=models.CASCADE, related_name='pattern_rules')
    source_bank        = models.CharField(max_length=32, blank=True)
    direction          = models.CharField(max_length=6, choices=Direction.choices)
    amount_min         = models.PositiveIntegerField(default=0)
    amount_max         = models.PositiveIntegerField(default=999_999_999)
    match_count        = models.PositiveIntegerField(default=0)
    confirm_count      = models.PositiveIntegerField(default=0) # how many times user confirmed (not undid)
    confidence         = models.FloatField(default=0.0)         # confirm_count / match_count
    last_seen          = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-confidence', '-match_count']

    def __str__(self):
        return (
            f"{self.source_bank} {self.direction} "
            f"Rs {self.amount_min:,}–{self.amount_max:,} "
            f"→ {self.suggested_pocket.name} "
            f"(conf: {self.confidence:.0%})"
        )

    def recalculate_confidence(self):
        if self.match_count == 0:
            self.confidence = 0.0
        else:
            self.confidence = self.confirm_count / self.match_count
        self.save(update_fields=['confidence'])


# ---------------------------------------------------------------------------
# DeviceToken
# ---------------------------------------------------------------------------

class Platform(models.TextChoices):
    ANDROID = 'android', 'Android'
    IOS     = 'ios',     'iOS'


class DeviceToken(models.Model):
    """
    Stores push notification tokens per device.
    Android uses local notifications (no token needed for basic use)
    but storing it here keeps the table consistent for both platforms.
    iOS requires this for APNs.
    """
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    token         = models.TextField(unique=True)
    platform      = models.CharField(max_length=8, choices=Platform.choices)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.platform} token for {self.user.username}"
