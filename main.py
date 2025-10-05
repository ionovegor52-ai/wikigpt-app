from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.config import Config
import wikipedia
import threading

# Запрос разрешений для Android
try:
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.INTERNET])
except:
    pass

# Настройки для корректной работы клавиатуры
Config.set('kivy', 'keyboard_mode', 'dock')
Config.set('kivy', 'keyboard_anim', True)

# Устанавливаем цвет окна сразу
Window.clearcolor = (0.05, 0.05, 0.1, 1)

class StyledLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self._update_rect, pos=self._update_rect)
        self.markup = True
        self.padding = [dp(15), dp(15)]
        self.background_color = (0.1, 0.1, 0.1, 1)
        
    def _update_rect(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(15)]
            )

class UserMessageLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self._update_rect, pos=self._update_rect)
        self.markup = True
        self.color = (1, 1, 1, 1)
        self.padding = [dp(15), dp(15)]
        
    def _update_rect(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.2, 0.4, 0.8, 1)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(15)]
            )

class ChatMessage(BoxLayout):
    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.padding = [dp(10), dp(5)]
        self.height = dp(80)
        
        if not is_user:
            self.add_widget(Widget(size_hint_x=None, width=dp(40)))
        
        message_container = BoxLayout(
            orientation='vertical',
            size_hint_x=0.8 if is_user else 0.75
        )
        
        header_label = Label(
            text='Вы:' if is_user else 'Ответ:',
            size_hint_y=None,
            height=dp(20),
            color=(0.7, 0.7, 0.7, 1),
            font_size='12sp',
            bold=True
        )
        
        if is_user:
            message_label = UserMessageLabel(
                text=text,
                size_hint_y=None,
                text_size=(None, None),
                halign='left',
                valign='top'
            )
        else:
            message_label = StyledLabel(
                text=text,
                size_hint_y=None,
                text_size=(None, None),
                halign='left',
                valign='top'
            )
        
        message_container.add_widget(header_label)
        message_container.add_widget(message_label)
        self.add_widget(message_container)
        
        if is_user:
            self.add_widget(Widget(size_hint_x=None, width=dp(40)))
        
        Clock.schedule_once(lambda dt: self.update_message_height(message_label), 0.1)
    
    def update_message_height(self, message_label):
        message_label.text_size = (message_label.width - dp(30), None)
        message_label.texture_update()
        
        text_height = message_label.texture_size[1]
        padding_height = dp(30)
        
        total_height = max(dp(60), text_height + padding_height)
        message_label.height = total_height
        self.height = total_height + dp(30)

class ChatApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_history = []
        self.theme = 'dark'

    def build(self):
        self.main_layout = BoxLayout(orientation='vertical', spacing=dp(0))
        self.update_main_background()
        self.main_layout.bind(pos=self.update_main_background, size=self.update_main_background)
        
        self.header_layout = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            padding=[dp(10), dp(5)],
            spacing=dp(10)
        )
        self.update_header_background()
        self.header_layout.bind(pos=lambda inst, val: self.update_header_background(), 
                          size=lambda inst, val: self.update_header_background())
        
        self.theme_button = Button(
            text='светлая',
            size_hint_x=0.2,
            background_color=(0.3, 0.3, 0.5, 1),
            color=(1, 1, 1, 1),
            font_size='12sp',
            background_normal=''
        )
        self.theme_button.bind(on_press=self.toggle_theme)
        
        self.header_label = Label(
            text='Wiki-gpt',
            size_hint_x=0.6,
            color=(1, 1, 1, 1),
            font_size='20sp',
            bold=True
        )
        
        self.new_chat_button = Button(
            text='Новый чат',
            size_hint_x=0.2,
            background_color=(0.3, 0.3, 0.5, 1),
            color=(1, 1, 1, 1),
            font_size='12sp',
            background_normal=''
        )
        self.new_chat_button.bind(on_press=self.new_chat)
        
        self.header_layout.add_widget(self.theme_button)
        self.header_layout.add_widget(self.header_label)
        self.header_layout.add_widget(self.new_chat_button)
        
        self.chat_scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=dp(5),
            bar_color=(0.3, 0.3, 0.3, 1)
        )
        
        self.chat_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            padding=[dp(10), dp(10)]
        )
        self.update_chat_background()
        self.chat_layout.bind(
            pos=lambda inst, val: self.update_chat_background(),
            size=lambda inst, val: self.update_chat_background(),
            minimum_height=self.chat_layout.setter('height')
        )
        
        self.chat_scroll.add_widget(self.chat_layout)
        
        self.input_layout = BoxLayout(
            size_hint_y=None,
            height=dp(70),
            spacing=dp(10),
            padding=[dp(15), dp(10)]
        )
        self.update_input_background()
        self.input_layout.bind(
            pos=lambda inst, val: self.update_input_background(),
            size=lambda inst, val: self.update_input_background()
        )
        
        self.input_field = TextInput(
            hint_text='введите слово...',
            size_hint_x=0.75,
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[dp(15), dp(12)],
            hint_text_color=(0.7, 0.7, 0.7, 1),
            multiline=False,
            font_size='16sp',
            write_tab=False,
            background_normal='',
            background_active=''
        )
        self.input_field.bind(on_text_validate=self.send_message)
        
        send_button = Button(
            text='Поиск',
            size_hint_x=0.25,
            background_color=(0.2, 0.4, 0.8, 1),
            color=(1, 1, 1, 1),
            font_size='16sp',
            background_normal=''
        )
        send_button.bind(on_press=self.send_message)
        
        self.input_layout.add_widget(self.input_field)
        self.input_layout.add_widget(send_button)
        
        self.main_layout.add_widget(self.header_layout)
        self.main_layout.add_widget(self.chat_scroll)
        self.main_layout.add_widget(self.input_layout)
        
        Window.softinput_mode = 'below_target'
        
        return self.main_layout
    
    def update_main_background(self, *args):
        self.main_layout.canvas.before.clear()
        with self.main_layout.canvas.before:
            if self.theme == 'dark':
                Color(0.05, 0.05, 0.1, 1)
            else:
                Color(0.95, 0.95, 0.95, 1)
            Rectangle(pos=self.main_layout.pos, size=self.main_layout.size)
    
    def update_header_background(self, *args):
        self.header_layout.canvas.before.clear()
        with self.header_layout.canvas.before:
            if self.theme == 'dark':
                Color(0.08, 0.08, 0.12, 1)
            else:
                Color(0.85, 0.85, 0.85, 1)
            Rectangle(pos=self.header_layout.pos, size=self.header_layout.size)
    
    def update_chat_background(self):
        self.chat_layout.canvas.before.clear()
        with self.chat_layout.canvas.before:
            if self.theme == 'dark':
                Color(0.05, 0.05, 0.1, 1)
            else:
                Color(0.95, 0.95, 0.95, 1)
            Rectangle(pos=self.chat_layout.pos, size=self.chat_layout.size)
    
    def update_input_background(self):
        self.input_layout.canvas.before.clear()
        with self.input_layout.canvas.before:
            if self.theme == 'dark':
                Color(0.08, 0.08, 0.12, 1)
            else:
                Color(0.85, 0.85, 0.85, 1)
            Rectangle(pos=self.input_layout.pos, size=self.input_layout.size)
    
    def toggle_theme(self, instance):
        if self.theme == 'dark':
            self.theme = 'light'
            self.theme_button.text = 'тёмная'
            self.header_label.color = (0.1, 0.1, 0.1, 1)
            self.theme_button.color = (0.1, 0.1, 0.1, 1)
            self.new_chat_button.color = (0.1, 0.1, 0.1, 1)
            self.input_field.background_color = (0.9, 0.9, 0.9, 1)
            self.input_field.foreground_color = (0.1, 0.1, 0.1, 1)
            self.input_field.hint_text_color = (0.5, 0.5, 0.5, 1)
        else:
            self.theme = 'dark'
            self.theme_button.text = 'светлая'
            self.header_label.color = (1, 1, 1, 1)
            self.theme_button.color = (1, 1, 1, 1)
            self.new_chat_button.color = (1, 1, 1, 1)
            self.input_field.background_color = (0.15, 0.15, 0.2, 1)
            self.input_field.foreground_color = (1, 1, 1, 1)
            self.input_field.hint_text_color = (0.7, 0.7, 0.7, 1)
        
        self.update_main_background()
        self.update_header_background()
        self.update_chat_background()
        self.update_input_background()
    
    def on_start(self):
        Clock.schedule_once(lambda dt: self.new_chat(), 0.1)
    
    def show_welcome_message(self):
        welcome_text = (
            "Добро пожаловать! Я могу найти информацию в Wikipedia. "
            "Напишите слово, чтобы узнать его значение!"
        )
        welcome_msg = ChatMessage(welcome_text, is_user=False)
        self.chat_layout.add_widget(welcome_msg)
        self.chat_history.append(('bot', welcome_text))
    
    def new_chat(self, instance=None):
        self.chat_layout.clear_widgets()
        self.chat_history = []
        self.show_welcome_message()
        self.chat_scroll.scroll_y = 1
        Clock.schedule_once(lambda dt: setattr(self.input_field, 'focus', True), 0.2)
    
    def send_message(self, instance):
        text = self.input_field.text.strip()
        if not text:
            return
        
        self.chat_history.append(('user', text))
        user_message = ChatMessage(text, is_user=True)
        self.chat_layout.add_widget(user_message)
        self.input_field.text = ''
        Clock.schedule_once(self.scroll_to_bottom, 0.1)
        
        loading_msg = ChatMessage('Поиск информации в Wikipedia...', is_user=False)
        self.chat_layout.add_widget(loading_msg)
        self.chat_history.append(('bot', 'Поиск информации...'))
        Clock.schedule_once(self.scroll_to_bottom, 0.1)
        
        threading.Thread(
            target=self.get_wikipedia_answer, 
            args=(text, loading_msg), 
            daemon=True
        ).start()
    
    def get_wikipedia_answer(self, query, loading_msg):
        try:
            wikipedia.set_lang("ru")
            search_results = wikipedia.search(query)
            if not search_results:
                answer = "Информация по данному запросу не найдена в Wikipedia."
            else:
                try:
                    page = wikipedia.page(search_results[0])
                    summary = wikipedia.summary(search_results[0], sentences=3)
                    answer = f"{summary}"
                except wikipedia.DisambiguationError as e:
                    options = ', '.join(e.options[:3])
                    answer = f"Найдено несколько вариантов: {options}."
                except wikipedia.PageError:
                    answer = "К сожелению мы ничего не нашли. Попробуйте изменить запрос."
                except Exception as e:
                    answer = f"Ой, кажется нет интернета."
        except Exception as e:
            answer = f"Ой, кажется нет интернета."
        
        Clock.schedule_once(lambda dt: self.update_message(loading_msg, answer), 0)
    
    def update_message(self, loading_msg, answer):
        self.chat_layout.remove_widget(loading_msg)
        if self.chat_history and self.chat_history[-1][1] == 'Поиск информации...':
            self.chat_history.pop()
        bot_message = ChatMessage(answer, is_user=False)
        self.chat_layout.add_widget(bot_message)
        self.chat_history.append(('bot', answer))
        Clock.schedule_once(self.scroll_to_bottom, 0.1)
    
    def scroll_to_bottom(self, dt):
        self.chat_scroll.scroll_y = 0

if __name__ == '__main__':
    ChatApp().run()
