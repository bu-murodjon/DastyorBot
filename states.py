from aiogram.fsm.state import State, StatesGroup


class OrderState(StatesGroup):
    waiting_for_order = State()
    waiting_for_phone = State()
    waiting_for_location = State()


class QuestionState(StatesGroup):
    waiting_for_question = State()