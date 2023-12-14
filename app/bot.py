#!/usr/bin/env python
import logging

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, JobQueue
import os
import time
from datetime import datetime
import re
from dotenv import load_dotenv
import asyncio

from postagde import postagde_request
import modifydb

# hack to not verify webdriver ssl?
#os.environ['WDM_SSL_VERIFY'] = '0'

# tokens!
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'bot.env'))
gh_token = os.environ.get('GH_TOKEN')
bot_api_key = os.environ.get('TG_BOT_KEY_POSTA')

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Zdravo, {user.mention_html()}!",
        #reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("""Pošalji mi kod za praćenje i dobij status.
                                    \n /add XX*********YY napomena - slediti za statusom sa napomenom.
                                    \n /list - za listu praćenih brojeva.
                                    \n /del XX*********YY - za brisanje broja""")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send all tracked when the command /list is issued."""
    md = modifydb.Modifydb('../main.db')
    track_list = md.select_by_userid(update.message.from_user.id)


    formatted_message = "Evo liste brojeva koje pratim:\n"
    if len(track_list) > 0:
        for trackno, note in track_list:
            formatted_message += f"{trackno} - {note}\n"
    else:
        formatted_message += f"Ne pratimo ništa\n"
    await update.message.reply_text(formatted_message)

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /add is issued."""
    pattern = r'^[A-Z]{2}\d{9}[A-Z]{2}$'

    #checking user input for bullshit
    if len(context.args) >= 1:
        trackno = context.args[0]
        if not re.match(pattern, trackno):
            await update.message.reply_text("Izvinjavam se, ovo ne izgleda kao broj za praćenje sa kojim mogu pomoći.")
            return
    else: 
        await update.message.reply_text("Treba broj za praćenje.")
        return


    user_id = update.message.from_user.id
    timestamp = time.time()
    pretty_time = datetime.fromtimestamp(timestamp).strftime('%d.%m.%Y %H:%M:%S')

    
    logging.info(context.args)

    md = modifydb.Modifydb('../main.db')
    
    if len(context.args) >= 2:
        note = ' '.join(context.args[1:])
        md.insert_data(user_id, trackno, pretty_time, 'no', note)
    else:
        md.insert_data(user_id, trackno, pretty_time, 'no')
        
    await update.message.reply_text(f"Ako se pojavi broj {trackno} obavestiću vas.")
          
async def del_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    pattern = r'^[A-Z]{2}\d{9}[A-Z]{2}$'

    #checking user input for bullshit
    if len(context.args) >= 1:
        trackno = context.args[0]
        if not re.match(pattern, trackno):
            await update.message.reply_text("Izvinjavam se, ovo ne izgleda kao broj za praćenje sa kojim mogu pomoći.")
            return
    else:
        await update.message.reply_text("Treba broj za brisanje.")
        return

    user_id = update.message.from_user.id

    md = modifydb.Modifydb('../main.db')
    md.delete_track(user_id,trackno)

    await update.message.reply_text(f"Broj {trackno} je obrisan.")

async def posta_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    async def krasota():
        user_id = update.message.from_user.id
        trackno = update.message.text        
        data_list = await postagde_request(update.message.text)
        formatted_message = "Informacije o " + trackno + ":\n"

        if "ispravnost" in data_list:
            formatted_message += data_list
            return formatted_message
        else:
            for entry in data_list:
                date = entry['date']
                location = entry['location']
                status = entry['status']
                formatted_message += f"{date}\n{location}\n{status}\n\n"

            data_timestamp = data_list[0]['date']
            md = modifydb.Modifydb('../main.db')
            md.insert_data(user_id, trackno, data_timestamp, 'no')
            if "Uručena" in data_list[0]['status']:
                md.set_received(trackno)
    
        return formatted_message

    await update.message.reply_text(await krasota())
    #await update.message.reply_text("Napisaću kada se promeni status paketa " + trackno + ".")

async def checkrs(context: ContextTypes.DEFAULT_TYPE) -> None:
    md = modifydb.Modifydb('../main.db')
    unreceived_list = md.select_unreceived()
    logging.info(f"Unreceived list: {unreceived_list}")
    # Unreceived list: [(161461120, 'LA050398758HU', '14.12.2023 07:11:40', 'fifine'), (161461120, 'LA050392494HU', '14.12.2023 07:11:46', 'golova'), (161461120, 'LA050389699HU', '14.12.2023 07:11:53', 'random')]

    if unreceived_list is None:
        logging.info('Nothing to check...')
        return None

    # Fetch data for multiple rows in a batch
    batch_data = await asyncio.gather(*[postagde_request(row[1]) for row in unreceived_list])
    logging.info(batch_data)

    for i, (user_id, trackno, db_timestamp, note) in enumerate(unreceived_list):
        new_data = batch_data[i]
        new_timestamp = new_data[0]
        #new_timestamp = "bururururu"
        logging.info(f"new_data value: {new_data}")
        logging.info(f"new_timestamp value: {new_timestamp}")

        formatted_message = f"Informacije o {trackno} ({note}):\n"
        for i in range(0, len(new_data), 4):
            timestamp = new_data[i]
            address = new_data[i + 1]
            status = new_data[i + 2]

            formatted_message += f"{timestamp}\n{address}\n{status}\n\n"

        logging.info(f"timestamp in DB: {db_timestamp}")
        logging.info(f"new timestamp: {new_timestamp}")

        if new_timestamp != db_timestamp and "ispravnost" not in formatted_message:
            md.update_timestamp(new_timestamp, trackno)
            if "Uručena" in formatted_message:
                md.set_received(trackno)
            await context.bot.send_message(chat_id=user_id, text=formatted_message)

    return


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_api_key).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("del", del_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, posta_reply))

    job_queue = application.job_queue
    job_queue.run_repeating(checkrs, interval=60, first=10)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()

