# -*- coding: utf-8 -*-
"""
Author(s): Kyle Kirby
Date edited: 2/25/2016

UIC Veterans in Engineering present... Smart Mirror

This python script is meant to be outputted to a monitor placed behind a 2 way mirror. It can be interacted with
if combined with a touch screen monitor. In order to pull current weather and calendar information, an internet connection is
required.



Must install the following to run:
-pillow: pip install Pillow
-pyowm: pip install pyowm
-google calendar api: pip install --upgrade google-api-python-client
-roboto / roboto condensed fonts
"""


from tkinter import *
from datetime import *
from io import BytesIO
from urllib.request import urlopen
from PIL import Image, ImageTk
import pyowm
import httplib2
import os
from calendar import monthrange
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

CUR_DIR = os.path.normcase(os.path.abspath(os.getcwd()))
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/self.readonly'
CLIENT_SECRET_FILE = os.path.normcase('gcalendar\\client_secret.json')
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
CALENDAR_ROWS = 6

# get_credentials is provided by google for their calendar api
def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def update_weather():
    owm = pyowm.OWM('ae1e2db8430532af4ab28ffd1bf45697')
    observation = owm.weather_at_place('Chicago,IL')
    return observation.get_weather()


def update_time():
    current_time = datetime.now().isoformat()
    year, month, day = current_time.split('-')
    day, hours = day.split('T')
    hours, minutes, seconds = hours.split(':')
    return year, month, day, hours, minutes, seconds


def image_from_site(url):
    u = urlopen(url)
    raw_data = u.read()
    u.close()
    return Image.open(BytesIO(raw_data))

class Clock(object):
    year, month, day, hours, minutes, seconds = update_time()

    def __init__(self, master):
        self.root = master
        self.clockFrame = Frame(master, bg='black')
        self.clockFrame.pack(side=RIGHT, anchor=NE)

        self.clockW = Label(self.clockFrame, text=" ", bg="black", fg="white", font=('roboto', 90))
        self.clockW.pack(anchor=NE)

        self.dateW = Label(self.clockFrame, text=" ", bg='black', fg='white', font=('roboto condensed', 30))
        self.dateW.pack(anchor=NE)
        self.update_clock()  # updates clock frame (time and date) every ~1 second

    def update_clock(self):
        self.year, self.month, self.day, self.hours, self.minutes, self.seconds = update_time()
        current_weekday = date(int(self.year), int(self.month), int(self.day)).weekday()
        self.clockW.configure(text=self.hours+":"+self.minutes)
        self.dateW.configure(text=WEEKDAYS[current_weekday] + ", " + MONTHS[int(self.month) - 1] + " " + self.day)
        self.root.after(1000, self.update_clock)


class Weather(object):
    def __init__(self, master):
        self.root = master
        self.weatherFrame = Frame(master, bg='black')
        self.weatherFrame.pack(side=LEFT, anchor=NW)
        self.current_tempW = Label(self.weatherFrame, image=ImageTk.PhotoImage(Image.open(CUR_DIR+os.path.normcase("\\icons\\01d.png"))), text=" ", compound=LEFT, font=('roboto', 40), bg='black', fg='white')
        self.current_tempW.pack()
        self.max_tempW = Label(self.weatherFrame, text=" ", font=('roboto', 20), bg='black', fg='white')
        self.max_tempW.pack(anchor=W)
        self.min_tempW = Label(self.weatherFrame, text=" ", font=('roboto', 20), bg='black', fg='white')
        self.min_tempW.pack(anchor=W)
        self.humidityW = Label(self.weatherFrame, text=" ", font=('roboto', 20), bg='black', fg='white')
        self.humidityW.pack(anchor=W)
        self.update_weather_data()  # updates weather frame every ~30 minutes

    def update_weather_data(self):
        try:  # update weather from online data
            current_weather = update_weather()
            temperatures = current_weather.get_temperature('fahrenheit')
            current_temp = temperatures['temp']
            weather_icon_name = current_weather.get_weather_icon_name()
            try:  # retrieve image from local directory
                weather_icon = Image.open(CUR_DIR+os.path.normcase(("\\icons\\"+weather_icon_name+".png")))
                weather_icon = weather_icon.resize((200, 200), Image.ANTIALIAS)
                weather_icon_tk = ImageTk.PhotoImage(weather_icon)
                self.current_tempW.configure(image=weather_icon_tk, text=str(int(current_temp)) + "°")
            except:  # if it cannot be found, get it online
                weather_icon_url = "http://openweathermap.org/img/w/" + weather_icon_name + ".png"
                weather_icon = image_from_site(weather_icon_url)
                weather_icon = weather_icon.resize((100, 100), Image.ANTIALIAS)
                weather_icon_tk = ImageTk.PhotoImage(weather_icon)
                self.current_tempW.configure(image=weather_icon_tk, text=str(int(current_temp)) + "°")
            self.current_tempW.image = weather_icon_tk  # reference the image so it does not get destroyed by garbage collector
            max_temp = temperatures['temp_max']
            self.max_tempW.configure(text="High: "+str(int(max_temp))+"°")
            min_temp = temperatures['temp_min']
            self.min_tempW.configure(text="Low:  "+str(int(min_temp))+"°")
            self.humidityW.configure(text="Humidity: "+str(int(current_weather.get_humidity()))+"%")
        except:  # could not get online weather data
            print(Clock.year + Clock.month + Clock.day + " at " + Clock.hours + ":" + Clock.minutes + " could not update weather data.")
        self.root.after(1800000, self.update_weather_data)


