# механика кнопки Скачать
from tkinter import *
import pytube
from tkinter import messagebox
root = Tk()
def download():
    # пробуем скачать видео по ссылке
    try:
        # формируем адрес
        ytlink=link1.get()
        # переводим его в нужный формат
        youtubelink=pytube.YouTube(ytlink)
        # получаем ссылку на видео с самым высоким качеством
        video=youtubelink.streams.get_highest_resolution()
        # скачиваем видео
        video.download()
        # выводим результат
        Result="Загрузка завершена"
        messagebox.showinfo("Готово",Result)
    # если скачать не получилось
    except:
        # выводим сообщение об ошибке
        Result="Ссылка не работает"
        messagebox.showerror("Ошибка",Result)