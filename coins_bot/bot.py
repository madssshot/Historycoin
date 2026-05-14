import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import database as db

TOKEN = "7309999677:AAH81sxLgRhIBHDx6eJaGgvxahdR34A86OU"
ADMIN_ID = 785061652
MINI_APP_URL = "https://historycoin-frontend.vercel.app"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

PERIODS = [
    ("1917-1924", "🔥 1917–1924 — Революция и Гражданская война"),
    ("1924-1947", "⚒️ 1924–1947 — НЭП и довоенный СССР"),
    ("1947-1961", "🏗️ 1947–1961 — Послевоенные реформы"),
    ("1961-1991", "☭ 1961–1991 — Поздний СССР"),
    ("1991-1998", "📉 1991–1998 — Гиперинфляция"),
    ("1998-2024", "🇷🇺 1998–2024 — Современный рубль"),
]

PERIOD_TEXTS = {
    "1917-1924": (
        "В годы Революции и Гражданской войны денежная система страны фактически распалась.\n\n"
        "Одновременно ходили царские рубли, «керенки», совзнаки и местные выпуски. "
        "Инфляция достигала сотен процентов в месяц — к 1921 году цены выросли "
        "в десятки тысяч раз по сравнению с 1914-м.\n\n"
        "В 1922–1924 годах прошла реформа: введён золотой червонец, "
        "совзнаки изъяты, рубль укрепился. "
        "Один новый рубль обменивался на 50 000 старых совзнаков образца 1923 года.\n\n"
        "🔗 Каталог монет и банкнот: https://www.russian-money.ru/"
    ),
    "1924-1947": (
        "После реформы рубль стал твёрдой валютой. В 1924 году выпущены "
        "первые советские монеты из меди, серебра и золота.\n\n"
        "В 1937 году на купюрах впервые появился портрет Ленина. "
        "Во время Второй мировой войны из-за военных расходов денежная масса выросла, "
        "но открытой гиперинфляции удалось избежать благодаря карточной системе.\n\n"
        "🔗 Каталог монет и банкнот: https://www.russian-money.ru/"
    ),
    "1947-1961": (
        "В 1947 году прошла денежная реформа: старые банкноты обменивались на новые "
        "в соотношении 10:1. Одновременно отменили карточки — впервые после 1941 года "
        "советские граждане могли свободно покупать продукты.\n\n"
        "Монеты 1947 года отличались детальной гравюрой и пышным оформлением. "
        "В 1961 году была проведена деноминация 10:1 — появились «хрущёвские фантики».\n\n"
        "🔗 Каталог монет и банкнот: https://www.russian-money.ru/"
    ),
    "1961-1991": (
        "Монеты и купюры образца 1961 года оставались в обращении почти 30 лет. "
        "Их прозвали «хрущёвскими фантиками» за небольшой размер.\n\n"
        "В народе прижились названия: трояк, пятёрка, червонец, четвертак, полтинник, сотня. "
        "В 1991 году, при нарастающем кризисе, вышли купюры в 200, 500 и 1000 рублей — "
        "«павловская реформа». Это были последние деньги СССР.\n\n"
        "🔗 Каталог монет и банкнот: https://www.russian-money.ru/"
    ),
    "1991-1998": (
        "После распада СССР в 1992 году Россия выпустила собственные монеты "
        "номиналом от 1 до 100 рублей.\n\n"
        "Однако из-за гиперинфляции их покупательная способность быстро падала. "
        "Уже к 1994 году чеканка монет практически прекратилась, а расчёты "
        "перешли на банкноты — сначала тысячные, затем миллионные номиналы.\n\n"
        "После деноминации 1998 года (1000:1) эти монеты были выведены из обращения.\n\n"
        "🔗 Каталог монет и банкнот: https://www.russian-money.ru/"
    ),
    "1998-2024": (
        "Деноминация 1998 года вернула привычный масштаб цен. "
        "На банкнотах появились архитектурные виды городов России: "
        "Красноярск, Владивосток, Хабаровск, Ярославль, Москва, Санкт-Петербург.\n\n"
        "В 2000-е годы вышли монеты из биметалла, затем стальные с никелевым покрытием. "
        "В 2023 году появилась цифровой рубль как третья форма национальной валюты.\n\n"
        "🔗 Каталог монет и банкнот: https://www.russian-money.ru/"
    ),
}


# --- FSM ---
class AuctionForm(StatesGroup):
    title = State()
    description = State()
    period = State()
    year = State()
    material = State()
    price = State()
    photo = State()


