import qrcode
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
import os
import asyncio
from aiogram.types import FSInputFile
from datetime import datetime
import uuid

dupend = []

API_TOKEN = '8512053762322'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Настройки сервера
NGINX_BASE_URL = "https://apanelllinks.koteichhost.ru/files"  # Замените на ваш домен
DOWNLOAD_FOLDER = "/www/wwwroot/apanelllinks.koteichhost.ru/files"  # Папка, которую раздает nginx

# Создаем папку если нет
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def generate_qr(url, filename):
    """Генерация QR-кода с ссылкой"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_filename = f"qr_{filename}.png"
    qr_path = os.path.join(DOWNLOAD_FOLDER, qr_filename)
    img.save(qr_path)
    return qr_filename, qr_path

def generate_unique_filename(original_name, user_id):
    """Генерация уникального имени файла"""
    extension = original_name.split('.')[-1] if '.' in original_name else 'jpg'
    unique_id = str(uuid.uuid4())[:8]
    return f"{user_id}_{unique_id}.{extension}"

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("""
Привет! Отправь одно фото и я:
1. Сохраню его на сервере
2. Создам QR-код со ссылкой для просмотра фото
3. Отправлю тебе QR-код""")

@dp.message(F.content_type == "photo")
async def download_photo(message: types.Message):
    try:
        # Получаем файл фото
        photo = message.photo[-1]
        file_id = photo.file_id
        
        # Получаем информацию о файле
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        # Создаем уникальное имя файла
        filename = generate_unique_filename(file_path, message.from_user.id)
        download_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # Скачиваем файл на сервер
        await bot.download_file(file_path, download_path)
        
        # Генерируем публичную ссылку через nginx
        file_url = f"{NGINX_BASE_URL}/{filename}"
        
        # Создаем QR-код со ссылкой
        qr_filename, qr_path = generate_qr(file_url, filename)
        qr_url = f"{NGINX_BASE_URL}/{qr_filename}"
        
        # Отправляем QR-код пользователю
        await message.answer_photo(
            photo=FSInputFile(qr_path),
            caption=f"""✅ Фото сохранено!

📁 Имя файла: {filename}
🔗 Ссылка для скачивания: {file_url}

📱 QR-код содержит ту же ссылку
Сканируйте его чтобы скачать фото"""
        )
        
        # Также отправляем прямую ссылку текстом
        await message.answer(
            f"📎 Прямая ссылка: {file_url}\n"
            f"📎 QR-код: {qr_url}"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке фото: {str(e)}")

@dp.message(F.content_type == "document")
async def download_document(message: types.Message):
    try:
        # Для документов (если нужно)
        document = message.document
        file_id = document.file_id
        
        # Получаем информацию о файле
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        # Создаем уникальное имя файла
        filename = generate_unique_filename(document.file_name, message.from_user.id)
        download_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # Скачиваем файл на сервер
        await bot.download_file(file_path, download_path)
        
        # Генерируем публичную ссылку
        file_url = f"{NGINX_BASE_URL}/{filename}"
        
        # Создаем QR-код со ссылкой
        qr_filename, qr_path = generate_qr(file_url, filename)
        
        # Отправляем QR-код пользователю
        await message.answer_photo(
            photo=FSInputFile(qr_path),
            caption=f"""✅ Файл сохранен!

📁 Имя файла: {filename}
📊 Размер: {document.file_size} байт
🔗 Ссылка: {file_url}"""
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке файла: {str(e)}")

@dp.message(Command("help"))
async def send_help(message: types.Message):
    await message.answer("""
📋 Доступные команды:
/start - начать работу
/help - показать справку

Просто отправьте фото или файл - я сохраню его и пришлю QR-код со ссылкой для скачивания.""")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    print("Бот запущен...")
    asyncio.run(main())
