from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

# =========================
# MIJOZ MENU
# =========================

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🛒 Buyurtma berish")
        ],
        [
            KeyboardButton(text="❓ Savol yo'llash")
        ],
        [
            KeyboardButton(text="📞 Aloqa"),
            KeyboardButton(text="📍 Filial")
        ]
    ],
    resize_keyboard=True
)

# =========================
# ADMIN MENU
# =========================

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🆕 Yangi buyurtmalar")
        ],
        [
            KeyboardButton(text="📦 Jarayondagi buyurtmalar")
        ],
        [
            KeyboardButton(text="✅ Tugagan buyurtmalar")
        ],
        [
            KeyboardButton(text="❓ Savollar")
        ],
        [
            KeyboardButton(text="📊 Statistika")
        ]
    ],
    resize_keyboard=True
)

# =========================
# ORQAGA
# =========================

back_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="⬅️ Orqaga")
        ]
    ],
    resize_keyboard=True
)

# =========================
# TELEFON
# =========================

phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📞 Telefon yuborish",
                request_contact=True
            )
        ],
        [
            KeyboardButton(text="⬅️ Orqaga")
        ]
    ],
    resize_keyboard=True
)

# =========================
# LOKATSIYA
# =========================

location_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📍 Lokatsiya yuborish",
                request_location=True
            )
        ],
        [
            KeyboardButton(text="⬅️ Orqaga")
        ]
    ],
    resize_keyboard=True
)

# =========================
# KURYER MENU
# =========================

courier_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📦 Mening buyurtmalarim"
            )
        ]
    ],
    resize_keyboard=True
)