class Calendar(object):
    def __init__(self, master, clock):
        self.root = master
        padx = 20
        pady = 20
        width = 3
        height = 3
        font = ('Roboto', 8)

        self.calendarYear, self.calendarMonth, self.calendarDay, self.calendarHours, self.calendarMinutes, self.calendarSeconds = update_time()
        self.calendarYear, self.calendarMonth, self.calendarDay, self.calendarHours, self.calendarMinutes, self.calendarSeconds = int(
            self.calendarYear), int(self.calendarMonth), int(self.calendarDay), int(self.calendarHours), int(
            self.calendarMinutes), float(self.calendarSeconds)
        self.week_ranges = []
        self.current_week_index = 0
        for i in range(0, CALENDAR_ROWS):
            self.week_ranges.append(range(0 + i * 7, 7 + i * 7))
            if self.calendarDay in self.week_ranges[i]:
                self.current_week_index = i
        self.month_start_weekday = self.find_month_start_weekday()
        self.month_end_week_index = self.find_week_index(self.calendarDay, self.month_start_weekday)
        self.calendarFrame = Frame(clock.clockFrame, bg='black')
        self.calendarFrame.pack(side=TOP, anchor=NW, fill=BOTH)

        # buttons

        # buttons displayed when month is showing
        self.calendarMonthButtonsFrame = Frame(self.calendarFrame, bg='black')
        self.previous_month_button = Button(self.calendarMonthButtonsFrame, text="<<", command=self.previous_month,
                                            bg='black',
                                            fg='white', font=font)
        self.previous_month_button.pack(side=LEFT, anchor=NW)
        self.calendarMonth_label = Label(self.calendarMonthButtonsFrame,
                                         text=MONTHS[self.calendarMonth - 1] + " " + str(self.calendarYear), bg='black',
                                         fg='white', font=font)
        self.calendarMonth_label.pack(side=LEFT, anchor=NW)
        self.next_month_button = Button(self.calendarMonthButtonsFrame, text=">>", command=self.next_month,
                                        bg='black', fg='white', font=font)
        self.next_month_button.pack(side=LEFT, anchor=NW)

        self.refreshMonth_button = Button(self.calendarMonthButtonsFrame, text="Refresh", command=self.update_calendar,
                                          bg='black', fg='white', font=font)
        self.refreshMonth_button.pack(side=RIGHT, anchor=NW)
        self.week_button = Button(self.calendarMonthButtonsFrame, text="Show Weekly", command=self.show_week,
                                  bg='black',
                                  fg='white', font=font)
        self.week_button.pack(side=RIGHT, anchor=NW)

        # buttons displayed when week is showing
        self.calendarWeekButtonsFrame = Frame(self.calendarFrame, bg='black')
        self.previous_week_button = Button(self.calendarWeekButtonsFrame, text="<<", command=self.previous_week,
                                           bg='black',
                                           fg='white', font=font)
        self.previous_week_button.pack(side=LEFT, anchor=NW)

        self.next_week_button = Button(self.calendarWeekButtonsFrame, text=">>", command=self.next_week,
                                       bg='black', fg='white', font=font)
        self.calendarWeek_label = Label(self.calendarWeekButtonsFrame,
                                        text=MONTHS[self.calendarMonth - 1] + " " + str(self.calendarYear),
                                        bg='black', fg='white', font=font)
        self.calendarWeek_label.pack(side=LEFT, anchor=NW)
        self.next_week_button.pack(side=LEFT, anchor=NW)
        self.refreshWeek_button = Button(self.calendarWeekButtonsFrame, text="Refresh", command=self.update_calendar,
                                         bg='black', fg='white', font=font)
        self.refreshWeek_button.pack(side=RIGHT, anchor=NW)
        self.month_button = Button(self.calendarWeekButtonsFrame, text="Show Monthly", command=self.show_month,
                                   bg='black', fg='white', font=font)
        self.month_button.pack(side=RIGHT, anchor=NW)

        # weekdaysFrame is a frame displaying names of weekdays above the calendar
        self.weekdaysFrame = Frame(self.calendarFrame)
        self.weekdaysW = []
        for i in range(0, 7):
            self.weekdaysW.append(Label(self.weekdaysFrame, text=WEEKDAYS[(i - 1)], padx=padx, pady=3, relief=RIDGE,
                                        height=1, width=width, bg='black', fg='white', bd=1, font=font))
            self.weekdaysW[i].pack(side=LEFT)

        # monthly calendar, can be accessed as a 2-D array
        frame_index = 0
        self.monthFrame = [Frame(self.calendarFrame, bg='black')]
        self.month_calendar = []
        self.calendar_labels = []
        for i in range(0, CALENDAR_ROWS * 7):
            self.month_calendar.append(Label(self.monthFrame[frame_index], text=str(i + 1), padx=padx, pady=pady,
                                             relief=RIDGE, height=height, width=width, bg='black', fg='white', bd=1,
                                             font=font, wraplength=50, anchor=N))
            self.calendar_labels.append(self.month_calendar[i])
            self.month_calendar[i].pack(side=LEFT)
            self.month_calendar[i].bind('<ButtonPress-1>', self.calendar_swipe)
            self.month_calendar[i].bind('<ButtonRelease-1>', self.calendar_swipe)
            if i == 6 or i == 13 or i == 20 or i == 27 or i == 34:  # if we have reached the end of a week, increment frame_index and add another row (another week) to monthFrame
                frame_index += 1
                self.monthFrame.append(Frame(self.calendarFrame, bg='black'))
        # calendar_day_frame is the frame which contains the data for the individual day when you click on a day ,
        # day_weekday is the label on top that shows the day of the week
        # calendar_day_labels will have labels appended to it for the date and each event
        self.calendar_day_frame = Frame(self.calendarFrame, bg='black')
        self.day_weekday = Label(self.calendar_day_frame, text=" ", padx=padx, pady=10,
                                 relief=RIDGE, width=7, bg='black', fg='white', bd=1, font=("Roboto",12))
        self.day_weekday.bind('<ButtonPress-1>', self.swipe_day)
        self.day_weekday.bind('<ButtonRelease-1>', self.swipe_day)
        self.calendar_day_labels = []
        self.day_weekday.pack(anchor=N, fill=X)
        self.is_showing_month = False
        self.is_showing_day = False
        # init swipe variables
        self.trackingSwipe = False
        self.x1 = 0
        self.y1 = 0
        self.y1 = 0
        self.y2 = 0
        # -------------------

        self.update_calendar_periodic()  # updates calendar every ~24 hours
        self.show_week()  # by default the monthly calendar is shown
        # ===================================================== End Calendar Frame =================================================

    def update_calendar(self):
        self.month_start_weekday = self.find_month_start_weekday()
        month_end_date = monthrange(self.calendarYear, self.calendarMonth)[1]

        for i in range(0, CALENDAR_ROWS * 7):  # repopulate calendar with correct dates
            if i < self.month_start_weekday or i > month_end_date - 1 + self.month_start_weekday:
                self.month_calendar[i].config(text=" ")
            else:
                self.month_calendar[i].config(text=str(i + 1 - self.month_start_weekday))

        self.current_week_index = self.find_week_index(self.calendarDay, self.month_start_weekday)
        self.month_end_week_index = self.find_week_index(month_end_date, self.month_start_weekday)
        # get data from google calendar api and update calendar with events
        try:
            credentials = get_credentials()
            http = credentials.authorize(httplib2.Http())
            service = discovery.build('calendar', 'v3', http=http)
            now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            eventsResult = service.events().list(
                calendarId='primary',
                timeMin=str(self.calendarYear) + "-" + str(self.calendarMonth) + "-" + "01" + now[10:], maxResults=31,
                singleEvents=True, orderBy='startTime').execute()
            events = eventsResult.get('items', [])
            # update calendar with events from google calendar api
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                if int(start[5:7]) == self.calendarMonth:
                    event_day = int(start[8:10])
                    event_time = start[11:16]

                    hour = int(start[11:13])
                    if hour > 12:
                        hour -= 12
                        event_time = str(hour) + start[13:16]
                        event_time += " pm"
                    elif hour == 12:
                        event_time += " pm"
                    elif hour < 10:
                        event_time = start[12:16] + " am"
                    else:
                        event_time += " am"
                    current_text = self.month_calendar[event_day + self.month_start_weekday - 1].cget("text")
                    self.month_calendar[event_day + self.month_start_weekday - 1].config(
                        text=current_text + "\n" + event_time + ": " + event['summary'])

        except:
            print(
                Clock.year + Clock.month + Clock.day + " at " + Clock.hours + ":" + Clock.minutes + " could not gather calendar data.")

    def find_month_start_weekday(self):

        month_start_weekday = date(self.calendarYear, self.calendarMonth, 1).weekday() + 1

        if month_start_weekday == 7:  # if starting weekday is sunday, make index = 0
            month_start_weekday = 0
        return month_start_weekday

    def find_week_index(self, day, month_start_weekday):

        for i in range(0, CALENDAR_ROWS):  # find current week in the calendar given the calendar day
            if (day + month_start_weekday - 1) in self.week_ranges[i]:
                return i
        return 0

    def update_month_label(self):
        self.calendarMonth_label.config(text=MONTHS[self.calendarMonth - 1] + " " + str(self.calendarYear))
        self.calendarWeek_label.config(text=MONTHS[self.calendarMonth - 1] + " " + str(self.calendarYear))

    def update_calendar_periodic(self):
        if date(int(Clock.year), int(Clock.month), int(Clock.day)).weekday() + 1 == 7:  # if it is sunday, update calendar to current day
            self.calendarYear, self.calendarMonth, self.calendarDay, self.calendarHours, self.calendarMinutes, self.calendarSeconds = update_time()
            self.calendarYear, self.calendarMonth, self.calendarDay, self.calendarHours, self.calendarMinutes, self.calendarSeconds = int(
                self.calendarYear), int(self.calendarMonth), int(self.calendarDay), int(self.calendarHours), int(
                self.calendarMinutes), float(self.calendarSeconds)
            if not self.is_showing_month:
                self.show_week()
            else:
                self.show_month()
            self.update_month_label()
        self.update_calendar()
        self.root.after(86400000, self.update_calendar_periodic)

    def next_month(self):
        temp_month = self.calendarMonth
        temp_year = self.calendarYear
        self.calendarMonth += 1
        if self.calendarMonth > 12:
            self.calendarMonth = 1
            self.calendarYear += 1
        if self.is_showing_day:
            if self.calendarDay > monthrange(temp_year, temp_month)[1]:
                self.calendarDay -= 7
            self.calendarDay += 7 - monthrange(temp_year, temp_month)[1]
        else:
            self.calendarDay = 1
        self.update_month_label()
        self.update_calendar()

    def previous_month(self):

        self.calendarMonth -= 1
        if self.calendarMonth < 1:
            self.calendarMonth = 12
            self.calendarYear -= 1
        if self.is_showing_day:
            if self.calendarDay < 1:
                self.calendarDay += 7
            self.calendarDay += monthrange(self.calendarYear, self.calendarMonth)[1] - 7
        else:
            self.calendarDay = monthrange(self.calendarYear, self.calendarMonth)[1]

        self.update_month_label()
        self.update_calendar()

    def next_week(self):
        self.current_week_index += 1
        self.calendarDay += 7
        if self.current_week_index > self.month_end_week_index:
            self.next_month()
            self.current_week_index = 0
        if not self.is_showing_day:
            self.show_week()
        else:
            self.current_week_index = self.find_week_index(self.calendarDay, self.month_start_weekday)

    def previous_week(self):
        self.current_week_index -= 1
        self.calendarDay -= 7
        if self.current_week_index < 0 or self.calendarDay < 1:
            self.previous_month()
            self.current_week_index = self.month_end_week_index
        if not self.is_showing_day:
            self.show_week()
        else:
            self.current_week_index = self.find_week_index(self.calendarDay, self.month_start_weekday)

    def next_year(self):
        self.calendarYear += 1
        self.calendarDay = monthrange(self.calendarYear, self.calendarMonth)[1]
        self.update_month_label()
        self.update_calendar()

    def previous_year(self):
        self.calendarYear -= 1
        self.calendarDay = monthrange(self.calendarYear, self.calendarMonth)[1]
        self.update_month_label()
        self.update_calendar()

    def next_day(self):
        self.calendarDay += 1
        if self.calendarDay > monthrange(self.calendarYear, self.calendarMonth)[1]: # second element of monthrange() tuple is the number of days in the month
            self.calendarDay -= 1
            self.next_month()  # if we went past the last day of the month, go to first day of next month
            self.show_day(Event, self.calendar_labels[self.month_start_weekday])
        else:
            self.show_day(Event, self.calendar_labels[self.calendarDay+self.month_start_weekday-1])

    def previous_day(self):
        self.calendarDay -= 1
        if self.calendarDay < 1:
            self.calendarDay += 1
            self.previous_month()  # if we went past the first day of the month, go to last day of previous month
            self.calendarDay = self.month_start_weekday+monthrange(self.calendarYear, self.calendarMonth)[1]
            self.show_day(Event, self.calendar_labels[self.month_start_weekday+monthrange(self.calendarYear, self.calendarMonth)[1]])
        else:
            self.show_day(Event, self.calendar_labels[self.calendarDay + self.month_start_weekday - 1])

    def swipe_day(self, event):
        MIN_SWIPE_DISTANCE = 30
        if int(event.type) == 4 and self.trackingSwipe is False:  # if event is button (button press)
            self.x1 = event.x_root
            self.y1 = event.y_root
            self.trackingSwipe = True
        elif int(event.type) == 5 and self.trackingSwipe is True:  # if event is buttonRelease
            self.x2 = event.x_root
            self.y2 = event.y_root
            self.trackingSwipe = False
            if self.x2 > self.x1 + MIN_SWIPE_DISTANCE:  # swipe right
                self.previous_day()
                # previous day
            elif self.x2 < self.x1 - MIN_SWIPE_DISTANCE:  # swipe left
                self.next_day()
                # next day
            elif self.y2 > self.y1 + MIN_SWIPE_DISTANCE:  # swipe down
                self.previous_week()
                self.show_day(Event, self.calendar_labels[self.calendarDay + self.month_start_weekday - 1])
                # previous week
            elif self.y2 < self.y1 - MIN_SWIPE_DISTANCE:  # swipe up
                self.next_week()
                self.show_day(Event, self.calendar_labels[self.calendarDay + self.month_start_weekday - 1])
                # next week
            else:  # the user did not swipe a large enough distance for it to be a valid swipe
                if self.is_showing_month:
                    self.show_month()
                else:
                    self.show_week()

    def show_day(self, event=Event, day_widget=Label):
        if self.is_showing_day:
            day_text = day_widget.cget("text")
        else:
            day_text = event.widget.cget("text")
        if day_text == " ":  # base case where calendar day clicked has no contents
            return
        self.is_showing_day = True
        self.weekdaysFrame.pack_forget()
        self.calendarMonthButtonsFrame.pack_forget()
        self.calendarWeekButtonsFrame.pack_forget()
        for i in range(0, CALENDAR_ROWS):
            self.monthFrame[i].pack_forget()
        lines = day_text.split("\n")
        for i in range(0, len(self.calendar_day_labels)):
            self.calendar_day_labels[0].pack_forget()
            del self.calendar_day_labels[0]
        self.calendarDay = int(lines[0])  # set calendarDay = the day selected
        i = 0
        bg_colors = ('#292929', 'black')
        for index in range(1, len(lines)):
            time_index = lines[index].find("m")  # finds index of first m, which would be the m in am or pm
            time_text = lines[index][0:time_index+1]  # would look like "8:00 am"
            event_text = lines[index][time_index+3:49]  # the rest of the text is the event

            # add new frame for event
            self.calendar_day_labels.append(Frame(self.calendar_day_frame, bg='black'))
            self.calendar_day_labels[i].pack(anchor=N, fill=X)
            i+=1
            # add event time to event frame
            self.calendar_day_labels.append(Label(self.calendar_day_labels[i-1], text=time_text, padx=2, pady=5, anchor=W,
                                                  relief=RIDGE, height=2, width=8, bg=bg_colors[(index+1)%2], fg='white', bd=1,
                                                  font=('Roboto', 14)))
            self.calendar_day_labels[i].pack(anchor=N, fill=X, side=LEFT)
            self.calendar_day_labels[i].bind('<ButtonPress-1>', self.swipe_day)
            self.calendar_day_labels[i].bind('<ButtonRelease-1>', self.swipe_day)
            i+=1
            # add event description to event frame
            self.calendar_day_labels.append(Label(self.calendar_day_labels[i-2], text=event_text, padx=2, pady=5, anchor=E,
                                                  relief=RIDGE, height=2, width=20, bg=bg_colors[(index+1)%2], fg='white', bd=1,
                                                  font=('Roboto', 14), wraplength=210))
            self.calendar_day_labels[i].pack(anchor=N, fill=X, side=RIGHT)
            self.calendar_day_labels[i].bind('<ButtonPress-1>', self.swipe_day)
            self.calendar_day_labels[i].bind('<ButtonRelease-1>', self.swipe_day)
            i+=1

        self.day_weekday.config(text=WEEKDAYS[date(self.calendarYear, self.calendarMonth, self.calendarDay).weekday()]+
                                ", "+MONTHS[self.calendarMonth-1]+" "+str(self.calendarDay)+", "+str(self.calendarYear))

        self.calendar_day_frame.pack(anchor=N, fill=BOTH)

    def calendar_swipe(self, event):  # check if user swiped, take action accordingly
        MIN_SWIPE_DISTANCE = 50
        if int(event.type) == 4 and self.trackingSwipe is False:  # if event is button (button press)
            self.x1 = event.x_root
            self.y1 = event.y_root
            self.trackingSwipe = True
        elif int(event.type) == 5 and self.trackingSwipe is True:  # if event is buttonRelease
            self.x2 = event.x_root
            self.y2 = event.y_root
            self.trackingSwipe = False
            if self.x2 > self.x1+MIN_SWIPE_DISTANCE:  # swipe right

                if self.is_showing_month:
                    self.previous_month()
                else:
                    self.previous_week()
            elif self.x2 < self.x1-MIN_SWIPE_DISTANCE:  # swipe left
                if self.is_showing_month:
                    self.next_month()
                else:
                    self.next_week()
            elif self.y2 > self.y1+MIN_SWIPE_DISTANCE:  # swipe down
                self.next_year()
            elif self.y2 < self.y1-MIN_SWIPE_DISTANCE:  # swipe up
                self.previous_year()
            else:  # the user did not swipe a large enough distance for it to be a valid swipe
                self.show_day(event)

    def show_month(self, event=Event):
        self.calendar_day_frame.pack_forget()
        self.weekdaysFrame.pack_forget()
        self.calendarWeekButtonsFrame.pack_forget()
        self.calendarMonthButtonsFrame.pack(side=TOP, anchor=NW, fill=X)
        self.weekdaysFrame.pack(anchor=W, fill=BOTH)
        for i in range(0, CALENDAR_ROWS):
            self.monthFrame[i].pack_forget()
        for i in range(0, CALENDAR_ROWS):
            self.monthFrame[i].pack(anchor=W, fill=BOTH)
        self.is_showing_month = True
        self.is_showing_day = False

    def show_week(self, event=Event):
        self.calendar_day_frame.pack_forget()
        self.weekdaysFrame.pack_forget()
        self.calendarMonthButtonsFrame.pack_forget()
        self.calendarWeekButtonsFrame.pack(side=TOP, anchor=NW, fill=X)
        self.weekdaysFrame.pack(anchor=W, fill=BOTH)
        for i in range(0, CALENDAR_ROWS):
            self.monthFrame[i].pack_forget()
        self.monthFrame[self.current_week_index].pack(anchor=W, fill=BOTH)
        self.is_showing_month = False
        self.is_showing_day = False


class App:

    def __init__(self, master):
        self.root = master
        clock = Clock(master)
        weather = Weather(master)
        calendar = Calendar(master, clock)

def config_root():
    root.configure(background='black')
    root.attributes('-fullscreen', True)

root = Tk()
config_root()

app = App(root)

root.mainloop()

