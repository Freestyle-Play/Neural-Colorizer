from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import os, threading, requests, datetime

import torch
#import fastai
from deoldify.visualize import *
if not torch.cuda.is_available():
    print('GPU not available.')

import warnings
warnings.filterwarnings("ignore")

token='Token'
bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

#b1 = KeyboardButton("")
#kb_client = ReplyKeyboardMarkup(resize_keyboard=True)
#kb_client.add(b1)

class Form(StatesGroup):
    img = State()
    rend_fact = State()
    data = State()
    


class Queue:
    def __init__(self):
        self._values = []

    def Push(self, data):
        self._values.append(data)

    def Pop(self):
        if (self.isEmpty()):
            raise IndexError("Queue is empty!")
        
        value = self._values[0]
        del self._values[0]
        return value

    def isEmpty(self) -> bool:
        return len(self._values) < 1

Work_Queue = Queue()
config = {}
Media_proc = False

if not os.path.exists("logs.txt"):
    with open("logs.txt", 'w'):
        pass

@dp.message_handler(commands=['start', 'help'], state="*")
async def start(message):
    await message.reply('Здравствуйте!\nЯ бот🤖 который может разукрашивать черно-белые фотографии и видео\n(Для поиска фотографий можно воспользоваться @pic)\n\n/begin чтобы загрузить файлы для работы!\n/cancel для отмены загрузки')

@dp.message_handler(commands=['stop'], state="*")
async def stopBot(message):
    if message.chat.id == 916083106:
        await message.answer("выключение")
        os.abort()

@dp.message_handler(commands=['cfg'], state="*")
async def menu(message):
    global config
    await message.answer(config)

@dp.message_handler(commands=['begin'], state = "*")
async def begin(message):
    await Form.img.set()

    await message.reply("Пришлите фотографию.🌇")


@dp.message_handler(commands=['cancel'], state="*")
async def begin(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено.")

@dp.message_handler(commands=['menu'], state="*")
async def menu(message):
    await message.reply('Здравствуйте!\nЯ бот🤖 который может разукрашивать черно-белые фотографии и видео\n(Для поиска фотографий можно воспользоваться @pic)\n\n/begin чтобы загрузить файлы для работы!\n/cancel для отмены загрузки')

@dp.message_handler(content_types=["voice"],state="*")
async def download_video(message: types.Message, state: FSMContext):
    print(message)

@dp.message_handler(content_types=["video"],state=Form.img)
async def download_video(message: types.Message, state: FSMContext):
    print("Захват видео")
    file_id = message.video.file_id # Get file id
    file = await bot.get_file(file_id) # Get file path
    await bot.download_file(file.file_path, "video.mp4")    


@dp.message_handler(content_types=['photo'], state=Form.img)
async def photo_handl(message : types.message, state: FSMContext):
    global config
    print(f'\n\n{str(datetime.datetime.now().hour)}:{str(datetime.datetime.now().minute)}:{str(datetime.datetime.now().second)} захват фото\n\n')
    file_info = await bot.get_file(message.photo[-1].file_id)
    await message.photo[-1].download(f"Downloaded\\{file_info.file_path.split('photos/')[1]}")
    if not os.path.exists(f"Downloaded\\{message.chat.id}.jpg"):
        os.rename(f"Downloaded\\{file_info.file_path.split('photos/')[1]}", f"Downloaded\\{message.chat.id}.jpg")
    else:
        os.remove(f"Downloaded\\{message.chat.id}.jpg")
        os.rename(f"Downloaded\\{file_info.file_path.split('photos/')[1]}", f"Downloaded\\{message.chat.id}.jpg")
    
    await message.reply("изображение успешно загружено! ✅")
    btn_1 = InlineKeyboardButton("Что такое рендер фактор⁉️", callback_data='factor_question')
    btn_2 = InlineKeyboardButton("Low🌅", callback_data='rf_low')
    btn_3 = InlineKeyboardButton("Medium🏞", callback_data='rf_medium')
    btn_4 = InlineKeyboardButton("Hight🎑", callback_data='rf_hight')
    if config.get(str(message.from_user.id)) == None:
        btn_5 = InlineKeyboardButton("Художественный 🌄", callback_data='artistic_togle')
        config[str(message.from_user.id)] = True
    else:
        if config.get(str(message.from_user.id)):
            btn_5 = InlineKeyboardButton("Художественный 🌄", callback_data='artistic_togle')
        else:
            btn_5 = InlineKeyboardButton("Стабильный 📊", callback_data='artistic_togle')  
    inline_kb1 = InlineKeyboardMarkup().add(btn_1).row(btn_2, btn_3, btn_4).add(btn_5)
    await message.answer("теперь давайте выберем фактор рендеринга.🎨", reply_markup=inline_kb1)
    

@dp.callback_query_handler(text="factor_question", state = "*")
async def inlines(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id, text='')
    btn_1 = InlineKeyboardButton("Назад◀", callback_data='back')
    inline_kb = InlineKeyboardMarkup().add(btn_1)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="фактор рендера определяет разрешение, с которым отображается цветная часть изображения. Более низкое разрешение будет отображаться быстрее, а цвета также будут выглядеть более яркими. В частности, изображения более старых и низкого качества, как правило, выигрывают от снижения коэффициента визуализации. Более высокие коэффициенты визуализации часто лучше для изображений более высокого качества, но цвета могут слегка размываться.", reply_markup=inline_kb)