def main_keyboard(is_admin=False):
    builder = ReplyKeyboardBuilder()
    builder.button(
        text="🪙 Открыть каталог",
        web_app=types.WebAppInfo(url=MINI_APP_URL)
    )
    builder.button(text="📜 Исторические периоды")
    builder.button(text="🔨 Аукцион")
    builder.button(text="👤 Мой профиль")
    if is_admin:
        builder.button(text="⚙️ Админ-панель")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    u = message.from_user
    db.upsert_user(u.id, u.username or "", u.full_name or "")
    is_admin = (u.id == ADMIN_ID)
    await message.answer(
        f"Привет, {u.full_name}! 🪙\n\n"
        "Добро пожаловать в гид по истории российских денег.\n\n"
        "Здесь ты найдёшь:\n"
        "• Историю монет и банкнот с 1917 по 2024 год\n"
        "• Что можно было купить на эти деньги\n"
        "• Аукцион коллекционных монет\n"
        "• Каталог с фотографиями\n\n"
        "🔗 Удобный поиск монет: https://www.russian-money.ru/",
        reply_markup=main_keyboard(is_admin)
    )


@dp.message(F.text == "📜 Исторические периоды")
async def show_periods(message: types.Message):
    builder = InlineKeyboardBuilder()
    for key, title in PERIODS:
        builder.button(text=title, callback_data=f"period_{key}")
    builder.adjust(1)
    await message.answer("Выберите период:", reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("period_"))
