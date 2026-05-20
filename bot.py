import asyncio

from flask import Flask
from threading import Thread
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from aiogram.filters import CommandStart
from aiogram.types import Message

from aiogram.fsm.context import FSMContext

from config import (
    BOT_TOKEN,
    ADMIN_ID,
    PHONE_NUMBER,
    BRANCH_ADDRESS,
    COURIERS
)

from keyboards import (
    main_keyboard,
    admin_keyboard,
    location_keyboard,
    phone_keyboard,
    courier_keyboard
)

from states import (
    OrderState,
    QuestionState
)

from data import (
    user_orders,
    user_questions
)

from database import (
    db,
    cursor
)

# =========================
# BOT
# =========================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

# =========================
# START
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message):

    # =========================
    # ADMIN
    # =========================

    if message.from_user.id == ADMIN_ID:

        await message.answer(
            "👨‍💼 Admin panel",
            reply_markup=admin_keyboard
        )

        return

    # =========================
    # KURYER
    # =========================

    if message.from_user.id in COURIERS.values():

        await message.answer(
            "🛵 Kuryer panel",
            reply_markup=courier_keyboard
        )

        return
    
    # =========================
    # MIJOZ
    # =========================

    text = (
    f"👋 Assalomu alaykum, {message.from_user.full_name}!\n\n"

    f"🛵 <b>Dastyor Delivery</b> xizmatiga xush kelibsiz.\n\n"

    f"📦 Biz sizga kerakli mahsulotlarni tez va qulay yetkazib beramiz.\n\n"

    f"✅ Mahsulot buyurtma berishingiz mumkin\n"
    f"✅ Operatorga savol yuborishingiz mumkin\n"
    f"✅ Lokatsiya yuborishingiz mumkin\n\n"

    f"⏰ Ish vaqti: 07:00 — 19:00\n"
    f"📍 Hudud: Buloqboshi tumani\n\n"

    f"Kerakli bo'limni tanlang 👇"
    )

    await message.answer(
        text,
        reply_markup=main_keyboard
    )

# =========================
# BUYURTMA BERISH
# =========================

@dp.message(F.text == "🛒 Buyurtma berish")
async def order_start(message: Message, state: FSMContext):

    await state.set_state(OrderState.waiting_for_order)

    await message.answer(
        "🛒 Kerakli mahsulotlarni yozib yuboring.\n\n"
        "Masalan:\n"
        "- 2 ta cola\n"
        "- 1 kg olma\n"
        "- 3 ta non"
    )

# =========================
# BUYURTMA MATNI
# =========================

@dp.message(OrderState.waiting_for_order)
async def order_text(message: Message, state: FSMContext):

    user_orders[message.from_user.id] = {
        "name": message.from_user.full_name,
        "username": message.from_user.username,
        "order": message.text
    }

    await state.set_state(OrderState.waiting_for_phone)

    await message.answer(
        "📞 Telefon raqamingizni yuboring.",
        reply_markup=phone_keyboard
    )

# =========================
# TELEFON
# =========================

@dp.message(OrderState.waiting_for_phone, F.contact)
async def get_phone(message: Message, state: FSMContext):

    user_orders[message.from_user.id]["phone"] = (
        message.contact.phone_number
    )

    await state.set_state(OrderState.waiting_for_location)

    await message.answer(
        "📍 Endi lokatsiyangizni yuboring.",
        reply_markup=location_keyboard
    )

# =========================
# LOKATSIYA
# =========================

