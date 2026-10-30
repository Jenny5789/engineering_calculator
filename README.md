# 공학용 계산기

Python과 Flet으로 만든 공학용 계산기. CASIO 공학용 계산기의 UI를 참고해 설계했고, 입력한 수식을 전처리해 삼각, 로그, 거듭제곱 등 함수를 계산.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flet](https://img.shields.io/badge/Flet-0.80+-02569B?style=for-the-badge)

## 기술 스택

| 구분 | 기술 | 용도 |
|---|---|---|
| 언어 | Python 3 | 전체 코드 |
| 표준 라이브러리 | math, re, sys | 수학 함수, 수식 전처리, 종료 |
| 외부 라이브러리 | flet | UI |

## 구현 역량

관련 이론은 [파이썬 기초 역량 정리](https://github.com/Jenny5789/python/tree/main/study_archive) 참조.

| 역량 | 구현 내용 | 코드 | 이론 |
|---|---|---|---|
| 수식 계산 | 수식 전처리 후 허용 함수만 넘긴 eval 평가 | [핵심 코드](#핵심-코드) | [함수와 lambda](https://github.com/Jenny5789/python/blob/main/study_archive/theory/08_functions.md)<br>[자료형(dict)](https://github.com/Jenny5789/python/blob/main/study_archive/theory/03_data_types.md) |
| 예외 처리 | 괄호 균형 검사, 오류 유형별 메시지 | [핵심 코드](#핵심-코드) | [예외 처리](https://github.com/Jenny5789/python/blob/main/study_archive/theory/13_exceptions.md) |
| 수식 편집 | 커서 위치 기준 문자열 슬라이싱으로 삽입, 삭제 | [engineering_calculator.py](engineering_calculator.py) | [줄 편집기 insert, delete](https://github.com/Jenny5789/python/blob/main/study_archive/data_structures/02_line_editor.py) |
| 상태 관리 | SHIFT, hyp 상태에 따른 버튼 라벨 전환, 계산 기록, 메모리 | [engineering_calculator.py](engineering_calculator.py) | [자료형(list, dict)](https://github.com/Jenny5789/python/blob/main/study_archive/theory/03_data_types.md) |

## 핵심 코드

[engineering_calculator.py](engineering_calculator.py)

```python
# 허용 함수만 담은 딕셔너리 (일부)
SAFE_FUNCTIONS = {
    'sin':  lambda x: math.sin(math.radians(x)),   # 각도(degree) 입력
    'log':  math.log10,
    'sqrt': math.sqrt,
    # ... 생략
}

def preprocess(expr: str) -> str:
    expr = expr.replace("^", "**")
    expr = expr.replace("×", "*")
    expr = re.sub(r'(\d+)!', r'factorial(\1)', expr)
    # ... 생략
    return expr

def calculate(expr: str) -> str:
    try:
        bracket_error = check_brackets(expr)       # 괄호 검사 먼저
        if bracket_error:
            return bracket_error

        processed = preprocess(expr)
        result = eval(processed, {"__builtins__": {}}, SAFE_FUNCTIONS)
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(round(result, 10))
    except ZeroDivisionError:
        return "Error: 0으로 나눌 수 없음"
    except SyntaxError:
        return "Error: 수식 오류"
    # ... 생략
```

- 화면용 기호를 파이썬 문법으로 치환한 뒤 계산
- eval의 내장 함수를 비우고 허용한 함수만 전달해 실행 범위 제한
- 오류 유형별 메시지를 반환해 화면에 원인 표시

## 주요 기능

| 기능 | 설명 |
|---|---|
| 연산 | 사칙연산, 괄호, 거듭제곱, 루트, 로그, Abs, %, π |
| 삼각, 쌍곡선함수 | SHIFT로 역삼각함수, hyp로 쌍곡선함수 전환 |
| 수식 편집 | 방향키로 커서 이동 후 중간 수정, DEL, AC |
| 기록과 메모리 | 위, 아래 방향키로 이전 계산식, M+, RCL, Ans |
| 오류 메시지 | 괄호 오류, 0으로 나눌 수 없음 등 원인 표시 |

<img src="images/screenshot_result.png" width="40%" alt="계산 결과">
<img src="images/screenshot_error1.png" width="40%" alt="괄호 오류">

<details>
<summary>전체 화면 보기</summary>

<img src="images/screenshot.png" width="400" alt="시작 화면">
<img src="images/screenshot_error2.png" width="400" alt="괄호 오류 2">

</details>

## 실행 방법

Python 3.x, Flet 0.80.0 이상.

```
pip install flet
python engineering_calculator.py
```