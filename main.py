main.py

import os import logging from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip from telegram import Update, Bot from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes import subprocess

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN") VIDEO_FILE = "input.mp4" SUB_FILE = "subtitles.srt" OUTPUT_FILE = "output.mp4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("Welcome! Please send a video file followed by an SRT subtitle file. I'll hardsub it for you!")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE): file = await update.message.video.get_file() await file.download_to_drive(VIDEO_FILE) context.user_data['video_received'] = True await update.message.reply_text("Video received. Now send the SRT file.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE): if not context.user_data.get('video_received'): await update.message.reply_text("Please send the video first.") return

file = await update.message.document.get_file()
await file.download_to_drive(SUB_FILE)
await update.message.reply_text("Subtitle received. Processing video...")

try:
    # Run ffmpeg command to hardsub
    command = [
        "ffmpeg", "-i", VIDEO_FILE, "-vf", f"subtitles={SUB_FILE}", OUTPUT_FILE
    ]
    subprocess.run(command, check=True)

    await update.message.reply_video(video=open(OUTPUT_FILE, 'rb'))
    await update.message.reply_text("Here is your hardsubbed video!")
except Exception as e:
    await update.message.reply_text(f"Error: {e}")

app = ApplicationBuilder().token(BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(MessageHandler(filters.VIDEO, handle_video)) app.add_handler(MessageHandler(filters.Document.MIME_TYPE("application/x-subrip"), handle_document))

if name == 'main': app.run_polling()