@dp.message(OrderState.waiting_for_location, F.location)
async def get_location(message: Message, state: FSMContext):

    user_id = message.from_user.id

    data = user_orders[user_id]

    username = data["username"]

    if username:
        username_text = f"@{username}"
    else:
        username_text = "Username yo'q"

    # =========================
    # DATABASE
    # =========================

    cursor.execute(
        """
        INSERT INTO orders (
            user_id,
            full_name,
            username,
            phone,
            order_text,
            latitude,
            longitude,
            status
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            data["name"],
            username_text,
            data["phone"],
            data["order"],
            str(message.location.latitude),
            str(message.location.longitude),
            "🆕 Yangi",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    db.commit()

    order_id = cursor.lastrowid

    # =========================
    # ADMIN XABARI
    # =========================

    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")

    admin_text = (
        f"📦 <b>YANGI BUYURTMA</b>\n\n"
        f"🕒 Vaqt: {current_time}\n\n"
        f"🆔 Buyurtma ID: #{order_id}\n\n"
        f"👤 Mijoz: {data['name']}\n"
        f"📱 Username: {username_text}\n"
        f"📞 Telefon: {data['phone']}\n\n"
        f"🛒 Buyurtma:\n"
        f"{data['order']}\n\n"
        f"📌 Status: 🆕 Yangi"
    )

    # =========================
    # LOCATION
    # =========================

    location = message.location

    location_link = (
        f"https://maps.google.com/?q="
        f"{location.latitude},"
        f"{location.longitude}"
    )

    # ADMINGA TEXT
    await bot.send_message(
        ADMIN_ID,
        admin_text + f"\n\n📍 Lokatsiya:\n{location_link}"
    )

    # ADMINGA LIVE LOCATION
    await bot.send_location(
        ADMIN_ID,
        latitude=location.latitude,
        longitude=location.longitude
    )

    await message.answer(
        "✅ Buyurtmangiz qabul qilindi!\n\n"
        "🚚 Operatorlar tez orada siz bilan bog'lanadi.",
        reply_markup=main_keyboard
    )

    await state.clear()

# =========================
# SAVOL YO'LLASH
# =========================

@dp.message(F.text == "❓ Savol yo'llash")
async def question_start(message: Message, state: FSMContext):

    await state.set_state(
        QuestionState.waiting_for_question
    )

    await message.answer(
        "❓ Savolingizni yozib yuboring."
    )

# =========================
# SAVOLNI OLISH
# =========================
   
@dp.message(QuestionState.waiting_for_question)
async def get_question(message: Message, state: FSMContext):

    user_id = message.from_user.id

    username = message.from_user.username

    if username:
        username_text = f"@{username}"
    else:
        username_text = "Username yo'q"

    # =========================
    # DATABASE
    # =========================

    cursor.execute(
        """
        INSERT INTO questions (
            user_id,
            full_name,
            username,
            question
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            message.from_user.full_name,
            username_text,
            message.text
        )
    )

    db.commit()

    question_id = cursor.lastrowid
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    admin_text = (
        f"❓ <b>YANGI SAVOL</b>\n\n"
        f"🕒 Vaqt: {current_time}\n\n"
        f"🆔 Savol ID: #{question_id}\n\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
        f"📱 Username: {username_text}\n\n"
        f"💬 Savol:\n"
        f"{message.text}"
    )

    await bot.send_message(
        ADMIN_ID,
        admin_text
    )

    await message.answer(
        "✅ Savolingiz operatorga yuborildi.\n\n"
        "📞 Tez orada javob beramiz.",
        reply_markup=main_keyboard
    )

    await state.clear()

# =========================
# ALOQA
# =========================

@dp.message(F.text == "📞 Aloqa")
async def contact_handler(message: Message):

    text = (
        f"📞 Aloqa uchun:\n\n"
        f"{PHONE_NUMBER}"
    )

    await message.answer(text)

# =========================
# FILIAL
# =========================

@dp.message(F.text == "📍 Filial")
async def branch_handler(message: Message):

    text = (
        f"📍 Filial manzili:\n\n"
        f"{BRANCH_ADDRESS}"
    )

    await message.answer(text)

# =========================
# ADMIN BUYURTMALAR
# =========================

# =========================
# YANGI BUYURTMALAR
# =========================

# =========================
# YANGI BUYURTMALAR
# =========================

# =========================
# YANGI BUYURTMALAR
# =========================

