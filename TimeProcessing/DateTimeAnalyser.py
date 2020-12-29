from deeppavlov import configs, build_model
from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger, Doc
from rutimeparser import parse, get_clear_text
import re
import time as time_
from datetime import datetime, timedelta, time, date
from razdel import tokenize


class DateTimeAnalyser():
    def __init__(self):
        self.ner_model = build_model(configs.ner.ner_ontonotes_bert_mult, download=False)
        self.segmenter = Segmenter()
        self.morph_vocab = MorphVocab()
        self.emb = NewsEmbedding()
        self.morph_tagger = NewsMorphTagger(self.emb)

    def date_with_year(self, month, day):
        now = self.get_now()
        result = datetime(now.year, month, day).date()
        if result >= now.date():
            return result
        else:
            return datetime(now.year + 1, month, day).date()

    def datetime_with_year(self, month, day, hours=0, minutes=0, seconds=0):
        d = self.date_with_year(month, day)
        t = time(hours, minutes, seconds)
        return datetime.combine(d, t)

    def get_now(self):
        t = time_.strptime(time_.asctime())
        return datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, 0)

    def get_now_time(self):
        t = time_.strptime(time_.asctime())
        return time(t.tm_hour, t.tm_min, 0)

    def normolize_spaces(self, str):
        tokens = list(tokenize(str))
        res = ''
        for t in tokens:
            res = res + t.text + ' '
        res = res[:-1]
        res = re.sub(r'(\d).(\d\d)', r'\1:\2', res)  # немного костыллинга
        res = re.sub(r'(\d\d).(\d\d)', r'\1:\2', res)
        res = re.sub(r'(\d)\s(\d\d)', r'\1:\2', res)  # немного костыллинга
        res = re.sub(r'(\d\d)\s(\d\d)', r'\1:\2', res)
        res = re.sub(r'(\d)\s.\s(\d\d)', r'\1:\2', res)  # немного костыллинга
        res = re.sub(r'(\d\d)\s.\s(\d\d)', r'\1:\2', res)

        # поиск стандартного формата времени
        tt = re.search(r'(\d\d):(\d\d)', res)
        ttt = re.search(r'(\d):(\d\d)', res)
        if tt is None and ttt is None:
            return [res, False]
        else:
            return [res, True]

    def find_repeat_flag(self, tt):
        if tt == 'каждый' or tt == 'по':
            return True
        return False

    def simple_parser(self, res):
        result_date = parse(res, now=self.get_now(), allowed_results=[date])
        result_time = parse(res, now=self.get_now(), allowed_results=[time])
        res_tot = parse(res, now=self.get_now(), allowed_results=[datetime])
        res_text = get_clear_text(res)
        if result_time != self.get_now_time():
            return [result_time, result_date, res_text, True]
        else:
            return [result_time, result_date, res_text, False]
        return

    def parser(self, str_):
        [_Time, _Date, msg, flag] = self.simple_parser(str_)
        if True:
            res = datetime(_Date.year, _Date.month, _Date.day, _Time.hour, _Time.minute, _Time.second)
            if res.date() < self.get_now().date():
                sec_time = res.timestamp()
                res = datetime.fromtimestamp(sec_time + 7 * 24 * 3600)
            return [res, msg]
        else:
            return [None, msg]

    def preprocessor(self, in_str_):
        str_ = in_str_.replace('половину ', 'пол', 1)
        str_ = str_.replace('пол ', 'пол', 1)
        str_ = str_.replace('пол-', 'пол', 1)
        str_ = re.sub(r'(\d)\s(\d\d)', r'\1:\2', str_)
        str_ = re.sub(r'(\d\d)\s(\d\d)', r'\1:\2', str_)
        str_ = re.sub(r'(\d).(\d\d)', r'\1:\2', str_)
        str_ = re.sub(r'(\d\d).(\d\d)', r'\1:\2', str_)
        return str_

    def get_lemms(self, str_):
        string = self.preprocessor(str_)
        lemms = self.get_extended_lemms(string)
        # for
        # if not self.find_repeat_flag(token.lemma):
        # if not token.lemma == 'напомнить':
        #             [num_lemma, flag] = self.convert_token(token.lemma)
        #             if flag:
        #                 res_str = res_str + num_lemma + ' '
        #             else:
        #                 res_str = res_str + token.text + ' '
        #     else:
        #         repeat_flag = True
        #     abs_flag = abs_flag or self.is_fixed_day(token.lemma)
        # [norm_str, repeat_flag, lemms] = self.convert_nums(str_)
        # [norm_sp_str, norm_flag] = self.normolize_spaces(norm_str)

        return [lemms]

    def get_time(self, lemms):
        block_word = ['напомнить', 'каждый', 'по']
        conv_lemms = list()
        for ll in lemms:
            [converted_lemms, conv_flag] = self.convert_token(ll[0])
            converted_lemms = converted_lemms.split(' ')
            if conv_flag:
                for c_l in converted_lemms:
                    conv_lemms.append([c_l, c_l])
            else:
                conv_lemms.append(ll)
        string_for_ner = ''
        for ll in conv_lemms:
            if self.is_num(ll[0]) != -1:
                string_for_ner = string_for_ner + ll[0] + ' '
            else:
                string_for_ner = string_for_ner + ll[1] + ' '
        ner_lemms = self.ner_model([string_for_ner])
        res = list()
        not_times = list()
        for i in range(0, len(ner_lemms[0][0])):
            if ner_lemms[1][0][i] == 'I-TIME' or ner_lemms[1][0][
                i] == 'B-TIME':  # or ner_lemms[1][0][i] == 'I-DATE' or ner_lemms[1][0][i] == 'B-DATE':
                res.append([conv_lemms[i][0], i])
            else:
                if conv_lemms[i][0] not in block_word:
                    not_times.append([conv_lemms[i][1], i])
        return [res, not_times]

    def nlp_analyser(self, str_):
        [norm_str, repeat_flag, lemms] = self.convert_nums(str_)
        [norm_sp_str, norm_flag] = self.normolize_spaces(norm_str)
        if lemms[0] == 'через' or lemms[1] == 'через' or lemms[2] == 'через':
            return [norm_sp_str, None]
        nn = ''
        for ll in lemms:
            nn = nn + ll + ' '
        types = self.ner_model([nn])
        times = list()
        indexes = list()
        lemms_ner = list()
        for i in range(0, len(types[0][0])):
            lemms_ner.append(types[0][0][i])
            if types[1][0][i] == 'I-TIME' or types[1][0][i] == 'B-TIME':
                times.append(types[0][0][i])
                indexes.append(i)
        [str_, time_flag] = self.normolize_time_3(times, indexes, lemms, lemms_ner, norm_sp_str)
        print(str_, time_flag)
        return [str_, time_flag]

    def get_norm_date_time(self, str_):
        [ch_time, time_flag] = self.nlp_analyser(str_)
        [res, msg] = self.parser(ch_time)
        if time_flag is not None:
            res = datetime(res.year, res.month, res.day, self.modify_time(res.hour, time_flag), res.minute)
        [l1] = self.get_tokens(str_)
        l1_low = list()
        for ll in l1:
            l1_low.append(ll.lower())
        [l2] = self.get_tokens(msg)
        msg_res = ''
        for ll in l2:
            if l1_low.count(ll) > 0:
                msg_res = msg_res + l1[l1_low.index(ll)] + ' '
        if len(msg_res) > 0:
            msg_res = msg_res[:len(msg_res) - 1]
        return [res, None, msg_res]

    def modify_time(self, dt, str_):
        if str_ == 'утро':
            # 3 12
            if dt != 12:
                dt = dt % 12
        if str_ == 'вечер':
            # 15 - 24
            if dt != 24:
                dt = dt % 12 + 12
        if str_ == 'день':
            # 12 - 18
            dt = dt % 12 + 12
        if str_ == 'ночь':
            # 0 - 3
            dt = dt % 12
        return dt

    def normolize_time_3(self, time_list, indexes, lemms, lemms_ner, norm_sp_str):
        count = 0
        tt_indexes = list()
        time_flag = None
        drop_index = list()
        for i in range(0, len(indexes)):
            if self.is_num(time_list[i]) != -1 or time_list[i] == ':' or time_list[i] == '.':
                count = count + 1
                tt_indexes.append(indexes[i])
            ll = lemms_ner[indexes[i]]
            if ll == 'утро' or ll == 'вечер' or ll == 'ночь' or ll == 'день' or ll == 'час' or ll == 'минута':
                drop_index.append(indexes[i])
            if ll == 'утро' or ll == 'вечер' or ll == 'ночь' or ll == 'день':
                time_flag = ll
        # if count == 1:
        comp_str = ''

        for i in range(0, len(lemms)):
            if i not in drop_index:
                comp_str = comp_str + lemms_ner[i]
                if len(tt_indexes) == 1 and i in tt_indexes:
                    comp_str = comp_str + ':00 '
                else:
                    if i not in tt_indexes or i == tt_indexes[len(tt_indexes) - 1]:
                        comp_str = comp_str + ' '

        comp_str = re.sub(r'(\d)\s(\d\d)', r'\1:\2', comp_str)  # немного костыллинга
        comp_str = re.sub(r'(\d\d)\s(\d\d)', r'\1:\2', comp_str)
        return [comp_str, time_flag]
        # else:
        #     return [None, time_flag, drop_index]

    def normolize_time_2(self, time_list, indexes, lemms):
        count = 0
        tt = list()
        time_flag = None
        drop_index = list()
        for i in range(0, len(indexes)):
            if self.is_num(time_list[i]) != -1:
                count = count + 1
                tt.append(time_list[i])
            ll = lemms[indexes[i]]
            if ll == 'утро' or ll == 'вечер' or ll == 'ночь' or ll == 'день' or ll == 'час' or ll == 'минута':
                time_flag = ll
                drop_index.append(indexes[i])
        # if count == 1:
        return [tt, time_flag, drop_index]
        # else:
        #     return [None, time_flag, drop_index]

    def normilize_time(self, times):
        minutes = 0
        hours = 0
        if len(times) == 2:
            hours = times[0]
            minutes = times[1]
        if len(times) == 3:
            if times[1] == ':' or times[1] == '.':
                hours = times[0]
                minutes = times[2]
        if len(times) > 2:
            h_flag = False
            for t in times:
                if self.is_num(t) != -1:
                    if not h_flag:
                        h_flag = True
                        hours = self.is_num(t)
                    else:
                        minutes = self.is_num(t)
        if times.count('минута') > 0:
            minutes = times[times.index('минута') - 1]
        if times.count('час') > 0:
            hours = times[times.index('час') - 1]
        if times.count('вечер') > 0:
            hours = str((int(hours) % 12 + 12) % 24)
        return [hours, minutes]

    def is_num(self, str):
        try:
            res = int(str)
        except ValueError:
            res = -1
        return res

    def get_tokens(self, str_):
        lemms = list()
        doc = Doc(str_)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        for token in doc.tokens:
            token.lemmatize(self.morph_vocab)
            lemms.append(token.text)
        return [lemms]

    def get_extended_lemms(self, str_):
        doc = Doc(str_)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        lemms = list()
        for token in doc.tokens:
            token.lemmatize(self.morph_vocab)
            lemms.append([token.lemma, token.text])
        return lemms

        # repeat_flag = False
        # abs_flag = False
        # lemms = list()
        # for token in doc.tokens:
        #     token.lemmatize(self.morph_vocab)
        #     lemms.append([token.lemma, token.text])
        #     if not self.find_repeat_flag(token.lemma):
        #         if not token.lemma == 'напомнить':
        #             [num_lemma, flag] = self.convert_token(token.lemma)
        #             if flag:
        #                 res_str = res_str + num_lemma + ' '
        #             else:
        #                 res_str = res_str + token.text + ' '
        #     else:
        #         repeat_flag = True
        #     abs_flag = abs_flag or self.is_fixed_day(token.lemma)
        # return [res_str[:-1], repeat_flag and abs_flag, lemms]

    def convert_token(self, str):
        if str == 'полпервого':
            return ['00 : 30', True]
        if str == 'полвторого':
            return ['01 : 30', True]
        if str == 'полтретьего':
            return ['02 : 30', True]
        if str == 'полчетвертого':
            return ['03 : 30', True]
        if str == 'полпятого':
            return ['04 : 30', True]
        if str == 'полшестого':
            return ['05 : 30', True]
        if str == 'полседьмого':
            return ['06 : 30', True]
        if str == 'полвосьмого':
            return ['07 : 30', True]
        if str == 'полдевятого':
            return ['08 : 30', True]
        if str == 'полдесятого':
            return ['09 : 30', True]
        if str == 'полодиннадцатого':
            return ['10 : 30', True]
        if str == 'полдвенадцатого':
            return ['11 : 30', True]
        if str == 'ноль':
            return ['0', True]
        if str == 'один':
            return ['1', True]
        if str == 'два':
            return ['2', True]
        if str == 'три':
            return ['3', True]
        if str == 'четыре':
            return ['4', True]
        if str == 'пять':
            return ['5', True]
        if str == 'шесть':
            return ['6', True]
        if str == 'семь':
            return ['7', True]
        if str == 'восемь':
            return ['8', True]
        if str == 'девять':
            return ['9', True]
        if str == 'десять':
            return ['10', True]
        if str == 'одининнадцать':
            return ['11', True]
        if str == 'двенадцать':
            return ['12', True]
        if str == 'тринадцать':
            return ['13', True]
        if str == 'четырнадцать':
            return ['14', True]
        if str == 'пятнадцать':
            return ['15', True]
        if str == 'шестнадцать':
            return ['16', True]
        if str == 'семьнадцать':
            return ['17', True]
        if str == 'восемнадцать':
            return ['18', True]
        if str == 'девятнадцать':
            return ['19', True]
        if str == 'двадцать':
            return ['20', True]
        if str == 'тридцать':
            return ['30', True]
        if str == 'сорок':
            return ['40', True]
        if str == 'пятьдесят':
            return ['50', True]
        if str == 'шестьдесят':
            return ['60', True]
        return [str, False]

    def is_fixed_day(self, s):
        if s == 'понедельник': return True
        if s == 'вторник': return True
        if s == 'среда': return True
        if s == 'четверг': return True
        if s == 'пятница': return True
        if s == 'суббота': return True
        if s == 'воскресение': return True
        if s == 'воскресенье': return True
        return False

    # def select_time(self, l_str):

    def find_text(self, data, txt):
        for ind_d in range(0, len(data)):
            if data[ind_d][0] == txt:
                return ind_d
        return -1

    def process(self, tt):
        norm_txt = self.preprocessor(tt)
        lemms = self.get_extended_lemms(norm_txt)
        [times, not_times] = self.get_time(lemms)
        Hour = -1
        Minute = -1
        TimeResult = None
        num_counter = 0
        nums = list()
        separation_flag = False
        times_indexes = list()
        for t in times:
            times_indexes.append(t[1])
        if times.count('в') > 0:
            times.remove('в')
        for t in times:
            if t[0] == ':':
                separation_flag = True
            if self.is_num(t[0]) != -1:
                num_counter = num_counter + 1
                nums.append(t[0])
        # простейший вариант 19:30
        if num_counter == 2 and len(times) == 2:
            Hour = nums[0]
            Minute = nums[1]
        if num_counter == 2 and len(times) == 3 and separation_flag == True:
            Hour = nums[0]
            Minute = nums[1]
        # в 9 часов вечера
        if num_counter == 1:
            if self.find_text(times, 'час') != -1:
                Hour = nums[0]
                Minute = 0
        if num_counter > 2:
            hour_index = self.find_text(times, 'час')
            minute_index = self.find_text(times, 'минута')
            if hour_index > 0:
                Hour = times[hour_index - 1][0]
            if minute_index > 0:
                minutes = 0
                if minute_index > hour_index:
                    for ind in range(hour_index + 1, minute_index):
                        minutes = minutes + int(times[ind][0])
                Minute = minutes
        path_of_day = ''
        if self.find_text(times, 'утро') > 0:
            path_of_day = 'утро'
        if self.find_text(times, 'день') > 0:
            path_of_day = 'день'
        if self.find_text(times, 'вечер') > 0:
            path_of_day = 'вечер'
        if self.find_text(times, 'ночь') > 0:
            path_of_day = 'ночь'

        Hour = self.modify_time(int(Hour), path_of_day)
        TimeResult = str(Hour) + ':'
        if int(Minute) < 10:
            TimeResult = TimeResult + '0' + str(Minute)
        else:
            TimeResult = TimeResult + str(Minute)
        rr = None
        if Hour > 0:
            res_event = ''
            time_pos = times[0][1]
            time_flag = False
            for rs in not_times:
                if time_pos > rs[1]:
                    res_event = res_event + ' ' + rs[0]
                else:
                    if not time_flag:
                        res_event = res_event + ' ' + TimeResult + ' ' + rs[0]
                        time_flag = True
                    else:
                        res_event = res_event + ' ' + rs[0]
            if not time_flag:
                res_event = res_event + ' ' + TimeResult

            rr = self.simple_parser(res_event)
        else:
            rr = self.simple_parser(tt)
        return [datetime(rr[1].year, rr[1].month, rr[1].day, rr[0].hour, rr[0].minute, rr[0].second), None, rr[2]]
