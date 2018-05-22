# -*- coding: UTF8 -*-
import datetime
import requests
from datetime import datetime
import sqlite3
import git
import os

#repo = git.cmd.Git("~/stickyNotes/stickyNotes/")
repo = git.cmd.Git(".")

class BotHandler:
    def __init__(self, token):
            self.token = token
            self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates(self, offset=0, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp

    def get_first_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[0]
        else:
            last_update = None

        return last_update


token = '612672943:AAH0p_nu0l2GMP0HJ1MepAufYt4hIPxkmzw'
wisdom_bot = BotHandler(token) #Your bot's name

def main():
    #Establish database connection.
    connection = sqlite3.connect('userLists.db')
    database = connection.cursor()
    new_offset = 0

    while True:
        all_updates=wisdom_bot.get_updates(new_offset)
        time = str(datetime.now())[11:19]
        if '09:00:00' < time < '09:00:30':
            repo.pull()
            users = database.execute("SELECT user_id, count FROM users;")
            users_list = []
            for user in users:
                users_list.append(user)

            for user in users_list:
                user_list = database.execute("SELECT * FROM user_list WHERE user_id={};".format(user[0]))
                i = 1
                for element in user_list:
                    if i == user[1]:
                        wisdom_bot.send_message(user[0], element[1])
                        database.execute("UPDATE users SET count=count+1 WHERE user_id={};".format(user[0]))
                        connection.commit()
                        repo.add(u=True)
                        repo.commit('-m "Add new user"')
                        repo.push()
                        break
                    i += 1

        if len(all_updates) > 0:
            for current_update in all_updates:
                first_update_id = current_update['update_id']
                if 'edited_message' in current_update:
                    new_offset = first_update_id + 1
                    break
                elif 'text' not in current_update['message']:
                    first_chat_text='New member'
                else:
                    first_chat_text = current_update['message']['text']
                first_chat_id = current_update['message']['chat']['id']
                if 'first_name' in current_update['message']:
                    first_chat_name = current_update['message']['chat']['first_name']
                elif 'new_chat_member' in current_update['message']:
                    first_chat_name = current_update['message']['new_chat_member']['username']
                elif 'from' in current_update['message']:
                    first_chat_name = current_update['message']['from']['first_name']
                else:
                    first_chat_name = "unknown"

                users = database.execute("SElECT name FROM users WHERE user_id={};".format(first_chat_id))
                i = 0
                for element in users:
                    i = 1
                if i == 0:
                    database.execute("INSERT INTO users (user_id, name) VALUES ({}, '{}');".format(first_chat_id, first_chat_name))
                    connection.commit()
                    repo.add(u=True)
                    repo.commit('-m "Add new user"')
                    repo.push()
                if first_chat_text == 'Hi' or first_chat_text == "hi" or first_chat_text == "hello" or first_chat_text == "Hello":
                    wisdom_bot.send_message(first_chat_id, 'Hello ' + first_chat_name)
                    new_offset = first_update_id + 1
                
                elif first_chat_text == "list" or first_chat_text == "List" or first_chat_text == "/list":
                    list_items = database.execute("SELECT list_item FROM user_list WHERE user_id={};".format(first_chat_id))
                    message = "Here is your list\n"
                    i = 1
                    for element in list_items:
                        message = message + '\n'+ str(i) + '. ' + str(element[0])
                        i += 1
                    wisdom_bot.send_message(first_chat_id, message)
                    new_offset = first_update_id + 1

                elif first_chat_text[:3] == "add" or first_chat_text[:3] == "Add":
                    database.execute("INSERT INTO user_list (user_id, list_item) VALUES ({}, '{}')".format(first_chat_id, first_chat_text[4:]))
                    connection.commit()
                    repo.add(u=True)
                    repo.commit('-m "Add item to a list"')
                    repo.push()
                    wisdom_bot.send_message(first_chat_id, 'Successfully added to your list')
                    new_offset = first_update_id + 1
            
                elif first_chat_text[:6] == "Delete" or first_chat_text[:6] == "delete":
                    if len(first_chat_text) < 7:
                        pass
                    else:
                        position = first_chat_text[7:]
                        try:
                            position = int(position)
                        except:
                            pass
                    list_items = database.execute("SELECT list_item FROM user_list WHERE user_id={};".format(first_chat_id))
                    i = 1
                    for element in list_items:
                        if i == position:
                            database.execute("DELETE FROM user_list WHERE list_item=?;", element)
                            wisdom_bot.send_message(first_chat_id, 'Successfully deleted')
                            connection.commit()
                            repo.add(u=True)
                            repo.commit('-m "Delete item from a list"')
                            repo.push()
                            new_offset = first_update_id + 1
                            break

                        elif i < position:
                            i += 1
                        else:
                            new_offset = first_update_id + 1
                            break
                
                elif first_chat_text == "count" or first_chat_text == "/count":
                    counts = database.execute("SELECT count FROM users WHERE user_id={};".format(first_chat_id))
                    for count in counts:
                        wisdom_bot.send_message(first_chat_id, 'The next item in queue is: {}'.format(count[0]))
                        new_offset = first_update_id + 1
                
                elif first_chat_text == "inc_count" or first_chat_text == "/inc_count":
                    database.execute("UPDATE users SET count=count+1 WHERE user_id={};".format(first_chat_id))
                    connection.commit()
                    repo.add(u=True)
                    repo.commit('-m "Add new user"')
                    repo.push()
                    wisdom_bot.send_message(first_chat_id, 'Successfully updated count')
                    new_offset = first_update_id + 1

                elif first_chat_text == "dec_count" or first_chat_text == "/dec_count":
                    database.execute("UPDATE users SET count=count-1 WHERE user_id={};".format(first_chat_id))
                    connection.commit()
                    repo.add(u=True)
                    repo.commit('-m "Add new user"')
                    repo.push()
                    wisdom_bot.send_message(first_chat_id, 'Successfully updated count')
                    new_offset = first_update_id + 1

                elif first_chat_text[:9] == "inc_count":
                    try:
                        count = int(first_chat_text[10:])
                        database.execute("UPDATE users SET count=count+{} WHERE user_id={};".format(count, first_chat_id))
                        connection.commit()
                        repo.add(u=True)
                        repo.commit('-m "Add new user"')
                        repo.push()
                        wisdom_bot.send_message(first_chat_id, 'Successfully updated count')
                    except:
                        wisdom_bot.send_message(first_chat_id, 'Sorry wrong format')
                    new_offset = first_update_id + 1

                elif first_chat_text[:9] == "dec_count":
                    try:
                        count = int(first_chat_text[10:])
                        database.execute("UPDATE users SET count=count-{} WHERE user_id={};".format(count, first_chat_id))
                        connection.commit()
                        repo.add(u=True)
                        repo.commit('-m "Add new user"')
                        repo.push()
                        wisdom_bot.send_message(first_chat_id, 'Successfully updated count')
                    except:
                        wisdom_bot.send_message(first_chat_id, 'Sorry wrong format')
                    new_offset = first_update_id + 1

                else:
                    wisdom_bot.send_message(first_chat_id,"""
This is how you can use me

Use 'Add XXX' to add an item to your list
Use 'List' to display your list
Use 'Delete X' to an item from your list
Use 'count' to check next item in line
Use 'inc_count XX' to increment 'count' by a number
Use 'dec_count XX' to decremet 'count' by a number
                        """)
                    new_offset = first_update_id + 1

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()