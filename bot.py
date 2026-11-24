import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
import yt_dlp

# Bot tokeningiz
BOT_TOKEN = "9188676247:AAHFUnZiObPT2A_TJwKyp0VwIYgH4Tv8tfU" # Tokeningiz shu holatda qoladi

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_video(url: str, user_id: int) -> str:
    """Havola orqali videoni tezroq yuklab oluvchi funksiya"""
    output_template = os.path.join(DOWNLOAD_DIR, f"{user_id}_%(id)s.%(ext)s")
    ydl_opts = {
        # Eng yuqori sifat o'rniga o'rtacha tezroq ishlaydigan formatni tanlaymiz
        "format": "mp4/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "max_filesize": 50 * 1024 * 1024,  # Telegram bot limiti: 50 MB
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Salom! Menga Instagram, TikTok yoki YouTube video havolasini yuboring.\n"
        "Tez fursatda yuklab beraman!"
    )


@dp.message(F.text.startswith(("http://", "https://")))
async def handle_video_link(message: types.Message):
    url = message.text.strip()
    status_msg = await message.answer("⏳ Video yuklanmoqda, iltimos kuting...")

    file_path = None
    try:
        loop = asyncio.get_running_loop()
        # Yuklash jarayoni osilib qolmasligi uchun executor ishlatamiz
        file_path = await asyncio.wait_for(
            loop.run_in_executor(None, download_video, url, message.from_user.id),
            timeout=60.0  # Agar 60 soniyadan oshib ketsa to'xtatadi
        )

        if file_path and os.path.exists(file_path):
            video_file = FSInputFile(file_path)
            await message.answer_video(
                video=video_file,
                caption="✅ Marhamat, videongiz tayyor!"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Videoni yuklab bo'lmadi.")

    except asyncio.TimeoutError:
        await status_msg.edit_text("❌ Vaqt tugadi (Timeout). Video juda katta yoki havola ishlamayapti.")
    except Exception as e:
        await status_msg.edit_text(
            "❌ Xatolik yuz berdi. Havola yopiq bo'lishi yoki hajmi 50 MB dan katta bo'lishi mumkin."
        )
        logging.error(f"Yuklashda xato: {e}")

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())