#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple To-DO bot created and designed by Enrico Cecchetti
     ienricocecchetti@gmail.com
     Enjoy and have fun with this code!
     --------------------------------
     please at least mention me on your project if you copy past my code :)
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from functions import dateparser, timeparser, timeDifferenceInSec
import logging
import sqlite3
import re
from datetime import date, datetime, timedelta

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi Mate press /help for more info')
    chat_id = update.message.chat_id
    chat_usr = update.message.from_user.username

    # check user existance (and update his info) or create a new one
    checkuser(chat_id, chat_usr)


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('🔴 Welcome my Master!! 🔴 \n'
                              'use the commands shown below to interact wih me:\n\n'
                              ' 📅 TODO Supporter 📅\n'
                              '/schedule <?>  - show daily due📓 \n'
                              '/remember <?>  - to setup event 📌 \n'
                              '/info <?>      - show info related to an event\n'
                              '/forget <?>    - to delete some due ❌ \n'
                              '/free          - to wipe all your due (⚠Attention⚠)\n\n')


def remember(bot, update, args, job_queue, chat_data):
    """Echo the user message."""
    chat_id = update.message.chat_id
    chat_usr = update.message.from_user.username

    # check user existance (and update his info) or create a new one
    checkuser(chat_id, chat_usr)
    # get the user-id to execute the query
    codu = getuser(chat_id)

    name = ""
    date = ""
    place = ""
    time = ""
    desc = ""
    if len(args) < 2:
        update.message.reply_text("Master please don't forget that i don't know all the info\n"
                                  "Please send me all the data, write: \n\n"
                                  "/remember <due><date><place><time><desc>\n\n"
                                  " ex: '/remember reunion 12/10/2019 Banca 13:00 reunion with China friends at POLITO'")
        return
    else:
        i = 0
        for par in args[0:]:
            i += 1
            matchObj = re.fullmatch(r'([^\s!/]+)', par, re.M | re.I)
            if matchObj:
                name += (matchObj.group()+" ")
                continue
            matchObj = re.match(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', par, re.M | re.I)
            if matchObj:
                date = matchObj.group()
                break

        for par in args[i:]:
            i += 1
            matchObj = re.fullmatch(r'([^\s!:]+)', par, re.M | re.I)
            if matchObj:
                place += (matchObj.group()+" ")
                continue
            matchObj = re.match(r'[0-9]{2}:[0-9]{2}', par, re.M | re.I)
            if matchObj:
                time = matchObj.group()
                break

        for par in args[i:]:
            desc += (re.match(r'([^\s]+)', par, re.M | re.I).group()+" ")

    if time == "":
        time = "08:00"

    if dateparser(date) != -1 and timeparser(time) != -1:
        conn = sqlite3.connect('todo.db')
        c = conn.cursor()
        # print("INSERT INTO todos (uid, name, date, place, time)
        # VALUES("+str(codu)+","+str(name)+","+str(date)+","+str(place)+","+str(time)+","+str(desc)+")")
        c.execute("INSERT INTO todos (uid, name, date, place, time, descr) "
                  "VALUES(?,?,?,?,?,?)", (codu, name, date, place, time, desc))
        conn.commit()
        conn.close()

        due_datetime = datetime.combine(dateparser(date),
                                        timeparser(time))
        today_date = datetime.now()
        # it will notify 1800 sec before the date and time selected so 30 min before
        diff_in_sec = timeDifferenceInSec(due_datetime, today_date) - 5400
        set_timer(update, diff_in_sec, job_queue, chat_id, chat_data)

        update.message.reply_text("Got it!! no problem i'll remember it for ya 💪 \n")
    else:
        update.message.reply_text("❌ Hey sir, Time or Date format is wrong... are you drunk? \n"
                                  "Remember that DATE must be like : dd/mm/yyyy \n"
                                  "and TIME must be in the format: hh:mm \n\n ")


def alarm(bot, job):
    """Send the alarm message."""
    bot.send_message(job.context, text='✔ Hey Master you have something to in half an hour... '
                                       'Check your appointments for details!')


def set_timer(update, args, job_queue, chat_id, chat_data):
    """Add a job to the queue."""
    try:
        # args[0] should contain the time for the timer in seconds
        #print("value in second = %s" % (int(args),))
        due = int(args)
        if due < 0:
            update.message.reply_text('Sorry we can not go back to future!')
            return

        # Add job to queue
        job = job_queue.run_once(alarm, due, context=chat_id)
        chat_data['job'] = job
        update.message.reply_text('Corresponding alarm successfully set!')

    except (IndexError, ValueError):
        update.message.reply_text('Sir, i got some problem setting the alarm! '
                                  'May i ask to to delete/reinsert the appointment!?')


def unset(bot, update, chat_data):
    """Remove the job if the user changed their mind."""
    if 'job' not in chat_data:
        # update.message.reply_text('You have no active timer')
        return

    job = chat_data['job']
    job.schedule_removal()
    del chat_data['job']

    # update.message.reply_text('Timer successfully unset!')


def info(bot, update, args):
    """Echo the user message."""
    chat_id = update.message.chat_id
    chat_usr = update.message.from_user.username

    # check user existance (and update his info) or create a new one
    checkuser(chat_id, chat_usr)
    # get the user-id to execute the query
    codu = getuser(chat_id)

    if len(args) == 0:
        update.message.reply_text("Master, please insert the note that you want me to show in details!\n"
                                  "ex: /info <codEvent>")
    else:
        conn = sqlite3.connect('todo.db')
        c = conn.cursor()
        print("SELECT * FROM todos WHERE uid="+str(codu)+" and tid="+str(args[0]))
        c.execute('SELECT * FROM todos WHERE uid=? and tid=?', (codu, args[0]))
        data = c.fetchone()
        if data[0] is not None:
            update.message.reply_text("🔻 NOTE SUMMARY for '"+data[2]+"'\n\n" +
                                      "APPOINTMENT named: "+data[2]+"\n" +
                                      "📆 will be on: "+data[3]+"\n" +
                                      "⏰ at: "+data[5] + "\n" +
                                      "🌍 in: "+str(data[4]).upper()+ "\n" +
                                      "📎 details: "+str(data[6]) + "\n\n")
        conn.close()


def forget(bot, update, args, chat_data):
    """Echo the user message."""
    chat_id = update.message.chat_id
    chat_usr = update.message.from_user.username

    # check user existance (and update his info) or create a new one
    checkuser(chat_id, chat_usr)
    # get the user-id to execute the query
    codu = getuser(chat_id)

    if isinstance(args, list):

        if len(args) == 0:
            update.message.reply_text("Master, please insert the note that you want me to delete!"
                                      "/forget <codEvent>")
        else:
            conn = sqlite3.connect('todo.db')
            c = conn.cursor()
            c.execute('DELETE FROM todos WHERE uid=? and tid=?', (codu, args[0]))
            conn.commit()
            conn.close()
            update.message.reply_text("Ok Master, i feel more free now!👾")
        return

    else:
        conn = sqlite3.connect('todo.db')
        c = conn.cursor()
        c.execute('DELETE FROM todos WHERE uid=? and tid=?', (codu, args))
        conn.commit()
        conn.close()

        unset(bot, update, chat_data)


def free(bot, update, chat_data):
    """Echo the user message."""
    chat_id = update.message.chat_id
    chat_usr = update.message.from_user.username

    # check user existance (and update his info) or create a new one
    checkuser(chat_id, chat_usr)
    # get the user-id to execute the query
    codu = getuser(chat_id)

    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('SELECT * FROM todos where uid=?', (codu,))
    data = c.fetchall()
    if len(data) != 0:
        for row in data:
            forget(bot, update, row[0], chat_data)

    update.message.reply_text("Master im going in Holiday! Im finally free to go... 😎")


def default(bot, update):
    """Echo the user message."""
    update.message.reply_text("yeah... you are right man!")

def manage_command(bot, update):
    update.message.reply_text("Unknown command. Press /help for more info")


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def checkuser(chat_id, chat_usr):
    """Send a message when the command /start is issued."""
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM user WHERE username=? or chat_id=?', (chat_usr, chat_id))
    data = c.fetchall()
    if data.pop(0)[0] == 0:
        print("new user found")
        c.execute('INSERT INTO user(username, chat_id) VALUES (?,?)', (chat_usr, chat_id))
    else:
        # update the infos
        c.execute('UPDATE user SET username=?, chat_id=? WHERE chat_id=?', (chat_usr, chat_id, chat_id))
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.commit()
    conn.close()


def getuser(chat_id):
    """Send a message when the command /start is issued."""
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('SELECT * FROM user WHERE chat_id=? ', (chat_id,))
    data = c.fetchall()
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    if len(data) != 0:
        cod = data.pop(0)[0]
    else:
        cod = -1

    conn.close()
    return cod


def print_appointment(row):
    temp = ""
    temp += ("Appointment: " + str(row[2]) + "[cod:" + str(row[0]) + "]\n")
    if row[3] != 0:
        temp += ("at: " + str(row[3]))
    if row[5] != 0:
        temp += (" " + str(row[5]))
    if row[4] != 0:
        temp += ("\nin: " + str(row[4]))
    return temp


def delete_old_schedule(bot, update):
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('SELECT * FROM todos')
    data = c.fetchall()
    if len(data) != 0:
        actual_date = date.today()
        for row in data:
            # data error in the record -> DELETE
            if dateparser(row[3]) == "" or dateparser(row[3]) == -1:
                # print("DELETE FROM todos WHERE tid=%s" % (row[0],))
                c.execute('DELETE FROM todos WHERE tid=?', (row[0],))

            # date is just expired so the appointment is old -> DELETE
            if dateparser(row[3]) < actual_date:
                # print("DELETE FROM todos WHERE tid=%s" % (row[0],))
                c.execute('DELETE FROM todos WHERE tid=?', (row[0],))
    conn.commit()
    conn.close()
    update.message.reply_text("Db cleaned Successfully my lord! 🙌")


def schedule(bot, update, args):
    """Echo the user message."""
    chat_id = update.message.chat_id
    chat_usr = update.message.from_user.username

    # check user existance (and update his info) or create a new one
    checkuser(chat_id, chat_usr)

    # get the user-id to execute the query
    codu = getuser(chat_id)
    if codu == -1:
        update.message.reply_text("Master i think there is some kind of problem with me...\n"
                                  "i can't do what you are asking me!\n")

    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('SELECT * FROM todos WHERE uid=?', (codu,))
    data = c.fetchall()
    if len(data) != 0:
        actual_date = date.today()
        appointments = ""
        if len(args) != 1:
            if len(args) == 0:
                # daily schedule
                update.message.reply_text("😵 Master, your daily appointment are:\n\n")
                for row in data:
                    if dateparser(row[3]) != -1 and dateparser(row[3]) == actual_date:
                        appointments += ("📌 " + print_appointment(row)+"\n")
                update.message.reply_text(appointments+"\n")
            else:
                # daily schedule
                update.message.reply_text("👮 Master i think you wrote something wrong...\n\n")
        else:
            if args[0].find("/") != -1 or args[0].find("-") != -1:
                # args is a date -> schedule of that day
                update.message.reply_text("😵 Master, your appointments for " + args[0] + "are:\n\n")
                for row in data:
                    if dateparser(row[3]) != -1 and dateparser(row[3]) == dateparser(args[0]):
                        appointments += ("📌 " + print_appointment(row) + "\n")
                    else:
                        update.message.reply_text("😵 wrong data format boss! I cant help you \n\n")
                update.message.reply_text(appointments + "\n")
            elif args[0] == "all":
                # args is all -> all my schedule
                update.message.reply_text("😵 Master, your appointments scheduled till now are:\n\n")
                for row in data:
                    appointments += ("📌 " + print_appointment(row) + "\n")
                update.message.reply_text(appointments + "\n")
            else:
                # arg is a number -> period schedule
                update.message.reply_text("😵 Master, your daily appointment are:\n\n")
                for row in data:
                    if dateparser(row[3]) != -1 and dateparser(row[3]) < (actual_date + timedelta(days=int(args[0]))):
                        appointments += ("📌 " + print_appointment(row) + "\n")
                update.message.reply_text(appointments + "\n")
        conn.close()

        update.message.reply_text("\nWanna know something else??\n"
                                  "Try:\n\n"
                                  "  /schedule             - for show all daily appointment\n"
                                  "  /schedule <dd/mm/yy>  - for schedule of a certain day\n"
                                  "  /schedule <# of days> - for next #n days schedule\n"
                                  "  /schedule all         - for all your appointment\n")
    else:
        update.message.reply_text("Master i don't remember anything for today! So take it easy and relax 🎉 \n\n")


def own(bot, update):
    update.message.reply_text("My Lord is the real IEC")


def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    # on different commands - todo ones
    dp.add_handler(CommandHandler("remember", remember,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("forget", forget,
                                  pass_args=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("schedule", schedule,
                                  pass_args=True))
    dp.add_handler(CommandHandler("info", info,
                                  pass_args=True))
    dp.add_handler(CommandHandler("free", free, 
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("clean", delete_old_schedule))
    dp.add_handler(CommandHandler("set", set_timer,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("unset", unset,
                                  pass_chat_data=True))

    # true owner egg
    dp.add_handler(CommandHandler("own", own))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, default))
    dp.add_handler(MessageHandler(Filters.command, manage_command))

    # Log all errors
    dp.add_error_handler(error)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()

