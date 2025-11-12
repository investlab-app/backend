from celery import shared_task

from modules.investors.services import InvestorValueHistoryService


@shared_task
def save_accounts_value_snapshot():
    service = InvestorValueHistoryService()
    result = service.save_for_all_investors()
    return result
