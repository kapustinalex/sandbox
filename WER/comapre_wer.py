from WER.wer import *

file_name = '/Users/alex/Documents/shmirev_1000_you_tube.res'
#file_name = '/Users/alex/Documents/kotov_1000_you_tube.res'

result = LoadResults(file_name)
wer_res = WER_calc(Preprocessor(result[0]), Preprocessor(result[1]))
print(wer_res)

# from WER.russian_stt_text_normalization.normalizer import Normalizer
#
# result = list()
# norm = Normalizer(device='cpu', jit_model='russian_stt_text_normalization/jit_s2s.pt')
# str_ = '1 столовая ложка нерафинированным'
# str_ = norm._norm_string(str_)
# print(str_)