from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from datetime import datetime, timedelta, date
import os
from docxtpl import DocxTemplate
from kivy.clock import Clock
import sys
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
import calendar
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(base_path)  # cofnij się o jeden katalog
    return os.path.join(base_path, relative_path)

class FormularzKlienta(BoxLayout):
    dzisiejsza_data = StringProperty('')
    koniec_miesiaca = StringProperty('')
    typ_umowy = StringProperty('czas_nieokreslony')
    typ_pokoju = StringProperty('dwuosobowy')
    klient_luxmed = BooleanProperty(False)
    cena_bazowa = NumericProperty(100.0)
    selected_template = None
    wybrany_plik = StringProperty('')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_dir = os.path.join(os.path.expanduser('~'), 'GeneratorUmow')
        self.klienci_dir = os.path.join(self.base_dir, 'klienci')
        os.makedirs(self.klienci_dir, exist_ok=True)
        
        # Ustaw domyślną datę
        self.dzisiejsza_data = datetime.now().strftime('%d.%m.%Y')
        
        # Oblicz ostatni dzień miesiąca
        today = date.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        self.koniec_miesiaca = date(today.year, today.month, last_day).strftime('%d.%m.%Y')
        
        # Ustaw domyślne wartości
        self.typ_umowy = 'czas_nieokreslony'
        self.typ_pokoju = 'dwuosobowy'
        
        # Poczekaj na inicjalizację widgetów
        Clock.schedule_once(self.init_widgets, 0)

    def init_widgets(self, dt):
        # Ustaw datę zakończenia dla czasu nieokreślonego
        self.ustaw_date_zakonczenia(True)
        # Zaktualizuj cenę
        self.update_cena()

    def update_cena(self, *args):
        if hasattr(self, 'ids') and 'cena' in self.ids:
            # Sprawdź czy daty są wypełnione
            if (self.ids.data_przyjecia_pacjenta.text and 
                self.ids.data_zakonczenia_umowy.text):
                self.ids.cena.text = self.oblicz_cene()
            else:
                self.ids.cena.text = "0.00 zł"

    def on_typ_pokoju(self, instance, value):
        self.update_cena()

    def on_typ_umowy(self, instance, value):
        self.update_cena()

    def on_klient_luxmed(self, instance, value):
        self.update_cena()

    def wybierz_szablon(self, instance):
        content = BoxLayout(orientation='vertical')
        
        # Tworzenie file choosera
        file_chooser = FileChooserListView(
            path=os.path.expanduser('~'),
            filters=['*.docx']
        )
        
        # Przyciski
        buttons = BoxLayout(size_hint_y=None, height='40dp')
        btn_cancel = Button(text='Anuluj')
        btn_select = Button(text='Wybierz')
        
        buttons.add_widget(btn_cancel)
        buttons.add_widget(btn_select)
        
        content.add_widget(file_chooser)
        content.add_widget(buttons)
        
        # Tworzenie popup
        popup = Popup(
            title='Wybierz szablon dokumentu',
            content=content,
            size_hint=(0.9, 0.9)
        )
        
        # Funkcje przycisków
        def on_select(instance):
            if file_chooser.selection:
                self.selected_template = file_chooser.selection[0]
                self.ids.template_label.text = f'Wybrany szablon: {os.path.basename(self.selected_template)}'
            popup.dismiss()
            
        def on_cancel(instance):
            popup.dismiss()
            
        btn_select.bind(on_release=on_select)
        btn_cancel.bind(on_release=on_cancel)
        
        popup.open()
    
    def generuj_dokumenty(self):
        try:
            # Sprawdź tylko wymagane pola
            if not self.ids.imie_nazwisko_zleceniodawcy.text:
                self.ids.message_label.text = 'Błąd: Imię i nazwisko zleceniodawcy jest wymagane'
                self.ids.message_label.color = (1, 0, 0, 1)
                return
            
            if not self.ids.data_przyjecia_pacjenta.text:
                self.ids.message_label.text = 'Błąd: Data przyjęcia pacjenta jest wymagana'
                self.ids.message_label.color = (1, 0, 0, 1)
                return

            # Zbierz dane, używając pustych stringów dla niewypełnionych pól
            dane = {
                'imie_nazwisko_zleceniodawcy': self.ids.imie_nazwisko_zleceniodawcy.text,
                'pesel_zleceniodawcy': self.ids.pesel_zleceniodawcy.text or '',
                'ulica': self.ids.ulica.text or '',
                'kod_pocztowy': self.ids.kod_pocztowy.text or '',
                'data_zawarcia_umowy': self.ids.data_zawarcia_umowy.text or datetime.now().strftime('%d.%m.%Y'),
                'data_przyjecia_pacjenta': self.ids.data_przyjecia_pacjenta.text,
                'data_zakonczenia_umowy': self.ids.data_zakonczenia_umowy.text or '',
                'imie_nazwisko_pacjenta': self.ids.imie_nazwisko_pacjenta.text or '',
                'pesel_pacjenta': self.ids.pesel_pacjenta.text or '',
                'numer_konta_zleceniodawcy': self.ids.numer_konta_zleceniodawcy.text or '',
                'telefon_zleceniodawcy': self.ids.telefon_zleceniodawcy.text or '',
                'email_zleceniodawcy': self.ids.email_zleceniodawcy.text or '',
                'cena': self.oblicz_cene(),
                'cena_slownie': self.liczba_na_slowa(float(self.oblicz_cene().replace(' zł', '').replace(',', '.')))
            }

            # Sprawdź czy wybrano szablon
            if not hasattr(self, 'selected_template'):
                self.ids.message_label.text = 'Błąd: Nie wybrano szablonu'
                self.ids.message_label.color = (1, 0, 0, 1)
                return

            # Utwórz folder dla klienta
            nazwa_folderu = os.path.join(self.klienci_dir, dane['imie_nazwisko_zleceniodawcy'])
            os.makedirs(nazwa_folderu, exist_ok=True)

            try:
                doc = DocxTemplate(self.selected_template)
                doc.render(dane)
                output_path = os.path.join(nazwa_folderu, f"umowa_{dane['imie_nazwisko_zleceniodawcy']}.docx")
                doc.save(output_path)

                # Wyczyść formularz
                self.ids.imie_nazwisko_zleceniodawcy.text = ''
                self.ids.pesel_zleceniodawcy.text = ''
                self.ids.ulica.text = ''
                self.ids.kod_pocztowy.text = ''
                self.ids.data_zawarcia_umowy.text = datetime.now().strftime('%d.%m.%Y')
                self.ids.data_przyjecia_pacjenta.text = datetime.now().strftime('%d.%m.%Y')
                if hasattr(self.ids, 'data_zakonczenia_umowy'):
                    nowy_koniec = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                    self.ids.data_zakonczenia_umowy.text = nowy_koniec.strftime('%d.%m.%Y')
                self.ids.imie_nazwisko_pacjenta.text = ''
                self.ids.pesel_pacjenta.text = ''
                self.ids.numer_konta_zleceniodawcy.text = ''
                self.ids.telefon_zleceniodawcy.text = ''
                self.ids.email_zleceniodawcy.text = ''

                self.ids.message_label.text = f'Dokumenty zostały zapisane w:\n{nazwa_folderu}'
                self.ids.message_label.color = (0, 0.7, 0, 1)
            except Exception as e:
                self.ids.message_label.text = f'Błąd: {str(e)}'
                self.ids.message_label.color = (1, 0, 0, 1)

        except Exception as e:
            self.ids.message_label.text = f'Błąd: {str(e)}'
            self.ids.message_label.color = (1, 0, 0, 1)

    def ustaw_date_zakonczenia(self, is_nieokreslony):
        if hasattr(self, 'ids') and 'data_zakonczenia_umowy' in self.ids:
            if is_nieokreslony:  # jeśli zaznaczono umowę na czas nieokreślony
                # Pobierz datę przyjęcia
                data_przyjecia = datetime.strptime(self.ids.data_przyjecia_pacjenta.text, '%d.%m.%Y')
                # Oblicz ostatni dzień miesiąca
                koniec_miesiaca = (data_przyjecia.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                # Konwertuj na string przed przypisaniem
                self.koniec_miesiaca = koniec_miesiaca.strftime('%d.%m.%Y')
                # Ustaw datę w polu tekstowym
                self.ids.data_zakonczenia_umowy.text = self.koniec_miesiaca
            else:  # jeśli zaznaczono umowę na czas określony
                self.ids.data_zakonczenia_umowy.text = ''
            # Po zmianie daty zakończenia, przelicz cenę
            self.update_cena()

    def oblicz_cene(self):
        try:
            # Sprawdź czy daty są w poprawnym formacie i nie są puste
            if not self.ids.data_przyjecia_pacjenta.text or not self.ids.data_zakonczenia_umowy.text:
                return "0.00 zł"
            
            try:
                data_przyjecia = datetime.strptime(self.ids.data_przyjecia_pacjenta.text, '%d.%m.%Y')
                data_konca = datetime.strptime(self.ids.data_zakonczenia_umowy.text, '%d.%m.%Y')
            except ValueError:
                # Jeśli data jest niepoprawna (np. podczas wpisywania), zwróć 0
                return "0.00 zł"
            
            # Ustaw stawki
            if hasattr(self, 'typ_pokoju') and self.typ_pokoju == 'jednoosobowy':
                stawka_miesieczna = 15550
                stawka_dzienna = 600
            else:  # dwuosobowy
                stawka_miesieczna = 7775
                stawka_dzienna = 350
            
            # Oblicz liczbę dni
            liczba_dni = (data_konca - data_przyjecia).days + 1
            
            # Oblicz cenę w zależności od typu umowy
            if hasattr(self, 'typ_umowy') and self.typ_umowy == 'czas_nieokreslony':
                # Dla czasu nieokreślonego liczymy proporcjonalnie z stawki miesięcznej
                ostatni_dzien = (data_przyjecia.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                dni_w_miesiacu = ostatni_dzien.day
                cena = (stawka_miesieczna / dni_w_miesiacu) * liczba_dni
            else:
                # Dla czasu określonego używamy stawki dziennej
                cena = stawka_dzienna * liczba_dni
            
            # Zastosuj zniżkę Luxmed jeśli potrzeba (-10%)
            if hasattr(self, 'klient_luxmed') and self.klient_luxmed:
                cena = cena * 0.9
            
            # Zaokrąglij do 2 miejsc po przecinku
            cena = round(cena, 2)
            
            return f"{cena:.2f} zł"
            
        except Exception as e:
            print(f"Błąd podczas obliczania ceny: {e}")
            return "0.00 zł"

    def liczba_na_slowa(self, liczba):
        try:
            # Zaokrąglij do 2 miejsc po przecinku
            liczba = round(float(liczba), 2)
            
            # Rozdziel na złote i grosze
            zlote = int(liczba)
            grosze = int(round((liczba - zlote) * 100))

            jednosci = ['', 'jeden', 'dwa', 'trzy', 'cztery', 'pięć', 'sześć', 'siedem', 'osiem', 'dziewięć']
            nascie = ['dziesięć', 'jedenaście', 'dwanaście', 'trzynaście', 'czternaście', 'piętnaście', 
                     'szesnaście', 'siedemnaście', 'osiemnaście', 'dziewiętnaście']
            dziesiatki = ['', 'dziesięć', 'dwadzieścia', 'trzydzieści', 'czterdzieści', 'pięćdziesiąt', 
                         'sześćdziesiąt', 'siedemdziesiąt', 'osiemdziesiąt', 'dziewięćdziesiąt']
            setki = ['', 'sto', 'dwieście', 'trzysta', 'czterysta', 'pięćset', 'sześćset', 'siedemset', 
                    'osiemset', 'dziewięćset']

            def konwertuj_liczbe(n):
                if n == 0:
                    return 'zero'
                
                wynik = []
                
                # Tysiące
                if n >= 1000:
                    tys = n // 1000
                    if tys == 1:
                        wynik.append('jeden tysiąc')
                    elif tys % 10 in [2, 3, 4] and (tys % 100 < 10 or tys % 100 > 20):
                        wynik.append(f'{konwertuj_liczbe(tys)} tysiące')
                    else:
                        wynik.append(f'{konwertuj_liczbe(tys)} tysięcy')
                    n = n % 1000
                
                # Setki
                if n >= 100:
                    wynik.append(setki[n // 100])
                    n = n % 100
                
                # Dziesiątki i jedności
                if n > 0:
                    if n < 10:
                        wynik.append(jednosci[n])
                    elif n < 20:
                        wynik.append(nascie[n-10])
                    else:
                        if n % 10 == 0:
                            wynik.append(dziesiatki[n // 10])
                        else:
                            wynik.append(f'{dziesiatki[n // 10]} {jednosci[n % 10]}')
                
                return ' '.join(wynik)

            # Konwertuj złote
            if zlote == 0:
                wynik = 'zero złotych'
            else:
                zl_str = konwertuj_liczbe(zlote)
                if zlote == 1:
                    wynik = 'jeden złoty'
                elif zlote % 10 in [2, 3, 4] and (zlote % 100 < 10 or zlote % 100 > 20):
                    wynik = f'{zl_str} złote'
                else:
                    wynik = f'{zl_str} złotych'

            # Dodaj grosze
            if grosze > 0:
                gr_str = konwertuj_liczbe(grosze)
                if grosze == 1:
                    wynik += ' jeden grosz'
                elif grosze % 10 in [2, 3, 4] and (grosze % 100 < 10 or grosze % 100 > 20):
                    wynik += f' {gr_str} grosze'
                else:
                    wynik += f' {gr_str} groszy'

            return wynik

        except Exception as e:
            print(f"Błąd podczas konwersji liczby na słowa: {e}")
            return "zero złotych"

    def pokaz_instrukcje(self):
        # Kolory dla popupu - jasna kolorystyka
        popup_bg_color = (1, 1, 1, 1)               # Białe tło
        input_bg_color = (0.95, 0.95, 0.95, 1)      # Bardzo jasne tło dla inputów
        text_color = (0.2, 0.2, 0.2, 1)             # Ciemny tekst
        accent_color = (0.2, 0.4, 0.8, 1)           # Niebieski akcent

        content = BoxLayout(orientation='vertical', spacing='10dp', padding='20dp')
        
        with content.canvas.before:
            Color(1, 1, 1, 1)  # Białe tło
            Rectangle(pos=content.pos, size=content.size)
            
        scroll = ScrollView(size_hint=(1, 1))
        variables_grid = GridLayout(cols=1, spacing='5dp', size_hint_y=None)
        variables_grid.bind(minimum_height=variables_grid.setter('height'))
        
        variables = [
            '{{imie_nazwisko_zleceniodawcy}}',
            '{{pesel_zleceniodawcy}}',
            '{{ulica}}',
            '{{kod_pocztowy}}',
            '{{data_zawarcia_umowy}}',
            '{{data_przyjecia_pacjenta}}',
            '{{data_zakonczenia_umowy}}',
            '{{imie_nazwisko_pacjenta}}',
            '{{pesel_pacjenta}}',
            '{{numer_konta_zleceniodawcy}}',
            '{{telefon_zleceniodawcy}}',
            '{{email_zleceniodawcy}}',
            '{{cena}}',
            '{{cena_slownie}}',
            '{{aneks}}',
            '{{pelnomocnik}}',
            '{{pelnomocnik_z_dnia}}'
        ]
        
        for var in variables:
            text_input = TextInput(
                text=var,
                size_hint_y=None,
                height='35dp',
                readonly=True,
                multiline=False,
                background_color=input_bg_color,
                foreground_color=text_color,
                cursor_color=text_color,
                padding=('10dp', '5dp'),
                font_size='14sp',
                halign='center'
            )
            variables_grid.add_widget(text_input)
        
        scroll.add_widget(variables_grid)
        
        close_button = Button(
            text='Zamknij',
            size_hint_y=None,
            height='40dp',
            background_color=accent_color,
            color=(1, 1, 1, 1)
        )
        
        content.add_widget(scroll)
        content.add_widget(close_button)
        
        popup = Popup(
            title='Zmienne w szablonie',
            content=content,
            size_hint=(None, None),
            size=('400dp', '500dp'),
            background='',  # Usuwamy domyślne tło
            background_color=(
                popup_bg_color[0], popup_bg_color[1], popup_bg_color[2], popup_bg_color[3]
            ),
            title_color=text_color,
            separator_color=accent_color
        )
        
        close_button.bind(on_release=popup.dismiss)
        popup.open()

class FormularzApp(App):
    def build(self):
        self.title = 'Magic Contracts'
        return FormularzKlienta()

if __name__ == '__main__':
    FormularzApp().run()