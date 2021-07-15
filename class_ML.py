import config # Важный файл в котором лежат все настройки и списки 
import difflib # Модуль для сравнивания двух строк
from random import choice # Модуль для выбора случайного элемента из списка
import gtts # Модуль для перевода текста в mp3 файл
import pygame as pg # Используется для проигрывания музыки
from datetime import datetime # Модуль для работы с датой и временем
import time # Для задержек
import speech_recognition as sr # Модуль для преобразования звука с микрофона в голос
import os # Модуль для работы с файловой системой
import pickle # Модуль для загрузки моделей ML
import requests # Модуль для обработки URL
from bs4 import BeautifulSoup # Модуль для работы с HTML


class VoiceBotClass():
	"""docstring for VoiceBotClass"""
	DEBUG = True
	news_p = []
	appid = "335b86ce0da0ac179b4bccf8f6c6b5a2"
	fail_pack = 0

	def __init__(self):
		super(VoiceBotClass, self).__init__()
		pg.init()
		self.model = pickle.load(open(config.nameModel, "rb")) # Создаем нашу ML
		self.vect = pickle.load(open(config.nameVectoraizer, "rb")) # Создаем векторайзер
		self.clock = pg.time.Clock()

	def log(self, message : str):
		with open('log.txt', 'a', encoding='utf-8') as f:
			line = f'{datetime.now()} --- {message}\n'
			f.write(line)

	def similarity(self, s1 : list, s2 : str):
		for i in s1:
			matcher = difflib.SequenceMatcher(None, i, s2)
			if matcher.ratio() > 0.6:
				return True
		return False

	def command(self):
		if self.fail_pack > 4:
			rep = choice(config.fraze['plug'])
			
			if self.DEBUG:
				print(rep)

			self.say_message(rep, 0)

			self.log(rep)
			return

		r = sr.Recognizer()
		
		with sr.Microphone() as source:
			# Просто вывод, чтобы мы знали когда говорить
			print("Говорите")
			self.say_message('', 2)
			r.pause_threshold = 1
			# используем adjust_for_ambient_noise для удаления посторонних шумов из аудио дорожки
			r.adjust_for_ambient_noise(source, duration=1)
			audio = r.listen(source)

		try: # Обрабатываем все при помощи исключений
			replica = r.recognize_google(audio, language="ru-RU").lower()
			# Просто отображаем текст что сказал пользователь
			if self.DEBUG:
				print(replica)

			self.log(replica)

			self.fail_pack = 0
			return replica
		# Если не смогли распознать текст, то будет вызвана эта ошибка
		except sr.UnknownValueError:
			print('No command')
			fail_pack += 1
			command()

	def say_date(self, replic):
		date = datetime.now()
		weekday = config.weekday[date.today().weekday()]
		date = str(date).split()
		day, time = date[0].split('-'), date[1].split(':')
		year = f'{config.y1[int(day[0][0])-2]} тысячи {config.y2[int(day[0][1])]} {config.y3[int(day[0][2])-1]} {config.y4[int(day[0][3])-1]} год'

		rep = ''

		if 'дата' in replic:
			rep =	f'{config.days[day[2]]} {config.mons[day[1]]}'
		elif 'день' in replic:
			rep = f'{weekday} {config.days[day[2]]} {config.mons[day[1]]}'
		elif 'год' in replic:
			rep = f'{year}'
		elif 'время' in replic:
			rep = f'{config.hours[time[0]]} часов {config.minuts[time[1]]} минут'

		if self.DEBUG:
			print(rep)
		self.say_message(rep, 0)
		self.log(rep)

	def exit_program(self):
		fraze = choice(config.bot['greetings.bye'])
		if self.DEBUG:
			print(fraze)

		self.say_message(fraze, 0)
		self.log(fraze)
		exit()

	def get_link_news(self):
		self.news_p.clear()
		response = requests.get(config.url_news)
		soup = BeautifulSoup(response.text, 'lxml')
		quotes = soup.find_all('a', class_='list-item__title color-font-hover-only')

		num = 1
		for i in quotes:
			self.news_p.append([i.text, 'https://ria.ru' + i.get('href')])
			print(f'{num})', i.text)
			self.say_message(str(num), False)
			time.sleep(0.2)
			self.say_message(i.text, False)
			num += 1
			if input('Choise this article (y/n)? ') == 'y':
				self.pars_news('https://ria.ru' + i.get('href'))

	def pars_news(self, link_):
		textarea = ''
		response = requests.get(link_)
		soup = BeautifulSoup(response.text, 'lxml')
		quotes = soup.find_all('div', class_="article__text")
		for i in quotes:
			textarea += i.text

		textarea = textarea.split('.')
		for rep in textarea:
			if rep:
				if self.DEBUG:
					print(rep)
				self.say_message(rep, 0)
				self.log(rep)

	def get_rate(self, replic):
		# Парсим всю страницу
		full_page = requests.get(config.DOLLAR_RUB)
		full1_page = requests.get(config.EUR_RUB)
		# Разбираем через BeautifulSoup
		soup = BeautifulSoup(full_page.text, 'lxml')
		soup1 = BeautifulSoup(full1_page.text, 'lxml')

		# Получаем нужное для нас значение и возвращаем его
		convert = soup.find_all("div", class_="currency-table__large-text")
		convert1 = soup1.find_all("div", class_="currency-table__large-text")

		rep = ''

		if 'доллар' in replic:
			rep = f'курс доллара {convert[0].text} рубля'
		elif 'евро' in replic:
			rep = f'курс евро {convert1[0].text} рубля'
		else:
			rep = f'курс доллара {convert[0].text} рубля курс евро {convert1[0].text} рубля'
		
		if self.DEBUG:
			print(rep)
		
		self.say_message(rep, 0)
		self.log(rep)

	def get_sait(self, replic):
		rep = replic.split(' ')[2]
		full_page = requests.get('https://znachenie-slova.ru/' + rep)

		soup = BeautifulSoup(full_page.text, 'lxml')
		i = soup.find("div", class_="voc_def")
		i = i.find_all('p')[1]
		rep = i.text.replace('1. ', '')
		if self.DEBUG:
			print(rep)
		self.say_message(rep, 0)
		self.log(rep)
		return

	def get_weather(self, replic):
		s_city = replic.split(' ')[1]
		res = requests.get("http://api.openweathermap.org/data/2.5/find",
			params={'q': s_city, 'type': 'like', 'units': 'metric', 'APPID': self.appid})
		data = res.json()
		ities = ["{} ({})".format(d['name'], d['sys']['country'])
			for d in data['list']]
		city_id = data['list'][0]['id']
		res = requests.get("http://api.openweathermap.org/data/2.5/weather",
			params={'id': city_id, 'units': 'metric', 'lang': 'ru', 'APPID': self.appid})
		data = res.json()
		cond = data['weather'][0]['description']
		temp = str(int(data['main']['temp']))

		r = f'Сегодня {cond}. Температура воздуха {temp} градусов цельсия'

		if self.DEBUG:
			print(r)
		self.say_message(r, 0)
		self.log(r)
		return

	def clasific_LR(self, replic):
		replic = replic.lower() # Убираем заглавные буквы

		if self.similarity(config.fraze['wiyn'], replic):
			if self.DEBUG:
				print(f"Меня зовут {config.nameBot}")
			self.say_message(f"Меня зовут {config.nameBot}", 0)
			self.log(f"Меня зовут {config.nameBot}")
			return 

		elif self.similarity(config.fraze['date'], replic):
			return self.say_date(replic)

		elif 'что такое' in replic:
			return self.get_sait(replic)

		elif self.similarity(config.fraze['rate'], replic):
			return self.get_rate(replic)

		elif self.similarity(config.fraze['news'], replic):
			return self.get_link_news()

		elif 'погода' in replic:
			return self.get_weather(replic)

		elif self.similarity(config.fraze['func'], replic):
			pass

		class_r = self.model.predict(self.vect.transform([replic]))[0]
        
		# Здесь мы определяем есть ли совпадения между речью человека и нашим датасетом
		maxi = 0

		for mx in self.model.predict_proba(self.vect.transform([replic]))[0]:
			if maxi < mx:
				maxi = mx

		if maxi < 0.1:
			rep = choice(config.fraze['plug'])
			if self.DEBUG:
				print(rep)
			self.say_message(rep, 0)
			self.log(rep)
			return


		if class_r == 'greetings.bye':
			self.exit_program()

		rep = choice(config.bot[class_r])
		if self.DEBUG:
			print(rep)
		self.say_message(rep, 0)
		self.log(rep)
		return

	def say_message(self, message, mode):
		if mode == 1:
			pg.mixer.music.load('error.mp3')
			pg.mixer.music.play(0)
		elif mode == 2:
			pg.mixer.music.load('eva.mp3')
			pg.mixer.music.play(0)
		else:
			tts = gtts.gTTS(text=message, lang='ru')
			tts.save("1.mp3")
			pg.mixer.music.load('1.mp3')
			pg.mixer.music.play(0)

		self.clock.tick(10)
		while pg.mixer.music.get_busy():
			pg.event.poll()
			self.clock.tick(10)

		pg.mixer.music.unload()
		if not mode:
			os.remove("1.mp3")

	def run(self):
		while True:
			try:
				replica = self.command()
				self.clasific_LR(input("Input your fraze: "))
			except Exception as e:
				print(e, type(e))
				self.log(f'{e} {type(e)}')
				self.say_message('', 1)

if __name__ == '__main__':
	Bot = VoiceBotClass()

	while True:
		
		try:
			replica = Bot.command()

			if replica:
				Bot.clasific_LR(replica)

		except Exception as e:
			print(e, type(e))
			Bot.log(f'{e} {type(e)}')
			Bot.say_message('', 1)
