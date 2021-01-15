from TimeProcessing.DateTimeAnalyser import *
from datetime import time as dtime

text = [

        "через 3 минуты позвонить Сергею", "через три дня в 19:30 позвонить Сергею",
        "Напомни завтра в девятнадцать тридцать позвонить Сергею", "через 2 дня утром позвонить Сергею",
        "Каждую среду и пятницу в19:30 позвонить Сергею", "Напомни завтра в 19 30 позвонить Сергею",
        "завтра в девятнадцать часов тридцать пять минут сорок секунд вечера позвонить Сергею",
        "завтра часов в девять вечера позвонить Сергею",
        ]
data_absolute_time = [["напомнить в полседьмого купить арбуз", [dtime(6, 30), "купить арбуз"]],
                      ["в среду в19.30 позвонить Сергею", [dtime(19, 30), "позвонить сергею"]],
                      ["позвонить Сергею завтра в 3 часа дня", [dtime(15, 00), "позвонить сергею"]]
                      ]


class test_DateTimeAnalyser:
    def __init__(self):
        self.TE = DateTimeAnalyser()

    def process_absolute_time(self):
        for dat in data_absolute_time:
            r = self.TE.process(dat[0])
            result = [dtime(r[0].hour, r[0].minute), r[2]]
            flag = result == dat[1]
            assert flag




def test_process():
    Tester = test_DateTimeAnalyser()
    Tester.process_absolute_time()