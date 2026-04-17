from django.test import TestCase
from django.contrib.auth import get_user_model
from core.utils import process_transaction, InsufficientFunds
from core.models import UserProfile, CoinTransaction, Notification, Document
from unittest.mock import patch

User = get_user_model()


class EconomyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        # profile should be auto-created by signal
        self.profile = self.user.profile

    def test_process_transaction_credit_updates_balances(self):
        # Ensure initial balances are zero
        self.assertEqual(self.profile.current_balance, 0)
        self.assertEqual(self.profile.lifetime_coins, 0)

        tx = process_transaction(self.user, 10, tx_type='signup', description='Welcome bonus')

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.current_balance, 10)
        self.assertEqual(self.profile.lifetime_coins, 10)

        # Verify ledger entry created
        self.assertTrue(CoinTransaction.objects.filter(pk=tx.pk).exists())
        # Verify notification created
        self.assertTrue(Notification.objects.filter(user=self.user, title__icontains='10').exists())

    def test_prevention_of_negative_balance_when_spending(self):
        # Give user some coins
        self.profile.current_balance = 5
        self.profile.save()

        with self.assertRaises(InsufficientFunds):
            process_transaction(self.user, -10, tx_type='spend', description='Buy premium')

        # Balance should remain unchanged
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.current_balance, 5)
        # No ledger entry should be created
        self.assertFalse(CoinTransaction.objects.filter(transaction_type='spend').exists())

    def test_notification_and_cointransaction_created(self):
        initial_tx_count = CoinTransaction.objects.count()
        initial_notif_count = Notification.objects.count()

        process_transaction(self.user, 20, tx_type='quality_bonus', description='Quality award')

        self.assertEqual(CoinTransaction.objects.count(), initial_tx_count + 1)
        self.assertEqual(Notification.objects.count(), initial_notif_count + 1)

    def test_atomic_rollback_when_notification_creation_fails(self):
        # When Notification.objects.create raises, the whole operation should rollback
        initial_balance = self.profile.current_balance
        initial_lifetime = self.profile.lifetime_coins
        initial_tx_count = CoinTransaction.objects.count()

        with patch('core.models.Notification.objects.create') as mock_create:
            mock_create.side_effect = Exception('Notification system failure')
            with self.assertRaises(Exception):
                process_transaction(self.user, 15, tx_type='ai_summary', description='AI summary reward')

        # Ensure balances unchanged and no transaction persisted
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.current_balance, initial_balance)
        self.assertEqual(self.profile.lifetime_coins, initial_lifetime)
        self.assertEqual(CoinTransaction.objects.count(), initial_tx_count)
