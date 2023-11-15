from telegram import Update, Bot, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, filters, Updater, MessageHandler,CallbackQueryHandler ,ConversationHandler, CommandHandler, CallbackContext, ContextTypes
from typing import Final
import nst
from io import BytesIO
from PIL import Image
import urllib.request as urllib2
import os
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning
from decouple import config
from model import get_llm
from create_chain import create_chain
from check_model import is_directory_empty, download_llm
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

CHOOSING, FIRST_PHOTO, SECOND_PHOTO, CHAT_WITH_BOT = range(4)

async def start_command(update:Update, context:CallbackContext):
    print(f'User {update.message.chat.id} with name {update.message.chat.full_name}')
    await update.message.reply_text(
        f"Hi {update.effective_user.first_name}! \nChoose an option:",
        reply_markup=main_menu_keyboard(),
    )
    return CHOOSING

def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("Style transfering")],
        [KeyboardButton("Assistant")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button_data = update.message.text

    if button_data == 'Style transfering':
        await transfer_command(update, context)
        return FIRST_PHOTO
    if button_data == 'Assistant':
        await update.message.reply_text("To stop chatting simply write 'exit'.")
        await chat_command(update, context)
        return CHAT_WITH_BOT

async def chat_command(update:Update, context: CallbackContext):
    message = update.message.text
    print(message)
    if message == 'exit':
        await update.message.reply_text("Got it.")
        return ConversationHandler.END
    answer = llm_chain(message)
    await update.message.reply_text(answer['text'])
    
async def cancel_command(update:Update, context: ContextTypes.DEFAULT_TYPE):  
    await update.message.reply_text('Got it, canceling')
    return ConversationHandler.END 

async def transfer_command(update:Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Send me first content photo')
    await update.message.reply_html('Dont forget to switch off <b>"Compress the image"</b> check mark before sending.')
    return FIRST_PHOTO

async def first_photo(update:Update, context: ContextTypes.DEFAULT_TYPE):
    global w, h
    first = await update.message.document.get_file()
    first_url = str(first.file_path)
    contents = urllib2.urlopen(first_url).read()
    context.user_data['first_photo'] = Image.open(BytesIO(contents)).convert('RGB')
    w, h = nst.save_size(context.user_data['first_photo'])
    print('first message size =',w,h)
    await update.message.reply_text("Send me second style photo \nThis one should be compressed")
    return SECOND_PHOTO

async def second_photo(update:Update, context: ContextTypes.DEFAULT_TYPE):
    second = await update.message.photo[-1].get_file()
    second_url = str(second.file_path)
    contents = urllib2.urlopen(second_url).read()
    context.user_data['second_photo'] = Image.open(BytesIO(contents)).convert('RGB')
    await update.message.reply_text("Processing...")
    output = nst.process_images(context.user_data['first_photo'], context.user_data['second_photo'])
    nst.imshow(output,w,h)
    await update.message.reply_text("Final photo:")
    await update.message.reply_document('../photos/final.jpg')
    os.remove('../photos/final.jpg')
    return CHOOSING

async def help_command(update:Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html('<b>This picture represents how am I working:</b>')
    await update.message.reply_photo('../photos/bot_start.png')
    await update.message.reply_html('You sending me two pictures: <b>first</b> is "content picture", \
                                    which represents on what I will place changes. \
                                    <b>Second</b> is "style image", from which I will take style. Easier than ever!')
    await update.message.reply_html('Assistant button starts chat with AI, that will provide answers on your questions about this bot. <b>Feel free to ask!</b>')
    return ConversationHandler.END
    
async def error(update:Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')



if __name__ == '__main__':
    print('Starting bot...')
    if is_directory_empty():
        print('downloading model...')
        download_llm()
        print("model is loaded")
    model = get_llm()
    llm_chain = create_chain(model)
    TOKEN = config('TOKEN')
    BOT_USERNAME: Final = '@styletrans_bot'
    bot = Bot(token=TOKEN)
    app = Application.builder().token(TOKEN).build()

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start_command),
                      CommandHandler('transfer', transfer_command),
                      CommandHandler('help',help_command)],
        fallbacks=[CommandHandler('cancel', cancel_command)],

        states={
            CHOOSING: [MessageHandler(filters.TEXT, button_click)],
            FIRST_PHOTO: [MessageHandler(filters.Document.ALL, first_photo)],
            SECOND_PHOTO: [MessageHandler(filters.PHOTO, second_photo)],
            CHAT_WITH_BOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat_command)]
        },
    ) 
)
    app.add_error_handler(error)
    print('Polling...')
    app.run_polling(poll_interval=3)