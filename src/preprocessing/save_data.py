"""
전처리 결과 저장 모듈

역할
- 최종 Festival Document를 JSONL로 저장한다.
- reject log를 JSONL로 저장한다.
- 한글이 깨지지 않도록 UTF-8을 사용한다.
"""


# TODO: 리스트 형태의 데이터를 JSONL 파일로 저장하는 함수를 작성한다.
#
# 함수명 예시
# save_jsonl(rows, path)
#
# 해야 할 일
# 1. 저장할 데이터와 출력 경로를 입력받는다.
# 2. UTF-8로 파일을 연다.
# 3. 데이터 하나를 JSON 한 줄로 저장한다.
# 4. 모든 데이터가 한 행씩 기록되도록 한다.
# 5. 한글이 Unicode escape 형태로만 저장되지 않도록 설정한다.
#
# 최종 구조
# 한 줄 = 축제 Document 하나