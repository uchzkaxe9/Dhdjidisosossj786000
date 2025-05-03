import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
import subprocess

user_sessions = {}  # Store user-specific temp files

# Start command with welcome message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Welcome to the Hardsub Bot!\n\n"
        "Yahaan aap apna video aur subtitle (.srt) file bhej kar ek hi video mein permanent subtitles add kar sakte ho.\n\n"
        "Steps:\n"
        "1. Pehle apna video (.mp4) bhejein.\n"
        "2. Phir usi video ke subtitles (.srt file) bhejein.\n"
        "3. Bot aapko ek final hardsubbed video bhej dega — subtitles permanently video ke andar honge.\n\n"
        "Ready when you are — bhej do video pehle!"
    )
    await update.message.reply_text(welcome_text)

# Handle video file
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    video = update.message.video or update.message.document
    file = await context.bot.get_file(video.file_id)

    video_path = f"temp/{user_id}_video.mp4"
    os.makedirs("temp", exist_ok=True)
    await file.download_to_drive(video_path)

    user_sessions[user_id] = {'video': video_path}
    await update.message.reply_text("Video received. Now send the SRT subtitle file.")

# Handle SRT file and hardsub it
async def handle_srt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    srt_file = update.message.document

    if not srt_file.file_name.endswith('.srt'):
        return await update.message.reply_text("Please send a valid .srt subtitle file.")

    file = await context.bot.get_file(srt_file.file_id)
    srt_path = f"temp/{user_id}_subs.srt"
    await file.download_to_drive(srt_path)

    if user_id not in user_sessions or 'video' not in user_sessions[user_id]:
        return await update.message.reply_text("Please send the video first before the subtitles.")

    video_path = user_sessions[user_id]['video']
    output_path = f"temp/{user_id}_output.mp4"

    await update.message.reply_text("Hardsubbing in progress... Please wait...")

    # FFmpeg command to hardsub
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"subtitles={srt_path}",
        "-c:a", "copy", output_path
    ]

    try:
        process = await asyncio.create_subprocess_exec(*cmd)
        await process.communicate()

        # Send final video
        await update.message.reply_video(video=open(output_path, 'rb'), caption="Here is your hardsubbed video!")

    except Exception as e:
        await update.message.reply_text(f"Error during processing: {str(e)}")

    finally:
        # Cleanup
        for f in [video_path, srt_path, output_path]:
            if os.path.exists(f):
                os.remove(f)
        user_sessions.pop(user_id, None)

# Run the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token("7711552770:AAF0PD8FtjGZo8wYcPMBOcQZxZTXtOw3KqY").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.MIME_TYPE("video/mp4"), handle_video))
    app.add_handler(MessageHandler(filters.Document.MIME_TYPE("application/x-subrip"), handle_srt))

    print("Bot is running...")
    app.run_polling()