@dp.callback_query_handler(text="artistic_togle", state = "*")
async def inlines(callback: types.CallbackQuery):
    global config
    await bot.answer_callback_query(callback.id, text='')
    if config.get(str(callback.from_user.id)):
        config[str(callback.from_user.id)] = False
    else:
        config[str(callback.from_user.id)] = True
    btn_1 = InlineKeyboardButton("Что такое рендер фактор⁉️", callback_data='factor_question')
    btn_2 = InlineKeyboardButton("Low🌅", callback_data='rf_low')
    btn_3 = InlineKeyboardButton("Medium🏞", callback_data='rf_medium')
    btn_4 = InlineKeyboardButton("Hight🎑", callback_data='rf_hight')
    if config.get(str(callback.from_user.id)):
        btn_5 = InlineKeyboardButton("Художественный 🌄", callback_data='artistic_togle')
    else:
        btn_5 = InlineKeyboardButton("Стабильный 📊", callback_data='artistic_togle')  
    inline_kb = InlineKeyboardMarkup().add(btn_1).row(btn_2, btn_3, btn_4).add(btn_5)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="теперь давайте выберем фактор рендеринга.🎨", reply_markup=inline_kb)



@dp.callback_query_handler(text="back", state = "*")
async def inlines(callback: types.CallbackQuery):
    global config
    await bot.answer_callback_query(callback.id, text='')
    btn_2 = InlineKeyboardButton("Low🌅", callback_data='rf_low')
    btn_3 = InlineKeyboardButton("Medium🏞", callback_data='rf_medium')
    btn_4 = InlineKeyboardButton("Hight🎑", callback_data='rf_hight')
    if config.get(str(callback.from_user.id)) == None:
        btn_5 = InlineKeyboardButton("Стабильный 📊", callback_data='artistic_togle')
        config[str(callback.from_user.id)] = False
    else:
        if config.get(str(callback.from_user.id)):
            btn_5 = InlineKeyboardButton("Художественный 🌄", callback_data='artistic_togle')
        else:
            btn_5 = InlineKeyboardButton("Стабильный 📊", callback_data='artistic_togle')  
    inline_kb = InlineKeyboardMarkup().row(btn_2, btn_3, btn_4).add(btn_5)
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="теперь давайте выберем фактор рендеринга.🎨", reply_markup=inline_kb)

@dp.callback_query_handler(text="rf_low", state = "*")
async def inlines(callback: types.CallbackQuery):
    global config
    await bot.answer_callback_query(callback.id, text='')
    print()
    print()

    image = f"Downloaded\\{callback.message.chat.id}.jpg"
    key = (callback.message.chat.id, callback.from_user.id)

    temp_data = {"path": image, "render_data": 10, "from":key, "artistic":config.get(str(callback.from_user.id))}
    Work_Queue.Push(temp_data)
    await bot.send_message(callback.message.chat.id ,text=f"вы добавлены в очередь - {len(Work_Queue._values)}⏳")

    if not Media_proc:
        thr = threading.Thread(target=Media_proccesing)
        thr.daemon = True
        thr.start()
        