@dp.message(F.text == "🆕 Yangi buyurtmalar")
async def new_orders(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("""
    SELECT id, full_name, phone, order_text, status
    FROM orders
    WHERE status IS NULL
    OR status = ''
    OR status = '🆕 Yangi'
    ORDER BY id DESC
    """)

    orders = cursor.fetchall()

    if not orders:

        await message.answer(
            "📭 Yangi buyurtmalar yo'q."
        )

        return

    text = "🆕 <b>YANGI BUYURTMALAR</b>\n\n"

    for order in orders:

        status = order[4]

        if not status:
            status = "🆕 Yangi"

        text += (
            f"🆔 #{order[0]}\n"
            f"👤 {order[1]}\n"
            f"📞 {order[2]}\n"
            f"🛒 {order[3]}\n"
            f"📌 {status}\n\n"
        )

    await message.answer(text)

# =========================
# JARAYONDAGI BUYURTMALAR
# =========================

@dp.message(F.text == "📦 Jarayondagi buyurtmalar")
async def processing_orders(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("""
    SELECT id, full_name, phone, order_text, status
    FROM orders
    WHERE status = '📦 Tayyorlanmoqda'
    OR status = '🛵 Kuryerda'
    OR status = '🛵 Kuryerga berildi'
    ORDER BY id DESC
    """)

    orders = cursor.fetchall()

    if not orders:

        await message.answer(
            "📭 Jarayondagi buyurtmalar yo'q."
        )

        return

    text = "📦 <b>JARAYONDAGI BUYURTMALAR</b>\n\n"

    for order in orders:

        text += (
            f"🆔 #{order[0]}\n"
            f"👤 {order[1]}\n"
            f"📞 {order[2]}\n"
            f"🛒 {order[3]}\n"
            f"📌 {order[4]}\n\n"
        )

    await message.answer(text)

# =========================
# TUGAGAN BUYURTMALAR
# =========================

@dp.message(F.text == "✅ Tugagan buyurtmalar")
async def completed_orders(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("""
    SELECT id, full_name, phone, order_text, status
    FROM orders
    WHERE status = '✅ Yetkazildi'
    OR status = '❌ Bekor qilindi'
    ORDER BY id DESC
    """)

    orders = cursor.fetchall()

    if not orders:

        await message.answer(
            "📭 Tugagan buyurtmalar yo'q."
        )

        return

    text = "✅ <b>TUGAGAN BUYURTMALAR</b>\n\n"

    for order in orders:

        text += (
            f"🆔 #{order[0]}\n"
            f"👤 {order[1]}\n"
            f"📞 {order[2]}\n"
            f"🛒 {order[3]}\n"
            f"📌 {order[4]}\n\n"
        )

    await message.answer(text)

# =========================
# ADMIN SAVOLLAR
# =========================

@dp.message(F.text == "❓ Savollar")
async def admin_questions(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("""
    SELECT id, full_name, question
    FROM questions
    ORDER BY id DESC
    """)

    questions = cursor.fetchall()

    if not questions:
        await message.answer("📭 Savollar yo'q.")
        return

    text = "❓ <b>BARCHA SAVOLLAR</b>\n\n"

    for question in questions:

        text += (
            f"🆔 #{question[0]}\n"
            f"👤 {question[1]}\n"
            f"💬 {question[2]}\n\n"
        )

    await message.answer(text)

# =========================
# ADMIN REPLY
# =========================

@dp.message(F.text.startswith("/reply"))
async def admin_reply(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        parts = message.text.split(maxsplit=2)

        question_id = int(parts[1])

        reply_text = parts[2]

    except:
        await message.answer(
            "❌ Format:\n/reply ID xabar"
        )
        return

    # =========================
    # QUESTION TOPISH
    # =========================

    cursor.execute(
        """
        SELECT user_id
        FROM questions
        WHERE id = ?
        """,
        (question_id,)
    )

    result = cursor.fetchone()

    if not result:
        await message.answer(
            "❌ Savol topilmadi."
        )
        return

    user_id = result[0]

    # =========================
    # USERGA YUBORISH
    # =========================

    await bot.send_message(
        user_id,
        f"💬 Operator javobi:\n\n{reply_text}"
    )

    await message.answer(
        "✅ Javob yuborildi."
    )

# =========================
# ORDER STATUS
# =========================

@dp.message(F.text.startswith("/status"))
async def change_status(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        parts = message.text.split(maxsplit=2)

        order_id = int(parts[1])

        new_status = parts[2]

    except:
        await message.answer(
            "❌ Format:\n/status ID status"
        )
        return

    # =========================
    # ORDERNI TOPISH
    # =========================

    cursor.execute(
        """
        SELECT user_id
        FROM orders
        WHERE id = ?
        """,
        (order_id,)
    )

    result = cursor.fetchone()

    if not result:
        await message.answer(
            "❌ Buyurtma topilmadi."
        )
        return

    user_id = result[0]

    # =========================
    # STATUS UPDATE
    # =========================

    cursor.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        (new_status, order_id)
    )

    db.commit()

    # =========================
    # MIJOZGA YUBORISH
    # =========================

    await bot.send_message(
        user_id,
        f"📦 Buyurtma holati yangilandi:\n\n{new_status}"
    )

    await message.answer(
        "✅ Status yangilandi."
    )

# =========================
# KURYERGA BIRIKTIRISH
# =========================

@dp.message(F.text.startswith("/assign"))
async def assign_courier(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        parts = message.text.split(maxsplit=2)

        order_id = int(parts[1])

        courier_name = parts[2]

    except:
        await message.answer(
            "❌ Format:\n/assign ID courier"
        )
        return

    # =========================
    # KURYER TEKSHIRISH
    # =========================

    if courier_name not in COURIERS:

        await message.answer(
            "❌ Kuryer topilmadi."
        )

        return

    courier_id = COURIERS[courier_name]

    # =========================
    # ORDER TOPISH
    # =========================

    cursor.execute(
        """
        SELECT full_name, phone, order_text
        FROM orders
        WHERE id = ?
        """,
        (order_id,)
    )

    order = cursor.fetchone()

    if not order:

        await message.answer(
            "❌ Buyurtma topilmadi."
        )

        return

    # =========================
    # DATABASE UPDATE
    # =========================

    cursor.execute(
        """
        UPDATE orders
        SET courier = ?,
            status = ?
        WHERE id = ?
        """,
        (
            courier_name,
            "🛵 Kuryerga berildi",
            order_id
        )
    )

    db.commit()

    # =========================
    # KURYERGA YUBORISH
    # =========================

    courier_text = (
        f"🛵 <b>YANGI BUYURTMA</b>\n\n"

        f"🆔 Buyurtma: #{order_id}\n\n"

        f"👤 Mijoz: {order[0]}\n"
        f"📞 Telefon: {order[1]}\n\n"

        f"🛒 Buyurtma:\n"
        f"{order[2]}"
    )

    await bot.send_message(
        courier_id,
        courier_text
    )

    await message.answer(
        "✅ Buyurtma kuryerga biriktirildi."
    )

# =========================
# KURYER BUYURTMALARI
# =========================

@dp.message(F.text == "📦 Mening buyurtmalarim")
async def courier_orders(message: Message):

    courier_name = None

    for name, user_id in COURIERS.items():

        if user_id == message.from_user.id:

            courier_name = name

            break

    if not courier_name:
        return

    # =========================
    # ORDERLAR
    # =========================

    cursor.execute(
        """
        SELECT id, full_name, phone, order_text, status
        FROM orders
        WHERE courier = ?
        AND status != '✅ Yetkazildi'
        ORDER BY id DESC
        """,
        (courier_name,)
    )

    orders = cursor.fetchall()

    if not orders:

        await message.answer(
            "📭 Sizda aktiv buyurtmalar yo'q."
        )

        return

    text = "🛵 <b>MENING BUYURTMALARIM</b>\n\n"

    for order in orders:

        text += (
            f"🆔 #{order[0]}\n"
            f"👤 {order[1]}\n"
            f"📞 {order[2]}\n"
            f"🛒 {order[3]}\n"
            f"📌 {order[4]}\n\n"
        )

    await message.answer(text)

# =========================
# KURYER DELIVERED
# =========================

@dp.message(F.text.startswith("/delivered"))
async def courier_delivered(message: Message):

    courier_name = None

    for name, user_id in COURIERS.items():

        if user_id == message.from_user.id:

            courier_name = name

            break

    if not courier_name:
        return

    try:

        parts = message.text.split()

        order_id = int(parts[1])

    except:

        await message.answer(
            "❌ Format:\n/delivered ID"
        )

        return

    # =========================
    # ORDERNI TEKSHIRISH
    # =========================

    cursor.execute(
        """
        SELECT user_id
        FROM orders
        WHERE id = ?
        AND courier = ?
        """,
        (order_id, courier_name)
    )

    order = cursor.fetchone()

    if not order:

        await message.answer(
            "❌ Buyurtma topilmadi."
        )

        return

    user_id = order[0]

    # =========================
    # STATUS UPDATE
    # =========================

    cursor.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        (
            "✅ Yetkazildi",
            order_id
        )
    )

    db.commit()

    # =========================
    # USER
    # =========================

    await bot.send_message(
        user_id,
        "✅ Buyurtmangiz yetkazib berildi.\n\n"
        "Dastyor xizmatidan foydalanganingiz uchun rahmat ❤️"
    )

    await message.answer(
        "✅ Buyurtma yopildi."
    )

# =========================
# STATISTIKA
# =========================

@dp.message(F.text == "📊 Statistika")
async def statistics(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.now().strftime("%d.%m.%Y")

    # =========================
    # BUGUNGI BUYURTMALAR
    # =========================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE created_at LIKE ?
        """,
        (today + "%",)
    )

    total_today = cursor.fetchone()[0]

    # =========================
    # YANGI
    # =========================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status = ?
        AND created_at LIKE ?
        """,
        ("🆕 Yangi", today + "%")
    )

    new_orders = cursor.fetchone()[0]

    # =========================
    # JARAYONDA
    # =========================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status = ?
        AND created_at LIKE ?
        """,
        ("🛵 Jarayonda", today + "%")
    )

    in_progress = cursor.fetchone()[0]

    # =========================
    # YETKAZILDI
    # =========================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status = ?
        AND created_at LIKE ?
        """,
        ("✅ Yetkazildi", today + "%")
    )

    delivered = cursor.fetchone()[0]

    # =========================
    # BEKOR QILINGAN
    # =========================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status = ?
        AND created_at LIKE ?
        """,
        ("❌ Bekor qilindi", today + "%")
    )

    cancelled = cursor.fetchone()[0]

    # =========================
    # TEXT
    # =========================

    stats_text = (
        f"📊 <b>BUGUNGI STATISTIKA</b>\n\n"
        f"📅 Sana: {current_date}\n\n"

        f"📦 Jami buyurtmalar: {total_today}\n\n"

        f"🆕 Yangi: {new_orders}\n"
        f"🛵 Jarayonda: {in_progress}\n"
        f"✅ Yetkazildi: {delivered}\n"
        f"❌ Bekor qilingan: {cancelled}"
    )

    await message.answer(stats_text)

# =========================
# ORDER SEARCH
# =========================

@dp.message(F.text.startswith("/find"))
async def find_order(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        query = message.text.replace(
            "/find",
            ""
        ).strip()

    except:

        await message.answer(
            "❌ Format:\n/find ID yoki ism"
        )

        return

    # =========================
    # ID BO'YICHA
    # =========================

    if query.isdigit():

        cursor.execute(
            """
            SELECT id,
                   full_name,
                   phone,
                   order_text,
                   status,
                   courier
            FROM orders
            WHERE id = ?
            """,
            (int(query),)
        )

    else:

        # =========================
        # ISM BO'YICHA
        # =========================

        cursor.execute(
            """
            SELECT id,
                   full_name,
                   phone,
                   order_text,
                   status,
                   courier
            FROM orders
            WHERE full_name LIKE ?
            ORDER BY id DESC
            """,
            (f"%{query}%",)
        )

    orders = cursor.fetchall()

    if not orders:

        await message.answer(
            "📭 Hech narsa topilmadi."
        )

        return

    text = "🔎 <b>QIDIRUV NATIJASI</b>\n\n"

    for order in orders:

        status = order[4]

        if not status:
            status = "🆕 Yangi"

        courier = order[5]

        if not courier:
            courier = "Biriktirilmagan"

        text += (
            f"🆔 #{order[0]}\n"
            f"👤 {order[1]}\n"
            f"📞 {order[2]}\n"
            f"🛒 {order[3]}\n"
            f"📌 {status}\n"
            f"🛵 {courier}\n\n"
        )

    await message.answer(text)

# =========================
# FLASK KEEP ALIVE
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Dastyor bot ishlayapti!"


def run_web():
    app.run(
        host="0.0.0.0",
        port=10000
    )

# =========================
# ISHGA TUSHIRISH
# =========================

async def main():

    print("🚀 Dastyor bot ishga tushdi...")

    Thread(target=run_web).start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