async def period_info(callback: types.CallbackQuery):
    key = callback.data[len("period_"):]
    title = next((t for k, t in PERIODS if k == key), key)
    text = PERIOD_TEXTS.get(key, "Информация скоро появится.")
    await callback.message.answer(
        f"<b>{title}</b>\n\n{text}",
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    await callback.answer()


@dp.message(F.text == "👤 Мой профиль")
async def show_profile(message: types.Message):
    user = db.get_user(message.from_user.id)
    if not user:
        db.upsert_user(message.from_user.id, message.from_user.username or "", message.from_user.full_name or "")
        user = db.get_user(message.from_user.id)
    score = user["score"]
    rank = "🥉 Новичок"
    if score >= 50:
        rank = "🥈 Любитель"
    if score >= 150:
        rank = "🥇 Коллекционер"
    if score >= 300:
        rank = "💎 Эксперт"
    await message.answer(
        f"👤 <b>{user['full_name']}</b>\n"
        f"🏅 Ранг: {rank}\n"
        f"⭐ Очки знаний: {score}\n\n"
        "Открывай Mini App для полного профиля с коллекцией и викториной! 👆",
        parse_mode="HTML"
    )


# ======= АУКЦИОН =======

@dp.message(F.text == "🔨 Аукцион")
async def auction_menu(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Смотреть лоты", callback_data="auction_list")
    builder.button(text="➕ Выставить монету", callback_data="auction_add")
    builder.adjust(1)
    await message.answer(
        "🔨 <b>Аукцион коллекционных монет</b>\n\n"
        "Здесь любой желающий может выставить свою монету на продажу "
        "или найти интересный экземпляр для коллекции.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "auction_list")
async def auction_list(callback: types.CallbackQuery):
    lots = db.get_auction_lots()
    if not lots:
        await callback.message.answer("Пока нет активных лотов. Будьте первым! Нажмите «Выставить монету».")
        await callback.answer()
        return
    for lot in lots[:10]:
        text = (
            f"🪙 <b>{lot['title']}</b>\n"
            f"📅 {lot.get('year', '—')} | {lot.get('period', '—')}\n"
            f"🧱 Материал: {lot.get('material', '—')}\n"
            f"💰 Цена: {lot['price']}\n"
            f"📝 {lot.get('description', '')[:200]}\n"
            f"👤 Продавец: {lot['seller_name']}"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="📩 Написать продавцу", url=f"tg://user?id={lot['seller_tg_id']}")
        if callback.from_user.id == ADMIN_ID:
            builder.button(text="🗑 Удалить лот", callback_data=f"del_lot_{lot['id']}")
        builder.adjust(1)

        if lot.get("photo_path") and os.path.exists(lot["photo_path"]):
            try:
                photo = types.FSInputFile(lot["photo_path"])
                await callback.message.answer_photo(photo, caption=text, parse_mode="HTML", reply_markup=builder.as_markup())
            except Exception:
                await callback.message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
        else:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("del_lot_"))
async def delete_lot_cb(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    lot_id = int(callback.data.split("_")[2])
    db.delete_lot(lot_id)
    await callback.answer("Лот удалён ✅", show_alert=True)


@dp.callback_query(F.data == "auction_add")
async def auction_add_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "➕ <b>Добавление лота</b>\n\nВведите название монеты или банкноты (например: «1 рубль 1924»):",
        parse_mode="HTML"
    )
    await state.set_state(AuctionForm.title)
    await callback.answer()


@dp.message(AuctionForm.title)
async def auction_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📝 Краткое описание (состояние, особенности):")
    await state.set_state(AuctionForm.description)


@dp.message(AuctionForm.description)
async def auction_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    builder = InlineKeyboardBuilder()
    for key, title in PERIODS:
        builder.button(text=title, callback_data=f"set_period_{key}")
    builder.adjust(1)
    await message.answer("📜 Выберите период:", reply_markup=builder.as_markup())
    await state.set_state(AuctionForm.period)


@dp.callback_query(F.data.startswith("set_period_"), AuctionForm.period)
async def auction_period(callback: types.CallbackQuery, state: FSMContext):
    key = callback.data[len("set_period_"):]
    title = next((t for k, t in PERIODS if k == key), key)
    await state.update_data(period=title)
    await callback.message.answer("📅 Год выпуска (например: 1924):")
    await state.set_state(AuctionForm.year)
    await callback.answer()


@dp.message(AuctionForm.year)
async def auction_year(message: types.Message, state: FSMContext):
    await state.update_data(year=message.text)
    await message.answer("🧱 Материал (например: Серебро, Медь, Сталь, Биметалл):")
    await state.set_state(AuctionForm.material)


@dp.message(AuctionForm.material)
async def auction_material(message: types.Message, state: FSMContext):
    await state.update_data(material=message.text)
    await message.answer("💰 Цена (например: 500 руб., договорная, от 1000 руб.):")
    await state.set_state(AuctionForm.price)


@dp.message(AuctionForm.price)
async def auction_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("📷 Отправьте фотографию монеты (или напишите «нет» чтобы пропустить):")
    await state.set_state(AuctionForm.photo)


@dp.message(AuctionForm.photo, F.photo)
async def auction_photo_yes(message: types.Message, state: FSMContext):
    data = await state.get_data()
    u = message.from_user

    os.makedirs("uploads", exist_ok=True)
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    photo_path = f"uploads/{u.id}_{file_id[:10]}.jpg"
    await bot.download_file(file.file_path, photo_path)

    lot_id = db.add_auction_lot(
        seller_tg_id=u.id,
        seller_name=u.full_name or u.username or str(u.id),
        title=data["title"],
        description=data.get("description", ""),
        period=data.get("period", ""),
        year=data.get("year", ""),
        material=data.get("material", ""),
        price=data["price"],
        photo_path=photo_path
    )
    await state.clear()

    # Уведомление администратора
    await bot.send_message(
        ADMIN_ID,
        f"🆕 Новый лот #{lot_id} от {u.full_name} (@{u.username})\n"
        f"<b>{data['title']}</b>\nЦена: {data['price']}",
        parse_mode="HTML"
    )

    await message.answer(
        f"✅ Лот «{data['title']}» выставлен на аукцион!\n"
        "Покупатели смогут написать вам напрямую.",
        reply_markup=main_keyboard(u.id == ADMIN_ID)
    )


@dp.message(AuctionForm.photo)
async def auction_photo_skip(message: types.Message, state: FSMContext):
    data = await state.get_data()
    u = message.from_user

    lot_id = db.add_auction_lot(
        seller_tg_id=u.id,
        seller_name=u.full_name or u.username or str(u.id),
        title=data["title"],
        description=data.get("description", ""),
        period=data.get("period", ""),
        year=data.get("year", ""),
        material=data.get("material", ""),
        price=data["price"],
        photo_path=""
    )
    await state.clear()

    await bot.send_message(
        ADMIN_ID,
        f"🆕 Новый лот #{lot_id} от {u.full_name}\n<b>{data['title']}</b>",
        parse_mode="HTML"
    )
    await message.answer(
        f"✅ Лот «{data['title']}» добавлен без фото.\n"
        "Покупатели смогут написать вам напрямую.",
        reply_markup=main_keyboard(u.id == ADMIN_ID)
    )


# ======= АДМИН ПАНЕЛЬ =======

@dp.message(F.text == "⚙️ Админ-панель")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    users = db.get_all_users()
    lots = db.get_auction_lots()
    deleted = db.get_auction_lots(status="deleted")
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Все пользователи", callback_data="admin_users")
    builder.button(text="📋 Активные лоты", callback_data="auction_list")
    builder.button(text="🗑 Удалённые лоты", callback_data="admin_deleted")
    builder.adjust(1)
    await message.answer(
        f"⚙️ <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: {len(users)}\n"
        f"📋 Активных лотов: {len(lots)}\n"
        f"🗑 Удалённых лотов: {len(deleted)}",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "admin_users")
async def admin_users(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    users = db.get_all_users()
    text = "👥 <b>Пользователи (топ по очкам):</b>\n\n"
    for i, u in enumerate(users[:20], 1):
        text += f"{i}. {u['full_name']} (@{u['username']}) — {u['score']} очков\n"
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "admin_deleted")
async def admin_deleted_lots(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    lots = db.get_auction_lots(status="deleted")
    if not lots:
        await callback.message.answer("Нет удалённых лотов.")
    else:
        text = "🗑 <b>Удалённые лоты:</b>\n\n"
        for lot in lots:
            text += f"• #{lot['id']} {lot['title']} от {lot['seller_name']}\n"
        await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())