@dp.callback_query_handler(text="rf_medium", state = "*")
async def inlines(callback: types.CallbackQuery):
    global config
    await bot.answer_callback_query(callback.id, text='')
    print()
    print()

    image = f"Downloaded\\{callback.message.chat.id}.jpg"
    key = (callback.message.chat.id, callback.from_user.id)

    temp_data = {"path": image, "render_data": 20, "from":key, "artistic":config.get(str(callback.from_user.id))}
    Work_Queue.Push(temp_data)
    await bot.send_message(callback.message.chat.id ,text=f"вы добавлены в очередь - {len(Work_Queue._values)}⏳")

    if not Media_proc:
        thr = threading.Thread(target=Media_proccesing)
        thr.daemon = True
        thr.start()
        

@dp.callback_query_handler(text="rf_hight", state = "*")
async def inlines(callback: types.CallbackQuery):
    global config
    await bot.answer_callback_query(callback.id, text='')
    print()
    print()

    image = f"Downloaded\\{callback.message.chat.id}.jpg"
    key = (callback.message.chat.id, callback.from_user.id)

    temp_data = {"path": image, "render_data": 40, "from": key,  "artistic":config.get(str(callback.from_user.id))}
    Work_Queue.Push(temp_data)
    await bot.send_message(callback.message.chat.id ,text=f"вы добавлены в очередь - {len(Work_Queue._values)}⏳")

    if not Media_proc:
        thr = threading.Thread(target=Media_proccesing)
        thr.daemon = True
        thr.start()
        

def Media_proccesing():
    global Media_proc
    Media_proc = True
    print(f'\n\n{str(datetime.datetime.now().hour)}:{str(datetime.datetime.now().minute)}:{str(datetime.datetime.now().second)} запуск обработки\n\n')
    torch.backends.cudnn.benchmark = True
    print(threading.active_count())
    stats = ([0.7137, 0.6628, 0.6519],[0.2970, 0.3017, 0.2979])
    while not Work_Queue.isEmpty():
        data = Work_Queue.Pop()
        colorizer = get_image_colorizer(artistic=data["artistic"],stats=stats)
        requests.post("https://api.telegram.org/bot"+token+"/sendMessage?chat_id=" + str(data["from"][0]) + f'&text=начинаю обработку🌄')
        print(f'{str(datetime.datetime.now().hour)}:{str(datetime.datetime.now().minute)}:{str(datetime.datetime.now().second)} начинаю обработку для {data["from"][1]}')
        colorizer.plot_transformed_image(data["path"], render_factor=data["render_data"], display_render_factor=True, watermarked=False, post_process=True, figsize=(8,8)) # Image
        files = {'photo': open(f"result_images\\{data['from'][0]}.jpg", 'rb')}
        #await bot.send_photo(data["from"][0], img)
        r = requests.post("https://api.telegram.org/bot"+token+"/sendPhoto?chat_id=" + str(data["from"][0]) + f'&caption=/begin чтобы загрузить ещё файлы для работы!', files=files)
        print(f'{str(datetime.datetime.now().hour)}:{str(datetime.datetime.now().minute)}:{str(datetime.datetime.now().second)} обработка завершена для {data["from"][1]}')
        print(f"RenderFactor = {data['render_data']}\nArtistic = {data['artistic']}\nQueue = {Work_Queue._values}")
        #requests.post("https://api.telegram.org/bot"+token+"/sendMessage?chat_id=" + str(data["from"][0]) + f'&text=/begin чтобы загрузить ещё файлы для работы!')
        torch.cuda.empty_cache()
    Media_proc = False

'''
@dp.message_handler(content_types=['video'], state=Form.vid)
async def photo_handl(message : types.message, state: Form.vid):
    file_info = await bot.get_file(message.video[-1].file_id)
    await message.video[-1].download(file_info.file_path.split('photos/')[1])
    Form.next()
    await message.answer("Видео успешно скачано!")
'''

@dp.message_handler()
async def message_handl(message : types.Message):
    if message.text == "hi":
        await message.answer("приветики 😁")

    if message.text.lower() == "привет":
        await message.answer("приветики 😁")
    #await message.answer(message.text)
    #await message.reply(message.text)
    #await bot.send_message(message.from_user.id, message.text)

if __name__ == '__main__':
    try:
        executor.start_polling(dp, skip_updates=True)     
    except Exception as e:
        with open("logs.txt", "a") as f:
            f.write(f"Error:{e}\n")
