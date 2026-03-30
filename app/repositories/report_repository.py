from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.report_message import ReportMessage
from app.models.report_ticket import ReportTicket


class ReportRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_tickets(self):
        statement = select(ReportTicket).options(
            selectinload(ReportTicket.messages).selectinload(ReportMessage.admin),
            selectinload(ReportTicket.assigned_admin),
        ).order_by(ReportTicket.updated_at.desc())
        return list(self.session.scalars(statement).unique())

    def get_ticket(self, ticket_id: int):
        statement = select(ReportTicket).where(ReportTicket.id == ticket_id).options(
            selectinload(ReportTicket.messages).selectinload(ReportMessage.admin),
            selectinload(ReportTicket.assigned_admin),
        )
        return self.session.scalar(statement)

    def get_open_ticket_by_tg_user_id(self, tg_user_id: int):
        statement = select(ReportTicket).where(
            ReportTicket.source_platform == 'telegram',
            ReportTicket.tg_user_id == tg_user_id,
            ReportTicket.status.in_(['open', 'in_progress']),
        ).order_by(ReportTicket.id.desc())
        return self.session.scalar(statement)

    def get_open_ticket_by_vk_user_id(self, vk_user_id: int):
        statement = select(ReportTicket).where(
            ReportTicket.source_platform == 'vk',
            ReportTicket.vk_user_id == vk_user_id,
            ReportTicket.status.in_(['open', 'in_progress']),
        ).order_by(ReportTicket.id.desc())
        return self.session.scalar(statement)

    def create_ticket(self, **kwargs):
        entity = ReportTicket(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update_ticket(self, entity, **kwargs):
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.session.flush()
        return entity

    def create_message(self, **kwargs):
        entity = ReportMessage(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity
