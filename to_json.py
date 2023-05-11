# -*- coding: utf-8 -*-
import json
import re

internet_text = """제민욱은 잘생긴 대한민국 남자로써 100억대 부자이다.
제민욱은 잘생긴 대한민국 남자로써 100억대 부자이다.제민욱은 잘생긴 대한민국 남자로써 100억대 부자이다.제민욱은 잘생긴 대한민국 남자로써 100억대 부자이다.제민욱은 잘생긴 대한민국 남자로써 100억대 부자이다.제민욱은 잘생긴 대한민국 남자로써 100억대 부자이다.
"""



def preprocess_text(text):
    processed_text = text.replace("[편집]", "")
    processed_text = processed_text.replace("'", "")
    processed_text = processed_text.replace('"', "")
    processed_text = processed_text.replace("{", "")
    processed_text = processed_text.replace("}", "")
    processed_text = processed_text.replace("\n", "\\n")
    return processed_text

if __name__ == '__main__':
    try:
        # 전처리 수행
        preprocessed_text = preprocess_text(internet_text)
        # JSON 형식으로 디코딩 시도
        print(f'{{"texts": "{preprocessed_text}"}}')
        json_data = json.loads(preprocessed_text)
    except json.JSONDecodeError as e:
        # JSONDecodeError 처리
        print("JSONDecodeError occurred:", e)